from kb_bot.db.repositories.topics import TopicsRepository
from kb_bot.domain.dto import TopicDTO


class TopicService:
    def __init__(self, topics_repo: TopicsRepository) -> None:
        self.topics_repo = topics_repo

    async def list_tree(self) -> list[TopicDTO]:
        topics = await self.topics_repo.list_tree()
        return [
            TopicDTO(id=topic.id, name=topic.name, full_path=topic.full_path, level=topic.level)
            for topic in topics
        ]

