from contextlib import suppress
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, types
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.common.config import cfg


class AuthChatMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[
            [types.Message | types.CallbackQuery, Dict[str, Any]], Awaitable[Any]
        ],
        event: types.Message | types.CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        command = (
            getattr(event, "text", "") or getattr(event, "caption", "") or ""
        ).strip()
        user_id = event.from_user.id

        if user_id != cfg.OWNER_ID:
            if command.startswith("/start"):
                with suppress(TelegramBadRequest, TelegramForbiddenError):
                    await event.answer("You are not allowed to use this bot")
            return

        return await handler(event, data)
