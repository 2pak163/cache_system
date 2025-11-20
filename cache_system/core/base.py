from abc import ABC, abstractmethod
from typing import Any,Optional,Dict,List,Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CacheEntry:
    key: Any
    value: Any
    timestamp: datetime
    access_count: int = 0
    size: int = 1

    def __post_init__(self):
        if self.access_count == 0:
            self.access_count = 1

@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    current_size: int = 0
    max_size: int = 0

    @property
    def hit_rate(self) -> float:
        total_accesses= self.hits + self.misses
        if total_accesses == 0:
            return 0.0
        return self.hits / total_accesses
    
    @property
    def miss_rate(self) -> float:
        return 1.0 - self.hit_rate
    
    @property
    def utilization(self) -> float:
        if self.max_size == 0:
            return 0.0
        return self.current_size / self.max_size
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "current_size": self.current_size,
            "max_size": self.max_size,
            "hit_rate": self.hit_rate,
            "miss_rate": self.miss_rate,
            "utilization": self.utilization,
        }

class CachePolicy(ABC):

    def __init__(self,capacity: int, name: str ="Cache" ):

        if capacity <= 0:
            raise ValueError("La capacidad de la caché debe ser un número positivo.")

        self._capacity = capacity
        self._name = name
        self._cache: Dict[Any, CacheEntry] = {}
        self._stats = CacheStats(max_size=capacity)

    @property
    def capacity(self) -> int:
        return self._capacity
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def stats(self) -> CacheStats:
        return self._stats
    
    @property
    def current_size(self) -> int:
        return len(self._cache)
    
    @property
    def is_full(self) -> bool:
        return self.current_size >= self._capacity
    
    @property
    def is_empty(self) -> bool:
        return self.current_size == 0
    
    def get(self,key: Any) -> Optional[Any]:
        if key in self._cache:
            self._stats.hits += 1
            entry = self._cache[key]
            self._on_access(key,entry)
            return entry.value
        else:
            self._stats.misses += 1
            return None
    
    def put(self,key: Any, value: Any, size: int = 1)-> None:
        if key in self._cache:
            self._update_entry(key, value, size)
        else:
            if self.is_full:
                self._evict()
            self._insert_entry(key, value, size)
    
    def delete(self,key: Any) -> bool:
        if key in self._cache:
            self._on_delete(key)
            del self._cache[key]
            self._stats.current_size = self.current_size
            return True
        return False
    
    def clear(self) -> None:
        self._cache.clear()
        self._on_clear()
        self._stats.current_size = 0

    def contains(self, key: Any) -> bool:
        return key in self._cache
    
    def keys(self) -> List[Any]:
        return list(self._cache.keys())
    
    def items(self) -> List[Tuple[Any, Any]]:
        return [(key, entry.value) for key, entry in self._cache.items()]
    
    def reset_stats(self) -> None:
        self._stats = CacheStats(current_size=self.current_size, max_size= self._capacity)

    @abstractmethod
    def _evict(self) -> None:
        pass    

    @abstractmethod
    def _on_access(self, key: Any ,entry: CacheEntry) -> None:
        pass
    
    @abstractmethod
    def _on_insert(self, key: Any, entry: CacheEntry) -> None:
        pass
    
    @abstractmethod
    def _on_update(self, key: Any, entry: CacheEntry) -> None:
        pass
    
    @abstractmethod
    def _on_delete(self, key: Any) -> None:
        pass
    
    @abstractmethod
    def _on_clear(self) -> None:
        pass

    def _insert_entry(self, key: Any, value: Any, size: int) -> None:
        entry = CacheEntry(key=key, value=value, timestamp=datetime.now(), size=size)
        self._cache[key]= entry
        self._stats.current_size = self.current_size
        self._on_insert(key, entry)
    
    def _update_entry(self, key: Any, value: Any, size: int) -> None:
        entry = self._cache[key]
        entry.value = value
        entry.size = size
        self._on_update(key, entry)
    
    def __repr__(self) -> str:
        """Representación en string del caché para debugging."""
        return (f"{self.__class__.__name__}(name='{self._name}', "
                f"capacity={self._capacity}, size={self.current_size}, "
                f"hit_rate={self._stats.hit_rate:.2%})")
    
    def __len__(self) -> int:
        return self.current_size
    
    def __contains__(self, key: Any) -> bool:
        return self.contains(key)