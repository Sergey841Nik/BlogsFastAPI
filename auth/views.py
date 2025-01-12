
from logging import getLogger
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Response, status

from .crud import add_users, find_one_or_none_users, get_all_users, add_new_role, change_user_role, delete_role
from .dependencies import get_current_user, get_current_admin
from .auth_jwt import validate_auth_user, create_access_token
from .schemes import UserRegister, EmailModel, UserAddDB, UserAuth, UserInfo, RoleAddDB, ChangeUserRole
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

@router.post("/add_role/")
async def add_role(
    role: RoleAddDB,
    session: AsyncSession = Depends(db_helper.session_dependency),
    user_data = Depends(get_current_admin),
):
    role_dict = role.model_dump()
    await add_new_role(session=session, values=RoleAddDB(**role_dict))
    return {"message": "Новая роль успешно добавлена"}

@router.put("/change_role/")
async def change_role(
    user_role: ChangeUserRole,
    session: AsyncSession = Depends(db_helper.session_dependency),
    user_data = Depends(get_current_admin),
):
    find_user = await find_one_or_none_users(session=session, filters=EmailModel(email=user_role.email))
    if not find_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail='Пользователь отсутствует')
    
    user_role_dict = user_role.model_dump()

    await change_user_role(session=session, values=ChangeUserRole(**user_role_dict))
    return {"message": "Роль успешно изменена"}

@router.delete("/delete_blog/{role_id}", summary="Удалить роль")
async def delete_role_endpoint(
    role_id: int,
    session: AsyncSession = Depends(db_helper.session_dependency),
    user_data = Depends(get_current_admin),
):
    result = await delete_role(role_id, session)
    if result['status'] == 'error':
        raise HTTPException(status_code=400, detail=result['message'])
    await session.commit()
    return result

@router.post("/logout/")
async def logout_user(response: Response):
    response.delete_cookie(key="access_token")
    return {'message': 'Пользователь успешно вышел из системы'}


@router.get("/me/")
async def get_me(user_data = Depends(get_current_user)) -> UserInfo:
    return UserInfo.model_validate(user_data)

@router.get("/all_users/")
async def all_users(
    session: AsyncSession = Depends(db_helper.session_dependency),
    user_data = Depends(get_current_admin),
) -> list[UserInfo]:
    return await get_all_users(session=session, filters=None) # type: ignore