from logging import getLogger

from fastapi import Request, HTTPException, status, Depends
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from .utils import decoded_jwt
from .crud import find_one_or_none_by_id
from core.models.db_helper import db_helper

logger = getLogger(__name__)

def get_token(request: Request) -> str:
    token = request.cookies.get('access_token')

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                             detail='Токен истек')
    return token


async def get_current_user(
        token: str = Depends(get_token),
        session: AsyncSession = Depends(db_helper.get_scoped_session),
):
    try:
        payload = decoded_jwt(token)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                               detail=f'Токен не валидный')

    user_id: str = payload.get('sub')
    user = await find_one_or_none_by_id(user_id=int(user_id), session=session)

    logger.info("Найден пользователь %s" % user)
    
    return user