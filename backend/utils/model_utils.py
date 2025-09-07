from typing import Type, TypeVar, List, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta
from pydantic import BaseModel
from sqlalchemy import select
from datetime import datetime
from enum import Enum as PyEnum

T = TypeVar('T', bound=BaseModel)
M = TypeVar('M', bound=DeclarativeMeta)

class ModelConverter:
    """SQLAlchemy和Pydantic模型相互转换工具类"""

    @staticmethod
    def _handle_enum_value(value: Any) -> Any:
        """
        处理枚举类型的值
        :param value: 原始值
        :return: 处理后的值
        """
        if isinstance(value, PyEnum):
            return value.value
        return value

    @staticmethod
    def _handle_datetime_value(value: Any) -> Any:
        """
        处理日期时间类型的值
        :param value: 原始值
        :return: 处理后的值
        """
        if isinstance(value, datetime):
            return value.isoformat() if value else None
        return value

    @staticmethod
    def to_dto(
        model_instance: M,
        dto_class: Type[T],
        exclude_fields: Optional[List[str]] = None
    ) -> T:
        """
        将SQLAlchemy模型实例转换为Pydantic DTO
        :param model_instance: SQLAlchemy模型实例
        :param dto_class: Pydantic DTO类
        :param exclude_fields: 要排除的字段列表
        :return: Pydantic DTO实例
        """
        if model_instance is None:
            return None

        # 处理字段排除
        if exclude_fields:
            # 获取模型实例的所有属性
            model_dict = {}
            for column in model_instance.__table__.columns:
                field_name = column.name
                if field_name not in exclude_fields:
                    value = getattr(model_instance, field_name)
                    # 处理枚举类型
                    value = ModelConverter._handle_enum_value(value)
                    # 处理datetime对象
                    value = ModelConverter._handle_datetime_value(value)
                    model_dict[field_name] = value

            return dto_class(**model_dict)
        else:
            # 使用Pydantic的model_validate方法进行转换
            return dto_class.model_validate(model_instance)

    @staticmethod
    def to_dict_list(
            model_instances: List[M],
            exclude_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        将SQLAlchemy模型实例列表转换为字典列表
        :param model_instances: SQLAlchemy模型实例列表
        :param exclude_fields: 要排除的字段列表
        :return: 字典列表
        """
        if not model_instances:
            return []

        return [ModelConverter.model_to_dict(instance, exclude_fields)
                for instance in model_instances]


    @staticmethod
    def to_dto_list(
        model_instances: List[M],
        dto_class: Type[T],
        exclude_fields: Optional[List[str]] = None
    ) -> List[T]:
        """
        将SQLAlchemy模型实例列表转换为Pydantic DTO列表
        :param model_instances: SQLAlchemy模型实例列表
        :param dto_class: Pydantic DTO类
        :param exclude_fields: 要排除的字段列表
        :return: Pydantic DTO实例列表
        """
        if not model_instances:
            return []

        return [ModelConverter.to_dto(instance, dto_class, exclude_fields)
                for instance in model_instances]

    @staticmethod
    def dto_to_model(
        dto_instance: T,
        model_class: Type[M],
        exclude_fields: Optional[List[str]] = None
    ) -> M:
        """
        将Pydantic DTO转换为SQLAlchemy模型实例
        :param dto_instance: Pydantic DTO实例
        :param model_class: SQLAlchemy模型类
        :param exclude_fields: 要排除的字段列表
        :return: SQLAlchemy模型实例
        """
        if dto_instance is None:
            return None

        # 将DTO转换为字典
        dto_dict = dto_instance.model_dump()

        # 处理字段排除
        if exclude_fields:
            filtered_dict = {k: v for k, v in dto_dict.items() if k not in exclude_fields}
        else:
            filtered_dict = dto_dict

        # 创建模型实例
        return model_class(**filtered_dict)

    @staticmethod
    def dto_list_to_model_list(
        dto_instances: List[T],
        model_class: Type[M],
        exclude_fields: Optional[List[str]] = None
    ) -> List[M]:
        """
        将Pydantic DTO列表转换为SQLAlchemy模型实例列表
        :param dto_instances: Pydantic DTO实例列表
        :param model_class: SQLAlchemy模型类
        :param exclude_fields: 要排除的字段列表
        :return: SQLAlchemy模型实例列表
        """
        if not dto_instances:
            return []

        return [ModelConverter.dto_to_model(instance, model_class, exclude_fields)
                for instance in dto_instances]

    @staticmethod
    async def get_and_convert(
        db: AsyncSession,
        model_class: Type[M],
        dto_class: Type[T],
        exclude_fields: Optional[List[str]] = None,
        **filters
    ) -> Optional[T]:
        """
        从数据库获取模型实例并转换为DTO
        :param db: 数据库会话
        :param model_class: SQLAlchemy模型类
        :param dto_class: Pydantic DTO类
        :param exclude_fields: 要排除的字段列表
        :param filters: 过滤条件
        :return: Pydantic DTO实例或None
        """
        stmt = select(model_class)
        for field, value in filters.items():
            if hasattr(model_class, field):
                stmt = stmt.where(getattr(model_class, field) == value)

        result = await db.execute(stmt)
        model_instance = result.scalar_one_or_none()

        if model_instance:
            return ModelConverter.to_dto(model_instance, dto_class, exclude_fields)
        return None

    @staticmethod
    async def list_and_convert(
        db: AsyncSession,
        model_class: Type[M],
        dto_class: Type[T],
        page: int = 1,
        page_size: int = 10,
        exclude_fields: Optional[List[str]] = None,
        **filters
    ) -> tuple[List[T], int]:
        """
        从数据库获取模型实例列表并转换为DTO列表
        :param db: 数据库会话
        :param model_class: SQLAlchemy模型类
        :param dto_class: Pydantic DTO类
        :param page: 页码
        :param page_size: 每页大小
        :param exclude_fields: 要排除的字段列表
        :param filters: 过滤条件
        :return: (DTO列表, 总数)
        """
        from sqlalchemy import func

        # 构建查询语句
        stmt = select(model_class)
        count_stmt = select(func.count()).select_from(model_class)

        # 添加过滤条件
        for field, value in filters.items():
            if hasattr(model_class, field):
                stmt = stmt.where(getattr(model_class, field) == value)
                count_stmt = count_stmt.where(getattr(model_class, field) == value)

        # 获取总数
        count_result = await db.execute(count_stmt)
        total = count_result.scalar_one()

        # 添加分页
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        # 执行查询
        result = await db.execute(stmt)
        model_instances = result.scalars().all()

        # 转换为DTO列表
        dto_list = ModelConverter.to_dto_list(model_instances, dto_class, exclude_fields)

        return dto_list, total

    @staticmethod
    def model_to_dict(
        model_instance: M,
        exclude_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        将SQLAlchemy模型实例转换为字典
        :param model_instance: SQLAlchemy模型实例
        :param exclude_fields: 要排除的字段列表
        :return: 字典
        """
        if model_instance is None:
            return {}

        result = {}
        for column in model_instance.__table__.columns:
            field_name = column.name
            if exclude_fields and field_name in exclude_fields:
                continue

            value = getattr(model_instance, field_name)
            # 处理枚举类型
            value = ModelConverter._handle_enum_value(value)
            # 处理特殊类型
            if isinstance(value, datetime):
                result[field_name] = value.isoformat() if value else None
            elif hasattr(value, '__dict__'):
                result[field_name] = str(value)
            else:
                result[field_name] = value

        return result

    @staticmethod
    def dict_to_model(
        data: Dict[str, Any],
        model_class: Type[M],
        exclude_fields: Optional[List[str]] = None
    ) -> M:
        """
        将字典转换为SQLAlchemy模型实例
        :param data: 字典数据
        :param model_class: SQLAlchemy模型类
        :param exclude_fields: 要排除的字段列表
        :return: SQLAlchemy模型实例
        """
        if exclude_fields:
            filtered_data = {k: v for k, v in data.items() if k not in exclude_fields}
        else:
            filtered_data = data
        return model_class(**filtered_data)

    @staticmethod
    def update_model_from_dto(
        model_instance: M,
        dto_instance: T,
        exclude_fields: Optional[List[str]] = None
    ) -> M:
        """
        将Pydantic DTO的数据更新到现有的SQLAlchemy模型实例中
        :param model_instance: 现有的SQLAlchemy模型实例
        :param dto_instance: Pydantic DTO实例
        :param exclude_fields: 要排除的字段列表
        :return: 更新后的SQLAlchemy模型实例
        """
        if model_instance is None:
            raise ValueError("Model instance cannot be None")

        if dto_instance is None:
            return model_instance

        # 将DTO转换为字典，只包含设置了值的字段
        dto_dict = dto_instance.model_dump(exclude_unset=True)

        # 处理字段排除
        if exclude_fields:
            filtered_dict = {k: v for k, v in dto_dict.items() if k not in exclude_fields}
        else:
            filtered_dict = dto_dict

        # 更新模型实例的属性
        for field, value in filtered_dict.items():
            if hasattr(model_instance, field):
                setattr(model_instance, field, value)

        return model_instance
