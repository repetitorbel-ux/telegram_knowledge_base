from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Any

import httpx

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"


class OpenAIEmbeddingProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        base_url: str | None = None,
        timeout_ms: int = 3000,
    ) -> None:
        if not api_key.strip():
            raise ValueError("OPENAI_API_KEY is required for OpenAI embedding provider.")
        self.api_key = api_key.strip()
        self.model = model.strip()
        self.base_url = (base_url or DEFAULT_OPENAI_BASE_URL).rstrip("/")
        self.timeout_sec = max(timeout_ms, 1000) / 1000.0

    async def embed(self, text: str) -> list[float]:
        payload = {
            "model": self.model,
            "input": text,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
            response = await client.post(f"{self.base_url}/embeddings", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return _extract_embedding_from_payload(data)


class LocalHTTPEmbeddingProvider:
    def __init__(self, url: str, model: str, *, timeout_ms: int = 3000) -> None:
        if not url.strip():
            raise ValueError("LOCAL_EMBEDDING_URL is required for local embedding provider.")
        self.url = url.strip()
        self.model = model.strip()
        self.timeout_sec = max(timeout_ms, 1000) / 1000.0
        self.max_attempts = 3
        self._is_ollama_api = "/api/embeddings" in self.url.lower()

    async def embed(self, text: str) -> list[float]:
        # Ollama /api/embeddings expects "prompt". OpenAI-compatible local servers
        # often expect "input". Sending both can effectively duplicate input and may
        # trigger context-length errors on Ollama, so we branch by endpoint style.
        if self._is_ollama_api:
            payload = {"model": self.model, "prompt": text}
        else:
            payload = {"model": self.model, "input": text}
        last_error: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_sec, trust_env=False) as client:
                    response = await client.post(self.url, json=payload)
                response.raise_for_status()
                data = response.json()
                return _extract_embedding_from_payload(data)
            except httpx.HTTPStatusError as exc:
                # Retry only for temporary server-side issues.
                status_code = exc.response.status_code
                if status_code < 500 or attempt >= self.max_attempts:
                    response_text = (exc.response.text or "").strip()
                    if response_text:
                        snippet = response_text[:500]
                        raise RuntimeError(
                            f"Local embedding provider HTTP {status_code}: {snippet}"
                        ) from exc
                    raise
                last_error = exc
            except (
                httpx.ReadTimeout,
                httpx.ConnectTimeout,
                httpx.RemoteProtocolError,
                httpx.ReadError,
                httpx.WriteError,
                httpx.ConnectError,
            ) as exc:
                if attempt >= self.max_attempts:
                    raise
                last_error = exc

            await asyncio.sleep(0.25 * attempt)

        if last_error is not None:
            raise last_error
        raise RuntimeError("Embedding provider failed without explicit error.")


def _extract_embedding_from_payload(payload: Any) -> list[float]:
    # OpenAI-compatible shape: {"data": [{"embedding": [...]}]}
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, Sequence) and data:
            first = data[0]
            if isinstance(first, dict) and isinstance(first.get("embedding"), Sequence):
                return [float(value) for value in first["embedding"]]

        # Local shape fallback: {"embedding": [...]}
        vector = payload.get("embedding")
        if isinstance(vector, Sequence):
            result = [float(value) for value in vector]
            if result:
                return result

    raise RuntimeError("Embedding provider returned unsupported response shape.")
