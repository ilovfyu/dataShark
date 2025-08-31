import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.core.logs.loguru_config import Logger
from backend.core.settings.config import get_settings
from backend.core.database.mysql import db
from backend.middleware.log_middleware import LoguruMiddleware

confi = get_settings()
logx = Logger.get_logger()


@asynccontextmanager
async def register_init(app: FastAPI):
    logx.info("🚀 Application starting up......")

    db.init_app(
        database_url=f"mysql+aiomysql://{confi.db_username}:{confi.db_password}@{confi.db_host}:{confi.db_port}/{confi.db_name}",
        echo=True if confi.debug else False,

    )
    try:
        await db.create_tables_safe()
        logx.info("✅ Database tables created successfully")
    except Exception as e:
        logx.error(f"❌ Failed to create database tables: {e}")
        raise
    await asyncio.sleep(1)
    yield
    logx.info("🚀 Application shutting down......")
    await asyncio.sleep(1)
    await db.close()


def configure_router(app: FastAPI):
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    @app.get("/users/{user_id}")
    async def get_user(user_id: int):
        """获取用户信息"""
        # 模拟数据库查询
        return {"user_id": user_id, "name": "John Doe"}

    pass



def configure_middleware(app: FastAPI):
    app.add_middleware(
        LoguruMiddleware,
        skip_routes=["/health", "/metrics", "/docs", "/redoc", "/openapi.json"],
        skip_keywords=["static", "favicon"]

    )
    pass




def create_app() -> FastAPI:
    app = FastAPI(
        title=confi.app_name,
        version=confi.version,
        description=confi.description,
        lifespan=register_init,
        # docs_url=confi.api_doc,
    )
    configure_router(app)
    configure_middleware(app)
    return app






