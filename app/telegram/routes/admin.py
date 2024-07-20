from contextlib import suppress

from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command

from app.common.config import cfg
from app.common.utils import get_logger, levelDEBUG, levelINFO

router = Router()
logger = get_logger(levelDEBUG if cfg.ENV == "dev" else levelINFO)


@router.message(Command("secrets_reload"))
async def secrets_reload_handler(message: types.Message):
    logger.info("Reloading secrets")
    error = await cfg.load_secrets_async()
    if error:
        logger.error(error)
        with suppress(TelegramBadRequest):
            await message.answer(text=error)
            return

    no_secrets = cfg.check_secrets(get_db=False)
    if no_secrets:
        logger.error(f"No secrets found: {no_secrets}")
        with suppress(TelegramBadRequest):
            await message.answer(text=f"No secrets found:\n{str(no_secrets)}")
            return

    cfg.apply_secrets(get_db=False)
    logger.info("Secrets were reloaded")
    with suppress(TelegramBadRequest):
        await message.answer(text="Reloaded")
