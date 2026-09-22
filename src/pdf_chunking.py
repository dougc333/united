"""PDF text extraction and recursive chunk-size analysis for the Streamlit app."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pymupdf
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"


@dataclass(frozen=True)
class ChunkPolicy:
    label: str
    chunk_size: int
    chunk_overlap: int
    unit: str = "tokens"


POLICIES = (
    ChunkPolicy("Token-aware · 128 tokens · 10% overlap", 128, 13),
    ChunkPolicy("Token-aware · 256 tokens · 10% overlap", 256, 26),
    ChunkPolicy("Token-aware · 384 tokens · 10% overlap", 384, 38),
    ChunkPolicy("Token-aware · 480 tokens · 10% overlap", 480, 48),
    ChunkPolicy("Token-aware · 512 tokens · 10% overlap (test.py)", 512, 51),
    ChunkPolicy("Character baseline · 2,500 chars · 100 overlap (test.py)", 2500, 100, "characters"),
)


def find_pdfs(root: Path) -> list[Path]:
    """Find PDFs below the root, including nested domain/path directories."""
    return sorted(
        (path for path in root.rglob("*") if path.is_file() and path.suffix.lower() == ".pdf"),
        key=lambda path: str(path.relative_to(root)).casefold(),
    )


def clean_extra_whitespace(text: str) -> str:
    """Match the whitespace normalization used in src/test.py."""
    return " ".join(text.split())


def extract_pages(pdf_path: Path) -> list[tuple[int, str]]:
    """Treat each PDF page as a document so one PDF has a length distribution."""
    pages: list[tuple[int, str]] = []
    with pymupdf.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            pages.append((page_number, clean_extra_whitespace(page.get_text("text"))))
    return pages


def count_tokens(text: str, tokenizer) -> int:
    if not text:
        return 0
    return len(tokenizer.encode(text, add_special_tokens=True, truncation=False))


def split_pdf(
    pages: list[tuple[int, str]],
    source: str,
    policy: ChunkPolicy,
    tokenizer,
) -> list[Document]:
    """Apply the test.py recursive splitter to one PDF's combined text."""
    if policy.unit == "tokens":
        splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
            tokenizer,
            chunk_size=policy.chunk_size,
            chunk_overlap=policy.chunk_overlap,
            add_start_index=True,
            strip_whitespace=True,
        )
    else:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=policy.chunk_size,
            chunk_overlap=policy.chunk_overlap,
            add_start_index=True,
            strip_whitespace=True,
        )

    full_text = clean_extra_whitespace(" ".join(text for _, text in pages if text))
    if not full_text:
        return []
    documents = [Document(page_content=full_text, metadata={"source": source})]
    # Do not deduplicate by content: identical policy text can occur in distinct PDFs.
    chunks = splitter.split_documents(documents)
    # LangChain can report start_index=-1 for a later, valid chunk when its
    # overlap search starts past the true match. Re-anchor every chunk against
    # the exact joined source so page/evidence scoring never treats -1 as 0.
    previous_start = -1
    for chunk in chunks:
        start = full_text.find(chunk.page_content, previous_start + 1)
        if start < 0:
            start = full_text.find(chunk.page_content)
        chunk.metadata["start_index"] = start
        if start >= 0:
            previous_start = start
    return chunks
