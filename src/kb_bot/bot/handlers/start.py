from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from kb_bot.bot.ui.keyboards import build_main_menu_keyboard

router = Router()


def render_welcome_text() -> str:
    return (
        "Telegram KB Bot готов к работе.\n\n"
        "Теперь можно пользоваться не только командами, но и кнопками меню ниже.\n"
        "Основные сценарии уже доступны через UI, а команды сохраняются как резервный режим.\n\n"
        "Быстрые действия:\n"
        "- Добавить запись\n"
        "- Искать по базе\n"
        "- Смотреть быстрые списки\n"
        "- Открывать темы и статистику\n\n"
        "Если предпочитаете команды, они тоже работают: /add, /search, /list, /topics, /stats."
    )


def render_restart_text() -> str:
    return (
        "Бот перезапущен и снова готов к работе.\n\n"
        "Главное меню уже прикреплено ниже, так что вводить /start после каждого рестарта не нужно."
    )


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    await message.answer(render_welcome_text(), reply_markup=build_main_menu_keyboard())
