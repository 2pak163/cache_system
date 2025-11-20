from collections import deque
from typing import Any, Optional
from datetime import datetime

from .base import CachePolicy, CacheEntry

class FIFOCache(CachePolicy):
    def __init__(self,capacity: int, name: str="FIFO"):
        super().__init__(capacity, name)
        self._insertion_queue = deque()
    
    def _evict(self) -> None:
        if not self._insertion_queue:
            return
        oldest_key = self._insertion_queue.popleft()
        if oldest_key in self._cache:
            del self._cache[oldest_key]
        self._stats.evictions += 1
        self._stats.current_size = self.current_size
    
    def _on_access(self, key: Any, entry: CacheEntry) -> None:
        pass
    
    def _on_insert(self, key: Any, entry: CacheEntry) -> None:
        self._insertion_queue.append(key)
    
    def _on_update(self, key: Any, entry: CacheEntry) -> None:
        pass

    def _on_delete(self, key: Any) -> None:
        try:
            self._insertion_queue.remove(key)
        except ValueError:
            pass
    
    def _on_clear(self) -> None:
        self._insertion_queue.clear()
    
    def get_insertion_order(self) -> list:
        return list(self._insertion_queue)
    
    def peek_next_eviction(self)-> Optional[Any]:
        if self._insertion_queue:
            return self._insertion_queue[0]
        return None
    
    def __repr__(self) -> str:
        """
        Representación en string mejorada para debugging.
        
        Muestra el orden de la cola además de la información básica.
        """
        queue_str = " -> ".join(str(k) for k in list(self._insertion_queue)[:5])
        if len(self._insertion_queue) > 5:
            queue_str += " -> ..."
        
        return (f"FIFOCache(name='{self._name}', capacity={self._capacity}, "
                f"size={self.current_size}, hit_rate={self._stats.hit_rate:.2%}, "
                f"queue=[{queue_str}])")
    
if __name__ == "__main__":
    # Crear un caché FIFO con capacidad de 3 elementos
    print("=== Demostración de FIFO Cache ===\n")
    
    cache = FIFOCache(capacity=3)
    
    # Insertar elementos
    print("1. Insertando elementos a, b, c:")
    cache.put('a', 100)
    cache.put('b', 200)
    cache.put('c', 300)
    print(f"   Orden de inserción: {cache.get_insertion_order()}")
    print(f"   Estado: {cache}\n")
    
    # Acceder a un elemento no cambia el orden
    print("2. Accediendo a 'a' (el más antiguo):")
    value = cache.get('a')
    print(f"   Valor recuperado: {value}")
    print(f"   Orden de inserción: {cache.get_insertion_order()}")
    print(f"   Nota: 'a' sigue siendo el primero para desalojo\n")
    
    # Insertar un cuarto elemento causa desalojo
    print("3. Insertando 'd' (caché lleno, debe desalojar 'a'):")
    cache.put('d', 400)
    print(f"   Orden de inserción: {cache.get_insertion_order()}")
    print(f"   Próximo a desalojar: {cache.peek_next_eviction()}")
    print(f"   Estado: {cache}\n")
    
    # Verificar que 'a' fue desalojado
    print("4. Intentando acceder a 'a' (debería estar desalojado):")
    value = cache.get('a')
    print(f"   Valor: {value}")
    print(f"   Estadísticas: {cache.stats.to_dict()}\n")
    
    # Demostrar que actualizar no cambia posición
    print("5. Actualizando 'b' con nuevo valor:")
    cache.put('b', 999)  # Actualizar, no insertar
    print(f"   Orden de inserción: {cache.get_insertion_order()}")
    print(f"   Nota: 'b' mantiene su posición\n")
    
    print("=== Demostración completada ===")
    print(f"\nEstadísticas finales:")
    for key, value in cache.stats.to_dict().items():
        print(f"  {key}: {value}")