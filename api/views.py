from logging import getLogger

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi.responses import JSONResponse

from api.dependencies import get_current_user_optional

from core.models.base import User
from core.models.db_helper import db_helper
from .schemes import (
    BlogCreateSchemaBase,
    BlogCreateSchemaAdd,
    BlogFullResponse,
    BlogNotFind,
)
from .crud import (
    add_blog_to_bd,
    add_tags_to_bd,
    add_blog_tags_to_bd,
    get_full_blog_info,
    delete_blog,
    change_blog_status,
    get_blog_list,
)

router = APIRouter(prefix="/api", tags=["API"])

logger = getLogger(__name__)


@router.post("/add_post/", summary="Добавление нового блога с тегами")
async def add_blog(
    add_data: BlogCreateSchemaBase,
    user_data: User = Depends(get_current_user_optional),
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    logger.info("Информация о юзере: %s" % user_data)

    blog_dict = add_data.model_dump()
    blog_dict["author"] = int(user_data.id)
    tags = blog_dict.pop("tags", [])

    try:
        blog = await add_blog_to_bd(
            session=session, values=BlogCreateSchemaAdd.model_validate(blog_dict)
        )
        blog_id = blog.id

        if tags:
            tags_ids = await add_tags_to_bd(session=session, tag_names=tags)
            await add_blog_tags_to_bd(
                session=session,
                blog_tag_pairs=[{"blog_id": blog_id, "tag_id": i} for i in tags_ids],
            )
            await session.commit()

        return {
            "status": "success",
            "message": f"Блог с ID {blog_id} успешно добавлен с тегами.",
        }
    except IntegrityError as e:
        if "UNIQUE constraint failed" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Блог с таким заголовком уже существует.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при добавлении блога. ERROR: {e}",
        )


async def get_blog_info(
    blog_id: int,
    session: AsyncSession = Depends(db_helper.session_dependency),
    user_data: User = Depends(get_current_user_optional),
):
    author_id = user_data.id if user_data else None
    return await get_full_blog_info(
        session=session, blog_id=blog_id, author_id=author_id
    )


@router.get("/get_blog/{blog_id}", summary="Получить информацию по блогу")
async def get_blog_endpoint(
    blog_id: int, 
    blog_info: BlogFullResponse | BlogNotFind = Depends(get_blog_info)
) -> BlogFullResponse | BlogNotFind:
    logger.info("Blog_info %s" % blog_info)
    return blog_info

@router.delete("/delete_blog/{blog_id}", summary="Удалить блог")
async def delete_blog_endpoint(
    blog_id: int,
    author: User = Depends(get_current_user_optional),
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    result = await delete_blog(blog_id, author.id, session)
    if result['status'] == 'error':
        raise HTTPException(status_code=400, detail=result['message'])
    await session.commit()
    return result

@router.put("/change_blog_status/{blog_id}", summary="Обновить блог")
async def change_blog_status_endpoint(
    blog_id: int,
    new_status: str,
    author: User = Depends(get_current_user_optional),
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    
    result = await change_blog_status(blog_id, new_status, author.id, session)
    if result['status'] == 'error':
        raise HTTPException(status_code=400, detail=result['message'])
    await session.commit()
    return result
    
@router.get('/blogs/', summary="Получить все блоги в статусе 'publish'")
async def get_blogs_info(
        author_id: int | None = None,
        tag: str | None = None,
        page: int = Query(1, ge=1, description="Номер страницы"),
        page_size: int = Query(10, ge=10, le=100, description="Записей на странице"),
        session: AsyncSession = Depends(db_helper.session_dependency),
):
    try:
        result = await get_blog_list(session=session, author_id=author_id, tag=tag, page=page,
                                             page_size=page_size)
        return result if result['blogs'] else BlogNotFind(message="Блоги не найдены", status='error')
    except Exception as e:
        logger.error(f"Ошибка при получении блогов: {e}")
        return JSONResponse(status_code=500, content={"detail": "Ошибка сервера"})