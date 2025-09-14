from typing import Optional

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

    secret_key: str = "9E8D9056-B1A5-4632-B417-6FEEC82A4CEC"
    access_token_expire_days: int = 3


    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None


    space_prefix: str = "space_session:"


    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore',
        env_file=".env"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()



