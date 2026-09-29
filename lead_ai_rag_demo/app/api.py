from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .graph import graph

app = FastAPI(title="United Lead AI RAG Demo", version="0.1.0")


class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=4000)
    thread_id: str | None = None


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"status": "ready"}


@app.post("/query")
def query(request: QueryRequest):
    thread_id = request.thread_id or str(uuid4())
    result = graph.invoke(
        {"query": request.query, "trace": []},
        config={"configurable": {"thread_id": thread_id}},
    )
    return {
        "thread_id": thread_id,
        "answer": result["answer"],
        "verified": result.get("verified", False),
        "verification_coverage": result.get("verification_coverage", 0),
        "needs_human_review": result.get("needs_human_review", False),
        "citations": result.get("citations", []),
        "trace": result.get("trace", []),
    }
