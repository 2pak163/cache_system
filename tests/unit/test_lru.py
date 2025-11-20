import pytest
from cache_system.core.lru import LRUCache


class TestLRUPolicy:
    """
    Tests específicos de la política Least Recently Used.
    
    LRU mantiene los elementos ordenados por recencia de acceso y desaloja
    el que no ha sido accedido durante más tiempo. Estos tests verifican
    que el reordenamiento funciona correctamente con cada acceso.
    """
    
    @pytest.fixture
    def lru_cache(self):
        """Crea un caché LRU fresco para cada test."""
        return LRUCache(capacity=3)
    
    def test_evicts_least_recently_used(self, lru_cache):
        """
        Verifica que LRU desaloja el elemento menos recientemente usado.
        
        Este es el test fundamental de LRU: cuando el caché está lleno,
        debe desalojar el elemento que fue accedido hace más tiempo.
        """
        lru_cache.put('a', 1)
        lru_cache.put('b', 2)
        lru_cache.put('c', 3)
        
        # Orden inicial: c (MRU), b, a (LRU)
        # El más reciente es 'c' porque fue insertado último
        orden = lru_cache.get_access_order()
        assert orden == ['c', 'b', 'a'], \
            "El orden debe ser del más reciente al menos reciente"
        
        # 'a' es el menos recientemente usado
        assert lru_cache.peek_lru() == 'a'
        assert lru_cache.peek_mru() == 'c'
        
        # Insertar 'd' debe desalojar 'a'
        lru_cache.put('d', 4)
        
        assert not lru_cache.contains('a'), \
            "El elemento LRU debe ser desalojado"
        assert lru_cache.contains('b')
        assert lru_cache.contains('c')
        assert lru_cache.contains('d')
    
    def test_access_moves_to_front(self, lru_cache):
        """
        Verifica que acceder a un elemento lo mueve a la posición MRU.
        
        Esta es la característica fundamental de LRU: cada acceso actualiza
        la posición del elemento, moviéndolo al frente de la lista de uso.
        """
        lru_cache.put('a', 1)
        lru_cache.put('b', 2)
        lru_cache.put('c', 3)
        
        # Orden inicial: c, b, a
        assert lru_cache.get_access_order() == ['c', 'b', 'a']
        
        # Acceder a 'a' (el LRU) debe moverlo al frente
        lru_cache.get('a')
        assert lru_cache.get_access_order() == ['a', 'c', 'b'], \
            "Acceder a 'a' debe moverlo a la posición MRU"
        assert lru_cache.peek_mru() == 'a', \
            "'a' debe ser ahora el más recientemente usado"
        assert lru_cache.peek_lru() == 'b', \
            "'b' debe ser ahora el menos recientemente usado"
        
        # Acceder a 'c' debe moverlo al frente
        lru_cache.get('c')
        assert lru_cache.get_access_order() == ['c', 'a', 'b'], \
            "Acceder a 'c' debe moverlo a la posición MRU"
        assert lru_cache.peek_lru() == 'b', \
            "'b' sigue siendo LRU porque no lo hemos accedido"
    
    def test_protects_frequently_accessed_elements(self, lru_cache):
        """
        Verifica que elementos accedidos frecuentemente están protegidos.
        
        Un elemento que se accede constantemente no debe ser desalojado,
        incluso si fue insertado hace tiempo. Esta es la ventaja de LRU
        sobre FIFO: reconoce y protege elementos populares.
        """
        lru_cache.put('a', 1)
        lru_cache.put('b', 2)
        lru_cache.put('c', 3)
        
        # Acceder repetidamente a 'a'
        for _ in range(5):
            lru_cache.get('a')
        
        # 'a' es ahora MRU, 'b' es LRU
        assert lru_cache.peek_mru() == 'a'
        assert lru_cache.peek_lru() == 'b'
        
        # Insertar 'd' desaloja 'b', NO 'a'
        lru_cache.put('d', 4)
        assert lru_cache.contains('a'), \
            "'a' debe sobrevivir porque fue accedido recientemente"
        assert not lru_cache.contains('b'), \
            "'b' debe ser desalojado porque es el LRU"
        
        # Seguir accediendo a 'a'
        lru_cache.get('a')
        
        # Insertar 'e' desaloja 'c', NO 'a'
        lru_cache.put('e', 5)
        assert lru_cache.contains('a'), \
            "'a' sigue protegido por accesos recientes"
        assert not lru_cache.contains('c'), \
            "'c' debe ser desalojado"
    
    def test_update_moves_to_front(self, lru_cache):
        """
        Verifica que actualizar un elemento lo mueve a la posición MRU.
        
        En LRU, actualizar el valor de una clave se considera un acceso,
        por lo que debe mover el elemento al frente.
        """
        lru_cache.put('a', 1)
        lru_cache.put('b', 2)
        lru_cache.put('c', 3)
        
        # 'a' es LRU en este momento
        assert lru_cache.peek_lru() == 'a'
        
        # Actualizar 'a' debe moverlo a MRU
        lru_cache.put('a', 999)
        
        assert lru_cache.peek_mru() == 'a', \
            "Actualizar debe mover a la posición MRU"
        assert lru_cache.get('a') == 999, \
            "El valor debe actualizarse"
        assert lru_cache.peek_lru() == 'b', \
            "'b' debe ser ahora el LRU"
    
    def test_sequential_accesses_update_order(self, lru_cache):
        """
        Verifica que una secuencia de accesos actualiza el orden correctamente.
        
        Este test simula un patrón más complejo de accesos para verificar
        que el reordenamiento funciona correctamente en escenarios realistas.
        """
        lru_cache.put('a', 1)
        lru_cache.put('b', 2)
        lru_cache.put('c', 3)
        
        # Orden inicial: c, b, a
        assert lru_cache.get_access_order() == ['c', 'b', 'a']
        
        # Secuencia de accesos: a, b, a, c
        lru_cache.get('a')  # Orden: a, c, b
        assert lru_cache.get_access_order() == ['a', 'c', 'b']
        
        lru_cache.get('b')  # Orden: b, a, c
        assert lru_cache.get_access_order() == ['b', 'a', 'c']
        
        lru_cache.get('a')  # Orden: a, b, c
        assert lru_cache.get_access_order() == ['a', 'b', 'c']
        
        lru_cache.get('c')  # Orden: c, a, b
        assert lru_cache.get_access_order() == ['c', 'a', 'b']
        
        # 'b' es ahora el LRU
        assert lru_cache.peek_lru() == 'b'
    
    def test_peek_methods_do_not_modify_state(self, lru_cache):
        """
        Verifica que peek_mru y peek_lru no modifican el orden.
        
        Estos métodos son para inspección y no deben tener efectos secundarios.
        """
        lru_cache.put('a', 1)
        lru_cache.put('b', 2)
        lru_cache.put('c', 3)
        
        # Obtener el orden inicial
        orden_inicial = lru_cache.get_access_order()
        
        # Llamar a peek múltiples veces
        for _ in range(5):
            lru_cache.peek_mru()
            lru_cache.peek_lru()
        
        # El orden no debe haber cambiado
        assert lru_cache.get_access_order() == orden_inicial, \
            "peek no debe modificar el orden de acceso"
    
    def test_delete_removes_from_access_order(self, lru_cache):
        """
        Verifica que delete elimina el elemento del orden de acceso.
        
        Cuando eliminamos un elemento, debe ser removido de la estructura
        que mantiene el orden LRU, no solo del almacenamiento principal.
        """
        lru_cache.put('a', 1)
        lru_cache.put('b', 2)
        lru_cache.put('c', 3)
        
        # Eliminar 'b' (el del medio)
        lru_cache.delete('b')
        
        # El orden debe actualizarse
        assert lru_cache.get_access_order() == ['c', 'a'], \
            "'b' debe haber sido eliminado del orden de acceso"
        
        # Si eliminamos el LRU actual
        lru_cache.delete('a')
        assert lru_cache.get_access_order() == ['c']
        assert lru_cache.peek_lru() == 'c'
        assert lru_cache.peek_mru() == 'c'
    
    def test_clear_resets_access_order(self, lru_cache):
        """
        Verifica que clear limpia completamente la estructura de orden LRU.
        """
        lru_cache.put('a', 1)
        lru_cache.put('b', 2)
        lru_cache.get('a')  # Mover 'a' al frente
        
        lru_cache.clear()
        
        # El orden debe estar vacío
        assert lru_cache.get_access_order() == []
        assert lru_cache.peek_lru() is None
        assert lru_cache.peek_mru() is None
        
        # Debe funcionar normalmente después de clear
        lru_cache.put('x', 10)
        assert lru_cache.get_access_order() == ['x']
    
    def test_lru_with_realistic_workload(self, lru_cache):
        """
        Verifica LRU con un patrón de acceso realista.
        
        Este test simula un escenario más cercano al uso real: algunos
        elementos se acceden frecuentemente (populares) y otros raramente.
        """
        # Insertar documentos
        lru_cache.put('config', 'datos_config')      # Archivo popular
        lru_cache.put('temp1', 'datos_temporales')   # Archivo temporal
        lru_cache.put('temp2', 'más_temporales')     # Otro temporal
        
        # Patrón de acceso: config se usa constantemente
        for _ in range(10):
            lru_cache.get('config')
            # Ocasionalmente accedemos a temp1
            if _ % 3 == 0:
                lru_cache.get('temp1')
        
        # Asegurar que config es el MRU con un acceso final
        lru_cache.get('config')
        
        # 'temp2' nunca fue accedido después de inserción, es el LRU
        assert lru_cache.peek_lru() == 'temp2'
        assert lru_cache.peek_mru() == 'config'
        
        # Insertar nuevo archivo desaloja temp2
        lru_cache.put('temp3', 'nuevos_temporales')
        assert not lru_cache.contains('temp2'), \
            "'temp2' debe ser desalojado (nunca fue accedido)"
        assert lru_cache.contains('config'), \
            "'config' debe sobrevivir (muy accedido)"
        assert lru_cache.contains('temp1'), \
            "'temp1' debe sobrevivir (accedido ocasionalmente)"
        
        # temp3 es ahora MRU porque fue recién insertado
        assert lru_cache.peek_mru() == 'temp3', \
            "'temp3' debe ser MRU (recién insertado)"
        
        # Pero 'config' sigue siendo importante, accederlo de nuevo
        lru_cache.get('config')
        
        # Ahora config vuelve a ser MRU
        assert lru_cache.peek_mru() == 'config', \
            "'config' debe ser MRU después de accederlo"


if __name__ == "__main__":
    """Permite ejecutar estos tests directamente con Python."""
    pytest.main([__file__, "-v"])