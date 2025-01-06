from logging import getLogger

from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from jwt.exceptions import InvalidTokenError

from .utils import decoded_jwt
from core.models.db_helper import db_helper

logger = getLogger(__name__)

def get_token(request: Request):
    token = request.cookies.get('access_token')

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                             detail='Токен истек')
    return token


async def get_current_user(
        token: str = Depends(get_token), 
        # session: AsyncSession = Depends(db_helper.session_dependency)
):
    try:
        payload = decoded_jwt(token)
    except InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                               detail=f'Токен не валидный')

    return payload