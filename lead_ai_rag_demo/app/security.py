from __future__ import annotations

import re

PATTERNS = (
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b"), "[REDACTED_PHONE]"),
    (
        re.compile(r"\b(?:member|patient)[ -]?(?:id|number)[: ]+[A-Za-z0-9-]+\b", re.IGNORECASE),
        "[REDACTED_MEMBER_ID]",
    ),
)


def redact_pii(text: str) -> str:
    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    return text
