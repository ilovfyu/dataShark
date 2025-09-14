from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.rbac import User, Role


class QueryUtils:


    @staticmethod
    async def is_admin(guid: str, db: AsyncSession) -> bool:
        stmt = select(User).where(User.guid == guid)
        result = await db.execute(stmt)
        user = result.scalar_one()
        if user.is_superuser:
            return True
        return False


    @staticmethod
    async def is_exist_admin(guid: str, db: AsyncSession) -> bool:
        stmt = select(User).where(User.guid == guid)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            return True
        return False



    @staticmethod
    async def get_admin_role(db: AsyncSession):
        stmt = select(Role).where(Role.name == "空间管理员")
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
