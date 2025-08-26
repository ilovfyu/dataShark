import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.core.logs.loguru_config import Logger
from backend.core.settings.config import get_settings
from backend.middleware.log_middleware import log_middleware

confi = get_settings()
logx = Logger.get_logger()


@asynccontextmanager
async def register_init(app: FastAPI):
    logx.info("🚀 Application starting up......")
    await asyncio.sleep(1)
    yield
    logx.info("🚀 Application shutting down......")
    await asyncio.sleep(1)



def configure_router(app: FastAPI):
    pass



def configure_middleware(app: FastAPI):
    app.add_middleware(log_middleware)
    pass



def configure_exception_handler(app: FastAPI):
    pass



def create_app() -> FastAPI:
    app = FastAPI(
        title=confi.app_name,
        version=confi.version,
        description=confi.description,
        lifespan=register_init,
        docs_url=confi.api_doc,
    )
    configure_router(app)
    configure_middleware(app)
    configure_exception_handler(app)

    return app





