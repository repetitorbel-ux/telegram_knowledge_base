import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from kb_bot.db.orm.base import Base


class KnowledgeEntryTopic(Base):
    __tablename__ = "knowledge_entry_topics"

    entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_entries.id", ondelete="CASCADE"), primary_key=True
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

