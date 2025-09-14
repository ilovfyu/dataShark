from enum import Enum


class UserStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    DISABLED = "disabled"
    DELETED = "deleted"


class RoleStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"



class RoleTypeEnum(str, Enum):
    SYSTEM = "system"
    CUSTOM = "custom"
    TEMPORARY = "temporary"
    WORKSPACE = "workspace"



class PermissionTypeEnum(str, Enum):
    MENU = "menu"
    BUTTON = "button"
    API = "api"
    DATA = "data"
    FIELD = "field"
    CUSTOM = "custom"


class PermissionActionEnum(str, Enum):
    CREATE = "create"  # 创建
    READ = "read"  # 读取
    UPDATE = "update"  # 更新
    DELETE = "delete"  # 删除
    LIST = "list"  # 列表查询
    EXPORT = "export"  # 导出
    IMPORT = "import"  # 导入
    APPROVE = "approve"  # 审批
    CUSTOM = "custom"  # 自定义操作

    VIEW = "view"  # 查看
    EXECUTE = "execute"  # 执行
    MANAGE = "manage"  # 管理
    AUDIT = "audit"  # 审计
    CONFIGURE = "configure"  # 配置



class PermissionStatusEnum(str, Enum):
    ACTIVE = "active"  # 启用
    DISABLED = "disabled"  # 禁用






class WorkSpaceStatusEnum(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DELETED = "deleted"
    UNACTIVE = "unactive"



class HttpMethodEnum(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    PATCH = "PATCH"
    TRACE = "TRACE"
    ALL = "ALL"




class PermissionResourceEnum(str, Enum):
    USER = "user"
    ROLE = "role"
    WORKSPACE = "workspace"
    PERMISSION = "permission"
    COMMON = "common"