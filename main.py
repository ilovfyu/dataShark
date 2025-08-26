from backend.core.application.enter import create_app
from backend.core.settings.config import get_settings

confi = get_settings()
app = create_app()


if __name__ == '__main__':
    import uvicorn
    config = uvicorn.Config(
        app=app,
        host=confi.api_host,
        port=confi.api_port,
        log_config=None,
    )
    server = uvicorn.Server(config=config)
    server.run()