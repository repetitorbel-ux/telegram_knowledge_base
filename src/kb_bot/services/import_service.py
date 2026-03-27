from dataclasses import dataclass

from kb_bot.core.import_parsing import parse_csv_rows, parse_json_rows
from kb_bot.db.orm.jobs import ImportJob
from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.db.repositories.jobs import JobsRepository
from kb_bot.db.repositories.statuses import StatusesRepository
from kb_bot.db.repositories.topics import TopicsRepository
from kb_bot.domain.errors import DuplicateEntryError
from kb_bot.services.entry_service import CreateManualEntryPayload, EntryService


@dataclass(slots=True)
class ImportResult:
    job_id: str
    total_records: int
    imported_records: int
    duplicate_records: int
    error_records: int


class ImportService:
    def __init__(
        self,
        session,
        jobs_repo: JobsRepository,
        entries_repo: EntriesRepository,
        topics_repo: TopicsRepository,
        statuses_repo: StatusesRepository,
    ) -> None:
        self.session = session
        self.jobs_repo = jobs_repo
        self.entries_repo = entries_repo
        self.topics_repo = topics_repo
        self.statuses_repo = statuses_repo

    async def import_rows(self, filename: str, source_format: str, payload: bytes) -> ImportResult:
        if source_format == "csv":
            rows = parse_csv_rows(payload)
        elif source_format == "json":
            rows = parse_json_rows(payload)
        else:
            raise ValueError("unsupported format")

        job = ImportJob(source_filename=filename, source_format=source_format, status="running")
        await self.jobs_repo.create_import_job(job)
        await self.session.commit()

        default_topic = await self.topics_repo.get_by_name("Useful Channels")
        if default_topic is None:
            # UAT/local databases may rename seed topics. Fallback to any active topic.
            topics = await self.topics_repo.list_tree()
            default_topic = topics[0] if topics else None
        if default_topic is None:
            raise RuntimeError("No active topics found. Create at least one topic before import.")

        entry_service = EntryService(
            session=self.session,
            entries_repo=self.entries_repo,
            topics_repo=self.topics_repo,
            statuses_repo=self.statuses_repo,
        )

        imported = 0
        duplicates = 0
        errors = 0
        error_messages = []

        for idx, row in enumerate(rows, start=1):
            title = (row.get("title") or "").strip()
            original_url = (row.get("original_url") or "").strip() or None
            notes = (row.get("notes") or "").strip() or None
            if not title:
                title = original_url or f"Imported item {idx}"

            topic_id = default_topic.id
            topic_raw = (row.get("topic_id") or "").strip()
            if topic_raw:
                try:
                    import uuid

                    parsed_topic_id = uuid.UUID(topic_raw)
                    topic = await self.topics_repo.get(parsed_topic_id)
                    if topic is not None:
                        topic_id = topic.id
                except ValueError:
                    pass

            try:
                await entry_service.create_manual(
                    CreateManualEntryPayload(
                        title=title,
                        primary_topic_id=topic_id,
                        original_url=original_url,
                        notes=notes,
                    )
                )
                imported += 1
            except DuplicateEntryError:
                duplicates += 1
            except Exception as exc:
                errors += 1
                error_messages.append(f"row {idx}: {exc}")

        job.status = "completed" if errors == 0 else "failed"
        job.total_records = len(rows)
        job.imported_records = imported
        job.duplicate_records = duplicates
        job.error_records = errors
        job.error_details = "\n".join(error_messages[:20]) if error_messages else None
        await self.session.commit()

        return ImportResult(
            job_id=str(job.id),
            total_records=job.total_records,
            imported_records=job.imported_records,
            duplicate_records=job.duplicate_records,
            error_records=job.error_records,
        )
