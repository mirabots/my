from contextlib import suppress
from datetime import datetime, time, timedelta, timezone

from aiogram.exceptions import TelegramBadRequest
from aiogram.utils import formatting

from app.common.config import cfg
from app.crud import anime as crud_anime
from app.db.common import get_model_dict
from app.externals.myanimelist import get_anime_info
from app.jobs._base import JobBase
from app.telegram.bot import bot


class AnimeJob(JobBase):
    def get_interval(self) -> int:
        try:
            if cfg.ANIME_UPDATE_TYPE == "delay":
                coeff = 1
                if cfg.ANIME_UPDATE_DELAY_UNIT == "minutes":
                    coeff = 60
                elif cfg.ANIME_UPDATE_DELAY_UNIT == "hours":
                    coeff = 60 * 60
                elif cfg.ANIME_UPDATE_DELAY_UNIT == "days":
                    coeff = 60 * 60 * 24
                return cfg.ANIME_UPDATE_DELAY_VALUE * coeff
            elif cfg.ANIME_UPDATE_TYPE == "update_at":
                update_at = time.fromisoformat(f"{cfg.ANIME_UPDATE_AT}:00")

                current_time = datetime.now(timezone.utc)
                planned_time = datetime(
                    current_time.year,
                    current_time.month,
                    current_time.day,
                    update_at.hour,
                    update_at.minute,
                    tzinfo=timezone.utc,
                )
                return (planned_time - current_time).seconds
        except Exception:
            self.logger.info(f"{self.job_name}: wrong interval params")
            return -1

    async def loop_task(self) -> None:
        curr_time = datetime.now(tz=timezone.utc)

        all_anime = await crud_anime.get_all_anime()
        for anime in all_anime:
            anime_id = anime["id"]
            anime_name = anime["name"]

            anime_info = await get_anime_info(anime_id)

            if not anime_info:
                with suppress(TelegramBadRequest):
                    await bot.send_message(
                        chat_id=cfg.OWNER_ID, text=f"Didn't get {anime_name} anime info"
                    )
                    return

            last_info = get_model_dict(await crud_anime.get_last_info(anime_id))

            message_info = [formatting.Bold(f"{anime_name}: \n")]
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
                        info_str = f"last_info[key] -> {anime_info[key]}"
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
                name=anime_name,
                rank=anime_info["rank"],
                mean=anime_info["mean"],
                users_all=anime_info["users_all"],
                users_scored=anime_info["users_scored"],
                status=anime_info["status"],
                updated=curr_time,
            )

            message_text, message_entities = formatting.Text(*message_info).render()

            with suppress(TelegramBadRequest):
                await bot.send_message(
                    chat_id=cfg.OWNER_ID, text=message_text, entities=message_entities
                )


anime_job = AnimeJob(job_name="Anime")
