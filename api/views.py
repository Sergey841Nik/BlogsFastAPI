from logging import getLogger

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi.responses import JSONResponse

from auth.dependencies import get_current_user
from core.models.base import User
from core.models.db_helper import db_helper
from .shemes import BlogCreateSchemaBase, BlogCreateSchemaAdd
from .crud import add_blog_to_bd, add_tags_to_bd, add_blog_tags_to_bd

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
