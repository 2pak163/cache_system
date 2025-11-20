from typing import Any, Optional, Dict 
from datetime import datetime
from collections import defaultdict, OrderedDict

from .base import CacheEntry, CachePolicy

class LFUCache(CachePolicy):
    def __init__(self,capacity: int, name: str = "LFUCache"):
        super().__init__(capacity,name)
        self._freq_map: Dict[int, OrderedDict] = defaultdict(OrderedDict)
        self._freq_key: Dict[Any, int] = {}
        self._min_freq: int = 0
    
    def _increment_frequency(self, key : Any) -> None:
        current_freq = self._freq_key[key]
        del self._freq_map[current_freq][key]
        if not self._freq_map[current_freq]:
            del self._freq_map[current_freq]
            if current_freq == self._min_freq:
                self._min_freq = current_freq + 1
        
        new_freq = current_freq + 1
        self._freq_map[new_freq][key]= None
        self._freq_key[key] = new_freq

    def _evict(self) -> None:
        if self._min_freq == 0 or not self._freq_map[self._min_freq]:
            return
        
        min_freq_keys = self._freq_map[self._min_freq]
        lfu_key, _ = min_freq_keys.popitem(last=False)
        if not min_freq_keys:
            del self._freq_map[self._min_freq]
        if lfu_key in self._freq_key:
            del self._freq_key[lfu_key]
        if lfu_key in self._cache:
            del self._cache[lfu_key]
        
        self._stats.evictions += 1
        self._stats.current_size = self.current_size

    def _on_access(self, key : Any, entry: CacheEntry) -> None:
        entry.timestamp = datetime.now()
        entry.access_count += 1
        self._increment_frequency(key)

    def _on_insert(self, key: Any, entry: CacheEntry) -> None:
        freq = 1
        self._freq_map[freq][key]= None
        self._freq_key[key]= freq
        self._min_freq = 1

    def _on_update(self, key: Any, entry: CacheEntry) -> None:
        self._on_access(key, entry)

    def _on_delete(self, key: Any) -> None:
        
        if key not in self._freq_key:
            return
        freq = self._freq_key[key]

        if freq in self._freq_map and key in self._freq_map[freq]:
            del self._freq_map[freq][key]

            if not self._freq_map[freq]:
                del self._freq_map[freq]

                if freq == self._min_freq:
                    self._min_freq = min(self._freq_map.keys()) if self._freq_map else 0
        
        del self._freq_key[key]
    
    def _on_clear(self) -> None:
        self._freq_map.clear()
        self._freq_key.clear()
        self._min_freq = 0
    
    def get_frequency_distribution(self) -> Dict[int, int]:
        return {freq : len(keys) for freq, keys in self._freq_map.items()}
    
    def get_elements_by_frequency(self) -> Dict[int, list]:
        return {freq: list(keys.keys()) for freq, keys in self._freq_map.items()}
    
    def peek_lfu(self) -> Optional[Any]:
        if self._min_freq == 0 or not self._freq_map[self._min_freq]:
            return None
        
        min_freq_keys = self._freq_map[self._min_freq]
        
        return next(iter(min_freq_keys))
    
    def get_key_frequency(self, key: Any) -> Optional[int]:
        return self._freq_key.get(key)
    
    def __repr__(self) -> str:
        """
        Representación en string mejorada para debugging.
        
        Muestra la distribución de frecuencias además de información básica.
        """
        freq_dist = self.get_frequency_distribution()
        freq_str = ", ".join(f"f{freq}:{count}" for freq, count in sorted(freq_dist.items()))
        
        return (f"LFUCache(name='{self._name}', capacity={self._capacity}, "
                f"size={self.current_size}, hit_rate={self._stats.hit_rate:.2%}, "
                f"min_freq={self._min_freq}, dist=[{freq_str}])")
    

if __name__ == "__main__":
    print("=== Demostración de LFU Cache ===\n")
    
    cache = LFUCache(capacity=3)
    
    # Insertar elementos
    print("1. Insertando elementos a, b, c:")
    cache.put('a', 100)
    cache.put('b', 200)
    cache.put('c', 300)
    print(f"   Frecuencias iniciales: {cache.get_elements_by_frequency()}")
    print(f"   Todos tienen frecuencia 1 (la inserción cuenta como primer acceso)")
    print(f"   LFU actual: {cache.peek_lfu()}")
    print(f"   Estado: {cache}\n")
    
    # Acceder a 'a' múltiples veces
    print("2. Accediendo a 'a' tres veces:")
    cache.get('a')
    cache.get('a')
    cache.get('a')
    print(f"   Frecuencias: {cache.get_elements_by_frequency()}")
    print(f"   'a' ahora tiene frecuencia 4 (1 inicial + 3 accesos)")
    print(f"   LFU actual: {cache.peek_lfu()}")
    print(f"   Estado: {cache}\n")
    
    # Acceder a 'b' una vez
    print("3. Accediendo a 'b' una vez:")
    cache.get('b')
    print(f"   Frecuencias: {cache.get_elements_by_frequency()}")
    print(f"   'b' ahora tiene frecuencia 2")
    print(f"   'c' sigue siendo LFU con frecuencia 1")
    print(f"   LFU actual: {cache.peek_lfu()}\n")
    
    # Insertar elemento nuevo causará desalojo de 'c' (LFU)
    print("4. Insertando 'd' (caché lleno, debe desalojar 'c' que es LFU):")
    cache.put('d', 400)
    print(f"   Frecuencias: {cache.get_elements_by_frequency()}")
    print(f"   'c' fue desalojado (tenía frecuencia 1)")
    print(f"   Estado: {cache}\n")
    
    # Verificar que 'c' fue desalojado
    print("5. Intentando acceder a 'c' (debería estar desalojado):")
    value = cache.get('c')
    print(f"   Valor: {value}\n")
    
    # Insertar otro elemento, ahora 'd' es LFU
    print("6. Insertando 'e' (caché lleno nuevamente):")
    print(f"   Antes de insertar, frecuencias: {cache.get_elements_by_frequency()}")
    print(f"   'b' tiene freq=2, 'd' tiene freq=1")
    print(f"   LFU actual: {cache.peek_lfu()} (será desalojado)")
    cache.put('e', 500)
    print(f"   Después de insertar: {cache.get_elements_by_frequency()}")
    print(f"   'd' fue desalojado (tenía la menor frecuencia)\n")
    
    # Mostrar que elemento muy popular no se desaloja
    print("7. Insertando 'f' (caché lleno nuevamente):")
    print(f"   Frecuencias antes: {cache.get_elements_by_frequency()}")
    print(f"   'a' tiene freq=4, está protegido por su alta frecuencia")
    print(f"   LFU actual: {cache.peek_lfu()}")
    cache.put('f', 600)
    print(f"   Frecuencias después: {cache.get_elements_by_frequency()}")
    print(f"   'e' fue desalojado (tenía la menor frecuencia)\n")
    
    print("=== Demostración completada ===")
    print(f"\nEstadísticas finales:")
    for key, value in cache.stats.to_dict().items():
        print(f"  {key}: {value}")
    
    print(f"\nElementos finales y sus frecuencias:")
    for freq, keys in cache.get_elements_by_frequency().items():
        for key in keys:
            print(f"  {key}: frecuencia={freq}")