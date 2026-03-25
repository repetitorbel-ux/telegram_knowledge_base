import csv
import io
import json
import uuid
from dataclasses import dataclass

from kb_bot.core.list_parsing import ListFilters
from kb_bot.db.orm.jobs import ExportJob
from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.db.repositories.jobs import JobsRepository


@dataclass(slots=True)
class ExportResult:
    job_id: str
    filename: str
    content: bytes
    total_records: int


class ExportService:
    def __init__(self, jobs_repo: JobsRepository, entries_repo: EntriesRepository, session) -> None:
        self.jobs_repo = jobs_repo
        self.entries_repo = entries_repo
        self.session = session

    async def export_entries(self, export_format: str, filters: ListFilters) -> ExportResult:
        snapshot = {
            "status_name": filters.status_name,
            "topic_id": str(filters.topic_id) if filters.topic_id else None,
            "limit": filters.limit,
        }
        job = ExportJob(export_format=export_format, status="running", filter_snapshot=json.dumps(snapshot))
        await self.jobs_repo.create_export_job(job)
        await self.session.commit()

        rows = await self.entries_repo.list_entries(
            status_name=filters.status_name,
            topic_id=filters.topic_id,
            limit=filters.limit,
        )

        if export_format == "csv":
            content = self._to_csv(rows)
            filename = "export.csv"
        else:
            content = self._to_json(rows)
            filename = "export.json"

        job.status = "completed"
        job.total_records = len(rows)
        await self.session.commit()

        return ExportResult(job_id=str(job.id), filename=filename, content=content, total_records=len(rows))

    @staticmethod
    def _to_json(rows: list[tuple]) -> bytes:
        payload = []
        for entry, status_name, topic_name in rows:
            payload.append(
                {
                    "id": str(entry.id),
                    "title": entry.title,
                    "status": status_name,
                    "topic": topic_name,
                    "original_url": entry.original_url,
                    "normalized_url": entry.normalized_url,
                    "notes": entry.notes,
                }
            )
        return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")

    @staticmethod
    def _to_csv(rows: list[tuple]) -> bytes:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "status", "topic", "original_url", "normalized_url", "notes"])
        for entry, status_name, topic_name in rows:
            writer.writerow(
                [
                    str(entry.id),
                    entry.title,
                    status_name,
                    topic_name,
                    entry.original_url or "",
                    entry.normalized_url or "",
                    entry.notes or "",
                ]
            )
        return output.getvalue().encode("utf-8")

