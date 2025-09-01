from backend.models.base import IBaseModel
from sqlalchemy import Column, String, Integer


class SysUser(IBaseModel):
    __tablename__ = "sys_user"
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    is_active = Column(Integer, default=1)
    phone = Column(String(20), unique=True, nullable=True)
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"
