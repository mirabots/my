from datetime import datetime

from sqlalchemy import MetaData
from sqlalchemy.orm import Mapped, declarative_base, mapped_column
from sqlalchemy.types import TIMESTAMP

SCHEMA = "mytgbot"
Base = declarative_base(metadata=MetaData(schema=SCHEMA))


class AnimeInfo(Base):
    __tablename__ = "anime_info"

    id: Mapped[int] = mapped_column(primary_key=True)
    anime_id: Mapped[int] = mapped_column(nullable=False)
    anime_name: Mapped[str] = mapped_column(nullable=False)
    rank: Mapped[int] = mapped_column(nullable=True)
    mean: Mapped[float] = mapped_column(nullable=False)
    users_all: Mapped[int] = mapped_column(nullable=False)
    users_scored: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)
    updated: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
