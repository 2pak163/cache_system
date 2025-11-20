import pytest
from cache_system.core.fifo import FIFOCache


class TestFIFOPolicy:
    """
    Tests específicos de la política First-In-First-Out.
    
    FIFO es la política más simple: desaloja siempre el elemento que fue
    insertado primero, sin importar cuántas veces haya sido accedido.
    Estos tests verifican que esta característica funciona correctamente.
    """
    
    @pytest.fixture
    def fifo_cache(self):
        """Crea un caché FIFO fresco para cada test."""
        return FIFOCache(capacity=3)
    
    def test_evicts_oldest_element(self, fifo_cache):
        """
        Verifica que FIFO desaloja el elemento insertado primero.
        
        Este es el test más fundamental para FIFO: cuando el caché está lleno
        y necesita hacer espacio, debe desalojar el elemento que fue insertado
        hace más tiempo, es decir, el primero en entrar.
        """
        # Insertar tres elementos en orden
        fifo_cache.put('primero', 1)
        fifo_cache.put('segundo', 2)
        fifo_cache.put('tercero', 3)
        
        # Verificar el orden de inserción
        orden = fifo_cache.get_insertion_order()
        assert orden == ['primero', 'segundo', 'tercero'], \
            "El orden debe reflejar la secuencia de inserción"
        
        # Insertar un cuarto elemento debe desalojar 'primero'
        fifo_cache.put('cuarto', 4)
        
        assert not fifo_cache.contains('primero'), \
            "El primer elemento insertado debe ser desalojado"
        assert fifo_cache.contains('segundo'), \
            "Los elementos más nuevos deben permanecer"
        assert fifo_cache.contains('tercero'), \
            "Los elementos más nuevos deben permanecer"
        assert fifo_cache.contains('cuarto'), \
            "El nuevo elemento debe estar presente"
    
    def test_access_does_not_change_eviction_order(self, fifo_cache):
        """
        Verifica que acceder a elementos NO cambia el orden de desalojo.
        
        Esta es la característica distintiva de FIFO: no importa cuántas veces
        accedas a un elemento, su posición en la cola de desalojo permanece
        igual. Esto contrasta con LRU donde cada acceso mueve el elemento
        al frente.
        """
        fifo_cache.put('a', 1)
        fifo_cache.put('b', 2)
        fifo_cache.put('c', 3)
        
        # Acceder repetidamente al elemento más antiguo
        fifo_cache.get('a')
        fifo_cache.get('a')
        fifo_cache.get('a')
        fifo_cache.get('a')
        fifo_cache.get('a')
        
        # El orden NO debe cambiar a pesar de los accesos
        assert fifo_cache.get_insertion_order() == ['a', 'b', 'c'], \
            "Los accesos no deben afectar el orden FIFO"
        
        # 'a' sigue siendo el próximo a desalojar
        assert fifo_cache.peek_next_eviction() == 'a', \
            "'a' debe seguir siendo el próximo a desalojar a pesar de los accesos"
        
        # Insertar nuevo elemento desaloja 'a' a pesar de sus múltiples accesos
        fifo_cache.put('d', 4)
        assert not fifo_cache.contains('a'), \
            "'a' debe ser desalojado porque fue el primero, no importan los accesos"
    
    def test_sequential_evictions_maintain_order(self, fifo_cache):
        """
        Verifica que múltiples desalojos consecutivos mantienen el orden FIFO.
        
        Cuando desalojamos múltiples elementos, cada uno debe ser eliminado
        en el orden correcto de inserción.
        """
        fifo_cache.put('a', 1)
        fifo_cache.put('b', 2)
        fifo_cache.put('c', 3)
        
        # Primer desalojo: debe eliminar 'a'
        fifo_cache.put('d', 4)
        assert not fifo_cache.contains('a')
        assert fifo_cache.get_insertion_order() == ['b', 'c', 'd']
        
        # Segundo desalojo: debe eliminar 'b' (ahora es el más antiguo)
        fifo_cache.put('e', 5)
        assert not fifo_cache.contains('b')
        assert fifo_cache.get_insertion_order() == ['c', 'd', 'e']
        
        # Tercer desalojo: debe eliminar 'c'
        fifo_cache.put('f', 6)
        assert not fifo_cache.contains('c')
        assert fifo_cache.get_insertion_order() == ['d', 'e', 'f']
        
        # Verificar que se registraron tres desalojos
        assert fifo_cache.stats.evictions == 3
    
    def test_peek_next_eviction_is_accurate(self, fifo_cache):
        """
        Verifica que peek_next_eviction muestra el elemento correcto.
        
        Este método debe mostrar qué elemento sería desalojado próximamente
        sin modificar el estado del caché.
        """
        # Caché vacío
        assert fifo_cache.peek_next_eviction() is None, \
            "Debe retornar None cuando el caché está vacío"
        
        # Con un elemento
        fifo_cache.put('a', 1)
        assert fifo_cache.peek_next_eviction() == 'a', \
            "El único elemento debe ser el próximo a desalojar"
        
        # Con dos elementos
        fifo_cache.put('b', 2)
        assert fifo_cache.peek_next_eviction() == 'a', \
            "'a' sigue siendo el más antiguo"
        
        # Con tres elementos (caché lleno)
        fifo_cache.put('c', 3)
        assert fifo_cache.peek_next_eviction() == 'a', \
            "'a' sigue siendo el más antiguo"
        
        # Después de un desalojo
        fifo_cache.put('d', 4)
        assert fifo_cache.peek_next_eviction() == 'b', \
            "Después de desalojar 'a', 'b' debe ser el próximo"
    
    def test_update_does_not_change_position(self, fifo_cache):
        """
        Verifica que actualizar un valor no cambia su posición en la cola.
        
        En FIFO estricto, actualizar el valor de una clave no debe cambiar
        su posición en el orden de desalojo. La clave mantiene su posición
        original basada en cuándo fue insertada la primera vez.
        """
        fifo_cache.put('a', 1)
        fifo_cache.put('b', 2)
        fifo_cache.put('c', 3)
        
        # Actualizar 'a' con un nuevo valor
        fifo_cache.put('a', 999)
        
        # El orden no debe cambiar
        assert fifo_cache.get_insertion_order() == ['a', 'b', 'c'], \
            "Actualizar no debe cambiar la posición en FIFO"
        
        # 'a' sigue siendo el próximo a desalojar
        assert fifo_cache.peek_next_eviction() == 'a'
        
        # Verificar que el valor se actualizó
        assert fifo_cache.get('a') == 999
        
        # Al insertar un nuevo elemento, 'a' debe ser desalojado
        fifo_cache.put('d', 4)
        assert not fifo_cache.contains('a')
    
    def test_delete_removes_from_queue(self, fifo_cache):
        """
        Verifica que delete elimina el elemento de la cola de inserción.
        
        Cuando eliminamos explícitamente un elemento, debe ser removido
        de la cola de inserción, no solo del almacenamiento principal.
        """
        fifo_cache.put('a', 1)
        fifo_cache.put('b', 2)
        fifo_cache.put('c', 3)
        
        # Eliminar el elemento del medio
        fifo_cache.delete('b')
        
        # El orden debe actualizarse
        assert fifo_cache.get_insertion_order() == ['a', 'c'], \
            "'b' debe haber sido eliminado de la cola"
        
        # El próximo a desalojar sigue siendo 'a'
        assert fifo_cache.peek_next_eviction() == 'a'
    
    def test_clear_resets_insertion_order(self, fifo_cache):
        """
        Verifica que clear limpia completamente la cola de inserción.
        
        Después de clear, el caché debe comportarse como si fuera nuevo.
        """
        fifo_cache.put('a', 1)
        fifo_cache.put('b', 2)
        fifo_cache.put('c', 3)
        
        fifo_cache.clear()
        
        # La cola debe estar vacía
        assert fifo_cache.get_insertion_order() == []
        assert fifo_cache.peek_next_eviction() is None
        
        # Debe funcionar normalmente después de clear
        fifo_cache.put('x', 10)
        assert fifo_cache.get_insertion_order() == ['x']
        assert fifo_cache.peek_next_eviction() == 'x'
    
    def test_fifo_with_mixed_operations(self, fifo_cache):
        """
        Verifica FIFO con una mezcla realista de operaciones.
        
        Este test simula un patrón más realista con inserciones,
        accesos, actualizaciones y desalojos mezclados.
        """
        # Escenario: llenar el caché
        fifo_cache.put('doc1', 'contenido1')
        fifo_cache.put('doc2', 'contenido2')
        fifo_cache.put('doc3', 'contenido3')
        
        # Acceder repetidamente a doc1 (el más antiguo)
        for _ in range(10):
            assert fifo_cache.get('doc1') == 'contenido1'
        
        # A pesar de los accesos, doc1 sigue siendo el más antiguo
        assert fifo_cache.peek_next_eviction() == 'doc1'
        
        # Insertar doc4 desaloja doc1
        fifo_cache.put('doc4', 'contenido4')
        assert not fifo_cache.contains('doc1')
        
        # Actualizar doc2
        fifo_cache.put('doc2', 'contenido2_actualizado')
        
        # doc2 sigue en su posición original (es el próximo a desalojar)
        assert fifo_cache.peek_next_eviction() == 'doc2'
        
        # Insertar doc5 desaloja doc2
        fifo_cache.put('doc5', 'contenido5')
        assert not fifo_cache.contains('doc2')
        
        # Estado final: doc3, doc4, doc5
        assert fifo_cache.contains('doc3')
        assert fifo_cache.contains('doc4')
        assert fifo_cache.contains('doc5')
        assert fifo_cache.get_insertion_order() == ['doc3', 'doc4', 'doc5']


if __name__ == "__main__":
    """Permite ejecutar estos tests directamente con Python."""
    pytest.main([__file__, "-v"])