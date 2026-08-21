import json
import logging
from typing import Dict, List, Any
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger("cortexflow")

class RedisManager:
    def __init__(self):
        self.client: aioredis.Redis = None
        self.is_connected: bool = False
        self._memory_store: Dict[str, List[Dict[str, Any]]] = {}

redis_manager = RedisManager()

async def connect_to_redis():
    try:
        client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        await client.ping()
        redis_manager.client = client
        redis_manager.is_connected = True
        logger.info("✅ Connected to Redis successfully.")
    except Exception as e:
        redis_manager.client = None
        redis_manager.is_connected = False
        logger.info("ℹ️ Redis server not running locally. Using fast In-Memory Store for conversation memory.")

async def close_redis_connection():
    if redis_manager.client and redis_manager.is_connected:
        try:
            await redis_manager.client.close()
            logger.info("Closed Redis connection.")
        except Exception:
            pass

async def get_redis():
    return redis_manager.client if redis_manager.is_connected else None

# Helper functions for memory & rate limiting
async def add_chat_memory(conversation_id: str, role: str, content: str, limit: int = 20):
    if not conversation_id:
        return
    
    if redis_manager.is_connected and redis_manager.client:
        try:
            key = f"chat_memory:{conversation_id}"
            msg = json.dumps({"role": role, "content": content})
            await redis_manager.client.rpush(key, msg)
            await redis_manager.client.ltrim(key, -limit, -1)
            await redis_manager.client.expire(key, 86400 * 3)  # 3 days TTL
            return
        except Exception:
            redis_manager.is_connected = False

    # In-memory RAM Fallback
    if conversation_id not in redis_manager._memory_store:
        redis_manager._memory_store[conversation_id] = []
    redis_manager._memory_store[conversation_id].append({"role": role, "content": content})
    if len(redis_manager._memory_store[conversation_id]) > limit:
        redis_manager._memory_store[conversation_id] = redis_manager._memory_store[conversation_id][-limit:]

async def get_chat_memory(conversation_id: str) -> List[Dict[str, Any]]:
    if not conversation_id:
        return []

    if redis_manager.is_connected and redis_manager.client:
        try:
            key = f"chat_memory:{conversation_id}"
            items = await redis_manager.client.lrange(key, 0, -1)
            return [json.loads(item) for item in items]
        except Exception:
            redis_manager.is_connected = False

    # In-memory RAM Fallback
    return list(redis_manager._memory_store.get(conversation_id, []))
