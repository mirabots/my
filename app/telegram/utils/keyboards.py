from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.telegram.utils.callbacks import (
    CallbackAbort,
    CallbackAnimeAction,
    CallbackAnimeAdd,
    CallbackAnimeChoose,
)


def get_keyboard_abort(action: str, name: str = "Abort") -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=name, callback_data=CallbackAbort(action=action))
    return keyboard


def get_keyboard_anime(all_anime: list[dict[str, str | int]]) -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()
    for anime in all_anime:
        keyboard.button(
            text=anime["name"], callback_data=CallbackAnimeChoose(id=anime["id"])
        )
    return keyboard


def get_keyboard_anime_add() -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()
    for action in ("Add",):
        keyboard.button(text=action, callback_data=CallbackAnimeAdd())
    return keyboard


def get_keyboard_anime_actions(id: int) -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()
    for action in ("Update", "Rename", "Delete"):
        keyboard.button(
            text=action, callback_data=CallbackAnimeAction(id=id, action=action)
        )
    return keyboard
