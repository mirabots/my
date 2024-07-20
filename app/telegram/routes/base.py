import time
from contextlib import suppress

from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.common.config import cfg
from app.common.utils import get_logger, levelDEBUG, levelINFO
from app.crud import anime as crud_anime
from app.telegram.commands import COMMANDS_BOT
from app.telegram.utils.callbacks import CallbackAbort

router = Router()
logger = get_logger(levelDEBUG if cfg.ENV == "dev" else levelINFO)


@router.message(Command("start"))
async def start_handler(message: types.Message):
    chat_id = message.chat.id
    owner_id = message.from_user.id

    logger.info(
        f"Start: {owner_id=} {message.from_user.username=} {chat_id=} {time.asctime()}"
    )
    with suppress(TelegramBadRequest):
        await message.answer(text="Bot started")


@router.message(Command("stop"))
async def stop_handler(message: types.Message):
    chat_id = message.chat.id
    owner_id = message.from_user.id

    logger.info(
        f"Start: {owner_id=} {message.from_user.username=} {chat_id=} {time.asctime()}"
    )
    with suppress(TelegramBadRequest):
        await message.answer(text="Bot stopped")


@router.message(Command("commands"))
async def commands_handler(message: types.Message):
    message_text = "Available commands:"
    for command in COMMANDS_BOT:
        if command.get("command"):
            message_text += f"\n● {command['description']}"
            message_text += f"\n○ {command['command']}"
        elif command.get("subcommands"):
            message_text += f"\n- {command['description']}"
            for subcommand in command["subcommands"]:
                message_text += f"\n  ● {subcommand['description']}"
                message_text += f"\n  ○ {subcommand['command']}"

    with suppress(TelegramBadRequest):
        await message.answer(text=message_text)


@router.callback_query(CallbackAbort.filter())
async def abort_handler(
    callback: types.CallbackQuery, callback_data: CallbackAbort, state: FSMContext
):
    await state.clear()

    action = callback_data.action
    action_text = ""
    if action == "anime":
        all_anime = await crud_anime.get_all_anime()
        message_text = "Anime:"
        if all_anime:
            for anime in all_anime:
                message_text += f"\n● {anime['name']}"
        else:
            message_text += " no titles"
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(text=message_text, reply_markup=None)
        return
    if action == "anime_a":
        action_text = "Add anime"
    if action == "anime_i":
        with suppress(TelegramBadRequest):
            await callback.message.edit_reply_markup(reply_markup=None)
        return

    with suppress(TelegramBadRequest):
        await callback.message.edit_text(
            text=f"{action_text} operation was aborted".lstrip().capitalize(),
            reply_markup=None,
        )
