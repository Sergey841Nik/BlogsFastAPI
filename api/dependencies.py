from logging import getLogger

from fastapi import Request, Depends
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from auth.crud import find_one_or_none_by_id
from auth.utils import decoded_jwt
from core.models.db_helper import db_helper

logger = getLogger(__name__)


def get_token_optional(request: Request) -> str | None:
    token = request.cookies.get("access_token")

    if not token:
        return None
    return token


async def get_current_user_optional(
    token: str | None = Depends(get_token_optional),
    session: AsyncSession = Depends(db_helper.get_scoped_session),
):
    try:
        payload = decoded_jwt(token) # type: ignore
    except InvalidTokenError:
        return None
    user_id: str = payload.get('sub') # type: ignore

    user = await find_one_or_none_by_id(user_id=int(user_id), session=session)

    logger.info("Найден пользователь %s" % user)
    
    return user
