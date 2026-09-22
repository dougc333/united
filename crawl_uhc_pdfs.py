#!/usr/bin/env python3
"""Crawl allowed public uhc.com pages and archive linked PDF documents."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html.parser
import json
import os
import re
import time
import urllib.parse
import urllib.robotparser
import xml.etree.ElementTree as ET
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ROOT = "https://www.uhc.com/"
USER_AGENT = "Mozilla/5.0 (compatible; UHC-PDF-Archive/1.0; +local-research)"
SITEMAP_INDEX = urllib.parse.urljoin(ROOT, "sitemap_index.xml")
ALLOWED_PAGE_HOSTS = {"uhc.com", "www.uhc.com"}


class LinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if value and key.casefold() in {"href", "src", "data-href", "data-url"}:
                self.links.append(value)


def request(url: str, timeout: int = 45) -> tuple[bytes, str, str]:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip()
    return response.content, content_type, response.url


def canonical(url: str, base: str = ROOT) -> str | None:
    absolute = urllib.parse.urljoin(base, url)
    parsed = urllib.parse.urlsplit(absolute)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc.casefold(), path, parsed.query, ""))


def is_pdf_url(url: str) -> bool:
    return urllib.parse.urlsplit(url).path.casefold().endswith(".pdf")


def safe_pdf_path(output_dir: Path, url: str) -> Path:
    parsed = urllib.parse.urlsplit(url)
    parts = [part for part in parsed.path.split("/") if part not in {"", ".", ".."}]
    filename = parts[-1] if parts else "document.pdf"
    parents = parts[:-1]
    if parsed.query:
        digest = hashlib.sha256(parsed.query.encode()).hexdigest()[:10]
        stem, suffix = os.path.splitext(filename)
        filename = f"{stem}-{digest}{suffix or '.pdf'}"
    return output_dir / "pdfs" / parsed.netloc.casefold() / Path(*parents) / filename


def load_robots() -> urllib.robotparser.RobotFileParser:
    body, _, _ = request(urllib.parse.urljoin(ROOT, "robots.txt"))
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(urllib.parse.urljoin(ROOT, "robots.txt"))
    parser.parse(body.decode("utf-8", errors="replace").splitlines())
    return parser


def sitemap_pages(robots: urllib.robotparser.RobotFileParser) -> set[str]:
    sitemap_queue = deque([SITEMAP_INDEX])
    seen_sitemaps: set[str] = set()
    pages: set[str] = {ROOT}
    while sitemap_queue:
        sitemap = sitemap_queue.popleft()
        if sitemap in seen_sitemaps:
            continue
        seen_sitemaps.add(sitemap)
        body, _, final_url = request(sitemap)
        root = ET.fromstring(body)
        locations = [node.text.strip() for node in root.iter() if node.tag.endswith("loc") and node.text]
        if root.tag.endswith("sitemapindex"):
            sitemap_queue.extend(locations)
            continue
        for location in locations:
            url = canonical(location, final_url)
            if not url:
                continue
            host = urllib.parse.urlsplit(url).hostname or ""
            if host in ALLOWED_PAGE_HOSTS and robots.can_fetch(USER_AGENT, url):
                pages.add(url)
    return pages


def download_pdf(url: str, output_dir: Path) -> dict[str, object]:
    destination = safe_pdf_path(output_dir, url)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size:
        return {"url": url, "path": str(destination), "bytes": destination.stat().st_size, "status": "existing"}
    body, content_type, final_url = request(url, timeout=90)
    if content_type != "application/pdf" and not body.startswith(b"%PDF-"):
        raise ValueError(f"not a PDF response ({content_type})")
    destination.write_bytes(body)
    return {"url": final_url, "path": str(destination), "bytes": len(body), "status": "downloaded"}


def write_manifest(output_dir: Path, records: list[dict[str, object]], errors: list[dict[str, str]], pages: int) -> None:
    payload = {
        "root": ROOT,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pages_crawled": pages,
        "pdf_count": len(records),
        "error_count": len(errors),
        "pdfs": sorted(records, key=lambda row: str(row["url"])),
        "errors": errors,
    }
    (output_dir / "manifest.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with (output_dir / "manifest.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["url", "path", "bytes", "status"])
        writer.writeheader()
        writer.writerows(payload["pdfs"])


def crawl(output_dir: Path, max_pages: int | None, workers: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    robots = load_robots()
    pending = deque(sorted(sitemap_pages(robots)))
    seen_pages: set[str] = set()
    pdf_urls: set[str] = set()
    manifest_path = output_dir / "manifest.json"
    previous = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    records_by_url = {
        str(record["url"]): record for record in previous.get("pdfs", [])
    }
    errors: list[dict[str, str]] = list(previous.get("errors", []))
    attempted_pdf_urls = set(records_by_url)
    attempted_pdf_urls.update(
        error["url"] for error in errors if error.get("stage") == "pdf"
    )
    print(f"Seeded {len(pending)} allowed pages from published sitemaps", flush=True)

    with (
        ThreadPoolExecutor(max_workers=workers) as page_executor,
        ThreadPoolExecutor(max_workers=workers) as download_executor,
    ):
        download_futures: dict[object, str] = {}

        def collect_downloads(*, wait_for_all: bool = False) -> None:
            futures = (
                list(as_completed(download_futures))
                if wait_for_all
                else [future for future in download_futures if future.done()]
            )
            for future in futures:
                url = download_futures.pop(future)
                try:
                    record = future.result()
                    records_by_url[str(record["url"])] = record
                except Exception as exc:
                    errors.append(
                        {"url": url, "stage": "pdf", "error": f"{type(exc).__name__}: {exc}"}
                    )

        while pending and (max_pages is None or len(seen_pages) < max_pages):
            batch: list[str] = []
            while pending and len(batch) < workers:
                url = pending.popleft()
                if url in seen_pages or not robots.can_fetch(USER_AGENT, url):
                    continue
                if max_pages is not None and len(seen_pages) + len(batch) >= max_pages:
                    break
                batch.append(url)
            if not batch:
                continue
            seen_pages.update(batch)
            futures = {page_executor.submit(request, url): url for url in batch}
            for future in as_completed(futures):
                url = futures[future]
                try:
                    body, content_type, final_url = future.result()
                    if content_type == "application/pdf" or body.startswith(b"%PDF-"):
                        pdf_urls.add(final_url)
                        continue
                    if content_type not in {"text/html", "application/xhtml+xml"}:
                        continue
                    parser = LinkParser()
                    parser.feed(body.decode("utf-8", errors="replace"))
                    for raw_link in parser.links:
                        link = canonical(raw_link, final_url)
                        if not link:
                            continue
                        if is_pdf_url(link):
                            host = urllib.parse.urlsplit(link).hostname or ""
                            if host not in ALLOWED_PAGE_HOSTS or robots.can_fetch(USER_AGENT, link):
                                pdf_urls.add(link)
                            continue
                        parsed = urllib.parse.urlsplit(link)
                        host = parsed.hostname or ""
                        page_link = urllib.parse.urlunsplit(
                            (parsed.scheme, parsed.netloc, parsed.path, "", "")
                        )
                        if host in ALLOWED_PAGE_HOSTS and robots.can_fetch(USER_AGENT, page_link) and page_link not in seen_pages:
                            pending.append(page_link)
                except Exception as exc:  # keep a complete crawl manifest
                    errors.append({"url": url, "stage": "page", "error": f"{type(exc).__name__}: {exc}"})

            for pdf_url in sorted(pdf_urls - attempted_pdf_urls):
                attempted_pdf_urls.add(pdf_url)
                download_futures[
                    download_executor.submit(download_pdf, pdf_url, output_dir)
                ] = pdf_url
            collect_downloads()
            if len(seen_pages) % 25 < workers:
                write_manifest(
                    output_dir,
                    list(records_by_url.values()),
                    errors,
                    len(seen_pages),
                )
            if len(seen_pages) % 100 < workers:
                print(
                    f"Crawled {len(seen_pages)} pages; discovered {len(pdf_urls)} PDFs; "
                    f"saved {len(records_by_url)}",
                    flush=True,
                )

        collect_downloads(wait_for_all=True)

    records = list(records_by_url.values())
    write_manifest(output_dir, records, errors, len(seen_pages))
    print(f"Complete: {len(records)} PDFs, {len(seen_pages)} pages, {len(errors)} errors", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--max-pages", type=int)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    if not 1 <= args.workers <= 12:
        parser.error("--workers must be between 1 and 12")
    crawl(args.output_dir.resolve(), args.max_pages, args.workers)


if __name__ == "__main__":
    main()
