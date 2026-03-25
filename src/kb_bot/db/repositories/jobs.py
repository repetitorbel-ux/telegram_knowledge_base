from sqlalchemy.ext.asyncio import AsyncSession

from kb_bot.db.orm.jobs import ExportJob, ImportJob


class JobsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_import_job(self, job: ImportJob) -> ImportJob:
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def create_export_job(self, job: ExportJob) -> ExportJob:
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)
        return job
