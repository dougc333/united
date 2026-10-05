from __future__ import annotations

import json
from typing import Protocol

from .models import Chunk, Verification
from .retrieval import tokenize


class PolicyModel(Protocol):
    def rewrite(self, query: str) -> str: ...
    def answer(self, query: str, context: list[Chunk]) -> tuple[str, list[dict]]: ...
    def verify(self, query: str, answer: str, context: list[Chunk]) -> Verification: ...


class DeterministicPolicyModel:
    """Offline model used for reproducible demos and tests."""

    def rewrite(self, query: str) -> str:
        aliases = {
            "chemo": "bendamustine",
            "scan": "advanced imaging",
            "glucose sensor": "continuous glucose monitor",
        }
        rewritten = query.lower()
        for source, target in aliases.items():
            rewritten = rewritten.replace(source, target)
        return rewritten + " policy approval criteria billing code"

    def answer(self, query: str, context: list[Chunk]) -> tuple[str, list[dict]]:
        if not context:
            return "Insufficient verified policy evidence.", []
        citations = [
            {
                "policy_id": doc.policy_id,
                "title": doc.title,
                "section": doc.section,
                "page": doc.page,
                "chunk_id": doc.id,
            }
            for doc in context
        ]
        evidence = " ".join(doc.text for doc in context)
        return f"Based on the retrieved policy evidence: {evidence}", citations

    def verify(self, query: str, answer: str, context: list[Chunk]) -> Verification:
        if not context or answer.startswith("Insufficient"):
            return Verification(False, 0.0, ("No usable evidence",))
        evidence_terms = set(tokenize(" ".join(doc.text for doc in context)))
        answer_terms = set(tokenize(answer)) - {"based", "retrieved", "policy", "evidence"}
        coverage = len(answer_terms & evidence_terms) / max(len(answer_terms), 1)
        return Verification(
            coverage >= 0.85,
            coverage,
            () if coverage >= 0.85 else ("Answer contains unsupported terms",),
        )


class BedrockPolicyModel:
    """Bedrock Converse implementation used when RAG_PROVIDER=bedrock."""

    def __init__(self, model_id: str, region: str):
        import boto3

        self.client = boto3.client("bedrock-runtime", region_name=region)
        self.model_id = model_id

    def _json(self, system: str, prompt: str) -> dict:
        response = self.client.converse(
            modelId=self.model_id,
            system=[{"text": system}],
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"temperature": 0, "maxTokens": 1000},
        )
        text = response["output"]["message"]["content"][0]["text"]
        return json.loads(text[text.find("{") : text.rfind("}") + 1])

    def rewrite(self, query: str) -> str:
        return self._json(
            "Return JSON only.", f'Rewrite for policy retrieval: {query}\nReturn {{"query":"..."}}'
        )["query"]

    def answer(self, query: str, context: list[Chunk]) -> tuple[str, list[dict]]:
        payload = [
            {"id": c.id, "policy_id": c.policy_id, "page": c.page, "text": c.text} for c in context
        ]
        result = self._json(
            "Answer only from evidence. Return JSON with answer and cited chunk_ids.",
            f"Question: {query}\nEvidence: {json.dumps(payload)}",
        )
        by_id = {c.id: c for c in context}
        citations = [
            {
                "policy_id": by_id[i].policy_id,
                "title": by_id[i].title,
                "section": by_id[i].section,
                "page": by_id[i].page,
                "chunk_id": i,
            }
            for i in result.get("chunk_ids", [])
            if i in by_id
        ]
        return result["answer"], citations

    def verify(self, query: str, answer: str, context: list[Chunk]) -> Verification:
        result = self._json(
            "Verify every claim against evidence. Return JSON only.",
            f"Question: {query}\nAnswer: {answer}\nEvidence: {json.dumps([c.text for c in context])}\n"
            'Return {"supported":true,"coverage":1.0,"unsupported_claims":[]}',
        )
        return Verification(
            bool(result["supported"]),
            float(result["coverage"]),
            tuple(result.get("unsupported_claims", [])),
        )
