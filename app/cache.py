"""In-memory TTL cache behind a tiny interface; swap for Redis without touching callers."""
import hashlib, json, threading, time
from typing import Any, Optional


class TTLCache:
    def __init__(self, ttl: int = 3600, max_items: int = 1000):
        self.ttl, self.max_items = ttl, max_items
        self._data: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def make_key(
        symptoms: list[str],
        age: int,
        sex: str,
        duration: Optional[int],
        temperature: Optional[float] = None,
        temperature_unit: str = "C",
    ) -> str:
        # Temperature and unit are included so different readings cannot share a result.
        payload = json.dumps(
            [sorted(symptoms), age // 10, sex, duration, temperature, temperature_unit],
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(self, key: str):
        with self._lock:
            hit = self._data.get(key)
            if not hit:
                return None
            if hit[0] < time.time():
                del self._data[key]
                return None
            return hit[1]

    def set(self, key: str, value: Any):
        with self._lock:
            if len(self._data) >= self.max_items:  # evict oldest-expiring
                self._data.pop(min(self._data, key=lambda k: self._data[k][0]))
            self._data[key] = (time.time() + self.ttl, value)
