from logging import getLogger

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.base import User


logger = getLogger(__name__)


async def find_one_or_none_users(session: AsyncSession, filters: BaseModel):
    filter_dict = filters.model_dump(exclude_unset=True)

    logger.info("Поиск одной записи по фильтрам: %s" % filter_dict)

    query = select(User).filter_by(**filter_dict)
    result = await session.execute(query)

    user = result.scalar_one_or_none()
    
    if user:
        logger.info("Запись найдена по фильтрам: %s" % filter_dict)
    else:
        logger.info("Запись не найдена по фильтрам: %s" % filter_dict)
    return user


async def add_users(session: AsyncSession, values: BaseModel):
        # Добавить одну запись
        values_dict = values.model_dump(exclude_unset=True)

        logger.info("Добавление записи с параметрами: %s" % values_dict["password"])

        new_user = User(**values_dict)
        session.add(new_user)
    
        await session.commit()
        logger.info(f"Запись успешно добавлена.")
        return new_user
       