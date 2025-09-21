from datetime import datetime, timedelta
from backend.core.settings.config import get_settings
from sqlalchemy import select, func, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.common.errors import BussinessCode, ErrorCode
from backend.common.exception_handler import BusinessException
from backend.constants.model_constant import UserStatusEnum
from backend.dto.rbac_dto import (
    UserCreateReqDto, LoginReqDto, UserUpdateReqDto, UserQueryListReqDto, UserStatusReqDto, UserChangePasswordReqDto,
    UserDeleteReqDto, RoleCreateReqDto, RoleUpdateReqDto, RoleDeleteReqDto, RoleListReqDto, CreatePermissionReqDto,
    UpdatePermissionReqDto, QueryPermissionListReqDto, DeletePermissionReqDto, PermissionGroupCreateReqDto,
    PermissionGroupDeleteReqDto, PermissionGroupListReqDto, PermissionGroupUpdateReqDto, RolePermissionAssignReqDto,
    UserRoleAssignReqDto, RolePermissionGroupAssignReqDto, GroupPermissionAssignReqDto, UserWorkspaceAssignReqDto,
    UserWorkspaceRoleAssignReqDto
)
from backend.models import (
    User, Role, UserRole, UserWorkspace, RolePermission, Permission, GroupPermissions, PermissionGroup
)
from backend.dto.base import NoneDataUnionResp, BasePageRespDto
from backend.models.rbac import RolePermissionGroup
from backend.utils.jwt_utils import get_password_hash, verify_password, create_access_token
from backend.utils.model_utils import ModelConverter, GeneratorUtils

confi = get_settings()

class RBACService:


    async def create_user(self, req: UserCreateReqDto, db: AsyncSession):
        try:
            stmt = select(User).where(User.username == req.username)
            stmt_result = await db.execute(stmt)
            exist_user = stmt_result.scalar_one_or_none()
            if exist_user:
                raise BusinessException(
                    message="用户名已存在",
                    code=BussinessCode.EXIST_ERROR.code,
                    status_code=ErrorCode.BAD_REQUEST,
                )
            user = User(
                username=req.username,
                hashed_password=get_password_hash(req.password),
                nickname=req.nickname,
                phone=req.phone,
                email=req.email,
                avatar_url=req.avatar_url,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            ## role
            role = UserRole(
                user_id=user.guid,
                role_id=3,
            )
            db.add(role)
            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            raise BusinessException(
                message=f"创建用户失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )



    async def login(self, req: LoginReqDto, db: AsyncSession):
        try:
            stmt = select(User).where(User.username == req.username)
            result = await db.execute(stmt)
            user: User = result.scalar_one_or_none()
            if not user:
                raise BusinessException(
                    message="用户不存在",
                    code=BussinessCode.NOT_EXIST_ERROR.code,
                    status_code=ErrorCode.UNAUTHORIZED,
                )
            if not verify_password(req.password, user.hashed_password):
                raise BusinessException(
                    message=f"用户名或密码错误",
                    code=BussinessCode.UNAUTHORIZED_ERROR.code,
                    status_code=ErrorCode.INTERNAL_SERVER_ERROR,
                )
            if user.status != UserStatusEnum.ACTIVE:
                raise BusinessException(
                    message=f"用户账户非激活状态",
                    code=BussinessCode.STATUS_ERROR.code,
                    status_code=ErrorCode.INTERNAL_SERVER_ERROR,
                )
            user.last_login_ip = req.ip
            user.last_login_time = datetime.now()
            db.add(user)
            await db.commit()

            access_token_expires = timedelta(days=confi.access_token_expire_days)
            access_token = create_access_token(
                data={"sub": user.guid}, expires_delta=access_token_expires
            )
            return {
                "access_token": access_token,
                "token_type": "bearer",
            }
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"登录失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )



    async def update_user(self, req: UserUpdateReqDto, db: AsyncSession):
        try:
            stmt = select(User).where(User.guid == req.guid)
            result = await db.execute(stmt)
            user: User = result.scalar_one_or_none()
            if not user:
                raise BusinessException(
                    message="用户不存在",
                    code=BussinessCode.NOT_EXIST_ERROR.code,
                    status_code=ErrorCode.BAD_ENTITY,
                )
            model = ModelConverter.update_model_from_dto(model_instance=user, dto_instance=req)
            db.add(model)
            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"更新用户失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )


    async def query_user_list(self, req: UserQueryListReqDto, db: AsyncSession):
        try:
            stmt = select(User)
            count_stmt = select(func.count()).select_from(User)

            if req.status:
                stmt = stmt.where(User.status == req.status)
                count_stmt = count_stmt.where(User.status == req.status)

            if req.start_login_time:
                stmt = stmt.where(User.last_login_time >= req.start_login_time)
                count_stmt = count_stmt.where(User.last_login_time >= req.start_login_time)

            if req.end_login_time:
                stmt = stmt.where(User.last_login_time <= req.end_login_time)
                count_stmt = count_stmt.where(User.last_login_time <= req.end_login_time)


            ## page
            stmt = stmt.offset(req.page_size * (req.page - 1)).limit(req.page_size)
            stmt = stmt.order_by(User.created_at.desc())

            result = await db.execute(stmt)
            users = result.scalars().all()

            count_result = await db.execute(count_stmt)
            total = count_result.scalar_one()

            user_list = ModelConverter.to_dict_list(users, exclude_fields=["hashed_password", "deleted_at"])
            return BasePageRespDto(total=total, data=user_list)
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"查询用户列表失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )



    async def query_user_detail(self, guid: str, db: AsyncSession):
        try:
            stmt = select(User).where(User.guid == guid)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                raise BusinessException(
                    message=f"用户不存在",
                    code=BussinessCode.NOT_EXIST_ERROR.code,
                    status_code=ErrorCode.BAD_REQUEST,
                )
            return ModelConverter.model_to_dict(user, exclude_fields=["hashed_password", "deleted_at"])
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"查询用户详情失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )





    async def user_change_status_api(self, req: UserStatusReqDto, db: AsyncSession):
        try:
            stmt = select(User).where(User.guid == req.guid)
            result = await db.execute(stmt)
            user: User = result.scalar_one_or_none()
            if not user:
                raise BusinessException(
                    message=f"用户不存在",
                    code=BussinessCode.NOT_EXIST_ERROR.code,
                    status_code=ErrorCode.BAD_REQUEST,
                )
            if user.is_superuser:
                raise BusinessException(
                    message=f"超级管理员不能变更状态",
                    code=BussinessCode.STATUS_ERROR.code,
                    status_code=ErrorCode.BAD_REQUEST,
                )
            user.status = req.status
            db.add(user)
            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"修改用户密码失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )




    async def user_change_password_api(self, req: UserChangePasswordReqDto, db: AsyncSession):
        try:
            stmt = select(User).where(User.guid == req.guid)
            result = await db.execute(stmt)
            user: User = result.scalar_one_or_none()
            if not user:
                raise BusinessException(
                    message=f"用户不存在",
                    code=BussinessCode.NOT_EXIST_ERROR.code,
                    status_code=ErrorCode.BAD_REQUEST,
                )
            if user.status != UserStatusEnum.ACTIVE:
                raise BusinessException(
                    message=f"用户状态异常",
                    code=BussinessCode.STATUS_ERROR.code,
                    status_code=ErrorCode.BAD_REQUEST,
                )
            user.hashed_password = get_password_hash(req.password)
            db.add(user)
            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"修改用户密码失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )



    async def delete_user(self, req: UserDeleteReqDto, db: AsyncSession):
        try:
            delete_user_role_stmt = delete(UserRole).where(UserRole.user_id.in_(req.guids))
            await db.execute(delete_user_role_stmt)

            delete_user_workspace_stmt = delete(UserWorkspace).where(UserWorkspace.user_id.in_(req.guids))
            await db.execute(delete_user_workspace_stmt)

            delete_user_stmt = delete(User).where(User.guid.in_(req.guids))
            await db.execute(delete_user_stmt)
            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"删除用户失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )




    async def create_role(self, req: RoleCreateReqDto, db: AsyncSession):
        try:
            stmt = select(Role).where(Role.name == req.name)
            result = await db.execute(stmt)
            role = result.scalar_one_or_none()
            if role:
                raise BusinessException(
                    message=f"角色已存在",
                    code=BussinessCode.EXIST_ERROR.code,
                    status_code=ErrorCode.BAD_REQUEST,
                )
            role = Role(
                name=req.name,
                description=req.description,
                status=req.status,
                role_type=req.role_type,
            )
            db.add(role)
            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"创建角色失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )



    async def update_role(self, req: RoleUpdateReqDto, db: AsyncSession):
        try:
            stmt = select(Role).where(Role.id == req.id)
            result = await db.execute(stmt)
            role = result.scalar_one_or_none()
            if not role:
                raise BusinessException(
                    message="角色不存在",
                    code=BussinessCode.NOT_EXIST_ERROR.code,
                    status_code=ErrorCode.BAD_REQUEST,
                )
            model = ModelConverter.update_model_from_dto(model_instance=role, dto_instance=req)
            db.add(model)
            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"更新角色失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )



    async def delete_role(self, req: RoleDeleteReqDto, db: AsyncSession):
        try:
            stmt = select(Role).where(Role.id == req.id)
            result = await db.execute(stmt)
            role = result.scalar_one_or_none()
            if not role:
                raise BusinessException(
                    message=f"角色不存在",
                    code=BussinessCode.NOT_EXIST_ERROR.code,
                    status_code=ErrorCode.BAD_REQUEST,
                )

            delete_user_role_stmt = delete(UserRole).where(UserRole.role_id == req.id)
            await db.execute(delete_user_role_stmt)

            delete_role_permission_stmt = delete(RolePermission).where(RolePermission.role_id == req.id)
            await db.execute(delete_role_permission_stmt)


            delete_role_permission_group_stmt = delete(RolePermissionGroup).where(RolePermissionGroup.role_id == req.id)
            await db.execute(delete_role_permission_group_stmt)

            delete_user_workspace_stmt = delete(UserWorkspace).where(UserWorkspace.role_id == req.id)
            await db.execute(delete_user_workspace_stmt)

            await db.delete(role)
            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"删除角色失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )



    async def query_role_list(self, req: RoleListReqDto, db: AsyncSession):
        try:
            stmt = select(Role)
            count_stmt = select(func.count()).select_from(Role)
            if req.status:
                stmt = stmt.where(Role.status == req.status)
                count_stmt = count_stmt.where(Role.status == req.status)
            if req.role_type:
                stmt = stmt.where(Role.role_type == req.role_type)
                count_stmt = count_stmt.where(Role.role_type == req.role_type)
            stmt = stmt.offset((req.page - 1) * req.page_size).limit(req.page_size)
            stmt = stmt.order_by(Role.created_at.desc())


            result = await db.execute(stmt)
            roles = result.scalars().all()

            count_result = await db.execute(count_stmt)
            total = count_result.scalar_one()

            role_list = ModelConverter.to_dict_list(roles, exclude_fields=["deleted_at"])
            return BasePageRespDto(
                total=total,
                data=role_list,
            )
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"查询角色列表失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )



    async def query_role_detail(self, id: int, db: AsyncSession):
        try:
            stmt = select(Role).where(Role.id == id)
            result = await db.execute(stmt)
            role = result.scalar_one_or_none()
            return ModelConverter.model_to_dict(role, exclude_fields=["deleted_at"])
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"查询角色详情失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )




    async def create_permission(self, req: CreatePermissionReqDto, db: AsyncSession):
        try:
            code = GeneratorUtils.generate_permission_code(req.resource, req.action)
            stmt = select(Permission).where(Permission.code == code)
            result = await db.execute(stmt)
            permission = result.scalar_one_or_none()
            if permission:
                raise BusinessException(
                    message="权限已存在",
                    code=BussinessCode.EXIST_ERROR.code,
                    status_code=ErrorCode.BAD_REQUEST,
                )
            permission = Permission(
                code=code,
                name=req.name,
                description=req.description,
                api_endpoint=req.api_endpoint,
                http_method=req.http_method,
                permission_type=req.permission_type,
                resource=req.resource,
                level=req.level,
                status=req.status,
                action=req.action
            )
            db.add(permission)
            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"创建权限失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )




    async def update_permission(self, req: UpdatePermissionReqDto, db: AsyncSession):
        try:
            stmt = select(Permission).where(Permission.id == req.id)
            result = await db.execute(stmt)
            permission = result.scalar_one_or_none()
            if not permission:
                raise BusinessException(
                    message=f"权限不存在",
                    code=BussinessCode.NOT_EXIST_ERROR.code,
                    status_code=ErrorCode.BAD_REQUEST,
                )
            if req.resource is not None:
                code = GeneratorUtils.generate_permission_code(req.resource, req.action)
                code_stmt = select(Permission).where(and_(Permission.code == code, Permission.id != req.id))
                code_result = await db.execute(code_stmt)
                exist_permission = code_result.scalar_one_or_none()
                if exist_permission:
                    raise BusinessException(
                        message=f"权限已存在",
                        code=BussinessCode.EXIST_ERROR.code,
                        status_code=ErrorCode.BAD_REQUEST,
                    )
                permission.code = code
            model = ModelConverter.update_model_from_dto(permission, req)
            db.add(model)
            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"更新权限失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )



    async def query_permission_list(self, req: QueryPermissionListReqDto, db: AsyncSession):
        try:
            stmt = select(Permission)
            count_stmt = select(func.count()).select_from(Permission)

            if req.status:
                stmt = stmt.where(Permission.status == req.status)
                count_stmt = count_stmt.where(Permission.status == req.status)
            if req.action:
                stmt = stmt.where(Permission.action == req.action)
                count_stmt = count_stmt.where(Permission.action == req.action)
            if req.http_method:
                stmt = stmt.where(Permission.http_method == req.http_method)
                count_stmt = count_stmt.where(Permission.http_method == req.http_method)
            if req.level:
                stmt = stmt.where(Permission.level == req.level)
                count_stmt = count_stmt.where(Permission.level == req.level)

            stmt = stmt.offset((req.page - 1) * req.page_size).limit(req.page_size)
            stmt = stmt.order_by(Permission.created_at.desc())

            result = await db.execute(stmt)
            permissions = result.scalars().all()

            count_result = await db.execute(count_stmt)
            total = count_result.scalar_one()

            permission_list = ModelConverter.to_dict_list(permissions, exclude_fields=["deleted_at"])
            return BasePageRespDto(
                total=total,
                data=permission_list,
            )
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"查询权限列表失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )



    async def delete_permission(self, req: DeletePermissionReqDto, db: AsyncSession):
        try:
            ## 删除角色关联
            delete_role_permission_stmt = delete(RolePermission).where(RolePermission.permission_id.in_(req.ids))
            await db.execute(delete_role_permission_stmt)

            delete_group_permission_stmt = delete(GroupPermissions).where(GroupPermissions.permission_id.in_(req.ids))
            await db.execute(delete_group_permission_stmt)

            delete_permission_stmt = delete(Permission).where(Permission.id.in_(req.ids))
            await db.execute(delete_permission_stmt)

            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"删除权限失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )



    async def permission_group_create(self, req: PermissionGroupCreateReqDto, db: AsyncSession):
        try:
            stmt = select(PermissionGroup).where(PermissionGroup.name == req.name)
            result = await db.execute(stmt)
            permission_group = result.scalar_one_or_none()
            if permission_group:
                raise BusinessException(
                    message=f"权限组已存在",
                    code=BussinessCode.EXIST_ERROR.code,
                    status_code=ErrorCode.BAD_REQUEST,
                )
            group = PermissionGroup(
                name=req.name,
                description=req.description,
                status=req.status,
            )
            db.add(group)
            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"创建权限组失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )




    async def permission_group_delete(self, req: PermissionGroupDeleteReqDto, db: AsyncSession):
        try:
            ## combine
            group_stmt = select(PermissionGroup).where(PermissionGroup.code == req.code)
            group_result = await db.execute(group_stmt)
            group = group_result.scalar_one_or_none()
            if not group:
                raise BusinessException(
                    message="权限组不存在",
                    code=BussinessCode.NOT_EXIST_ERROR.code,
                    status_code=ErrorCode.BAD_REQUEST,
                )
            delete_group_permission_stmt = delete(GroupPermissions).where(GroupPermissions.group_code == group.code)
            await db.execute(delete_group_permission_stmt)

            await db.delete(group)
            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"删除权限组失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )




    async def permission_group_list(self, req: PermissionGroupListReqDto, db: AsyncSession):
        try:
            stmt = select(PermissionGroup)
            count_stmt = select(func.count()).select_from(PermissionGroup)

            if req.status:
                stmt = stmt.where(PermissionGroup.status == req.status)
                count_stmt = count_stmt.where(PermissionGroup.status == req.status)

            stmt = stmt.offset((req.page - 1) * req.page_size).limit(req.page_size)
            result = await db.execute(stmt)
            permission_groups = result.scalars().all()
            count_result = await db.execute(count_stmt)
            total = count_result.scalar_one()

            permission_group_list = ModelConverter.to_dict_list(permission_groups)
            return BasePageRespDto(
                total=total,
                data=permission_group_list,
            )
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"查询权限组列表失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )




    async def permission_group_update(self, req: PermissionGroupUpdateReqDto, db: AsyncSession):
        try:
            group_stmt = select(PermissionGroup).where(PermissionGroup.code == req.code)
            group_result = await db.execute(group_stmt)
            group = group_result.scalar_one_or_none()
            if not group:
                raise BusinessException(
                    message=f"权限组不存在",
                    code=BussinessCode.NOT_EXIST_ERROR.code,
                    status_code=ErrorCode.BAD_REQUEST,
                )
            model = ModelConverter.update_model_from_dto(group, req)
            db.add(model)
            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"更新权限组失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )



    async def user_roles_assign(self, req: UserRoleAssignReqDto, db: AsyncSession):
        try:
            delete_stmt = select(UserRole).where(UserRole.user_id == req.guid)
            delete_result = await db.execute(delete_stmt)
            for user_role in delete_result.scalars().all():
                await db.delete(user_role)
            for role_id in req.role_ids:
                user_role = UserRole(
                    user_id=req.guid,
                    role_id=role_id,
                )
                db.add(user_role)
            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"分配用户角色失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )




    async def role_permission_assign(self, req: RolePermissionAssignReqDto, db: AsyncSession):
        try:
            delete_stmt = select(RolePermission).where(RolePermission.role_id == req.role_id)
            delete_result = await db.execute(delete_stmt)
            for role_perm in delete_result.scalars().all():
                await db.delete(role_perm)

            for permission_id in req.permission_ids:
                role_perm = RolePermission(
                    role_id=req.role_id,
                    permission_id=permission_id,
                )
                await db.add(role_perm)
            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"分配角色权限失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )




    async def role_permission_group_assign(self, req: RolePermissionGroupAssignReqDto, db: AsyncSession):
        try:
            pass
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"分配角色权限组失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )




    async def group_permission_assign(self, req: GroupPermissionAssignReqDto, db: AsyncSession):
        try:
            pass
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"分配权限组权限失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )




    async def user_workspace_assign(self, req: UserWorkspaceAssignReqDto, db: AsyncSession):
        try:
            pass
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"分配用户工作空间失败, {str(e)}",
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
            )






    async def assign_user_workspace_role(self, req: UserWorkspaceRoleAssignReqDto, db: AsyncSession):
        pass


rbac_service = RBACService()