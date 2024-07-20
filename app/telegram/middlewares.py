from contextlib import suppress
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, types
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.common.config import cfg


class AuthChatMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any],
    ) -> Any:
        command = event.text.rstrip()
        user_id = event.from_user.id
        user_name = event.from_user.username

        if command == "/start":
            if user_name.lower() not in cfg.TELEGRAM_ALLOWED:
                with suppress(TelegramBadRequest, TelegramForbiddenError):
                    await event.answer("You are not allowed to use this bot")
                return
            else:
                return await handler(event, data)

        if user_id != cfg.OWNER_ID:
            return

        return await handler(event, data)
