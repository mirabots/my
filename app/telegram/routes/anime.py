from contextlib import suppress
from copy import copy
from datetime import datetime, timedelta

from aiogram import Bot, F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting

from app.common.config import cfg
from app.common.utils import get_logger, levelDEBUG, levelINFO
from app.crud import anime as crud_anime
from app.db.common import get_model_dict
from app.externals.myanimelist import get_anime_info
from app.telegram.utils.callbacks import (
    CallbackAnimeAction,
    CallbackAnimeAdd,
    CallbackAnimeChoose,
)
from app.telegram.utils.forms import FormAnimeAdd, FormAnimeRename
from app.telegram.utils.keyboards import (
    get_keyboard_abort,
    get_keyboard_anime,
    get_keyboard_anime_actions,
    get_keyboard_anime_add,
)

router = Router()
logger = get_logger(levelDEBUG if cfg.ENV == "dev" else levelINFO)


@router.message(Command("anime"))
async def anime_handler(message: types.Message):
    all_anime = await crud_anime.get_all_anime()

    main_keyboard = get_keyboard_anime(all_anime)
    main_keyboard.adjust(1)

    add_keyboard = get_keyboard_anime_add()
    main_keyboard.attach(add_keyboard)

    abort_keyboard = get_keyboard_abort("anime", "End")
    main_keyboard.attach(abort_keyboard)

    with suppress(TelegramBadRequest):
        await message.answer(text="Anime:", reply_markup=main_keyboard.as_markup())


@router.callback_query(CallbackAnimeAdd.filter())
async def anime_add_handler(
    callback: types.CallbackQuery, callback_data: CallbackAnimeAdd, state: FSMContext
):
    with suppress(TelegramBadRequest):
        abort_keyboard = get_keyboard_abort("anime_a")

        await callback.message.edit_text(
            text="Add anime\nEnter MAL anime id:",
            reply_markup=abort_keyboard.as_markup(),
        )

        await state.set_data(
            {
                "outgoing_form_message_id": callback.message.message_id,
            }
        )
        await state.set_state(FormAnimeAdd.anime_id)


@router.message(FormAnimeAdd.anime_id)
async def anime_add_id_form(
    message: types.Message, state: FSMContext, bot: Bot
) -> None:
    state_data = await state.get_data()
    try:
        outgoing_form_message_id = state_data["outgoing_form_message_id"]
    except Exception:
        await state.clear()
        return

    with suppress(TelegramBadRequest):
        await bot.edit_message_reply_markup(
            chat_id=message.from_user.id,
            message_id=outgoing_form_message_id,
            reply_markup=None,
        )

    try:
        anime_id = int(message.text.rstrip())
        anime_info = await get_anime_info(anime_id)
        if anime_info.get("error_code") != None:
            raise
    except Exception:
        await state.clear()
        await message.answer(text="Wrong MAL anime id given")
        return

    last_info = await crud_anime.get_last_info(anime_id)
    if last_info:
        await state.clear()
        await message.answer(text="Anime exists")
        return

    abort_keyboard = get_keyboard_abort("anime_a")
    sended_message = await message.answer(
        text="Enter anime name:", reply_markup=abort_keyboard.as_markup()
    )
    await state.set_data(
        {"outgoing_form_message_id": sended_message.message_id, "anime_id": anime_id}
    )
    await state.set_state(FormAnimeAdd.anime_name)


@router.message(FormAnimeAdd.anime_name)
async def anime_add_name_form(
    message: types.Message, state: FSMContext, bot: Bot
) -> None:
    state_data = await state.get_data()

    outgoing_form_message_id = state_data["outgoing_form_message_id"]
    with suppress(TelegramBadRequest):
        await bot.edit_message_reply_markup(
            chat_id=message.from_user.id,
            message_id=outgoing_form_message_id,
            reply_markup=None,
        )

    anime_id = copy(state_data["anime_id"])
    anime_name = message.text.rstrip()
    await state.clear()

    anime_info = await get_anime_info(anime_id)
    if "mean" not in anime_info.keys():
        await message.answer(text="No anime data was given from MAL, aborted")
        return

    await crud_anime.add_anime_info(
        id=anime_id,
        name=anime_name,
        rank=anime_info["rank"],
        mean=anime_info["mean"],
        users_all=anime_info["users_all"],
        users_scored=anime_info["users_scored"],
        status=anime_info["status"],
        updated=anime_info["updated"],
    )
    await message.answer(text="Anime was added")


@router.callback_query(CallbackAnimeChoose.filter())
async def anime_info_handler(
    callback: types.CallbackQuery, callback_data: CallbackAnimeChoose
):
    anime_id = callback_data.id
    anime_info = get_model_dict(await crud_anime.get_last_info(anime_id))
    with suppress(TelegramBadRequest):
        message_info = [formatting.Bold(f"{anime_info['anime_name']}: \n")]
        for key in ("rank", "mean", "users_all", "users_scored", "status", "updated"):
            value = anime_info[key]
            if isinstance(value, str):
                info_str = value
            elif isinstance(value, datetime):
                info_str = value.strftime("%Y-%m-%d %H:%M:%S")
            elif value == None:
                info_str = "-"
            else:
                info_str = "{:,}".format(value).replace(",", " ")

            message_info.extend(
                [
                    formatting.Bold(f"{key.replace('_', ' ').capitalize()}:   "),
                    f" {info_str}\n",
                ]
            )
        message_text, message_entities = formatting.Text(*message_info).render()
        abort_keyboard = get_keyboard_abort("anime_i", "End")
        actions_keyboard = get_keyboard_anime_actions(anime_id)
        actions_keyboard.adjust(2)
        actions_keyboard.attach(abort_keyboard)

        await callback.message.edit_text(
            text=message_text,
            entities=message_entities,
            reply_markup=actions_keyboard.as_markup(),
        )


@router.callback_query(CallbackAnimeAction.filter(F.action == "Update"))
async def anime_update_handler(
    callback: types.CallbackQuery, callback_data: CallbackAnimeAction
):
    anime_id = callback_data.id
    anime_info = await get_anime_info(anime_id)

    if not anime_info:
        with suppress(TelegramBadRequest):
            await callback.message.edit_text(
                text=callback.message.text + "\nUpdate error",
                entities=callback.message.entities,
                reply_markup=None,
            )
            return

    last_info = get_model_dict(await crud_anime.get_last_info(anime_id))

    message_info = [formatting.Bold(f"{last_info['anime_name']}: \n")]
    for key in anime_info.keys():
        try:
            diff = anime_info[key] - last_info[key]
        except Exception:
            diff = None
        if isinstance(diff, timedelta):
            info_str = f"+{diff.days} d, {diff.seconds // 3600} h, {(diff.seconds // 60) % 60} m"
            diff_str = ""
        elif diff == None:
            if last_info[key] == anime_info[key]:
                info_str = last_info[key]
            else:
                info_str = f"{last_info[key]} -> {anime_info[key]}"
            diff_str = ""
        else:
            diff_str = "{:,}".format(round(diff, 3)).replace(",", " ")
            if diff >= 0:
                diff_str = "+" + diff_str
            info_str = "{:,}".format(anime_info[key]).replace(",", " ")
        message_info.extend(
            [
                formatting.Bold(f"{key.replace('_', ' ').capitalize()}:   "),
                f" {info_str}",
            ]
        )
        if diff_str:
            message_info.append(formatting.Italic(f" ({diff_str})"))
        message_info.append("\n")

    await crud_anime.add_anime_info(
        id=anime_id,
        name=last_info["anime_name"],
        rank=anime_info["rank"],
        mean=anime_info["mean"],
        users_all=anime_info["users_all"],
        users_scored=anime_info["users_scored"],
        status=anime_info["status"],
        updated=anime_info["updated"],
    )

    message_text, message_entities = formatting.Text(*message_info).render()

    with suppress(TelegramBadRequest):
        await callback.message.edit_text(
            text=message_text, entities=message_entities, reply_markup=None
        )


@router.callback_query(CallbackAnimeAction.filter(F.action == "Rename"))
async def anime_rename_handler(
    callback: types.CallbackQuery, callback_data: CallbackAnimeAction, state: FSMContext
):
    with suppress(TelegramBadRequest):
        await callback.message.edit_reply_markup(reply_markup=None)

        abort_keyboard = get_keyboard_abort("anime_r")
        sended_message = await callback.message.answer(
            text="Rename anime to:", reply_markup=abort_keyboard.as_markup()
        )

        await state.set_data(
            {
                "outgoing_form_message_id": sended_message.message_id,
                "anime_id": callback_data.id,
            }
        )
        await state.set_state(FormAnimeRename.anime_name)


@router.message(FormAnimeRename.anime_name)
async def anime_rename_form(
    message: types.Message, state: FSMContext, bot: Bot
) -> None:
    state_data = await state.get_data()
    try:
        outgoing_form_message_id = state_data["outgoing_form_message_id"]
    except Exception:
        await state.clear()
        return

    with suppress(TelegramBadRequest):
        await bot.edit_message_reply_markup(
            chat_id=message.from_user.id,
            message_id=outgoing_form_message_id,
            reply_markup=None,
        )

    await crud_anime.rename_anime(state_data["anime_id"], message.text.rstrip())
    await state.clear()
    await message.answer(text="Anime was renamed")


@router.callback_query(CallbackAnimeAction.filter(F.action == "Delete"))
async def anime_delete_handler(
    callback: types.CallbackQuery, callback_data: CallbackAnimeAction
):
    with suppress(TelegramBadRequest):
        await callback.message.edit_reply_markup(reply_markup=None)
        await crud_anime.delete_anime(callback_data.id)
        await callback.message.answer(text="Anime was deleted")
