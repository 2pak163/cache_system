from typing import Any, Optional
from datetime import datetime
from .base import CacheEntry, CachePolicy

class DLinkedNode:
    def __init__ (self, key: Any = None):
        self.key = key
        self.prev: Optional['DLinkedNode'] = None
        self.next: Optional['DLinkedNode'] = None
class LRUCache(CachePolicy):
    def __init__(self, capacity: int, name: str = "LRUCache"):
        super().__init__(capacity,name)
        self._node_map: dict[Any, DLinkedNode]= {}
        self._head= DLinkedNode()
        self._tail= DLinkedNode()
        self._head.next= self._tail
        self._tail.prev= self._head
    
    def _add_to_front(self, node: DLinkedNode) -> None:
        node.next= self._head.next
        node.prev= self._head
        self._head.next.prev= node
        self._head.next= node
    
    def _remove_node(self, node: DLinkedNode) -> None:
        node.prev.next= node.next
        node.next.prev= node.prev
        node.prev= None
        node.next= None
    
    def _move_to_front(self, node: DLinkedNode) -> None:
        self._remove_node(node)
        self._add_to_front(node)
    
    def _evict(self) -> None:
        lru_node= self._tail.prev
        if lru_node == self._head:
            return
        lru_key= lru_node.key
        self._remove_node(lru_node)
        
        if lru_key in self._node_map:
            del self._node_map[lru_key]
        
        if lru_key in self._cache:
            del self._cache[lru_key]

        self._stats.evictions += 1
        self._stats.current_size= self.current_size

    def _on_access(self, key: Any, entry: CacheEntry) -> None:
        entry.timestamp= datetime.now()
        entry.access_count += 1

        if key in self._node_map:
            node= self._node_map[key]
            self._move_to_front(node)
    
    def _on_insert(self, key: Any, entry: CacheEntry) -> None:
        new_node= DLinkedNode(key)
        self._add_to_front(new_node)
        self._node_map[key]= new_node
    
    def _on_update(self, key: Any, entry: CacheEntry) -> None:
        self._on_access(key, entry)
        
    def _on_delete(self, key: Any) -> None:
        if key in self._node_map:
            node= self._node_map[key]
            self._remove_node(node)
            del self._node_map[key]
    
    def _on_clear(self) -> None:
        self._node_map.clear()
        self._head.next= self._tail
        self._tail.prev= self._head
    
    def get_access_order(self)-> list:
        order = []
        current = self._head.next

        while current != self._tail:
            order.append(current.key)
            current = current.next
        return order
    
    def peek_lru(self) -> Optional[Any]:
        lru_node = self._tail.prev
        if lru_node == self._head:
            return None
        return lru_node.key
    
    def peek_mru(self)-> Optional[Any]:
        mru_node= self._head.next
        if mru_node == self._tail:
            return None
        return mru_node.key
    
    def __repr__(self) -> str:
        """
        Representación en string mejorada para debugging.
        
        Muestra el orden de acceso además de la información básica.
        """
        order = self.get_access_order()
        order_str = " -> ".join(str(k) for k in order[:5])
        if len(order) > 5:
            order_str += " -> ..."
        
        return (f"LRUCache(name='{self._name}', capacity={self._capacity}, "
                f"size={self.current_size}, hit_rate={self._stats.hit_rate:.2%}, "
                f"order=[{order_str}] (MRU->LRU))")

if __name__ == "__main__":
    print("=== Demostración de LRU Cache ===\n")
    
    cache = LRUCache(capacity=3)
    
    # Insertar elementos
    print("1. Insertando elementos a, b, c:")
    cache.put('a', 100)
    cache.put('b', 200)
    cache.put('c', 300)
    print(f"   Orden de acceso (MRU->LRU): {cache.get_access_order()}")
    print(f"   MRU: {cache.peek_mru()}, LRU: {cache.peek_lru()}")
    print(f"   Estado: {cache}\n")
    
    # Acceder a 'a' lo mueve al frente
    print("2. Accediendo a 'a' (estaba en posición LRU):")
    value = cache.get('a')
    print(f"   Valor recuperado: {value}")
    print(f"   Orden de acceso: {cache.get_access_order()}")
    print(f"   MRU: {cache.peek_mru()}, LRU: {cache.peek_lru()}")
    print(f"   Nota: 'a' ahora es MRU, 'b' es LRU\n")
    
    # Insertar un cuarto elemento desaloja el LRU
    print("3. Insertando 'd' (caché lleno, debe desalojar LRU='b'):")
    cache.put('d', 400)
    print(f"   Orden de acceso: {cache.get_access_order()}")
    print(f"   MRU: {cache.peek_mru()}, LRU: {cache.peek_lru()}")
    print(f"   Estado: {cache}\n")
    
    # Verificar que 'b' fue desalojado
    print("4. Intentando acceder a 'b' (debería estar desalojado):")
    value = cache.get('b')
    print(f"   Valor: {value}\n")
    
    # Demostrar la diferencia con FIFO
    print("5. Accediendo repetidamente a 'c' y luego insertando 'e':")
    cache.get('c')
    cache.get('c')
    cache.get('c')
    print(f"   Después de acceder 3 veces a 'c': {cache.get_access_order()}")
    cache.put('e', 500)
    print(f"   Después de insertar 'e': {cache.get_access_order()}")
    print(f"   Nota: 'a' fue desalojado (era LRU), 'c' se salvó por los accesos\n")
    
    # Actualizar un elemento también lo mueve al frente
    print("6. Actualizando 'd' con nuevo valor:")
    cache.put('d', 999)
    print(f"   Orden de acceso: {cache.get_access_order()}")
    print(f"   Nota: 'd' ahora es MRU debido a la actualización\n")
    
    print("=== Demostración completada ===")
    print(f"\nEstadísticas finales:")
    for key, value in cache.stats.to_dict().items():
        print(f"  {key}: {value}")