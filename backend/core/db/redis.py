import asyncio
import json
from typing import Optional, Any, Union
import redis.asyncio as redis
from backend.core.settings.config import get_settings
from backend.core.logs.loguru_config import Logger

logx = Logger.get_logger()
confi = get_settings()

class AsyncRedis:
    def __init__(self):
        self._redis = None
        self._connection_params = {
            "host": confi.redis_host or "localhost",
            "port": confi.redis_port or 6379,
            "db": confi.redis_db or 0,
            "password": confi.redis_password or None,
            "encoding": "utf-8",
            "decode_responses": True,
        }

    async def init_app(self, **kwargs):
        """初始化Redis连接"""
        # 合并连接参数
        connection_params = {**self._connection_params, **kwargs}

        try:
            self._redis = redis.Redis(**connection_params)
            # 测试连接
            await self._redis.ping()
            logx.info("Redis连接初始化成功")
        except Exception as e:
            logx.error(f"Redis连接初始化失败: {e}")
            raise

    async def close(self):
        """关闭Redis连接"""
        if self._redis:
            await self._redis.close()
            logx.info("Redis连接已关闭")

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置键值对"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            result = await self._redis.set(key, value, ex=expire)
            return result
        except Exception as e:
            logx.error(f"Redis设置键值对失败: {e}")
            return False

    async def get(self, key: str) -> Optional[str]:
        """获取键值"""
        try:
            return await self._redis.get(key)
        except Exception as e:
            logx.error(f"Redis获取键值失败: {e}")
            return None

    async def delete(self, *keys: str) -> int:
        """删除键"""
        try:
            return await self._redis.delete(*keys)
        except Exception as e:
            logx.error(f"Redis删除键失败: {e}")
            return 0

    async def exists(self, *keys: str) -> int:
        """检查键是否存在"""
        try:
            return await self._redis.exists(*keys)
        except Exception as e:
            logx.error(f"Redis检查键存在性失败: {e}")
            return 0

    async def expire(self, key: str, seconds: int) -> bool:
        """设置键过期时间"""
        try:
            return await self._redis.expire(key, seconds)
        except Exception as e:
            logx.error(f"Redis设置过期时间失败: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """获取键剩余过期时间"""
        try:
            return await self._redis.ttl(key)
        except Exception as e:
            logx.error(f"Redis获取过期时间失败: {e}")
            return -1

    async def hset(self, name: str, key: str, value: Any) -> int:
        """设置哈希表字段的值"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return await self._redis.hset(name, key, value)
        except Exception as e:
            logx.error(f"Redis设置哈希字段失败: {e}")
            return 0

    async def hget(self, name: str, key: str) -> Optional[str]:
        """获取哈希表字段的值"""
        try:
            return await self._redis.hget(name, key)
        except Exception as e:
            logx.error(f"Redis获取哈希字段失败: {e}")
            return None

    async def hgetall(self, name: str) -> dict:
        """获取哈希表所有字段和值"""
        try:
            return await self._redis.hgetall(name)
        except Exception as e:
            logx.error(f"Redis获取哈希表失败: {e}")
            return {}

    async def hmset(self, name: str, mapping: dict) -> bool:
        """同时将多个 field-value (域-值)对设置到哈希表中"""
        try:
            # 处理字典中的复杂对象
            processed_mapping = {}
            for k, v in mapping.items():
                if isinstance(v, (dict, list)):
                    processed_mapping[k] = json.dumps(v)
                else:
                    processed_mapping[k] = v
            return await self._redis.hmset(name, processed_mapping)
        except Exception as e:
            logx.error(f"Redis批量设置哈希字段失败: {e}")
            return False

    async def hdel(self, name: str, *keys: str) -> int:
        """删除哈希表一个或多个字段"""
        try:
            return await self._redis.hdel(name, *keys)
        except Exception as e:
            logx.error(f"Redis删除哈希字段失败: {e}")
            return 0

    async def sadd(self, name: str, *values: str) -> int:
        """向集合添加一个或多个成员"""
        try:
            return await self._redis.sadd(name, *values)
        except Exception as e:
            logx.error(f"Redis向集合添加成员失败: {e}")
            return 0

    async def srem(self, name: str, *values: str) -> int:
        """移除集合中一个或多个成员"""
        try:
            return await self._redis.srem(name, *values)
        except Exception as e:
            logx.error(f"Redis从集合移除成员失败: {e}")
            return 0

    async def smembers(self, name: str) -> set:
        """返回集合中的所有成员"""
        try:
            return await self._redis.smembers(name)
        except Exception as e:
            logx.error(f"Redis获取集合成员失败: {e}")
            return set()

    async def sismember(self, name: str, value: str) -> bool:
        """判断成员元素是否是集合的成员"""
        try:
            return await self._redis.sismember(name, value)
        except Exception as e:
            logx.error(f"Redis检查集合成员失败: {e}")
            return False

    async def incr(self, name: str, amount: int = 1) -> int:
        """将 key 中储存的数字值增一"""
        try:
            return await self._redis.incr(name, amount=amount)
        except Exception as e:
            logx.error(f"Redis自增操作失败: {e}")
            return 0

    async def decr(self, name: str, amount: int = 1) -> int:
        """将 key 中储存的数字值减一"""
        try:
            return await self._redis.decr(name, amount=amount)
        except Exception as e:
            logx.error(f"Redis自减操作失败: {e}")
            return 0

    async def lpush(self, name: str, *values: str) -> int:
        """将一个或多个值插入到列表头部"""
        try:
            return await self._redis.lpush(name, *values)
        except Exception as e:
            logx.error(f"Redis列表左插入失败: {e}")
            return 0

    async def rpush(self, name: str, *values: str) -> int:
        """将一个或多个值插入到列表尾部"""
        try:
            return await self._redis.rpush(name, *values)
        except Exception as e:
            logx.error(f"Redis列表右插入失败: {e}")
            return 0

    async def lrange(self, name: str, start: int, end: int) -> list:
        """获取列表指定范围内的元素"""
        try:
            return await self._redis.lrange(name, start, end)
        except Exception as e:
            logx.error(f"Redis获取列表元素失败: {e}")
            return []

    async def pipeline(self):
        """创建管道"""
        try:
            return self._redis.pipeline()
        except Exception as e:
            logx.error(f"Redis创建管道失败: {e}")
            return None

    @property
    def redis(self):
        """获取原始redis连接对象"""
        return self._redis

redis_client = AsyncRedis()
