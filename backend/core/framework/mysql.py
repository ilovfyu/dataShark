from typing import AsyncGenerator, Optional, List, Type
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, DeclarativeMeta
from backend.core.logs.loguru_config import Logger
from backend.core.settings.config import get_settings

# 配置日志
logger = Logger.get_logger()
confi = get_settings()

Base = declarative_base()

class AsyncDatabase:
    def __init__(self):
        self._engine = None
        self._session_factory = None
        self._models = []
    def init_app(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_pre_ping: bool = True,
        pool_recycle: int = 3600
    ):
        try:
            # 创建异步引擎
            self._engine = create_async_engine(
                database_url,
                echo=echo,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=pool_pre_ping,
                pool_recycle=pool_recycle,
            )

            # 创建会话工厂
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False
            )

            logger.info("Database engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize db engine: {e}")
            raise


    def register_model(self, model: Type[DeclarativeMeta]):
        "注册模型"
        if model not in self._models:
            self._models.append(model)
            logger.debug(f"Register model: {model.__name__}")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call init_app first.")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def get_session_no_commit(self) -> AsyncGenerator[AsyncSession, None]:
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call init_app first.")

        async with self._session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    async def execute_transaction(self, func):
        async with self._session_factory() as session:
            try:
                result = await func(session)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise

    async def close(self):
        if self._engine:
            await self._engine.dispose()
            logger.info("Database engine closed")

    @property
    def engine(self):
        return self._engine

    @property
    def session_factory(self):
        return self._session_factory

    async def create_tables(self, models: Optional[List[Type[DeclarativeMeta]]] = None):
        """创建指定模型的表"""
        if not self._engine:
            raise RuntimeError("Database not initialized. Call init_app first.")

        # 如果没有指定模型，则使用已注册的模型
        if models is None:
            models = self._models

        if not models:
            logger.warning("No models to create tables for")
            return

        async with self._engine.begin() as conn:
            for model in models:
                if hasattr(model, '__table__'):
                    await conn.run_sync(model.__table__.create, checkfirst=True)
                    logger.info(f"Created table for model: {model.__name__}")


    async def create_tables_safe(self):
        if not self._engine:
            raise RuntimeError("Database not initialized. Call init_app first.")
        if self._models:
            async with self._engine.begin() as conn:
                for model in self._models:
                    if hasattr(model, '__table__'):
                        await conn.run_sync(model.__table__.create, checkfirst=True)
                        logger.info(f"Created table for registered model: {model.__name__}")




db = AsyncDatabase()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI依赖注入函数
    """
    async for session in db.get_session():
        yield session

async def get_db_readonly() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI只读依赖注入函数
    """
    async for session in db.get_session_no_commit():
        yield session


# backend/core/framework/mysql.py

import asyncio
import json
from typing import Dict, AsyncGenerator, Optional, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeMeta
from sqlalchemy.exc import SQLAlchemyError
from backend.core.logs.loguru_config import Logger

logger = Logger.get_logger()









class WorkspaceDatabaseManager:
    """工作空间数据库管理器"""

    def __init__(self):
        """初始化工作空间数据库管理器"""
        self._engines: Dict[str, Any] = {}
        self._session_factories: Dict[str, Any] = {}
        self._lock = asyncio.Lock()  # 用于线程安全

    def get_engine(self, workspace_id: str, database_url: str):
        """
        获取工作空间数据库引擎

        :param workspace_id: 工作空间ID
        :param database_url: 数据库URL
        :return: 数据库引擎
        """
        if workspace_id not in self._engines:
            try:
                engine = create_async_engine(
                    database_url,
                    echo=False,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    pool_timeout=30
                )
                self._engines[workspace_id] = engine
                logger.info(f"创建工作空间 {workspace_id} 的数据库引擎成功")
            except Exception as e:
                logger.error(f"创建工作空间 {workspace_id} 的数据库引擎失败: {e}")
                raise

        return self._engines[workspace_id]

    def get_session_factory(self, workspace_id: str, database_url: str):
        """
        获取工作空间会话工厂

        :param workspace_id: 工作空间ID
        :param database_url: 数据库URL
        :return: 会话工厂
        """
        if workspace_id not in self._session_factories:
            engine = self.get_engine(workspace_id, database_url)
            session_factory = async_sessionmaker(
                bind=engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False
            )
            self._session_factories[workspace_id] = session_factory
            logger.info(f"创建工作空间 {workspace_id} 的会话工厂成功")

        return self._session_factories[workspace_id]

    async def get_session(self, workspace_id: str, database_url: str) -> AsyncGenerator[AsyncSession, None]:
        """
        获取工作空间数据库会话

        :param workspace_id: 工作空间ID
        :param database_url: 数据库URL
        :return: 数据库会话
        """
        # 使用锁确保线程安全
        async with self._lock:
            session_factory = self.get_session_factory(workspace_id, database_url)

        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"工作空间 {workspace_id} 数据库会话执行失败: {e}")
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"工作空间 {workspace_id} 数据库会话发生未知错误: {e}")
                raise
            finally:
                await session.close()

    async def get_session_no_commit(self, workspace_id: str, database_url: str) -> AsyncGenerator[AsyncSession, None]:
        """
        获取工作空间数据库只读会话（不自动提交）

        :param workspace_id: 工作空间ID
        :param database_url: 数据库URL
        :return: 数据库会话
        """
        # 使用锁确保线程安全
        async with self._lock:
            session_factory = self.get_session_factory(workspace_id, database_url)

        async with session_factory() as session:
            try:
                yield session
                # 只读会话不提交
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"工作空间 {workspace_id} 只读会话执行失败: {e}")
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"工作空间 {workspace_id} 只读会话发生未知错误: {e}")
                raise
            finally:
                await session.close()

    async def close_engine(self, workspace_id: str):
        """
        关闭工作空间数据库引擎

        :param workspace_id: 工作空间ID
        """
        async with self._lock:
            if workspace_id in self._engines:
                engine = self._engines.pop(workspace_id)
                await engine.dispose()
                logger.info(f"关闭工作空间 {workspace_id} 的数据库引擎成功")

            # 同时清理会话工厂
            if workspace_id in self._session_factories:
                del self._session_factories[workspace_id]

    async def close_all_engines(self):
        """关闭所有工作空间数据库引擎"""
        async with self._lock:
            # 创建副本以避免在迭代时修改字典
            workspace_ids = list(self._engines.keys())

            for workspace_id in workspace_ids:
                await self.close_engine(workspace_id)

            logger.info("关闭所有工作空间数据库引擎成功")

    def is_engine_exists(self, workspace_id: str) -> bool:
        """
        检查工作空间数据库引擎是否存在

        :param workspace_id: 工作空间ID
        :return: 是否存在
        """
        return workspace_id in self._engines

    async def test_connection(self, workspace_id: str, database_url: str) -> bool:
        """
        测试工作空间数据库连接

        :param workspace_id: 工作空间ID
        :param database_url: 数据库URL
        :return: 连接是否成功
        """
        try:
            engine = self.get_engine(workspace_id, database_url)
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"工作空间 {workspace_id} 数据库连接测试失败: {e}")
            return False

    async def get_engine_stats(self) -> Dict[str, Any]:
        """
        获取所有引擎的统计信息

        :return: 引擎统计信息
        """
        async with self._lock:
            return {
                "total_engines": len(self._engines),
                "workspace_ids": list(self._engines.keys()),
                "engines_info": {
                    workspace_id: {
                        "has_session_factory": workspace_id in self._session_factories
                    }
                    for workspace_id in self._engines.keys()
                }
            }


# 全局实例
workspace_db_manager = WorkspaceDatabaseManager()
