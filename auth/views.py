
from logging import getLogger
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Response, status

from .crud import add_users, find_one_or_none_users
from .dependencies import get_current_user
from .auth_jwt import validate_auth_user, create_access_token
from .schemes import UserRegister, EmailModel, UserAddDB, UserAuth, UserInfo
from core.models.db_helper import db_helper

router = APIRouter(prefix='/auth', tags=['Auth'])

logger = getLogger(__name__)

@router.post("/register/", status_code=status.HTTP_201_CREATED)
async def register_users(
    user: UserRegister, 
    session: AsyncSession = Depends(db_helper.session_dependency)
) -> dict:
    find_user = await find_one_or_none_users(session=session, filters=EmailModel(email=user.email))
    if find_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail='Пользователь уже существует')
    
    user_dict = user.model_dump()
    
    del user_dict['confirm_password']
    await add_users(session=session, values=UserAddDB(**user_dict))
    return {'message': f'Вы успешно зарегистрированы!'}


@router.post("/login/")
async def auth_user(
    response: Response,
    user: UserAuth,
    session: AsyncSession = Depends(db_helper.session_dependency)
) -> dict:
    
    check_user = await validate_auth_user(email=user.email, password=user.password, session=session)

    access_token = create_access_token(check_user)
    response.set_cookie(key='access_token', value=access_token, httponly=True)
    return {'ok': True, 'access_token': access_token, 'message': 'Авторизация успешна!'}


@router.post("/logout/")
async def logout_user(response: Response):
    response.delete_cookie(key="access_token")
    return {'message': 'Пользователь успешно вышел из системы'}


@router.get("/me/")
async def get_me(user_data = Depends(get_current_user)) -> UserInfo:
    return UserInfo.model_validate(user_data)