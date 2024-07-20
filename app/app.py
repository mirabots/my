from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from litestar import Litestar, Request, Response
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR

from app.api.webhooks import router as litestar_router
from app.common.config import cfg
from app.common.utils import get_logger, get_logging_config, levelDEBUG, levelINFO
from app.db.common import _engine, check_db
from app.jobs.anime import anime_job
from app.telegram.bot import bot, dp
from app.telegram.commands import COMMANDS_TG
from app.telegram.middlewares import AuthChatMiddleware
from app.telegram.routes.admin import router as telegram_router_admin
from app.telegram.routes.anime import router as telegram_router_anime
from app.telegram.routes.base import router as telegram_router_base

logger = get_logger(levelDEBUG if cfg.ENV == "dev" else levelINFO)
logging_config = get_logging_config(levelDEBUG if cfg.ENV == "dev" else levelINFO)


@asynccontextmanager
async def lifespan_function(app: Litestar) -> AsyncGenerator[None, None]:
    await check_db(logger)

    # webhook_info = await bot.get_webhook_info()
    # if webhook_info.url != f"https://{cfg.DOMAIN}/webhooks/telegram":
    await bot.set_webhook(
        url=f"https://{cfg.DOMAIN}/webhooks/telegram",
        secret_token=cfg.TELEGRAM_SECRET,
        drop_pending_updates=True,
    )

    dp.include_router(telegram_router_base)
    dp.include_router(telegram_router_admin)
    dp.include_router(telegram_router_anime)
    dp.message.middleware(AuthChatMiddleware())
    await bot.set_my_commands(COMMANDS_TG)
    await bot.set_my_description("mirakzen personal bot")

    await anime_job.start()

    if cfg.ENV != "dev":
        await bot.send_message(chat_id=cfg.OWNER_ID, text="ADMIN MESSAGE\nBOT STARTED")

    try:
        yield
    finally:
        await bot.session.close()
        await _engine.dispose()

        await anime_job.stop()


def internal_server_error_handler(request: Request, exc: Exception) -> Response:
    logger.warning(exc)
    return Response(
        status_code=500,
        content={"detail": "Server error"},
    )


app = Litestar(
    [litestar_router],
    lifespan=[lifespan_function],
    logging_config=logging_config,
    exception_handlers={
        HTTP_500_INTERNAL_SERVER_ERROR: internal_server_error_handler,
    },
)
