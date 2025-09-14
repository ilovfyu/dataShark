# backend/models/workspace.py
import uuid
from sqlalchemy import Column, String, Text, Boolean, BigInteger, Enum
from backend.models.base import IBaseModel
from backend.constants.model_constant import WorkSpaceStatusEnum


class Workspace(IBaseModel):
    """
    工作空间模型
    """
    __tablename__ = "sys_workspace"
    name = Column(String(100), nullable=False, unique=True, index=True, comment="工作空间名称")
    description = Column(Text, nullable=True, comment="工作空间描述")
    code = Column(String(50), nullable=False, unique=True, default=lambda: str(uuid.uuid4()),  index=True, comment="工作空间编码")
    database_url = Column(String(500), nullable=False, comment="工作空间数据库连接URL")
    status = Column(Enum(WorkSpaceStatusEnum), default=WorkSpaceStatusEnum.ACTIVE, comment="工作空间状态")
    owner_id = Column(String(36), nullable=False, comment="拥有者用户ID")
    config = Column(Text, nullable=True, comment="工作空间配置信息Json")

    def __repr__(self):
        return f"<Workspace(id={self.id}, name='{self.name}', code='{self.code}')>"




class UserWorkspace(IBaseModel):
    """
    用户工作空间关联模型
    """
    __tablename__ = "sys_user_workspace"
    user_id = Column(String(36), index=True, nullable=False, comment="用户ID")
    workspace_id = Column(String(36), index=True, nullable=False, comment="工作空间ID")
    role_id = Column(BigInteger, index=True, nullable=False, comment="在该工作空间中的角色ID")
    is_active = Column(Boolean, default=True, comment="是否激活")

    def __repr__(self):
        return f"<UserWorkspace(user_id='{self.user_id}', workspace_id='{self.workspace_id}')>"
