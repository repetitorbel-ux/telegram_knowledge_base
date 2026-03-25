import uuid

from kb_bot.core.topic_slug import slugify_topic_name
from kb_bot.db.orm.topic import Topic
from kb_bot.db.repositories.topics import TopicsRepository
from kb_bot.domain.dto import TopicDTO
from kb_bot.domain.errors import TopicConflictError, TopicNotFoundError


class TopicService:
    def __init__(self, topics_repo: TopicsRepository, session=None) -> None:
        self.topics_repo = topics_repo
        self.session = session if session is not None else topics_repo.session

    async def list_tree(self) -> list[TopicDTO]:
        topics = await self.topics_repo.list_tree()
        return [
            TopicDTO(id=topic.id, name=topic.name, full_path=topic.full_path, level=topic.level)
            for topic in topics
        ]

    async def create_topic(self, name: str, parent_topic_id: uuid.UUID | None = None) -> TopicDTO:
        topic_name = name.strip()
        if not topic_name:
            raise ValueError("topic name is required")

        slug = slugify_topic_name(topic_name)
        parent = None
        if parent_topic_id is not None:
            parent = await self.topics_repo.get(parent_topic_id)
            if parent is None:
                raise TopicNotFoundError("parent topic not found")

        full_path = slug if parent is None else f"{parent.full_path}.{slug}"
        if await self.topics_repo.get_by_full_path(full_path):
            raise TopicConflictError("topic with this path already exists")

        level = 0 if parent is None else parent.level + 1
        topic = Topic(
            name=topic_name,
            slug=slug,
            parent_topic_id=parent_topic_id,
            full_path=full_path,
            full_path_ltree=full_path,
            level=level,
            sort_order=0,
            is_active=True,
            is_archived=False,
        )
        await self.topics_repo.create(topic)
        await self.session.commit()
        await self.session.refresh(topic)
        return TopicDTO(id=topic.id, name=topic.name, full_path=topic.full_path, level=topic.level)

    async def rename_topic(self, topic_id: uuid.UUID, new_name: str) -> TopicDTO:
        topic = await self.topics_repo.get(topic_id)
        if topic is None:
            raise TopicNotFoundError("topic not found")

        parent_path = ""
        if topic.parent_topic_id is not None:
            parent = await self.topics_repo.get(topic.parent_topic_id)
            if parent is None:
                raise TopicNotFoundError("parent topic not found")
            parent_path = parent.full_path

        old_prefix = topic.full_path
        new_slug = slugify_topic_name(new_name)
        new_full_path = new_slug if not parent_path else f"{parent_path}.{new_slug}"

        existing = await self.topics_repo.get_by_full_path(new_full_path)
        if existing is not None and existing.id != topic.id:
            raise TopicConflictError("topic with this path already exists")

        topic.name = new_name.strip()
        topic.slug = new_slug
        topic.full_path = new_full_path
        topic.full_path_ltree = new_full_path

        descendants = await self.topics_repo.list_descendants(old_prefix)
        for child in descendants:
            suffix = child.full_path[len(old_prefix) :]
            child.full_path = f"{new_full_path}{suffix}"
            child.full_path_ltree = child.full_path

        await self.session.commit()
        await self.session.refresh(topic)
        return TopicDTO(id=topic.id, name=topic.name, full_path=topic.full_path, level=topic.level)
