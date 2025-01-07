from logging import getLogger

from fastapi import Request, HTTPException, status, Depends
from jwt.exceptions import InvalidTokenError

from .utils import decoded_jwt

logger = getLogger(__name__)

def get_token(request: Request) -> str:
    token = request.cookies.get('access_token')

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                             detail='Токен истек')
    return token


async def get_current_user(
        token: str = Depends(get_token), 
) -> dict:
    try:
        payload = decoded_jwt(token)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                               detail=f'Токен не валидный')

    return payload