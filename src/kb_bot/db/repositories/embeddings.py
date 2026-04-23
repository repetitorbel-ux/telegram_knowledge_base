import uuid
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession


class EmbeddingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_embedding(
        self,
        entry_id: uuid.UUID,
        provider: str,
        model: str,
        embedding: list[float],
        content_hash: str,
    ) -> None:
        embedding_literal = "[" + ",".join(f"{value:.12g}" for value in embedding) + "]"
        stmt = text(
            """
            INSERT INTO knowledge_entry_embeddings
                (entry_id, provider, model, embedding_dim, embedding, content_hash, updated_at)
            VALUES
                (:entry_id, :provider, :model, :embedding_dim, CAST(:embedding AS vector), :content_hash, NOW())
            ON CONFLICT (entry_id) DO UPDATE
            SET
                provider = EXCLUDED.provider,
                model = EXCLUDED.model,
                embedding_dim = EXCLUDED.embedding_dim,
                embedding = EXCLUDED.embedding,
                content_hash = EXCLUDED.content_hash,
                updated_at = NOW();
            """
        )
        await self.session.execute(
            stmt,
            {
                "entry_id": entry_id,
                "provider": provider,
                "model": model,
                "embedding_dim": len(embedding),
                "embedding": embedding_literal,
                "content_hash": content_hash,
            },
        )
        await self.session.flush()

    async def get_embedding_row(self, entry_id: uuid.UUID) -> dict[str, Any] | None:
        stmt = text(
            """
            SELECT entry_id, provider, model, embedding_dim, content_hash, updated_at
            FROM knowledge_entry_embeddings
            WHERE entry_id = :entry_id
            LIMIT 1;
            """
        )
        result = await self.session.execute(stmt, {"entry_id": entry_id})
        row = result.mappings().first()
        if row is None:
            return None
        return dict(row)

    async def find_similar_entries(
        self,
        query_embedding: list[float],
        provider: str,
        model: str,
        limit: int,
        exclude_entry_id: uuid.UUID | None = None,
    ) -> list[tuple[uuid.UUID, float]]:
        embedding_literal = "[" + ",".join(f"{value:.12g}" for value in query_embedding) + "]"
        where_exclude = "AND entry_id != :exclude_entry_id" if exclude_entry_id is not None else ""
        stmt = text(
            f"""
            SELECT
                entry_id,
                1 - (embedding <=> CAST(:query_embedding AS vector)) AS semantic_score
            FROM knowledge_entry_embeddings
            WHERE provider = :provider
              AND model = :model
              {where_exclude}
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :limit;
            """
        )
        params: dict[str, Any] = {
            "query_embedding": embedding_literal,
            "provider": provider,
            "model": model,
            "limit": limit,
        }
        if exclude_entry_id is not None:
            params["exclude_entry_id"] = exclude_entry_id

        result = await self.session.execute(stmt, params)
        return [(row[0], float(row[1])) for row in result.all()]

    async def score_candidates(
        self,
        query_embedding: list[float],
        provider: str,
        model: str,
        candidate_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, float]:
        if not candidate_ids:
            return {}

        embedding_literal = "[" + ",".join(f"{value:.12g}" for value in query_embedding) + "]"
        stmt = (
            text(
                """
                SELECT
                    entry_id,
                    1 - (embedding <=> CAST(:query_embedding AS vector)) AS semantic_score
                FROM knowledge_entry_embeddings
                WHERE provider = :provider
                  AND model = :model
                  AND entry_id IN :candidate_ids;
                """
            )
            .bindparams(bindparam("candidate_ids", expanding=True))
        )
        result = await self.session.execute(
            stmt,
            {
                "query_embedding": embedding_literal,
                "provider": provider,
                "model": model,
                "candidate_ids": candidate_ids,
            },
        )
        return {row[0]: float(row[1]) for row in result.all()}
