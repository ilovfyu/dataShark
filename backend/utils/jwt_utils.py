# backend/core/security/jwt_utils.py
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from backend.core.settings.config import get_settings
from backend.core.logs.loguru_config import Logger


confi = get_settings()
logger = Logger.get_logger()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    encode.update({"exp": expire})
    jwt_token = jwt.encode(encode, confi.secret_key, algorithm=ALGORITHM)
    return jwt_token

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, confi.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        logger.error("decode access token failed.")
        return None



token_blacklist = set()
def is_token_blacklisted(token: str) -> bool:
    try:
        # 解码令牌以验证其有效性
        payload = jwt.decode(token, confi.secret_key, algorithms=[ALGORITHM])
        exp = payload.get("exp")
        # 只有未过期的令牌才加入黑名单
        if exp and datetime.utcfromtimestamp(exp) > datetime.utcnow():
            token_blacklist.add(token)
            return True
        return False
    except JWTError:
        return False