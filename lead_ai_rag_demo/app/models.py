from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Chunk:
    id: str
    parent_id: str
    policy_id: str
    title: str
    section: str
    page: int
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float
    dense_rank: int | None = None
    sparse_rank: int | None = None


@dataclass(frozen=True)
class Verification:
    supported: bool
    coverage: float
    unsupported_claims: tuple[str, ...] = ()
