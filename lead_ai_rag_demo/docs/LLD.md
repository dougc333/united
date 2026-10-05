# Low-level design

`RAGState` is the durable graph contract. Every node returns a partial state update and a trace event. Conditional edges enforce two invariants: an insufficient retrieval cannot reach generation, and an unverified answer cannot reach the successful terminal state. `MAX_CORRECTIONS` prevents infinite loops.

The retriever indexes child chunks for precision and expands distinct `parent_id` values for generation context. RRF combines dense and BM25 ranks. The fixture corpus is intentionally synthetic and small; production adapters must replace it without changing graph control flow.

Security boundaries: never trust an LLM to authorize documents or perform claim payment. Apply tenant/member access filters before retrieval, redact sensitive input before logging, and route low-confidence output to a credentialed reviewer.

