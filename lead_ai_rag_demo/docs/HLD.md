# High-level design

The demo separates deterministic controls from model judgment. PII protection runs before retrieval. A LangGraph workflow owns routing, bounded corrections, parent expansion, answer generation, verification, and escalation. Retrieval uses dense/sparse fusion over child chunks and returns parent sections for generation. The local provider makes the demo reproducible; the Bedrock provider uses the same graph contract.

Production deployment should place FastAPI in AgentCore Runtime or ECS/Fargate, use Bedrock Knowledge Bases or PGVector for retrieval, store checkpoints in DynamoDB/PostgreSQL/AgentCore Memory, enforce document authorization at retrieval time, and emit OpenTelemetry spans for every node.

```text
Client -> API/RBAC -> PII protection -> LangGraph
  -> router -> hybrid retrieval -> relevance grade
     -> rewrite/retry (bounded) -> parent expansion
     -> generation -> evidence verification
        -> response OR authorized human review
```

