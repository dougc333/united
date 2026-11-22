#!/usr/bin/env python3
"""Replace inferred Figure 18 values with a source-faithful semantic table."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup


BASE = Path("/Users/dc/united/pdfs/www.ey.com/content/dam/ey-unified-site/ey-com/en-us/insights/insurance/documents")
STEM = "ey-limra-workforce-benefits-study-final-2025"
sys.path.insert(0, "/Users/dc/united/src")
from ey_docling_pipeline import atomic_json, atomic_write, make_chunks  # noqa: E402


ROWS = [
    ("Quote and implementation", "Self-service/real-time quoting", "48%", "7%", "35%"),
    ("Quote and implementation", "Automated data exchange", "57%", "8%", "24%"),
    ("Quote and implementation", "Digital implementation of a new carrier or benefit", "63%", "9%", "23%"),
    ("Quote and implementation", "Digital submission for evidence of insurability", "65%", "9%", "20%"),
    ("Enrollment", "Decision support tools for employees", "66%", "9%", "21%"),
    ("Enrollment", "Personalized enrollment materials", "74%", "7%", "16%"),
    ("Enrollment", "Digital employee communications on new benefits offerings", "76%", "8%", "13%"),
    ("Enrollment", "E-signature capabilities", "84%", "5%", "9%"),
    ("Enrollment", "Online enrollment", "86%", "7%", "4%"),
    ("Ongoing service", "Live chat/chatbot", "54%", "12%", "23%"),
    ("Ongoing service", "Mobile app (for employer or employees)", "68%", "6%", "20%"),
    ("Ongoing service", "Online eligibility updates", "79%", "5%", "13%"),
    ("Ongoing service", "Online billing and payment", "89%", "5%", "4%"),
    ("Claims", "Same-day claims decisions", "32%", "6%", "52%"),
    ("Claims", "Proactively trigger claims based on medical data", "42%", "7%", "41%"),
    ("Claims", "Real-time integration for claims management with HRIS systems", "51%", "8%", "31%"),
    ("Claims", "Integrated claims experience based on singular event", "58%", "8%", "28%"),
    ("Claims", "Text messaging to employees regarding claims status", "55%", "7%", "26%"),
    ("Claims", "Digital claims submission", "78%", "6%", "12%"),
]


def main() -> None:
    html_path = BASE / f"{STEM}_semantic-corrected.html"
    verification_path = BASE / f"{STEM}_visual-verification.json"
    json_path = BASE / f"{STEM}_docling.json"
    chunks_path = BASE / f"{STEM}_rag-chunks.jsonl"
    manifest_path = BASE / f"{STEM}_pipeline-manifest.json"

    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "lxml")
    page = soup.find(id="page-024")
    figure = page.find("figure")
    for group in figure.find_all("section", recursive=False):
        group.decompose()
    table_markup = BeautifulSoup("""
<table aria-label="Figure 18 chart data">
<caption>Figure 18 chart data. The final two series are visibly present but have no printed values.</caption>
<thead><tr><th>Process</th><th>Technology tool</th><th>Already have and use</th>
<th>Already have but do not use</th><th>Do not have but want</th>
<th>Do not have and do not want</th><th>Don't know</th></tr></thead><tbody></tbody></table>
""", "lxml").find("table")
    tbody = table_markup.find("tbody")
    for group, label, used, unused, wanted in ROWS:
        row = soup.new_tag("tr")
        values = (group, label, used, unused, wanted, "not labeled", "not labeled")
        for value in values:
            cell = soup.new_tag("td")
            cell.string = value
            row.append(cell)
        tbody.append(row)
    figure.append(table_markup)
    atomic_write(html_path, str(soup))

    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    item = next(page for page in verification["pages"] if page["page"] == 24)
    item.update({
        "status": "verified",
        "semantic_table_present": True,
        "summary": item["summary"] + " A deterministic repair converted the chart lists to a table and removed inferred values for unlabeled segments.",
        "unsupported_inferred_values_removed": ["1%", "2%", "3%"],
    })
    item["issues"].append({
        "category": "table_structure",
        "source_evidence": "The final two colored chart segments have no printed numeric labels.",
        "candidate_evidence": "The first visual reconstruction inferred 1%, 2%, and 3% remainder values and used lists instead of a table.",
        "correction": "Removed inferred percentages, represented both unlabeled series as 'not labeled', and created a semantic table.",
    })
    verification["verified_pages"] = 29
    verification["needs_review_pages"] = []
    atomic_json(verification_path, verification)

    document_json = json.loads(json_path.read_text(encoding="utf-8"))
    record = next(page for page in document_json["pages"] if page["page"] == 24)
    record["visual_verification"] = item
    atomic_json(json_path, document_json)

    page_records = []
    for section in soup.select("section.document-page"):
        number = int(section["data-page"])
        metadata = section.find("p", class_="page-metadata")
        if metadata:
            metadata.extract()
        verification_item = next(page for page in verification["pages"] if page["page"] == number)
        page_records.append({
            "page": number,
            "section": section.get("data-section", f"Page {number}"),
            "source_pdf": f"{STEM}_page_{number}.pdf",
            "semantic_html": section.decode_contents(),
            "visual_verification": verification_item,
        })
    chunks = make_chunks(page_records)
    atomic_write(chunks_path, "".join(json.dumps(chunk, ensure_ascii=False) + "\n" for chunk in chunks))

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
        "needs_review_pages": [],
        "chunk_count": len(chunks),
        "postprocessing": [
            "Page 24: converted explicit chart values to a semantic table",
            "Page 24: removed inferred values for unlabeled chart segments",
        ],
    })
    atomic_json(manifest_path, manifest)
    print(json.dumps({"status": "complete", "verified_pages": 29, "chunks": len(chunks)}, indent=2))


if __name__ == "__main__":
    main()
