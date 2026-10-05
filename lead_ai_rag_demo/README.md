# Lead AI Engineer healthcare RAG demo

Production-shaped, locally runnable demonstration of a stateful healthcare-policy RAG workflow. It uses synthetic data and is not affiliated with UnitedHealth Group. It must not be used for coverage, care, payment, or claim decisions.

## What it demonstrates

- Explicit LangGraph state, cycles and conditional edges
- Hybrid child retrieval with BM25, dense-like similarity and RRF
- Hierarchical small-to-big parent expansion
- Corrective RAG query rewriting with a strict retry limit
- Self-RAG-style answer/evidence verification
- Safe escalation instead of an unverified answer
- PII redaction before retrieval and tracing
- FastAPI, Streamlit, Docker, health checks and deterministic golden evals
- Optional Bedrock Converse provider (`RAG_PROVIDER=bedrock`)

## Run locally

```bash
cd /Users/dc/united/lead_ai_rag_demo
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest
.venv/bin/python -m app.evaluate
.venv/bin/python -m uvicorn app.api:app --reload --port 8000
```

In a second terminal:

```bash
cd /Users/dc/united/lead_ai_rag_demo
.venv/bin/python -m streamlit run streamlit_app.py
```

Open `http://localhost:8501`. API documentation is at `http://localhost:8000/docs`.

## Try it

```bash
curl -s http://localhost:8000/query \
  -H 'content-type: application/json' \
  -d '{"query":"What billing code and preferred product apply to bendamustine?"}'
```

Use `What is the coverage policy for teleportation?` to demonstrate two bounded correction attempts followed by human-review escalation.

## Bedrock mode

```bash
cp .env.example .env
# Set RAG_PROVIDER=bedrock and a model ID available in your AWS account.
set -a; source .env; set +a
.venv/bin/python -m uvicorn app.api:app --port 8000
```

The current Bedrock adapter handles rewriting, generation and verification. Replace the fixture retriever with Bedrock Knowledge Base `Retrieve` or PGVector for production. Do not put credentials in `.env` or Git; use an IAM role.

## Important production gaps

This is a portfolio demo, not a finished healthcare system. Before production: add real identity/RBAC, tenant-aware metadata filters, durable AWS-backed checkpoints, Bedrock Guardrails, OpenTelemetry export, encryption/KMS policies, audited human review, prompt-injection tests, load tests, and a clinically/business-approved golden dataset.

See [HLD](docs/HLD.md) and [LLD](docs/LLD.md).
