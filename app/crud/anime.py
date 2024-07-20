from datetime import datetime

from sqlalchemy import delete, desc, insert, select, update

from app.db.common import async_session
from app.db.models import AnimeInfo


async def get_all_anime() -> list[AnimeInfo]:
    async with async_session() as session, session.begin():
        all_anime = (
            await session.execute(
                select(AnimeInfo.anime_id, AnimeInfo.anime_name).distinct()
            )
        ).fetchall()
        return [{"id": anime[0], "name": anime[1]} for anime in all_anime]


async def add_anime_info(
    id: int,
    name: str,
    rank: int,
    mean: float,
    users_all: int,
    users_scored: int,
    status: str,
    updated: datetime,
) -> None:
    async with async_session() as session, session.begin():
        await session.execute(
            insert(AnimeInfo).values(
                anime_id=id,
                anime_name=name,
                rank=rank,
                mean=mean,
                users_all=users_all,
                users_scored=users_scored,
                status=status,
                updated=updated,
            )
        )


async def delete_anime(id: int) -> None:
    async with async_session() as session, session.begin():
        await session.execute(delete(AnimeInfo).where(AnimeInfo.anime_id == id))


async def rename_anime(id: int, new_name: str) -> None:
    async with async_session() as session, session.begin():
        await session.execute(
            update(AnimeInfo)
            .where(AnimeInfo.anime_id == id)
            .values(anime_name=new_name)
        )


async def get_last_info(id: int) -> AnimeInfo:
    async with async_session() as session, session.begin():
        return await session.scalar(
            select(AnimeInfo)
            .where(AnimeInfo.anime_id == id)
            .order_by(desc(AnimeInfo.updated))
            .limit(1)
        )
