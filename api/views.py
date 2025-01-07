from logging import getLogger

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi.responses import JSONResponse

from api.dependencies import get_current_user_optional
from auth.dependencies import get_current_user
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
)

router = APIRouter(prefix="/api", tags=["API"])

logger = getLogger(__name__)


@router.post("/add_post/", summary="Добавление нового блога с тегами")
async def add_blog(
    add_data: BlogCreateSchemaBase,
    user_data: dict = Depends(get_current_user),
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    logger.info("Информация о юзере: %s" % user_data)

    blog_dict = add_data.model_dump()
    blog_dict["author"] = int(user_data["sub"])
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
    user_data: dict | None = Depends(get_current_user_optional),
):
    author_id = user_data["sub"] if user_data else None
    return await get_full_blog_info(
        session=session, blog_id=blog_id, author_id=author_id
    )


@router.get("/get_blog/{blog_id}", summary="Получить информацию по блогу")
async def get_blog_endpoint(
    blog_id: int, 
    blog_info: BlogFullResponse | BlogNotFind = Depends(get_blog_info)
) -> BlogFullResponse | BlogNotFind:
    logger.info("Blog_info %s" % blog_info.tags[0].name)
    return blog_info
