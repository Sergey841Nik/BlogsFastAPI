from datetime import timedelta
from logging import getLogger

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr

from .crud import find_one_or_none_users
from .utils import validate_password, encoded_jwt
from .schemes import EmailModel
from core.models.base import User
from core.models.db_helper import db_helper

logger = getLogger(__name__)


async def validate_auth_user(
    email: EmailStr,
    password: str,
    session: AsyncSession,
):
    unauthed_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )
    user = await find_one_or_none_users(
        session=session, filters=EmailModel(email=email)
    )

    if not user:
        raise unauthed_exc  # если пользователь не найден

    if not validate_password(
        password=password, hash_password=user.password
    ):  # проверяем пароль
        raise unauthed_exc

    return user


# создание токена
def create_jwt(
    token_type: str,
    token_data: dict,
) -> str:
    jwt_payload = {"type": token_type}
    jwt_payload.update(token_data)
    return encoded_jwt(
        payload=jwt_payload,
    )


# создание аксес токена
def create_access_token(user: User) -> str:
    jwt_payload = {
        "sub": str(user.id),
    }
    return create_jwt(
        token_type="accses",
        token_data=jwt_payload,
    )
