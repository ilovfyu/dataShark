from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache



class Settings(BaseSettings):


    app_name: str = "DATA_SHARK"
    debug: bool = True
    version: str = "rc_0.0.1"
    description: str = "spark manager platform."
    api_host: str = "0.0.0.0"
    api_port: int = 4106
    api_root_path: str = "/data_shark/v1/api"
    api_doc: str = f"{api_root_path}/docs"


    log_dir: str = "logs"
    log_level: str = "INFO"
    log_rotation: str = "10 MB"
    log_retention: str = "7 days"
    log_serializer: bool = True
    log_compress: bool = False
    log_sqlecho: bool = True



    db_username: str = "root"
    db_password: str = "niosle#123"
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_name: str = "data_shark"


    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore',
        env_file=".env"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()



