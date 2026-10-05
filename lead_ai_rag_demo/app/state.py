from __future__ import annotations

from typing import Any, TypedDict


class RAGState(TypedDict, total=False):
    query: str
    safe_query: str
    route: str
    rewritten_query: str
    hits: list[Any]
    context: list[Any]
    answer: str
    citations: list[dict[str, Any]]
    retrieval_sufficient: bool
    verified: bool
    verification_coverage: float
    correction_count: int
    needs_human_review: bool
    trace: list[dict[str, Any]]
