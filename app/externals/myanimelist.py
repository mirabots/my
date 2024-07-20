from datetime import datetime, timezone

import httpx

from app.common.config import cfg
from app.common.utils import get_logger, levelDEBUG, levelINFO

logger = get_logger(levelDEBUG if cfg.ENV == "dev" else levelINFO)


async def get_anime_info(id: int) -> dict[str, float | int | datetime]:
    fields = ["mean", "num_list_users", "num_scoring_users", "rank", "status"]
    try:
        async with httpx.AsyncClient(
            base_url=cfg.MAL_API,
            params={"fields": ",".join(fields)},
            headers={cfg.MAL_HEADER: cfg.MAL_CLIENT_ID},
        ) as ac:
            response = await ac.get(f"/anime/{id}")
            if response.status_code != 200:
                details = ""
                try:
                    details = str(response.json())
                except Exception:
                    pass
                logger.error(
                    f"Error getting anime {id} info. Code: {response.status_code}, Details: {details}."
                )
                return {"error_code": response.status_code}
    except Exception:
        logger.error(f"Error getting anime {id} info from MAL api")
        return {"error_code": ""}

    try:
        anime_info = response.json()
        return {
            "rank": anime_info["rank"],
            "mean": anime_info["mean"],
            "users_all": anime_info["num_list_users"],
            "users_scored": anime_info["num_scoring_users"],
            "status": anime_info["status"],
            "updated": datetime.now(timezone.utc),
        }
    except Exception:
        logger.error(f"Error getting anime {id} details from API response")
        return {}
