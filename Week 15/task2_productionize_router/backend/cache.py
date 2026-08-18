"""Small in-memory TTL cache for repeated identical requests. Good enough for
a single-process deployment; a multi-worker/multi-replica deployment would
need a shared store (e.g. Redis) instead -- noted in the README."""
import time
from collections import OrderedDict
from typing import Any, Optional


class TTLCache:
    def __init__(self, max_size: int, ttl_seconds: int):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        timestamp, value = entry
        if time.time() - timestamp > self.ttl_seconds:
            del self._store[key]
            return None
        self._store.move_to_end(key)
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.time(), value)
        self._store.move_to_end(key)
        while len(self._store) > self.max_size:
            self._store.popitem(last=False)
