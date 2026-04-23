import hashlib
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from kb_bot.db.orm.entry import KnowledgeEntry
from kb_bot.db.repositories.embeddings import EmbeddingsRepository


class EmbeddingProvider(Protocol):
    async def embed(self, text: str) -> list[float]:
        ...


@dataclass(slots=True)
class EmbeddingServiceConfig:
    provider_name: str
    model_name: str
    embedding_dim: int


class EmbeddingService:
    MAX_EMBEDDING_TEXT_CHARS = 6000
    MIN_EMBEDDING_TEXT_CHARS = 512

    def __init__(
        self,
        session: AsyncSession,
        embeddings_repo: EmbeddingsRepository,
        provider: EmbeddingProvider,
        config: EmbeddingServiceConfig,
    ) -> None:
        self.session = session
        self.embeddings_repo = embeddings_repo
        self.provider = provider
        self.config = config

    async def upsert_for_entry(self, entry: KnowledgeEntry) -> bool:
        text_payload = self.render_entry_text(entry)
        if not text_payload:
            return False

        content_hash = self.compute_content_hash(entry)
        existing = await self.embeddings_repo.get_embedding_row(entry.id)
        if existing is not None:
            if (
                existing.get("provider") == self.config.provider_name
                and existing.get("model") == self.config.model_name
                and existing.get("content_hash") == content_hash
            ):
                return False

        embedding = await self._embed_with_context_fallback(text_payload)
        if len(embedding) != self.config.embedding_dim:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.config.embedding_dim}, got {len(embedding)}."
            )

        await self.embeddings_repo.upsert_embedding(
            entry_id=entry.id,
            provider=self.config.provider_name,
            model=self.config.model_name,
            embedding=embedding,
            content_hash=content_hash,
        )
        await self.session.commit()
        return True

    @staticmethod
    def render_entry_text(entry: KnowledgeEntry) -> str:
        # Keep this deterministic so identical content produces the same embedding payload.
        parts = [
            (entry.title or "").strip(),
            (entry.description or "").strip(),
            (entry.notes or "").strip(),
            (entry.normalized_url or "").strip(),
        ]
        payload = "\n".join(part for part in parts if part)
        if len(payload) <= EmbeddingService.MAX_EMBEDDING_TEXT_CHARS:
            return payload
        return payload[: EmbeddingService.MAX_EMBEDDING_TEXT_CHARS]

    @classmethod
    def compute_content_hash(cls, entry: KnowledgeEntry) -> str:
        payload = cls.render_entry_text(entry)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    async def _embed_with_context_fallback(self, text_payload: str) -> list[float]:
        current_payload = text_payload
        for _ in range(5):
            try:
                return await self.provider.embed(current_payload)
            except Exception as exc:
                message = str(exc).lower()
                if "context length" not in message and "input length exceeds" not in message:
                    raise
                if len(current_payload) <= self.MIN_EMBEDDING_TEXT_CHARS:
                    raise
                next_size = max(self.MIN_EMBEDDING_TEXT_CHARS, len(current_payload) // 2)
                current_payload = current_payload[:next_size]

        raise RuntimeError("Embedding provider context fallback exhausted without success.")
