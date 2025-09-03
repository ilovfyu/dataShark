from sqlalchemy import Column, String, Text, Boolean, BigInteger
from backend.models.base import IBaseModel


class Role(IBaseModel):
    __tablename__ = "sys_role"
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)



class Permission(IBaseModel):
    __tablename__ = "sys_permission"
    resource = Column(String(255), index=True)
    action = Column(String(20), index=True)



class User(IBaseModel):
    __tablename__ = "sys_user"

    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

    def has_permission(self, permissions: list, resource: str, action: str) -> bool:
        if self.is_superuser:
            return True

        for permission in permissions:
            if permission.resource == resource and permission.action == action:
                return True
        return False


class UserRole(IBaseModel):
    __tablename__ = 'sys_user_role'

    user_id = Column(BigInteger, index=True, nullable=False)
    role_id = Column(BigInteger, index=True, nullable=False)

    __table_args__ = (
    )


class RolePermission(IBaseModel):
    __tablename__ = 'sys_role_permission'

    role_id = Column(BigInteger, index=True, nullable=False)
    permission_id = Column(BigInteger, index=True, nullable=False)
    __table_args__ = (
    )