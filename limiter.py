import time
import redis
from typing import Dict, Tuple

class DistributedTokenBucket:
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        # Establish connection to Redis cluster/node for atomic operations
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
        # Local in-memory caching tier to bypass network roundtrips for highly active clients
        self.local_cache: Dict[str, Tuple[float, bool]] = {}
        self.local_cache_ttl = 0.05  # 50ms local memory lockout window

    def is_allowed(self, client_id: str, rate: int, capacity: int) -> bool:
        current_time = time.time()
        
        # 1. Check local in-memory cache to minimize cross-network roundtrip latency
        if client_id in self.local_cache:
            cached_time, last_result = self.local_cache[client_id]
            if current_time - cached_time < self.local_cache_ttl and not last_result:
                return False  # Swiftly reject without hitting Redis if recently blocked

        # 2. Centralized atomic execution using a Redis Lua script to prevent race conditions
        lua_script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        
        -- Retrieve current state or initialize
        local data = redis.call('HMGET', key, 'tokens', 'last_updated')
        local tokens = tonumber(data[1])
        local last_updated = tonumber(data[2])
        
        if not tokens then
            tokens = capacity
            last_updated = now
        else
            -- Calculate elapsed time and add tokens matching the bucket configuration
            local elapsed = now - last_updated
            tokens = math.min(capacity, tokens + (elapsed * refill_rate))
        end
        
        -- Check if a token is available
        if tokens >= 1 then
            tokens = tokens - 1
            redis.call('HMSET', key, 'tokens', tokens, 'last_updated', now)
            redis.call('EXPIRE', key, 60) -- Automatically clear idle keys
            return 1
        else
            redis.call('HMSET', key, 'tokens', tokens, 'last_updated', now)
            return 0
        end
        """
        
        try:
            # Execute atomically inside the Redis cluster environment
            allowed = self.redis.eval(lua_script, 1, f"rate_limit:{client_id}", capacity, rate, current_time)
            is_allowed = bool(allowed)
        except redis.RedisError:
            # Graceful degradation fallback to allowing the request if Redis is down
            is_allowed = True

        # Update local fast-path tracking cache
        self.local_cache[client_id] = (current_time, is_allowed)
        return is_allowed
