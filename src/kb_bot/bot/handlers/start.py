from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    await message.answer(
        "Telegram KB Bot MVP is running.\n"
        "Commands:\n"
        "/start - health and help\n"
        "/topics - list available topics\n"
        "/add - add URL or note entry\n"
        "/search <query> - search entries\n"
        "/status <entry_uuid> <status name> - update entry status\n"
        "/entry <entry_uuid> - show entry details\n"
        "/list [status=New] [topic=<uuid>] [limit=20] - list entries\n"
        "/topic_add <name> OR /topic_add <parent_uuid|root> <name>\n"
        "/topic_rename <topic_uuid> <new_name>"
    )
