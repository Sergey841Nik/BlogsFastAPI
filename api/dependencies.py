from logging import getLogger

from fastapi import Request, Depends
from jwt.exceptions import InvalidTokenError

from auth.utils import decoded_jwt

logger = getLogger(__name__)


def get_token_optional(request: Request) -> str | None:
    token = request.cookies.get("access_token")

    if not token:
        return None
    return token


async def get_current_user_optional(
    token: str | None = Depends(get_token_optional),
) -> dict | None:
    try:
        payload = decoded_jwt(token)
    except InvalidTokenError:
        return None

    return payload
