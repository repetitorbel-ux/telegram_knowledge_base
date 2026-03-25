from aiogram import Router
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.bot.handlers.add import create_add_router
from kb_bot.bot.handlers.entry import create_entry_router
from kb_bot.bot.handlers.forward_save import create_forward_save_router
from kb_bot.bot.handlers.list_entries import create_list_router
from kb_bot.bot.handlers.search import create_search_router
from kb_bot.bot.handlers.start import router as start_router
from kb_bot.bot.handlers.status import create_status_router
from kb_bot.bot.handlers.topic_manage import create_topic_manage_router
from kb_bot.bot.handlers.topics import create_topics_router


def build_router(session_factory: async_sessionmaker) -> Router:
    router = Router()
    router.include_router(start_router)
    router.include_router(create_topics_router(session_factory))
    router.include_router(create_add_router(session_factory))
    router.include_router(create_search_router(session_factory))
    router.include_router(create_status_router(session_factory))
    router.include_router(create_entry_router(session_factory))
    router.include_router(create_list_router(session_factory))
    router.include_router(create_topic_manage_router(session_factory))
    router.include_router(create_forward_save_router(session_factory))
    return router
