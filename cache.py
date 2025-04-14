import os
import json
import logging
import redis
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

# Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # Default to 1 hour

try:
    redis_client = redis.from_url(REDIS_URL)
    redis_client.ping()  # Test connection
    logger.info("Redis connection established successfully")
except redis.exceptions.ConnectionError as e:
    logger.warning(f"Failed to connect to Redis: {e}. Caching will be disabled.")
    redis_client = None

class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that can handle datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def json_datetime_hook(obj):
    """JSON decoder hook to convert datetime strings back to datetime objects."""
    for key, value in obj.items():
        if isinstance(value, str):
            try:
                obj[key] = datetime.fromisoformat(value)
            except (ValueError, TypeError):
                pass
    return obj

def cache_enabled():
    """Check if the cache is enabled."""
    return redis_client is not None

async def get_cached(key):
    """Get a value from the cache."""
    if not cache_enabled():
        return None
    
    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value, object_hook=json_datetime_hook)
        return None
    except Exception as e:
        logger.error(f"Error getting from cache: {e}")
        return None

async def set_cached(key, value, ttl=None):
    """Set a value in the cache."""
    if not cache_enabled():
        return False
    
    ttl = ttl or CACHE_TTL
    
    try:
        redis_client.setex(
            key,
            ttl,
            json.dumps(value, cls=DateTimeEncoder)
        )
        return True
    except Exception as e:
        logger.error(f"Error setting cache: {e}")
        return False

async def delete_cached(key):
    """Delete a value from the cache."""
    if not cache_enabled():
        return False
    
    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Error deleting from cache: {e}")
        return False

async def get_cached_user(telegram_id):
    """Get a user from the cache."""
    return await get_cached(f"user:{telegram_id}")

async def set_cached_user(telegram_id, user_data):
    """Set a user in the cache."""
    return await set_cached(f"user:{telegram_id}", user_data)

async def get_cached_group(telegram_id):
    """Get a group from the cache."""
    return await get_cached(f"group:{telegram_id}")

async def set_cached_group(telegram_id, group_data):
    """Set a group in the cache."""
    return await set_cached(f"group:{telegram_id}", group_data)

async def get_cached_quotes():
    """Get all quotes from the cache."""
    return await get_cached("quran_quotes")

async def set_cached_quotes(quotes):
    """Set all quotes in the cache."""
    return await set_cached("quran_quotes", quotes, 86400)  # Cache for 24 hours 