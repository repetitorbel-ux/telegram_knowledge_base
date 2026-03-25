import uuid
from dataclasses import dataclass

from kb_bot.core.list_parsing import ListFilters
from kb_bot.db.orm.saved_view import SavedView
from kb_bot.db.repositories.saved_views import SavedViewsRepository


@dataclass(slots=True)
class SavedViewDTO:
    id: uuid.UUID
    name: str
    filter_snapshot: dict


class CollectionService:
    def __init__(self, saved_views_repo: SavedViewsRepository, session) -> None:
        self.saved_views_repo = saved_views_repo
        self.session = session

    async def create_saved_view(self, name: str, filters: ListFilters) -> SavedViewDTO:
        title = name.strip()
        if not title:
            raise ValueError("collection name is required")
        if await self.saved_views_repo.get_by_name(title):
            raise ValueError("collection with this name already exists")

        snapshot = {
            "status_name": filters.status_name,
            "topic_id": str(filters.topic_id) if filters.topic_id else None,
            "limit": filters.limit,
        }
        view = SavedView(name=title, filter_snapshot=snapshot)
        await self.saved_views_repo.create(view)
        await self.session.commit()
        await self.session.refresh(view)
        return SavedViewDTO(id=view.id, name=view.name, filter_snapshot=view.filter_snapshot)

    async def list_saved_views(self) -> list[SavedViewDTO]:
        rows = await self.saved_views_repo.list_all()
        return [SavedViewDTO(id=row.id, name=row.name, filter_snapshot=row.filter_snapshot) for row in rows]

    async def get_saved_view(self, view_id: uuid.UUID) -> SavedViewDTO | None:
        row = await self.saved_views_repo.get(view_id)
        if row is None:
            return None
        return SavedViewDTO(id=row.id, name=row.name, filter_snapshot=row.filter_snapshot)

