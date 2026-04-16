from aiogram.fsm.state import State, StatesGroup


class AddEntryStates(StatesGroup):
    waiting_content = State()
    waiting_title = State()
    waiting_topic = State()


class GuidedSearchStates(StatesGroup):
    waiting_query = State()
    showing_results = State()


class TopicCreateStates(StatesGroup):
    waiting_name = State()


class TopicRenameStates(StatesGroup):
    waiting_name = State()


class EntryMoveStates(StatesGroup):
    waiting_topic_name = State()


class EntryEditStates(StatesGroup):
    waiting_value = State()


class GuidedImportStates(StatesGroup):
    waiting_document = State()
