from aiogram.fsm.state import State, StatesGroup


class FormAnimeAdd(StatesGroup):
    anime_id = State()
    anime_name = State()


class FormAnimeRename(StatesGroup):
    anime_name = State()
