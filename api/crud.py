from logging import getLogger

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel

from core.models.base import Blog, Tag, BlogTag

logger = getLogger(__name__)

async def add_tags_to_bd(session: AsyncSession, tag_names: list[str]) -> list[int]:
    """
    Метод для добавления тегов в базу данных.
    Принимает список строк (тегов), проверяет, существуют ли они в базе данных,
    добавляет новые и возвращает список ID тегов.

    :param session: Сессия базы данных.
    :param tag_names: Список тегов в нижнем регистре.
    :return: Список ID тегов.
    """
    tag_ids = []
    for tag_name in tag_names:
        tag_name = tag_name.lower()  # Приводим тег к нижнему регистру
        # Пытаемся найти тег в базе данных
        stmt = select(Tag).filter_by(name=tag_name)
        result = await session.execute(stmt)
        tag = result.scalars().first()

        if tag:
            # Если тег найден, добавляем его ID в список
            tag_ids.append(tag.id)
        else:
            # Если тег не найден, создаем новый тег
            new_tag = Tag(name=tag_name)
            session.add(new_tag)
            try:
                await session.flush()  # Это создает новый тег и позволяет получить его ID
                logger.info("Тег '%s' добавлен в базу данных." % tag_name)
                tag_ids.append(new_tag.id)
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error("Ошибка при добавлении тега '%s': %s" % (tag_name, e))
                raise e

    return tag_ids

async def add_blog_to_bd(session: AsyncSession, values: BaseModel):
    # Добавить одну запись
    values_dict = values.model_dump(exclude_unset=True)

    logger.info("Добавление записи с параметрами: %s" % values_dict)

    new_blogs = Blog(**values_dict)
    session.add(new_blogs)

    await session.commit()
    logger.info(f"Запись успешно добавлена.")
    return new_blogs

async def add_blog_tags_to_bd(session: AsyncSession, blog_tag_pairs: list[dict]) -> None:
    """
    Метод для массового добавления связок блогов и тегов в базу данных.
    Принимает список словарей с blog_id и tag_id, добавляет соответствующие записи.

    :param session: Сессия базы данных.
    :param blog_tag_pairs: Список словарей с ключами 'blog_id' и 'tag_id'.
    :return: None
    """
    # Сначала создаем все объекты BlogTag
    blog_tag_instances = []
    for pair in blog_tag_pairs:
        blog_id = pair.get('blog_id')
        tag_id = pair.get('tag_id')
        if blog_id and tag_id:
            # Создаем объект BlogTag
            blog_tag = BlogTag(blog_id=blog_id, tag_id=tag_id)
            blog_tag_instances.append(blog_tag)
        else:
            logger.warning(f"Пропущен неверный параметр в паре: {pair}")

    if blog_tag_instances:
        session.add_all(blog_tag_instances)  # Добавляем все объекты за один раз
        try:
            await session.flush()  # Применяем изменения и сохраняем записи в базе данных
            logger.info("%s связок блогов и тегов успешно добавлено." % len(blog_tag_instances))
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Ошибка при добавлении связок блогов и тегов: %s" % e)
            raise e
    else:
        logger.warning("Нет валидных данных для добавления в таблицу blog_tags.")