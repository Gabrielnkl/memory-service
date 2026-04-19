# redis.py - Redis Cache Operations
#
# Redis provides fast, short-term memory storage. It stores:
# - Recent messages per user (last N messages)
# - Session context
# - Temporary data that doesn't need persistence
#
# Redis is much faster than PostgreSQL but data is lost on restart.
# Use it for frequently accessed, short-lived data.
#
# What you need to implement:
# 1. Set up Redis connection using redis-py library
# 2. Create RedisService class
# 3. Implement store_recent_message(user_id: str, message: dict) method:
#    - Store message in a Redis list (LPUSH)
#    - Trim list to keep only last N messages (LTRIM)
#    - Set TTL if needed
# 4. Implement get_recent_messages(user_id: str, limit: int = 10) method:
#    - Get recent messages from Redis list (LRANGE)
#    - Return as list of message dicts
# 5. Implement clear_user_cache(user_id: str) method:
#    - Delete user's message list
# 6. Add connection pooling and error handling
# 7. Consider using Redis hashes or sorted sets for more complex data
#
# For production:
# - Add Redis cluster support
# - Add connection retry logic
# - Add Redis pub/sub for real-time features

# TODO: Import redis library
# TODO: Create RedisService class
# TODO: Implement store_recent_message method
# TODO: Implement get_recent_messages method
# TODO: Implement cache management methods
# TODO: Add connection handling and error recovery

import os
import json
import redis.asyncio as redis
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()


class RedisService:
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.ttl = int(os.getenv("REDIS_TTL", 3600))  # default: 1 hour
        self.max_messages = int(os.getenv("REDIS_MAX_MESSAGES", 10))

    async def connect(self):
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD", None),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True  # important for string handling
        )

        # Test connection
        try:
            await self.client.ping()
            print("[Redis] Connected successfully")
        except Exception as e:
            print(f"[Redis] Connection error: {e}")
            raise

    def _get_key(self, user_id: str) -> str:
        return f"user:{user_id}:messages"

    async def store_recent_message(self, user_id: str, message: Dict):
        """
        Store message in Redis list (most recent first)
        """
        key = self._get_key(user_id)

        try:
            # Convert dict → JSON string
            message_json = json.dumps(message)

            # LPUSH (add to head)
            await self.client.lpush(key, message_json)

            # Keep only last N messages
            await self.client.ltrim(key, 0, self.max_messages - 1)

            # Set TTL (refresh on every write)
            await self.client.expire(key, self.ttl)

        except Exception as e:
            print(f"[Redis] Error storing message: {e}")

    async def get_recent_messages(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict]:
        key = self._get_key(user_id)

        try:
            # Get messages (most recent first)
            messages = await self.client.lrange(key, 0, limit - 1)

            # Convert JSON → dict
            return [json.loads(m) for m in messages]

        except Exception as e:
            print(f"[Redis] Error fetching messages: {e}")
            return []

    async def clear_user_cache(self, user_id: str):
        key = self._get_key(user_id)

        try:
            await self.client.delete(key)
        except Exception as e:
            print(f"[Redis] Error clearing cache: {e}")