"""Offline checks for quote validation, page mapping, and retrieval metrics."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.eval_pipeline import (
    append_evals,
    error_path,
    evidence_offsets,
    generate_page_evals,
    grade_ranked,
    load_evals,
    load_page_errors,
    page_spans,
    rank_queries,
    relevant_chunk_ids,
    update_page_error,
)


class FakeResponseClient:
    def __init__(self, data):
        self.responses = self
        self.data = data

    def create(self, **kwargs):
        assert kwargs["store"] is False
        assert kwargs["input"][0]["content"][1]["type"] == "input_image"
        return SimpleNamespace(output_text=json.dumps(self.data))


class EvalPipelineTests(unittest.TestCase):
    def test_page_errors_persist_and_clear(self):
        with tempfile.TemporaryDirectory() as directory:
            path = error_path(Path(directory) / "sample_eval.jsonl")
            update_page_error(path, "digest-a", 1, "ValueError: non-verbatim quote")
            self.assertEqual(load_page_errors(path, "digest-a"),
                             {1: "ValueError: non-verbatim quote"})
            self.assertEqual(load_page_errors(path, "digest-b"), {})
            update_page_error(path, "digest-a", 1, None)
            self.assertEqual(load_page_errors(path, "digest-a"), {})

    def test_full_corpus_ranking(self):
        class FakeModel:
            def encode(self, texts, **kwargs):
                vectors = {"wrong": [1.0, 0.0], "right": [0.0, 1.0], "query": [0.0, 1.0]}
                return [vectors[text] for text in texts]

        chunks = [SimpleNamespace(page_content="wrong"), SimpleNamespace(page_content="right")]
        self.assertEqual(rank_queries([{"query": "query"}], chunks, FakeModel()), [[1, 0]])

    def test_verbatim_quotes_and_three_evals(self):
        rows = [
            {"query": f"Question {i}?", "answer": "Alpha", "evidence_quote": "Alpha policy"}
            for i in range(3)
        ]
        actual = generate_page_evals(FakeResponseClient({"evals": rows}), "test", b"png", "Alpha policy is here", 2)
        self.assertEqual(len(actual), 3)
        self.assertEqual(actual[0]["page_num"], 2)
        rows[0]["evidence_quote"] = "fabricated"
        with self.assertRaises(ValueError):
            generate_page_evals(FakeResponseClient({"evals": rows}), "test", b"png", "Alpha policy is here", 2)

    def test_page_offsets_and_boundary_miss(self):
        pages = [(1, "same target"), (2, "same target approved")]
        self.assertEqual(page_spans(pages), {1: (0, 11), 2: (12, 32)})
        row = {"page_num": 2, "evidence_quote": "same target"}
        self.assertEqual(evidence_offsets(row, pages), [(12, 23)])
        chunks = [
            SimpleNamespace(page_content="same target", metadata={"start_index": 0}),
            SimpleNamespace(page_content="same tar", metadata={"start_index": 12}),
            SimpleNamespace(page_content="target approved", metadata={"start_index": 17}),
            SimpleNamespace(page_content="same target approved", metadata={"start_index": 12}),
        ]
        self.assertEqual(relevant_chunk_ids(row, pages, chunks), {3})
        self.assertFalse(grade_ranked([0, 1, 2], {3})["recall_at_3"])

    def test_metrics(self):
        grade = grade_ranked([4, 2, 1], {1})
        self.assertEqual([grade[f"recall_at_{k}"] for k in (1, 2, 3)], [0, 0, 1])
        self.assertAlmostEqual(grade["mrr_at_3"], 1 / 3)
        self.assertAlmostEqual(grade["ndcg_at_3"], 1 / 2)
        self.assertEqual(grade_ranked([4, 2, 1], set())["ndcg_at_3"], 0)

    def test_jsonl_resume_and_pdf_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test_eval.jsonl"
            append_evals(path, [{"query": "q", "page_num": 1, "pdf_sha256": "one"}])
            self.assertEqual(len(load_evals(path, "one")), 1)
            append_evals(path, [{"query": "replacement", "page_num": 1, "pdf_sha256": "one"}])
            self.assertEqual([row["query"] for row in load_evals(path, "one")], ["replacement"])
            with self.assertRaises(ValueError):
                load_evals(path, "two")


if __name__ == "__main__":
    unittest.main()
