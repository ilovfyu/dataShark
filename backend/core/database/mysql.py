from typing import AsyncGenerator, Optional, List, Type
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, DeclarativeMeta
from sqlalchemy.pool import QueuePool
from backend.core.logs.loguru_config import Logger

# 配置日志
logger = Logger.get_logger()

Base = declarative_base()

class AsyncDatabase:
    def __init__(self):
        self._engine = None
        self._session_factory = None

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
            logger.error(f"Failed to initialize database engine: {e}")
            raise

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
        if not self._engine:
            raise RuntimeError("Database not initialized. Call init_app first.")

        async with self._engine.begin() as conn:
            if models:
                for model in models:
                    if hasattr(model, '__table__'):
                        await conn.run_sync(model.__table__.create, checkfirst=True)
                        logger.info(f"Created table for model: {model.__name__}")
            else:
                await conn.run_sync(Base.metadata.create_all, checkfirst=True)
                logger.info("Created all tables")


    async def create_tables_safe(self):
        if not self._engine:
            raise RuntimeError("Database not initialized. Call init_app first.")

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
            logger.info("Created tables safely")




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
