import json
from contextlib import suppress
from datetime import datetime, timezone
from typing import Any

from aiogram import types
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils import formatting
from litestar import Router, get, post
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_200_OK

from app.common.config import cfg
from app.common.utils import get_logger, levelDEBUG, levelINFO
from app.telegram.bot import bot, dp

logger = get_logger(levelDEBUG if cfg.ENV == "dev" else levelINFO)


@post("/webhooks/telegram")
async def webhook_telegram(data: dict[str, Any], headers: dict[str, str]) -> Any:
    header_secret = headers.get("X-Telegram-Bot-Api-Secret-Token".lower(), "")
    if header_secret != cfg.TELEGRAM_SECRET:
        logger.error("Secrets don't match")
        raise HTTPException(status_code=401, detail="NOT VERIFIED")
    logger.debug(data)
    telegram_update = types.Update(**data)
    return await dp.feed_update(bot=bot, update=telegram_update)


@post("/webhooks/notifications", status_code=HTTP_200_OK)
async def webhook_notifications_post(
    data: dict[str, Any], headers: dict[str, str]
) -> dict[str, str]:
    header_secret = headers.get("X-MyBot-Notifications-Secret-Token".lower(), "")
    if header_secret != cfg.NOTIFICATIONS_SECRET_POST:
        logger.error("Secrets don't match")
        raise HTTPException(status_code=401, detail="NOT VERIFIED")

    notification_sender = data["sender"]
    if notification_sender not in cfg.NOTIFICATIONS_ALLOWED:
        logger.error("Sender not allowed")
        raise HTTPException(status_code=401, detail="NOT ALLOWED")

    notification_info: dict[str, Any] = data["content"]
    sender = notification_info["sender"]
    message = notification_info["message"]
    payload = notification_info.get("payload")

    if not payload:
        message_text, message_entities = formatting.Text(
            formatting.Bold(f"{sender}:"), "\n", message
        ).render()
        with suppress(TelegramBadRequest):
            await bot.send_message(
                chat_id=cfg.OWNER_ID, text=message_text, entities=message_entities
            )
    else:
        jsoned_payload = json.dumps(
            payload, ensure_ascii=False, indent=4, separators=(",", ": ")
        )

        if len(sender + message + jsoned_payload) > 4000:
            current_datetime = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
            file = types.BufferedInputFile(
                jsoned_payload.encode(), f"{sender}_{current_datetime}.json"
            )
            message_text, message_entities = formatting.Text(
                formatting.Bold(f"{sender}:"), "\n", message
            ).render()
            with suppress(TelegramBadRequest):
                await bot.send_document(
                    chat_id=cfg.OWNER_ID,
                    caption=message_text,
                    caption_entities=message_entities,
                    document=file,
                )
        else:
            message_text, message_entities = formatting.Text(
                formatting.Bold(f"{sender}:"),
                "\n",
                message,
                "\n",
                formatting.Pre(jsoned_payload, language="json"),
            ).render()
            with suppress(TelegramBadRequest):
                await bot.send_message(
                    chat_id=cfg.OWNER_ID, text=message_text, entities=message_entities
                )

    return {"description": "Got"}


@get("/webhooks/notifications", status_code=HTTP_200_OK)
async def webhook_notifications_get(
    secret: str = "", sender: str = "", message: str = ""
) -> str:
    if secret != cfg.NOTIFICATIONS_SECRET_GET:
        logger.error("Secrets don't match")
        raise HTTPException(status_code=401, detail="NOT VERIFIED")

    if sender not in cfg.NOTIFICATIONS_ALLOWED:
        logger.error("Sender not allowed")
        raise HTTPException(status_code=401, detail="NOT ALLOWED")

    message_text, message_entities = formatting.Text(
        formatting.Bold(f"{sender}:"), "\n", message
    ).render()
    with suppress(TelegramBadRequest):
        await bot.send_message(
            chat_id=cfg.OWNER_ID, text=message_text, entities=message_entities
        )

    return "Notification sended"


router = Router(
    path="",
    route_handlers=[
        webhook_telegram,
        webhook_notifications_post,
        webhook_notifications_get,
    ],
)
