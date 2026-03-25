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
        "/add - add URL or note entry"
    )

