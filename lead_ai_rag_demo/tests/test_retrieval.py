from app.retrieval import HybridRetriever
from app.security import redact_pii


def test_hybrid_retrieval_finds_exact_billing_code():
    ids = [hit.chunk.id for hit in HybridRetriever().search("J9033", k=3)]
    assert ids[0] == "c-benda-code"


def test_parent_expansion_returns_policy_context():
    retriever = HybridRetriever()
    parents = retriever.expand_parents(retriever.search("continued CGM coverage", k=1))
    assert parents[0].id == "p-diabetes"
    assert "medically necessary" in parents[0].text


def test_pii_redaction():
    redacted = redact_pii("Member ID: ABC-123 and email me@example.com")
    assert "ABC-123" not in redacted
    assert "me@example.com" not in redacted
