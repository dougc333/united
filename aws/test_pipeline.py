import json
from io import BytesIO
import unittest
from unittest.mock import patch

import pymupdf
from PIL import Image

from pipeline import clean_html, output_prefix, page_assets, parse_s3_uri, parse_verdict, run_page, word_coverage


class FakeS3:
    def __init__(self):
        self.objects = {}

    def put_object(self, **kwargs):
        self.objects[kwargs["Key"]] = kwargs["Body"]


class PipelineTests(unittest.TestCase):
    def test_s3_paths(self):
        self.assertEqual(parse_s3_uri("s3://demo/input/a.pdf"), ("demo", "input/a.pdf"))
        self.assertEqual(output_prefix("input/a.pdf", None), "processed/a")
        with self.assertRaises(ValueError):
            parse_s3_uri("/tmp/a.pdf")
        with self.assertRaises(ValueError):
            output_prefix("a.pdf", "../other")

    def test_page_split_and_raster(self):
        doc = pymupdf.open()
        for name in ("first", "second"):
            page = doc.new_page(width=400, height=600)
            page.insert_text((25, 50), name)
        pdf, png = page_assets(doc, 1)
        page = pymupdf.open(stream=pdf, filetype="pdf")
        self.assertEqual(len(page), 1)
        self.assertIn("second", page[0].get_text())
        self.assertTrue(png.startswith(b"\x89PNG"))
        page.close()
        doc.close()

    def test_reject_active_html_and_broken_verdict(self):
        self.assertIn("<html", clean_html("```html\n<html><body>OK</body></html>\n```"))
        with self.assertRaises(ValueError):
            clean_html("<html><script>bad()</script></html>")
        with self.assertRaises(ValueError):
            parse_verdict(json.dumps({"equivalent": "true", "issues": []}))

    def test_ocr_coverage_counts_duplicates(self):
        self.assertEqual(word_coverage("Treanda Treanda J9033", "<html>Treanda J9033</html>"), 2 / 3)
        self.assertEqual(word_coverage("Treanda J9033", "<html>Treanda J9033</html>"), 1)

    def test_page_revisions_are_bounded_and_audited(self):
        png = BytesIO()
        Image.new("RGB", (200, 300), "white").save(png, format="PNG")
        s3 = FakeS3()
        llm_answers = iter([
            "<html><body>Treanda</body></html>",
            '{"equivalent": false, "issues": ["J9033 missing"]}',
            "<html><body>Treanda J9033</body></html>",
            '{"equivalent": true, "issues": []}',
        ])
        with patch("pipeline.textract_ocr", return_value=({"Blocks": []}, "Treanda J9033")), \
             patch("pipeline.bedrock_text", side_effect=lambda *args: next(llm_answers)), \
             patch("pipeline.render_html", return_value=png.getvalue()):
            report = run_page(s3, None, None, "bucket", "output", "model", b"%PDF-test",
                              png.getvalue(), 1, max_revisions=1, min_coverage=1)
        self.assertEqual(report["status"], "auto_pass")
        self.assertEqual(len(report["attempts"]), 2)
        self.assertIn("output/page_0001/source_page_1.pdf", s3.objects)
        self.assertIn("output/page_0001/revision_00_side_by_side.png", s3.objects)
        self.assertIn("output/page_0001/final.html", s3.objects)

    def test_unresolved_page_requires_review(self):
        png = BytesIO()
        Image.new("RGB", (200, 300), "white").save(png, format="PNG")
        with patch("pipeline.textract_ocr", return_value=({"Blocks": []}, "Treanda J9033")), \
             patch("pipeline.bedrock_text", side_effect=[
                 "<html><body>Treanda</body></html>",
                 '{"equivalent": true, "issues": []}',
             ]), patch("pipeline.render_html", return_value=png.getvalue()):
            report = run_page(FakeS3(), None, None, "bucket", "output", "model", b"%PDF-test",
                              png.getvalue(), 1, max_revisions=0, min_coverage=1)
        self.assertEqual(report["status"], "review")
        self.assertLess(report["attempts"][0]["coverage"], 1)


if __name__ == "__main__":
    unittest.main()
