"""GroundX retriever backend for the AI-Q knowledge layer.

Registers backend name "groundx" so AI-Q workflow configs can select it:

    knowledge_search:
      _type: knowledge_retrieval
      backend: groundx
      groundx_api_key: ${GROUNDX_API_KEY}
      groundx_base_url: ${GROUNDX_BASE_URL:-https://api.groundx.ai/api}

Collections map to GroundX buckets (collection_name -> bucket name, resolved
once and cached). Every chunk carries page-level provenance from GroundX
bounding boxes, satisfying the knowledge layer's strict citation contract.

Written against the aiq_agent knowledge-layer contract as of July 2026;
validate inside an AI-Q checkout before production use. The API key travels
only in the X-API-Key header.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from aiq_agent.knowledge.base import BaseRetriever
from aiq_agent.knowledge.factory import register_retriever
from aiq_agent.knowledge.schema import Chunk, ContentType, RetrievalResult

_DEFAULT_BASE_URL = "https://api.groundx.ai/api"


@register_retriever("groundx")
class GroundXRetriever(BaseRetriever):
    """Retrieve chunks from GroundX hybrid search (keyword + vector + rerank)."""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.base_url = (self.config.get("groundx_base_url") or _DEFAULT_BASE_URL).rstrip("/")
        self.api_key = self.config.get("groundx_api_key")
        if not self.api_key:
            raise ValueError("groundx_api_key is required (env: GROUNDX_API_KEY)")
        self._bucket_ids: dict[str, int] = {}

    @property
    def backend_name(self) -> str:
        return "groundx"

    async def _bucket_id(self, client: httpx.AsyncClient, collection_name: str) -> int:
        if collection_name in self._bucket_ids:
            return self._bucket_ids[collection_name]
        r = await client.get(f"{self.base_url}/v1/bucket", headers=self._headers())
        r.raise_for_status()
        for b in r.json().get("buckets", []):
            self._bucket_ids[b["name"]] = b["bucketId"]
        if collection_name not in self._bucket_ids:
            raise KeyError(f"No GroundX bucket named {collection_name!r}")
        return self._bucket_ids[collection_name]

    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    async def retrieve(
        self,
        query: str,
        collection_name: str,
        top_k: int = 5,
        filters: dict | None = None,
    ) -> RetrievalResult:
        async with httpx.AsyncClient(timeout=60) as client:
            bucket_id = await self._bucket_id(client, collection_name)
            payload: dict[str, Any] = {"query": query, "n": top_k}
            if filters:
                payload["filter"] = filters
            r = await client.post(
                f"{self.base_url}/v1/search/{bucket_id}",
                headers=self._headers(),
                json=payload,
            )
            r.raise_for_status()
            search = r.json().get("search", {})

        results = search.get("results", [])
        max_score = max((res.get("score", 0.0) for res in results), default=1.0) or 1.0
        chunks = [self._normalize(res, max_score) for res in results]
        return RetrievalResult(
            chunks=chunks,
            query=query,
            backend=self.backend_name,
            total_tokens=sum(len(c.content.split()) for c in chunks),
        )

    def _normalize(self, res: dict[str, Any], max_score: float) -> Chunk:
        text = res.get("suggestedText") or res.get("text") or ""
        file_name = res.get("fileName") or "unknown"
        boxes = res.get("boundingBoxes") or []
        page = boxes[0].get("pageNumber") if boxes else None

        content_type = ContentType.TEXT
        structured: str | None = None
        stripped = text.lstrip()
        if stripped.startswith("{"):
            try:
                record = json.loads(stripped.splitlines()[0])
                if record.get("record_type") in ("summary", "table") and record.get("table_title"):
                    content_type = ContentType.TABLE
                    structured = stripped
                    text = record.get("retrieval_anchor") or record.get("purpose") or text
            except (json.JSONDecodeError, AttributeError):
                pass

        citation = f"{file_name}, p. {page}" if page else file_name
        return Chunk(
            chunk_id=str(res.get("chunkId") or res.get("documentId") or citation),
            content=text,
            score=min(max(res.get("score", 0.0) / max_score, 0.0), 1.0),
            file_name=file_name,
            page_number=page,
            display_citation=citation,
            content_type=content_type,
            structured_data=structured,
        )
