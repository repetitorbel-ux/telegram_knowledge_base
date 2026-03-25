from aiogram.fsm.state import State, StatesGroup


class AddEntryStates(StatesGroup):
    waiting_content = State()
    waiting_title = State()
    waiting_topic = State()

