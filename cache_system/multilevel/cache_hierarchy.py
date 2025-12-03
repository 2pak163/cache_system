from typing import Any, Optional, List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..core.base import CachePolicy, CacheStats

@dataclass
class LevelStats:
    name:str
    hits: int = 0
    misses: int = 0
    promotions: int = 0
    demotions: int = 0
    total_latency_ms: float = 0.0

    @property
    def hit_rate(self) -> float:
        total=self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def avg_latency_ms(self) -> float:
        total_accesses = self.hits + self.misses
        return self.total_latency_ms / total_accesses if total_accesses > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return{
            "name": self.name,
            "hits": self.hits,
            "misses": self.misses,
            "promotions": self.promotions,
            "demotions": self.demotions,
            "hit_rate": self.hit_rate,
            "total_latency_ms": self.total_latency_ms,
            "avg_latency_ms": self.avg_latency_ms,
        }

@dataclass
class CacheLevel:
    cache: CachePolicy
    name: str
    latency_ms: float
    stats: LevelStats

    def __repr__(self) -> str:
        return (f"CacheLevel(name='{self.name}', "
                f"policy={self.cache.__class__.__name__}, "
                f"capacity={self.cache.capacity}, "
                f"size={self.cache.current_size}, "
                f"latency={self.latency_ms}ms)")
    
class CacheHierarchy:
    def __init__(self, name: str = "MultilevelCache"):
        self._name = name
        self._levels: List[CacheLevel] = []

        self._total_hits = 0
        self._total_misses = 0
        self._total_promotions = 0
        self._total_latency_ms = 0.0

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def num_levels(self) -> int:
        return len(self._levels)
    
    @property
    def total_capacity(self) -> int:
        return sum(level.cache.capacity for level in self._levels)
    
    @property
    def total_size(self) -> int:
        return sum(level.cache.current_size for level in self._levels)
    
    def add_level(self, cache: CachePolicy, name: str, latency_ms: float) -> None:
        if name is None:
            name = f"L{len(self._levels)+1}"

        if any(level.name == name for level in self._levels):
            raise ValueError(f"Ya exists un nivel de caché con el nombre '{name}'")
    
        level = CacheLevel(
            cache=cache,
            name=name,
            latency_ms=latency_ms,
            stats=LevelStats(name=name)
        )
        self._levels.append(level)

    def get(self, key: Any) -> Optional[Any]:
        cumulative_latency = 0.0
        for level_index, level in enumerate(self._levels):
            cumulative_latency += level.latency_ms
            level.stats.total_latency_ms += level.latency_ms

            value= level.cache.get(key)

            if value is not None:
                level.stats.hits += 1
                self._total_hits += 1
                self._total_latency_ms += cumulative_latency

                if level_index > 0:
                    self._promote_to_upper_levels(key, value , level_index)
                
                return value
            else:
                level.stats.misses += 1

        self._total_misses += 1
        return None
    
    def put(self, key: Any, value: Any) -> None:
        if not self._levels:
            raise RuntimeError("No hay niveles de caché en la jerarquía.")
        for level in self._levels:
            level.cache.put(key, value)
    
    def delete(self, key: Any) -> bool:
        deleted= False
        for level in self._levels:
            if level.cache.delete(key):
                deleted=True
        return deleted
    
    def contains(self, key: Any) -> bool:
        return any(level.cache.contains(key) for level in self._levels)
    
    def clear(self) -> None:
        for level in self._levels:
            level.cache.clear()
    
    def reset_stats(self) -> None:
        for level in self._levels:
            level.stats = LevelStats(name=level.name)
            level.cache.reset_stats()
        
        self._total_hits = 0
        self._total_misses = 0
        self._total_promotions = 0
        self._total_latency_ms = 0.0

    def _promote_to_upper_levels(self, key: Any, value: Any, from_level_index: int) -> None:
        for upper_level_index in range(from_level_index):
            upper_level = self._levels[upper_level_index]
            upper_level.cache.put(key, value)
            upper_level.stats.promotions += 1
            self._total_promotions += 1
    
    def get_level(self, name: str) -> Optional[CacheLevel]:
        for level in self._levels:
            if level.name == name:
                return level
        return None
    
    def get_level_stats(self, name: str)-> Optional[LevelStats]:
        level = self.get_level(name)
        return level.stats if level else None
    
    def get_all_stats(self) -> Dict[str, Any]:
        total_accesses = self._total_hits + self._total_misses

        return{
            'global': {
                'total_hits': self._total_hits,
                'total_misses': self._total_misses,
                'total_accesses': total_accesses,
                'global_hit_rate': self._total_hits / total_accesses if total_accesses > 0 else 0.0,
                'total_promotions': self._total_promotions,
                'total_latency_ms': self._total_latency_ms,
                'avg_latency_ms': self._total_latency_ms / total_accesses if total_accesses > 0 else 0.0,
                'num_levels': self.num_levels,
                'total_capacity': self.total_capacity,
                'total_size': self.total_size
            },
            'levels':[level.stats.to_dict() for level in self._levels]
        }
    
    def get_level_details(self)-> List[Dict[str, Any]]:
        details = []
        for level in self._levels:
            details.append({
                'name': level.name,
                'policy': level.cache.__class__.__name__,
                'capacity': level.cache.capacity,
                'current_size': level.cache.current_size,
                'utilization': level.cache.stats.utilization,
                'latency_ms': level.latency_ms,
                'cache_stats': level.cache.stats.to_dict(),
                'level_stats': level.stats.to_dict()
            })
        return details
    
    def __repr__(self) -> str:
        """Representación en string del sistema multinivel."""
        levels_str = " -> ".join([
            f"{level.name}({level.cache.__class__.__name__}/{level.cache.capacity})"
            for level in self._levels
        ])
        
        total_accesses = self._total_hits + self._total_misses
        hit_rate = self._total_hits / total_accesses if total_accesses > 0 else 0.0
        
        return (f"CacheHierarchy(name='{self._name}', "
                f"levels=[{levels_str}], "
                f"hit_rate={hit_rate:.2%}, "
                f"size={self.total_size}/{self.total_capacity})")
    
    def __len__(self) -> int:
        return self.num_levels

if __name__ == "__main__":
    from ..core.lru import LRUCache
    from ..core.lfu import LFUCache
    from ..core.fifo import FIFOCache
    
    print("=== Demostración de Sistema de Caché Multinivel ===\n")
    
    # Crear jerarquía de 3 niveles
    hierarchy = CacheHierarchy(name="MemoryHierarchy")
    
    # L1: Pequeño y rápido (LRU)
    hierarchy.add_level(LRUCache(capacity=3), name="L1", latency_ms=1)
    
    # L2: Mediano (LRU)
    hierarchy.add_level(LRUCache(capacity=10), name="L2", latency_ms=5)
    
    # L3: Grande (LFU - protege elementos populares)
    hierarchy.add_level(LFUCache(capacity=50), name="L3", latency_ms=20)
    
    print(f"Sistema creado: {hierarchy}\n")
    
    # Insertar datos
    print("1. Insertando datos en la jerarquía:")
    for i in range(15):
        hierarchy.put(f'key{i}', f'value{i}')
    print(f"   Insertados 15 elementos")
    print(f"   Estado: {hierarchy}\n")
    
    # Acceder a algunos elementos (simular patrón de uso)
    print("2. Patrón de acceso:")
    # Acceso frecuente a key0 (será promovido)
    for _ in range(5):
        hierarchy.get('key0')
    print(f"   'key0' accedido 5 veces")
    
    # Acceso ocasional a key5
    hierarchy.get('key5')
    hierarchy.get('key5')
    print(f"   'key5' accedido 2 veces")
    
    # Acceso único a key10
    hierarchy.get('key10')
    print(f"   'key10' accedido 1 vez\n")
    
    # Mostrar estadísticas
    print("3. Estadísticas del sistema:")
    stats = hierarchy.get_all_stats()
    
    print(f"\n   Estadísticas globales:")
    for key, value in stats['global'].items():
        if isinstance(value, float):
            print(f"     {key}: {value:.2f}")
        else:
            print(f"     {key}: {value}")
    
    print(f"\n   Estadísticas por nivel:")
    for level_stats in stats['levels']:
        print(f"\n     {level_stats['name']}:")
        print(f"       Hits: {level_stats['hits']}")
        print(f"       Misses: {level_stats['misses']}")
        print(f"       Hit rate: {level_stats['hit_rate']:.2%}")
        print(f"       Promotions: {level_stats['promotions']}")
    
    print("\n=== Demostración completada ===") 