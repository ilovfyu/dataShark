from datetime import timedelta
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.common.errors import ErrorCode, BussinessCode
from backend.common.exception_handler import BusinessException
from backend.constants.model_constant import UserStatusEnum
from backend.dto.rbac import (
    UserCreateReq, UserCreateResp, UserDeleteReq, UserUpdateReq, UserQueryListReq, LoginReq, LoginResp, RoleListReq,
    QueryUserRoleListReq, QueryUserRoleListResp, QueryRoleModel
)
from backend.models.rbac import User, UserRole, Role
from backend.utils.jwt import get_password_hash, verify_password, create_access_token
from backend.dto.base import (
    NoneDataUnionResp, BasePageReq, BasePageResp
)
from backend.utils.model_utils import ModelConverter
from backend.utils.query_utils import QueryUtils
from backend.core.settings.config import get_settings

confi = get_settings()


class RBACService:

    async def create_user(self, data: UserCreateReq, db: AsyncSession) -> UserCreateResp:
        """
        创建用户
        :param data:
        :param db:
        :return:
        """
        try:
            exist_user = await self.get_user_by_name(data.username, db)
            if exist_user:
                raise BusinessException(
                    message="用户已存在",
                    code=BussinessCode.USER_EXIST,
                    status_code=ErrorCode.BAD_REQUEST,
                )
            user = User(
                username=data.username,
                hashed_password=get_password_hash(data.password)
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            db.add(
                UserRole(
                    user_id=user.guid,
                    role_id=5,
                )
            )
            await db.commit()
            return ModelConverter.to_dto(user, UserCreateResp)
        except BusinessException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            raise BusinessException(
                message=f"用户创建失败, {str(e)}",
                code=BussinessCode.BUSSINESS_ERROR,
                status_code=ErrorCode.INTERNAL_ERROR,
            )

    async def get_user_by_name(self, username: str, db: AsyncSession):
        """
        根据用户名获取用户
        :param username:
        :param db:
        :return:
        """
        stmt = await db.execute(select(User).where(User.username == username))
        return stmt.scalar_one_or_none()

    async def delete_user(self, req: UserDeleteReq, db: AsyncSession) -> NoneDataUnionResp:
        """
        删除用户
        :param guid:
        :param db:
        :return:
        """
        try:
            for guid in req.guids:
                if not await QueryUtils.is_exist_admin(guid, db):
                    raise BusinessException(
                        message=f"删除的用户不存在, {guid}",
                        code=BussinessCode.USER_NOT_EXIST,
                        status_code=ErrorCode.BAD_REQUEST
                    )
                if await QueryUtils.is_admin(guid, db):
                    raise BusinessException(
                        message=f"不能删除超级管理员用户: {guid}",
                        code=BussinessCode.NOT_ALLOW_PARAM,
                        status_code=ErrorCode.BAD_REQUEST
                    )

            role_stmt = delete(UserRole).where(UserRole.user_id.in_(req.guids))
            await db.execute(role_stmt)
            user_stmt = delete(User).where(User.guid.in_(req.guids))
            await db.execute(user_stmt)
            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            raise BusinessException(
                message=f"删除用户失败, {str(e)}",
                status_code=ErrorCode.INTERNAL_ERROR,
                code=BussinessCode.BUSSINESS_ERROR,
            )

    async def update_user(self, req: UserUpdateReq, db: AsyncSession):
        """
        更新用户
        :param req:
        :param db:
        :return:
        """
        try:
            stmt = select(User).where(User.guid == req.guid)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                raise BusinessException(
                    message="用户不存在",
                    status_code=ErrorCode.BAD_REQUEST,
                    code=BussinessCode.USER_NOT_EXIST,
                )
            ModelConverter.update_model_from_dto(
                model_instance=user,
                dto_instance=req,
                exclude_fields=["guid"],
            )
            db.add(user)
            await db.flush()
            await db.refresh(user)
            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            raise BusinessException(
                message=f"更新用户失败, {str(e)}",
                status_code=ErrorCode.INTERNAL_ERROR,
                code=BussinessCode.BUSSINESS_ERROR,
            )

    async def query_user_detail(self, guid: str, db: AsyncSession):
        try:
            stmt = select(User).where(User.guid == guid)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                raise BusinessException(
                    message="用户不存在",
                    status_code=ErrorCode.BAD_REQUEST,
                    code=BussinessCode.USER_NOT_EXIST,
                )
            return ModelConverter.model_to_dict(
                model_instance=user,
                exclude_fields=[
                    "hashed_password",
                ]
            )

        except Exception as e:
            raise BusinessException(
                message=f"查询用户详情失败, {str(e)}",
                status_code=ErrorCode.INTERNAL_ERROR,
                code=BussinessCode.BUSSINESS_ERROR,
            )

    async def query_user_list(self, req: UserQueryListReq, db: AsyncSession):
        try:
            stmt = select(User)
            count_stmt = select(func.count()).select_from(User)
            if req.status:
                stmt = stmt.where(User.status == req.status)
            count_result = await db.execute(count_stmt)
            total = count_result.scalar_one()

            stmt = stmt.offset(req.page_size * (req.page - 1)).limit(req.page_size)
            result = await db.execute(stmt)
            users = result.scalars().all()

            user_lists = ModelConverter.to_dict_list(users, exclude_fields=["hashed_password"])
            return BasePageResp(
                data=user_lists,
                total=total,
            )
        except Exception as e:
            raise BusinessException(
                message=f"查询用户列表失败, {str(e)}",
                status_code=ErrorCode.INTERNAL_ERROR,
                code=BussinessCode.BUSSINESS_ERROR,
            )

    async def login_user(self, req: LoginReq, db: AsyncSession):
        try:
            stmt = select(User).where(User.username == req.username)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if not user or not verify_password(req.password, user.hashed_password):
                raise BusinessException(
                    message="用户名或密码错误",
                    status_code=ErrorCode.UNAUTHORIZED,
                    code=BussinessCode.VERIFY_ERROR,
                )
            if user.status != UserStatusEnum.ACTIVE:
                raise BusinessException(
                    message="用户状态异常",
                    status_code=ErrorCode.FORBIDDEN,
                    code=BussinessCode.STATUS_ERROR,
                )
            refresh_token_expires = timedelta(days=confi.access_token_expire_days or 7)
            token = create_access_token(
                data={
                    "sub": user.guid, "username": user.username
                },
                expires_delta=refresh_token_expires,
            )
            return LoginResp(
                access_token=token,
            )
        except Exception as e:
            raise BusinessException(
                message=f"用户登录失败, {str(e)}",
                status_code=ErrorCode.INTERNAL_ERROR,
                code=BussinessCode.BUSSINESS_ERROR,
            )

    async def get_current_user_info(self, current_user: User):
        try:
            user_info = ModelConverter.model_to_dict(current_user)
            return user_info
        except Exception as e:
            raise BusinessException(
                message=f"获取用户信息失败, {str(e)}",
                status_code=ErrorCode.INTERNAL_ERROR,
                code=BussinessCode.BUSSINESS_ERROR,
            )

    async def query_role_list(self, req: RoleListReq, db: AsyncSession):
        try:
            stmt = select(Role)
            count_stmt = select(func.count()).select_from(Role)
            if req.status:
                stmt = stmt.where(Role.status == req.status)
                count_stmt = count_stmt.where(Role.status == req.status)
            if req.role_type:
                stmt = stmt.where(Role.role_type == req.role_type)
                count_stmt = count_stmt.where(Role.role_type == req.role_type)

            count_result = await db.execute(count_stmt)
            total = count_result.scalar_one()

            stmt = stmt.offset(req.page_size * (req.page - 1)).limit(req.page_size)
            result = await db.execute(stmt)
            roles = result.scalars().all()
            role_list = ModelConverter.to_dict_list(roles)
            return BasePageResp(
                total=total,
                data=role_list
            )
        except Exception as e:
            raise BusinessException(
                message=f"获取角色列表失败, {str(e)}",
                status_code=ErrorCode.INTERNAL_ERROR,
                code=BussinessCode.BUSSINESS_ERROR,
            )

    async def query_user_role_list(self, req: QueryUserRoleListReq, db: AsyncSession):
        try:
            user_stmt = select(User).where(User.guid == req.guid)
            result = await db.execute(user_stmt)
            user = result.scalar_one_or_none()
            if not user:
                raise BusinessException(
                    status_code=ErrorCode.BAD_REQUEST,
                    code=BussinessCode.USER_NOT_EXIST,
                )

            ## 查询用户角色关联信息
            stmt = (
                select(UserRole, Role).join(Role, UserRole.role_id == Role.id).where(UserRole.user_id == req.guid)
            )
            count_stmt = (
                select(func.count()).select_from(UserRole)
                .join(Role, UserRole.role_id == Role.id)
                .where(UserRole.user_id == req.guid)
            )

            count_result = await db.execute(count_stmt)
            total = count_result.scalar_one()
            stmt = (
                stmt.offset(req.page_size * (req.page - 1)).limit(req.page_size)
            )
            result = await db.execute(stmt)
            user_roles = result.all()

            user_role_list = []
            for user_role, role in user_roles:
                model = QueryRoleModel(
                        role_name=role.name,
                        role_type=role.role_type,
                        status=role.status,
                        description=role.description,
                        create_time=role.created_at,
                        update_time=role.updated_at,
                    )
                user_role_list.append(model.model_dump())
            resp = QueryUserRoleListResp(
                total=total,
                guid=user.guid,
                username=user.username,
                data=user_role_list
            )
            return resp.model_dump()
        except Exception as e:
            raise BusinessException(
                message=f"获取用户角色列表失败, {str(e)}",
                status_code=ErrorCode.INTERNAL_ERROR,
                code=BussinessCode.BUSSINESS_ERROR,
            )



    async def update_user_role(self, req: UpdateUserRoleReq, db: AsyncSession):


rbac_service = RBACService()
