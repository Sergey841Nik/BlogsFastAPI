from logging import getLogger

from pydantic import BaseModel
from sqlalchemy import select, update, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from core.models.base import User, Role


logger = getLogger(__name__)

async def find_one_or_none_by_id(user_id: int, session: AsyncSession):
    # Найти запись по ID
    logger.info(f"Поиск {User.__name__} с ID: {user_id}")
    try:
        query = select(User).filter_by(id=user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        if user:
            logger.info(f"Запись с ID {user_id} найдена.")
        else:
            logger.info(f"Запись с ID {user_id} не найдена.")
        return user
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при поиске записи с ID {user_id}: {e}")
        raise


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

async def get_all_users(session: AsyncSession, filters: BaseModel | None):
    if filters:
        filter_dict = filters.model_dump(exclude_unset=True)
    else:
        filter_dict = {}

    logger.info("Поиск одной записи по фильтрам: %s" % filter_dict)

    query = select(User).filter_by(**filter_dict)
    result = await session.execute(query)
    users = result.scalars().all()
    if users:
        logger.info("Запись найдена по фильтрам: %s" % filter_dict)
    else:
        logger.info("Запись не найдена по фильтрам: %s" % filter_dict)
    return users


async def add_users(session: AsyncSession, values: BaseModel):
    # Добавить одну запись
    values_dict = values.model_dump(exclude_unset=True)

    logger.info("Добавление записи с параметрами: %s" % values_dict["password"])

    new_user = User(**values_dict)
    session.add(new_user)

    await session.commit()
    logger.info(f"Запись успешно добавлена.")
    return new_user

async def change_user_role(session: AsyncSession, values: BaseModel):
    values_dict = values.model_dump(exclude_unset=True)

    logger.info("Изменение роли с параметрами: %s" % values_dict)
    # stmt = text("""
    #             UPDATE users SET role_id = :role_id WHERE email = :email
    #         """)
    # stmt = stmt.bindparams(role_id=values_dict["role_id"], email=values_dict["email"])
    stmt = (
            update(User)
            .where(User.email == values_dict["email"])
            .values(role_id=values_dict["role_id"])
            )
    await session.execute(stmt)
    await session.commit()


async def add_new_role(session: AsyncSession, values: BaseModel):
    values_dict = values.model_dump(exclude_unset=True)

    logger.info("Добавление роль с параметрами: %s" % values_dict)

    new_role = Role(**values_dict)
    session.add(new_role)

    await session.commit()
    logger.info(f"Роль успешно добавлена.")
    return new_role

async def delete_role(
        role_id: int,
        session: AsyncSession,
):
    query = select(Role).filter_by(id=role_id)
    result = await session.execute(query)
    role = result.scalar_one_or_none()
    
    if not role:
        return {
            'message': f"Роль с ID {role_id} не найдена.",
            'status': 'error'
        }
    
    await session.delete(role)
    await session.flush()

    return {
            'message': f"Роль с ID {role_id} успешно удален.",
            'status': 'success'
        }