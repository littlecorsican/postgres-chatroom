import redis.asyncio as redis
from typing import Optional, Any, Dict, List
import json
from config import Config

class RedisClient:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        
    async def connect(self):
        """Connect to Redis"""
        if not self.redis_client:
            self.redis_client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                password=Config.REDIS_PASSWORD,
                decode_responses=True,
                encoding='utf-8'
            )
            # Test connection
            await self.redis_client.ping()
            print("Connected to Redis")
            
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            print("Disconnected from Redis")
            
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        if not self.redis_client:
            await self.connect()
        return await self.redis_client.get(key)
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set key-value pair with optional expiration"""
        if not self.redis_client:
            await self.connect()
        return await self.redis_client.set(key, value, ex=ex)
    
    async def publish(self, channel: str, message: str) -> int:
        """Publish message to channel"""
        if not self.redis_client:
            await self.connect()
        return await self.redis_client.publish(channel, message)
    
    async def pipeline(self) -> redis.client.Pipeline:
        """Get Redis pipeline for batch operations"""
        if not self.redis_client:
            await self.connect()
        return self.redis_client.pipeline()
    
    async def subscribe(self, channel: str):
        """Subscribe to a Redis channel"""
        if not self.redis_client:
            await self.connect()
        self.pubsub = self.redis_client.pubsub()
        await self.pubsub.subscribe(channel)
        return self.pubsub
    
    async def listen(self):
        """Listen for messages on subscribed channels"""
        if not self.pubsub:
            raise RuntimeError("Must subscribe to channels before listening")
        
        async for message in self.pubsub.listen():
            if message['type'] == 'message':
                yield message['data']

# Global Redis client instance
redis_client = RedisClient()
