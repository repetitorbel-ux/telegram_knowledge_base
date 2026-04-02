from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from kb_bot.bot.ui.keyboards import build_main_menu_keyboard

router = Router()


def render_welcome_text() -> str:
    return "Telegram KB Bot готов к работе."


def render_boot_text() -> str:
    return "Бот запущен и готов к работе."


def render_restart_text() -> str:
    return "Бот перезапущен и снова готов к работе."


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    await message.answer(render_welcome_text(), reply_markup=build_main_menu_keyboard())
