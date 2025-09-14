import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.api.router import main_apirouter
from backend.core.db.redis import redis_client
from backend.core.logs.loguru_config import Logger
from backend.core.settings.config import get_settings
from backend.core.db.mysql import db
from backend.middleware.log_middleware import LoguruMiddleware
from backend.middleware.request_id_middleware import RequestIDMiddleware
from backend.common.exception_handler import configure_exception_handlers
import backend.models

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
        logx.error(f"❌ Failed to create db tables: {e}")
        raise

    try:
        await redis_client.init_app()
        logx.info("✅ Database tables created successfully")
    except Exception as e:
        logx.info(f"❌ Failed to create db tables: {e}")
        raise
    await asyncio.sleep(1)
    yield
    logx.info("🚀 Application shutting down......")
    await asyncio.sleep(1)
    await db.close()


def configure_router(app: FastAPI):
    app.include_router(main_apirouter, prefix=confi.api_root_path)



def configure_middleware(app: FastAPI):
    app.add_middleware(
        LoguruMiddleware,
        skip_routes=["/health", "/metrics", "/docs", "/redoc", "/openapi.json"],
        skip_keywords=["static", "favicon"]

    )
    app.add_middleware(RequestIDMiddleware)




def create_app() -> FastAPI:
    app = FastAPI(
        title=confi.app_name,
        version=confi.version,
        description=confi.description,
        lifespan=register_init,
    )
    configure_router(app)
    configure_middleware(app)
    configure_exception_handlers(app)
    return app






