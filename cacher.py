# cacher.py module
# coding: utf-8
from collections import OrderedDict, Counter
import hashlib
import time
import json
import asyncio
from typing import Any, Callable, Dict, Generic, Optional, TypeVar

K = TypeVar("K")  # Key type
V = TypeVar("V")  # Value type

class CacheBackend(Generic[K, V]):
    """Backend that manages the cache data storage using an OrderedDict."""

    def __init__(self, capacity: int, eviction_policy: str = "lru"):
        self.cache = OrderedDict()
        self.usage = Counter() if eviction_policy == "lfu" else None
        self.capacity = capacity
        self.eviction_policy = eviction_policy

    def get(self, key: K) -> Optional[V]:
        if self.eviction_policy == "lfu" and key in self.cache:
            self.usage[key] += 1
        return self.cache.get(key)

    def put(self, key: K, value: V) -> None:
        self.cache[key] = value
        if self.eviction_policy == "lfu":
            self.usage[key] += 1
        if len(self.cache) > self.capacity:
            if self.eviction_policy == "lfu":
                least_used = self.usage.most_common()[:-2:-1][0][0]
                del self.cache[least_used]
                del self.usage[least_used]
            else:  # Default is LRU
                self.cache.popitem(last=False)

    def serialize(self) -> str:
        """Serialize the cache (without timestamps) to a JSON string."""
        serialized_data = {key: value[1] for key, value in self.cache.items()}
        return json.dumps(serialized_data)

    @classmethod
    def deserialize(cls, data: str, capacity: int) -> "CacheBackend":
        """Deserialize a JSON string to create a CacheBackend instance and add current timestamps."""
        cache_data = json.loads(data)
        current_timestamp = time.time()
        cache_with_timestamps = {key: (current_timestamp, value) for key, value in cache_data.items()}
        instance = cls(capacity=capacity)
        instance.cache = cache_with_timestamps
        return instance

class Cache(Generic[K, V]):
    """Interface for caching mechanism with TTL and stats."""

    def __init__(self, backend: CacheBackend[K, V], ttl: Optional[int] = 300):
        self.backend = backend
        self.ttl = ttl
        self.hits = 0
        self.misses = 0
        self.lock = asyncio.Lock()
        self.cleanup_interval = ttl // 2 or 300  # clean up half of the TTL or every 5 mins
        self.cleanup_task = asyncio.create_task(self.cleanup_expired_entries())

    async def cleanup_expired_entries(self):
        """Periodically clean up expired cache entries."""
        while True:
            await asyncio.sleep(self.cleanup_interval)
            async with self.lock:
                current_time = time.time()
                expired_keys = [
                    key for key, (timestamp, _) in self.backend.cache.items()
                    if self.ttl and current_time - timestamp > self.ttl
                ]
                for key in expired_keys:
                    del self.backend.cache[key]

    async def get(self, key: K) -> Optional[V]:
        async with self.lock:
            entry = self.backend.get(key)
            if entry:
                timestamp, value = entry
                if self.ttl and time.time() - timestamp > self.ttl:
                    del self.backend.cache[key]
                    return None
                self.hits += 1
                return value
            else:
                self.misses += 1
                return None

    async def put(self, key: K, value: V) -> None:
        async with self.lock:
            self.backend.put(key, (time.time(), value))

    async def stats(self) -> Dict[str, Any]:
        async with self.lock:
            oldest_entry = (
                next(iter(self.backend.cache.values())) if self.backend.cache else None
            )
            return {
                "hits": self.hits,
                "misses": self.misses,
                "size": len(self.backend.cache),
                "oldest_entry_timestamp": oldest_entry[0] if oldest_entry else None,
            }

    def async_memoize(self, func: Callable) -> Callable:
        """Async memoization function to cache the results of async function calls."""

        async def async_wrapper(*args, **kwargs):
            key = hashlib.sha256(str(args).encode() + str(kwargs).encode()).hexdigest()  # Using SHA256 instead of MD5
            result = await self.get(key)
            if not result:
                result = await func(*args, **kwargs)
                await self.put(key, result)
            return result

        return async_wrapper

if __name__ == "__main__":
    # Sample usage to demonstrate the new structure.
    backend = CacheBackend(capacity=3)
    cache = Cache(backend=backend, ttl=300)
    # Further usage logic here
