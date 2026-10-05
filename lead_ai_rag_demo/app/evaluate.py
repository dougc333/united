from __future__ import annotations

import json
from pathlib import Path

from .retrieval import HybridRetriever


def reciprocal_rank(ids: list[str], expected: set[str]) -> float:
    return next((1 / rank for rank, value in enumerate(ids, start=1) if value in expected), 0.0)


def evaluate(path: Path) -> dict[str, float]:
    retriever = HybridRetriever()
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    totals = {"recall_at_1": 0.0, "recall_at_3": 0.0, "mrr_at_5": 0.0}
    for row in rows:
        ids = [hit.chunk.id for hit in retriever.search(row["query"], k=5)]
        expected = set(row["relevant_chunk_ids"])
        totals["recall_at_1"] += float(bool(set(ids[:1]) & expected))
        totals["recall_at_3"] += float(bool(set(ids[:3]) & expected))
        totals["mrr_at_5"] += reciprocal_rank(ids, expected)
    return {key: value / len(rows) for key, value in totals.items()}


if __name__ == "__main__":
    metrics = evaluate(Path("evals/golden.jsonl"))
    print(json.dumps(metrics, indent=2))
