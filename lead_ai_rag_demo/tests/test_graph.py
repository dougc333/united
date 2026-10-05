from app.graph import build_graph


def test_graph_returns_verified_cited_answer():
    result = build_graph().invoke(
        {"query": "What billing code and preferred product apply to bendamustine?", "trace": []},
        config={"configurable": {"thread_id": "test-verified"}},
    )
    assert result["verified"] is True
    assert result["citations"]
    assert any(item["node"] == "verify" for item in result["trace"])


def test_unknown_query_is_bounded_and_escalated():
    result = build_graph().invoke(
        {"query": "What is the coverage policy for teleportation?", "trace": []},
        config={"configurable": {"thread_id": "test-escalate"}},
    )
    assert result["needs_human_review"] is True
    assert result["correction_count"] == 2
