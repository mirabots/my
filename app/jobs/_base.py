import asyncio
from abc import ABC, abstractmethod

from app.common.config import cfg
from app.common.utils import get_logger, levelDEBUG, levelINFO


class JobBase(ABC):
    def __init__(self, job_name: str) -> None:
        self.job_name = job_name
        self.logger = get_logger(levelDEBUG if cfg.ENV == "dev" else levelINFO)

    @abstractmethod
    def get_interval(self) -> int:
        pass

    @abstractmethod
    async def loop_task(self) -> None:
        pass

    async def loop(self) -> None:
        while True:
            try:
                interval = self.get_interval()
                if interval == -1:
                    await self.stop()
                    return
                await asyncio.sleep(interval)
                await self.loop_task()
            except asyncio.CancelledError:
                return
            except Exception as e:
                self.logger.error(f"Loop Job for {self.job_name}: {str(e)}")

    async def start(self):
        self.logger.info(f"{self.job_name}: job start")
        self.task = asyncio.create_task(self.loop())

    async def stop(self):
        try:
            self.logger.info(f"{self.job_name}: job stop")
            self.task.cancel()
        except Exception as e:
            self.logger.warning(f"{self.job_name}: {str(e)}")
