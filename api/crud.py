from logging import getLogger

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel

from core.models.base import Blog, Tag, BlogTag
from .schemes import BlogFullResponse

logger = getLogger(__name__)


async def add_tags_to_bd(session: AsyncSession, tag_names: list[str]) -> list[int]:
    """
    Метод для добавления тегов в базу данных.
    Принимает список строк (тегов), проверяет, существуют ли они в базе данных,
    добавляет новые и возвращает список ID тегов.
    Args:
        session (AsyncSession): Сессия базы данных.
        tag_names (list[str]): Список тегов в нижнем регистре.
    Returns:
        list[int]: Список ID тегов.
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


async def add_blog_tags_to_bd(
    session: AsyncSession, blog_tag_pairs: list[dict]
) -> None:
    """
    Функция добавляет связки блогов и тегов в базу данных.
    Args:
        session (AsyncSession): Объект сессии базы данных.
        blog_tag_pairs (list[dict]): Список словарей, где каждый словарь содержит пару blog_id и tag_id.
    Returns:
        None
    """
    # Сначала создаем все объекты BlogTag
    blog_tag_instances = []
    for pair in blog_tag_pairs:
        blog_id = pair.get("blog_id")
        tag_id = pair.get("tag_id")
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
            logger.info(
                "%s связок блогов и тегов успешно добавлено." % len(blog_tag_instances)
            )
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Ошибка при добавлении связок блогов и тегов: %s" % e)
            raise e
    else:
        logger.warning("Нет валидных данных для добавления в таблицу blog_tags.")


async def get_full_blog_info(
    session: AsyncSession, blog_id: int, author_id: int | None = None
):
    """
    Метод для получения полной информации о блоге, включая данные об авторе и тегах.
    Для опубликованных блогов доступ к информации открыт всем пользователям.
    Для черновиков доступ открыт только автору блога.
    """
    query = (
        select(Blog)
        .options(
            joinedload(Blog.user),  # Подгружаем данные о пользователе (авторе)
            selectinload(Blog.tags),  # Подгружаем связанные теги
        )
        .filter_by(id=blog_id)
    )

    # Выполняем запрос
    result = await session.execute(query)

    blog = result.scalar_one_or_none()

    logger.info("Blog %s" % blog)

    if not blog:
        return {
            "message": f"Блог с ID {blog_id} не найден или у вас нет прав на его просмотр.",
            "status": "error",
        }

    if blog.status == "draft" and (author_id != blog.author):
        return {
            "message": "Этот блог находится в статусе черновика, и доступ к нему имеют только авторы.",
            "status": "error",
        }

    return blog


async def delete_blog(
    id_blog: int,
    author_id: int,
    session: AsyncSession,
):
    query = select(Blog).filter_by(id=id_blog)
    result = await session.execute(query)
    blog = result.scalar_one_or_none()

    if not blog:
        return {"message": f"Блог с ID {id_blog} не найден.", "status": "error"}
    if blog.author != author_id:
        return {"message": "У вас нет прав на удаление этого блога.", "status": "error"}

    await session.delete(blog)
    await session.flush()

    return {"message": f"Блог с ID {id_blog} успешно удален.", "status": "success"}


async def change_blog_status(
    blog_id: int,
    new_status: str,
    author_id: int,
    session: AsyncSession,
) -> dict:
    """
    Метод для изменения статуса блога.

    Args:
        blog_id (int): ID блога.
        new_status (str): Новый статус блога. Должен быть 'draft' или 'published'.
        author_id (int): ID автора блога.
        session (AsyncSession): Сессия базы данных.

    Returns:
        dict: Словарь с информацией о результате операции.
   """

    if new_status not in ["draft", "published"]:
        return {
            "message": "Недопустимый статус. Используйте 'draft' или 'published'.",
            "status": "error",
        }
    try:
        query = select(Blog).filter_by(id=blog_id)
        result = await session.execute(query)
        blog = result.scalar_one_or_none()

        if not blog:
            return {"message": f"Блог с ID {blog_id} не найден.", "status": "error"}
        if blog.author != author_id:
            return {
                "message": "У вас нет прав на изменение статуса этого блога.",
                "status": "error",
            }
        if blog.status == new_status:
            return {
                "message": f"Статус блога с ID {blog_id} уже {new_status}.",
                "status": "error",
            }

        blog.status = new_status
        await session.flush()
        return {
            "message": f"Статус блога с ID {blog_id} успешно изменен на {new_status}.",
            "status": "success",
        }

    except SQLAlchemyError as e:
        await session.rollback()
        return {
            "message": f"Произошла ошибка при изменении статуса блога: {str(e)}",
            "status": "error",
        }
    
    
async def get_blog_list(
        session: AsyncSession, 
        author_id: int | None = None, 
        tag: str | None = None,
        page: int = 1, 
        page_size: int = 10
):
    
    # Ограничение параметров
    page_size = max(3, min(page_size, 100))
    page = max(1, page)

    # Начальная сборка базового запроса
    base_query = select(Blog).options(
        joinedload(Blog.user),
        selectinload(Blog.tags)
    ).filter_by(status='published')

    # Фильтрация по автору
    if author_id is not None:
        base_query = base_query.filter_by(author=author_id)

    # Фильтрация по тегу
    if tag:
        base_query = base_query.join(Blog.tags).filter(Blog.tags.any(Tag.name.ilike(f"%{tag.lower()}%")))

    # Подсчет общего количества записей
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await session.scalar(count_query)

    # Если записей нет, возвращаем пустой результат
    if not total_result:
        return {
            "page": page,
            "total_page": 0,
            "total_result": 0,
            "blogs": []
        }

    # Расчет количества страниц
    total_page = (total_result + page_size - 1) // page_size

    # Применение пагинации
    offset = (page - 1) * page_size
    paginated_query = base_query.offset(offset).limit(page_size)

    # Выполнение запроса и получение результатов
    result = await session.execute(paginated_query)
    blogs = result.scalars().all()

    # Удаление дубликатов блогов по их ID
    unique_blogs = []
    seen_ids = set()
    for blog in blogs:
        if blog.id not in seen_ids:
            unique_blogs.append(BlogFullResponse.model_validate(blog))
            seen_ids.add(blog.id)

    # Логирование
    filters = []
    if author_id is not None:
        filters.append(f"author_id={author_id}")
    if tag:
        filters.append(f"tag={tag}")
    filter_str = " & ".join(filters) if filters else "no filters"

    logger.info(f"Page {page} fetched with {len(blogs)} blogs, filters: {filter_str}")
    # Формирование результата
    return {
        "page": page,
        "total_page": total_page,
        "total_result": total_result,
        "blogs": unique_blogs
    }