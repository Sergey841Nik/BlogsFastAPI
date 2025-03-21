from logging import getLogger

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemes import BlogFullResponse, BlogNotFind
from api.views import get_blog_info
from api.dependencies import get_current_user_optional
from api.crud import get_blog_list
import markdown2

from core.models.base import User
from core.models.db_helper import db_helper
from auth.views import auth_user

logger = getLogger(__name__)

router = APIRouter(tags=['ФРОНТЕНД'])

templates = Jinja2Templates(directory='templates')

@router.get('/blogs/{blog_id}/')
async def get_blog_post(
        request: Request,
        blog_id: int,
        blog_info: BlogFullResponse | BlogNotFind = Depends(get_blog_info),
        user_data: User | None = Depends(get_current_user_optional)
):
    if isinstance(blog_info, dict):
        return templates.TemplateResponse(
            "404.html", {"request": request, "blog_id": blog_id}
        )
    else:
        blog = BlogFullResponse.model_validate(blog_info).model_dump()
        # Преобразование Markdown в HTML
        blog['content'] = markdown2.markdown(blog['content'], extras=['fenced-code-blocks', 'tables'])
        logger.info("blogs_id: %s" % blog_id)
        return templates.TemplateResponse(
            "post.html",
            {"request": request, "article": blog, "current_user_id": user_data.id if user_data else None}
        )
    

@router.get('/blogs/')
async def get_blog_posts(
        request: Request,
        author_id: int | None = None,
        tag: str | None = None,
        page: int = 1,
        page_size: int = 3,
        session: AsyncSession = Depends(db_helper.session_dependency),
):
    blogs = await get_blog_list(
        session=session,
        author_id=author_id,
        tag=tag,
        page=page,
        page_size=page_size
    )
    logger.info("blogs: %s" % blogs)
    return templates.TemplateResponse(
        "posts.html",
        {
            "request": request,
            "article": blogs,
            "filters": {
                "author_id": author_id,
                "tag": tag,
            }
        }
    )

@router.get("/login/")
async def login(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "title": "Авторизация"
        })
