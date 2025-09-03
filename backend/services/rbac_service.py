from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from backend.dto.rbac import UserCreate


class AuthService:

    async def create_user_service(self, user: UserCreate, session: AsyncSession):
        """
        用户注册
        :param user:
        :param session:
        :return:
        """
        pass











auth_service = AuthService()















