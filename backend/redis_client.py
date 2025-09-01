import redis.asyncio as redis
import json
import os
from dotenv import load_dotenv
from typing import Optional, Any, Dict, List
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        """Initialize Redis connection with credentials from environment"""
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_db = int(os.getenv("REDIS_DB", 0))
        self.redis_password = os.getenv("REDIS_PASSWORD", None)
        self.redis_ssl = os.getenv("REDIS_SSL", "false").lower() == "true"
        
        # Create Redis connection pool
        self.pool = redis.ConnectionPool(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            password=self.redis_password,
            ssl=self.redis_ssl,
            decode_responses=True,
            max_connections=20
        )
        
        self.client = None
        self.pubsub = None
    
    async def connect(self):
        """Establish Redis connection"""
        try:
            self.client = redis.Redis(connection_pool=self.pool)
            self.pubsub = self.client.pubsub()
            # Test connection
            await self.client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def ping(self) -> bool:
        """Ping Redis server to test connection"""
        try:
            if not self.client:
                await self.connect()
            result = await self.client.ping()
            return result
        except Exception as e:
            logger.error(f"Redis PING error: {e}")
            return False
    
    async def disconnect(self):
        """Close Redis connection"""
        try:
            if self.pubsub:
                await self.pubsub.close()
            if self.client:
                await self.client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        try:
            if not self.client:
                await self.connect()
            value = await self.client.get(key)
            return value
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set key-value pair with optional expiration"""
        try:
            if not self.client:
                await self.connect()
            result = await self.client.set(key, value, ex=ex)
            return result
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    async def set_json(self, key: str, value: Dict[str, Any], ex: Optional[int] = None) -> bool:
        """Set JSON value by key"""
        try:
            json_value = json.dumps(value)
            return await self.set(key, json_value, ex=ex)
        except Exception as e:
            logger.error(f"Redis SET JSON error for key {key}: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get JSON value by key"""
        try:
            value = await self.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET JSON error for key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete key"""
        try:
            if not self.client:
                await self.connect()
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            if not self.client:
                await self.connect()
            result = await self.client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration"""
        try:
            if not self.client:
                await self.connect()
            result = await self.client.expire(key, seconds)
            return result
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False
    
    async def publish(self, channel: str, message: str) -> int:
        """Publish message to channel"""
        try:
            if not self.client:
                await self.connect()
            result = await self.client.publish(channel, message)
            logger.debug(f"Published message to channel {channel}: {result} subscribers")
            return result
        except Exception as e:
            logger.error(f"Redis PUBLISH error for channel {channel}: {e}")
            return 0
    
    async def publish_json(self, channel: str, message: Dict[str, Any]) -> int:
        """Publish JSON message to channel"""
        try:
            json_message = json.dumps(message)
            return await self.publish(channel, json_message)
        except Exception as e:
            logger.error(f"Redis PUBLISH JSON error for channel {channel}: {e}")
            return 0
    
    async def subscribe(self, channel: str):
        """Subscribe to channel"""
        try:
            if not self.pubsub:
                await self.connect()
            await self.pubsub.subscribe(channel)
            logger.info(f"Subscribed to channel: {channel}")
        except Exception as e:
            logger.error(f"Redis SUBSCRIBE error for channel {channel}: {e}")
            raise
    
    async def unsubscribe(self, channel: str):
        """Unsubscribe from channel"""
        try:
            if self.pubsub:
                await self.pubsub.unsubscribe(channel)
                logger.info(f"Unsubscribed from channel: {channel}")
        except Exception as e:
            logger.error(f"Redis UNSUBSCRIBE error for channel {channel}: {e}")
    
    async def listen(self):
        """Listen for messages on subscribed channels"""
        try:
            if not self.pubsub:
                await self.connect()
            
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    yield message
        except Exception as e:
            logger.error(f"Redis LISTEN error: {e}")
            raise
    
    def pipeline(self):
        """Get Redis pipeline for batch operations"""
        try:
            if not self.client:
                raise ConnectionError("Redis not connected")
            return self.client.pipeline()
        except Exception as e:
            logger.error(f"Redis PIPELINE error: {e}")
            raise
    
    async def execute_pipeline(self, pipeline_commands: List[tuple]) -> List[Any]:
        """Execute pipeline commands"""
        try:
            if not self.client:
                await self.connect()
            
            pipe = self.client.pipeline()
            
            for command, *args in pipeline_commands:
                getattr(pipe, command)(*args)
            
            results = await pipe.execute()
            return results
        except Exception as e:
            logger.error(f"Redis PIPELINE EXECUTE error: {e}")
            raise
    
    async def lpush(self, key: str, value: str) -> int:
        """Push value to left of list"""
        try:
            if not self.client:
                await self.connect()
            result = await self.client.lpush(key, value)
            return result
        except Exception as e:
            logger.error(f"Redis LPUSH error for key {key}: {e}")
            return 0
    
    async def rpush(self, key: str, value: str) -> int:
        """Push value to right of list"""
        try:
            if not self.client:
                await self.connect()
            result = await self.client.rpush(key, value)
            return result
        except Exception as e:
            logger.error(f"Redis RPUSH error for key {key}: {e}")
            return 0
    
    async def lrange(self, key: str, start: int = 0, end: int = -1) -> List[str]:
        """Get range of list elements"""
        try:
            if not self.client:
                await self.connect()
            result = await self.client.lrange(key, start, end)
            return result
        except Exception as e:
            logger.error(f"Redis LRANGE error for key {key}: {e}")
            return []
    
    async def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim list to specified range"""
        try:
            if not self.client:
                await self.connect()
            result = await self.client.ltrim(key, start, end)
            return result
        except Exception as e:
            logger.error(f"Redis LTRIM error for key {key}: {e}")
            return False

# Global Redis client instance
redis_client = RedisClient()
