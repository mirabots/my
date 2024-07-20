import sys
from datetime import time
from time import sleep

import httpx
import requests
import yaml
from aiofile import async_open

from app.common.utils import (
    disable_unnecessary_loggers,
    get_args,
    get_logger,
    levelDEBUG,
    levelINFO,
)


class ConfigManager:
    def __init__(self) -> None:
        self._config_file = "config/config.yaml"
        self.BOT_ACTIVE = True

        self.secrets_data = {}
        args = get_args()
        self.ENV = args.env

        if self.ENV == "dev":
            disable_unnecessary_loggers()

        self.logger = get_logger(levelDEBUG if self.ENV == "dev" else levelINFO)

        self.load_creds_sync()
        error = self.get_creds()
        if error:
            self.logger.error(error)
            sys.exit(1)
        self.logger.info("Creds from config were loaded")

        error = self.load_secrets_sync()
        if error:
            self.logger.error(error)
            self.logger.error("waiting 120 secs for secrets storage")
            sleep(120)
        error = self.load_secrets_sync()
        if error:
            self.logger.error(error)
            sys.exit(1)

        no_secrets = self.check_secrets(get_db=True)
        if no_secrets:
            self.logger.error(f"No secrets found: {no_secrets}")
            sys.exit(1)
        self.apply_secrets(get_db=True)
        self.logger.info("Secrets were loaded")

    def load_creds_sync(self) -> None:
        with open(self._config_file, "r") as f:
            self.creds_data = yaml.safe_load(f.read())

    async def load_creds_async(self) -> None:
        async with async_open(self._config_file, "r") as f:
            self.creds_data = yaml.safe_load(await f.read())

    def get_creds(self) -> str:
        try:
            self.SECRETS_DOMAIN = self.creds_data["secrets_domain"] or ""
            self.SECRETS_HEADER = self.creds_data["secrets_header"] or ""
            self.SECRETS_TOKEN = self.creds_data["secrets_token"] or ""
        except Exception:
            return "Error getting secrets creds from config-file"
        return ""

    async def update_creds(self, updated_creds: dict) -> None:
        self.creds_data.update(updated_creds)

        self.SECRETS_DOMAIN = self.data["secrets_domain"]
        self.SECRETS_HEADER = self.data["secrets_header"]
        self.SECRETS_TOKEN = self.data["secrets_token"]

        async with async_open(self._config_file, "w") as f:
            yaml.dump(self.creds_data, f)

    def load_secrets_sync(self) -> str:
        try:
            response = requests.get(
                f"{self.SECRETS_DOMAIN}/api/secrets",
                headers={self.SECRETS_HEADER: self.SECRETS_TOKEN},
            )
            if response.status_code != 200:
                return (
                    f"Error getting data from secrets response - {response.status_code}"
                )
        except Exception as e:
            return f"Error getting data from secrets - {e}"

        try:
            self.secrets_data = response.json()["content"]
            return ""
        except Exception:
            return "Error getting secrets from response"

    async def load_secrets_async(self) -> str:
        try:
            async with httpx.AsyncClient(
                base_url=self.SECRETS_DOMAIN,
                headers={self.SECRETS_HEADER: self.SECRETS_TOKEN},
            ) as ac:
                response = await ac.get("/api/secrets")
                if response.status_code != 200:
                    return f"Error getting data from secrets response - {response.status_code}"
        except Exception as e:
            return f"Error getting data from secrets - {e}"

        try:
            self.secrets_data = response.json()["content"]
            return ""
        except Exception:
            return "Error getting secrets from response"

    def check_secrets(self, get_db: bool) -> list[str]:
        no_secrets = []

        # database: need to get only at startup
        if get_db:
            db_data = self.secrets_data.get(f"{self.ENV}/db")
            try:
                db_data["connection string"]
            except Exception:
                no_secrets.append(f"{self.ENV}/db")

        # owner
        owner_data = self.secrets_data.get(f"{self.ENV}/owner")
        try:
            owner_data["login"]
            owner_data["id"]
        except Exception:
            no_secrets.append(f"{self.ENV}/owner")

        # domain
        domain_data = self.secrets_data.get(f"{self.ENV}/domain")
        try:
            domain_data["domain"]
        except Exception:
            no_secrets.append(f"{self.ENV}/domain")

        # myanimelist
        mal_data = self.secrets_data.get(f"{self.ENV}/mal")
        try:
            mal_data["api_url"]
            mal_data["header"]
            mal_data["client_id"]
        except Exception:
            no_secrets.append(f"{self.ENV}/mal")

        # telegram
        telegram_data = self.secrets_data.get(f"{self.ENV}/telegram")
        try:
            telegram_data["token"]
            telegram_data["secret"]
            ALLOWED = telegram_data["allowed"]
            if not isinstance(ALLOWED, list):
                raise
        except Exception:
            no_secrets.append(f"{self.ENV}/telegram")

        # anime update
        anime_data = self.secrets_data.get(f"{self.ENV}/jobs/anime")
        try:
            UPDATE_TYPE = anime_data["type"]
            if UPDATE_TYPE == "delay":
                anime_data["delay_value"]
                DELAY_UNIT = anime_data["delay_unit"]
                if DELAY_UNIT not in ("minutes", "hours", "days"):
                    raise
            elif UPDATE_TYPE == "update_at":
                time.fromisoformat(f"{anime_data['update_at']}:00")
            else:
                raise
        except Exception:
            no_secrets.append(f"{self.ENV}/jobs/anime")

        # notifications
        notifications_data = self.secrets_data.get(f"{self.ENV}/notifications")
        try:
            notifications_data["secret"]
            ALLOWED = notifications_data["allowed"]
            if not isinstance(ALLOWED, list):
                raise
        except Exception:
            no_secrets.append(f"{self.ENV}/notifications")

        return no_secrets

    def apply_secrets(self, get_db: bool) -> None:
        # database: need to get only at startup
        if get_db:
            db_data = self.secrets_data.get(f"{self.ENV}/db")
            self.DB_CONNECTION_STRING = db_data["connection string"]

        # owner
        owner_data = self.secrets_data.get(f"{self.ENV}/owner")
        self.OWNER_LOGIN = owner_data["login"]
        self.OWNER_ID = owner_data["id"]

        # domain
        domain_data = self.secrets_data.get(f"{self.ENV}/domain")
        self.DOMAIN = domain_data["domain"]

        # myanimelist
        mal_data = self.secrets_data.get(f"{self.ENV}/mal")
        self.MAL_API = mal_data["api_url"]
        self.MAL_HEADER = mal_data["header"]
        self.MAL_CLIENT_ID = mal_data["client_id"]

        # telegram
        telegram_data = self.secrets_data.get(f"{self.ENV}/telegram")
        self.TELEGRAM_TOKEN = telegram_data["token"]
        self.TELEGRAM_SECRET = telegram_data["secret"]
        self.TELEGRAM_ALLOWED = telegram_data["allowed"]

        # anime update
        anime_data = self.secrets_data.get(f"{self.ENV}/jobs/anime")
        self.ANIME_UPDATE_TYPE = anime_data["type"]
        self.ANIME_UPDATE_DELAY_VALUE = anime_data.get("delay_value")
        self.ANIME_UPDATE_DELAY_UNIT = anime_data.get("delay_unit")
        self.ANIME_UPDATE_AT = anime_data.get("update_at")

        # notifications
        notifications_data = self.secrets_data.get(f"{self.ENV}/notifications")
        self.NOTIFICATIONS_SECRET = notifications_data["secret"]
        self.NOTIFICATIONS_ALLOWED = notifications_data["allowed"]


cfg = ConfigManager()
