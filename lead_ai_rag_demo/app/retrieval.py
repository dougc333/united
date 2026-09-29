from __future__ import annotations

import math
import re
from collections import Counter

from .corpus import CHILDREN, PARENTS
from .models import Chunk, Hit

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def _cosine(query: str, document: str) -> float:
    q, d = Counter(tokenize(query)), Counter(tokenize(document))
    dot = sum(value * d.get(token, 0) for token, value in q.items())
    qn = math.sqrt(sum(value * value for value in q.values()))
    dn = math.sqrt(sum(value * value for value in d.values()))
    return dot / (qn * dn) if qn and dn else 0.0


def _bm25(query: str, documents: list[Chunk]) -> list[float]:
    tokenized = [tokenize(doc.text) for doc in documents]
    avgdl = sum(map(len, tokenized)) / max(len(tokenized), 1)
    query_tokens = tokenize(query)
    scores: list[float] = []
    for terms in tokenized:
        counts = Counter(terms)
        score = 0.0
        for token in query_tokens:
            containing = sum(token in doc_terms for doc_terms in tokenized)
            idf = math.log(1 + (len(documents) - containing + 0.5) / (containing + 0.5))
            frequency = counts[token]
            denom = frequency + 1.5 * (1 - 0.75 + 0.75 * len(terms) / max(avgdl, 1))
            score += idf * (frequency * 2.5 / denom) if denom else 0.0
        scores.append(score)
    return scores


class HybridRetriever:
    """Dense-like lexical similarity + BM25 fused with reciprocal-rank fusion."""

    def __init__(self, children: list[Chunk] | None = None):
        self.children = children or CHILDREN

    def search(self, query: str, k: int = 5) -> list[Hit]:
        dense_scores = [_cosine(query, chunk.text) for chunk in self.children]
        sparse_scores = _bm25(query, self.children)
        dense_order = sorted(range(len(self.children)), key=dense_scores.__getitem__, reverse=True)
        sparse_order = sorted(
            range(len(self.children)), key=sparse_scores.__getitem__, reverse=True
        )
        dense_rank = {index: rank for rank, index in enumerate(dense_order, start=1)}
        sparse_rank = {index: rank for rank, index in enumerate(sparse_order, start=1)}
        fused = {
            index: 1 / (60 + dense_rank[index]) + 1 / (60 + sparse_rank[index])
            for index in range(len(self.children))
        }
        order = sorted(fused, key=fused.__getitem__, reverse=True)[:k]
        return [
            Hit(self.children[index], fused[index], dense_rank[index], sparse_rank[index])
            for index in order
        ]

    @staticmethod
    def expand_parents(hits: list[Hit]) -> list[Chunk]:
        seen: set[str] = set()
        parents: list[Chunk] = []
        for hit in hits:
            if hit.chunk.parent_id not in seen:
                seen.add(hit.chunk.parent_id)
                parents.append(PARENTS[hit.chunk.parent_id])
        return parents


def is_sufficient(query: str, hits: list[Hit]) -> bool:
    if not hits:
        return False
    stopwords = {"what", "which", "does", "the", "and", "for", "is", "a", "an", "to"}
    domain_generic = {
        "policy",
        "coverage",
        "approval",
        "criteria",
        "billing",
        "code",
        "require",
        "required",
        "requirements",
        "documentation",
    }
    query_terms = set(tokenize(query)) - stopwords
    subject_terms = query_terms - domain_generic
    evidence_terms = set(tokenize(" ".join(hit.chunk.text for hit in hits[:3])))
    coverage = len(query_terms & evidence_terms) / max(len(query_terms), 1)
    # Generic words such as "policy" or "coverage" must not validate an
    # unrelated subject (for example, "teleportation coverage policy").
    subject_match = bool(subject_terms & evidence_terms)
    return subject_match and coverage >= 0.35
