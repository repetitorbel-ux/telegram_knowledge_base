from sqlalchemy import func, select

from kb_bot.db.orm.entry import KnowledgeEntry
from kb_bot.db.orm.jobs import ImportJob
from kb_bot.db.orm.status import Status
from kb_bot.db.orm.topic import Topic


class StatsService:
    def __init__(self, session) -> None:
        self.session = session

    async def get_stats(self) -> dict:
        total_entries = await self._scalar(select(func.count()).select_from(KnowledgeEntry))
        by_status = await self._status_counts()
        by_topic = await self._topic_counts()
        duplicates_prevented = await self._scalar(
            select(func.coalesce(func.sum(ImportJob.duplicate_records), 0)).select_from(ImportJob)
        )

        inbox_size = by_status.get("New", 0)
        backlog = by_status.get("To Read", 0)
        verified_count = by_status.get("Verified", 0)
        verified_coverage = (verified_count / total_entries) if total_entries else 0.0

        return {
            "total_entries": total_entries,
            "by_status": by_status,
            "by_topic": by_topic,
            "duplicates_prevented": duplicates_prevented,
            "inbox_size": inbox_size,
            "backlog": backlog,
            "verified_coverage": round(verified_coverage, 3),
        }

    async def _status_counts(self) -> dict[str, int]:
        stmt = (
            select(Status.display_name, func.count(KnowledgeEntry.id))
            .join(KnowledgeEntry, KnowledgeEntry.status_id == Status.id)
            .group_by(Status.display_name)
        )
        rows = (await self.session.execute(stmt)).all()
        return {name: count for name, count in rows}

    async def _topic_counts(self) -> dict[str, int]:
        stmt = (
            select(Topic.name, func.count(KnowledgeEntry.id))
            .join(KnowledgeEntry, KnowledgeEntry.primary_topic_id == Topic.id)
            .group_by(Topic.name)
        )
        rows = (await self.session.execute(stmt)).all()
        return {name: count for name, count in rows}

    async def _scalar(self, stmt) -> int:
        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)

