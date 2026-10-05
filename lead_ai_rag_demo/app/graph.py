from __future__ import annotations

import os
from typing import Literal

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from .llm import BedrockPolicyModel, DeterministicPolicyModel, PolicyModel
from .retrieval import HybridRetriever, is_sufficient
from .security import redact_pii
from .state import RAGState


def _event(state: RAGState, node: str, **details) -> list[dict]:
    return [*state.get("trace", []), {"node": node, **details}]


def build_graph(model: PolicyModel | None = None, retriever: HybridRetriever | None = None):
    provider = os.getenv("RAG_PROVIDER", "local")
    if model is None and provider == "bedrock":
        model = BedrockPolicyModel(
            os.environ["BEDROCK_MODEL_ID"], os.getenv("AWS_REGION", "us-east-1")
        )
    model = model or DeterministicPolicyModel()
    retriever = retriever or HybridRetriever()
    max_corrections = int(os.getenv("MAX_CORRECTIONS", "2"))

    def protect(state: RAGState):
        safe = redact_pii(state["query"])
        return {
            "safe_query": safe,
            "correction_count": 0,
            "trace": _event(state, "protect", redacted=safe != state["query"]),
        }

    def route(state: RAGState):
        query = state["safe_query"].lower()
        selected = (
            "structured"
            if any(token in query for token in ("j9033", "billing code", "policy id"))
            else "semantic"
        )
        return {"route": selected, "trace": _event(state, "route", route=selected)}

    def retrieve(state: RAGState):
        query = state.get("rewritten_query") or state["safe_query"]
        hits = retriever.search(query, k=5)
        return {
            "hits": hits,
            "trace": _event(state, "retrieve", query=query, hit_ids=[h.chunk.id for h in hits]),
        }

    def grade(state: RAGState):
        sufficient = is_sufficient(
            state.get("rewritten_query") or state["safe_query"], state["hits"]
        )
        return {
            "retrieval_sufficient": sufficient,
            "trace": _event(state, "grade_retrieval", sufficient=sufficient),
        }

    def after_grade(state: RAGState) -> Literal["expand", "rewrite", "human_review"]:
        if state["retrieval_sufficient"]:
            return "expand"
        return "rewrite" if state.get("correction_count", 0) < max_corrections else "human_review"

    def rewrite(state: RAGState):
        rewritten = model.rewrite(state.get("rewritten_query") or state["safe_query"])
        count = state.get("correction_count", 0) + 1
        return {
            "rewritten_query": rewritten,
            "correction_count": count,
            "trace": _event(state, "rewrite", query=rewritten, attempt=count),
        }

    def expand(state: RAGState):
        context = retriever.expand_parents(state["hits"][:3])
        return {
            "context": context,
            "trace": _event(state, "expand_parent", parent_ids=[c.id for c in context]),
        }

    def generate(state: RAGState):
        answer, citations = model.answer(state["safe_query"], state["context"])
        return {
            "answer": answer,
            "citations": citations,
            "trace": _event(state, "generate", citation_count=len(citations)),
        }

    def verify(state: RAGState):
        result = model.verify(state["safe_query"], state["answer"], state["context"])
        return {
            "verified": result.supported,
            "verification_coverage": result.coverage,
            "trace": _event(state, "verify", supported=result.supported, coverage=result.coverage),
        }

    def after_verify(state: RAGState) -> Literal["done", "rewrite", "human_review"]:
        if state["verified"]:
            return "done"
        return "rewrite" if state.get("correction_count", 0) < max_corrections else "human_review"

    def human_review(state: RAGState):
        return {
            "needs_human_review": True,
            "verified": False,
            "answer": "Automated verification did not pass. Route this request to an authorized reviewer.",
            "trace": _event(state, "human_review", reason="bounded correction attempts exhausted"),
        }

    graph = StateGraph(RAGState)
    for name, function in {
        "protect": protect,
        "route": route,
        "retrieve": retrieve,
        "grade": grade,
        "rewrite": rewrite,
        "expand": expand,
        "generate": generate,
        "verify": verify,
        "human_review": human_review,
    }.items():
        graph.add_node(name, function)
    graph.add_edge(START, "protect")
    graph.add_edge("protect", "route")
    graph.add_edge("route", "retrieve")
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges(
        "grade",
        after_grade,
        {"expand": "expand", "rewrite": "rewrite", "human_review": "human_review"},
    )
    graph.add_edge("rewrite", "retrieve")
    graph.add_edge("expand", "generate")
    graph.add_edge("generate", "verify")
    graph.add_conditional_edges(
        "verify", after_verify, {"done": END, "rewrite": "rewrite", "human_review": "human_review"}
    )
    graph.add_edge("human_review", END)
    return graph.compile(checkpointer=InMemorySaver())


graph = build_graph()
