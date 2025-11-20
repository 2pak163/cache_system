import pytest
from cache_system.core.lfu import LFUCache


class TestLFUPolicy:
    """
    Tests específicos de la política Least Frequently Used.
    
    LFU rastrea cuántas veces se ha accedido cada elemento y desaloja
    el que tiene el menor contador de accesos. Estos tests verifican
    que el rastreo de frecuencias funciona correctamente.
    """
    
    @pytest.fixture
    def lfu_cache(self):
        """Crea un caché LFU fresco para cada test."""
        return LFUCache(capacity=3)
    
    def test_evicts_least_frequently_used(self, lfu_cache):
        """
        Verifica que LFU desaloja el elemento con menor frecuencia.
        
        Este es el test fundamental de LFU: cuando el caché está lleno,
        debe desalojar el elemento que ha sido accedido menos veces.
        """
        lfu_cache.put('a', 1)
        lfu_cache.put('b', 2)
        lfu_cache.put('c', 3)
        
        # Todos comienzan con frecuencia 1 (la inserción cuenta como acceso)
        assert lfu_cache.get_key_frequency('a') == 1
        assert lfu_cache.get_key_frequency('b') == 1
        assert lfu_cache.get_key_frequency('c') == 1
        
        # Acceder a 'a' varias veces incrementa su frecuencia
        lfu_cache.get('a')
        lfu_cache.get('a')
        lfu_cache.get('a')
        
        # 'a' ahora tiene frecuencia 4 (1 inicial + 3 accesos)
        assert lfu_cache.get_key_frequency('a') == 4
        
        # Acceder a 'b' una vez
        lfu_cache.get('b')
        assert lfu_cache.get_key_frequency('b') == 2
        
        # 'c' sigue con frecuencia 1, es el LFU
        assert lfu_cache.peek_lfu() == 'c'
        
        # Insertar 'd' debe desalojar 'c' (menor frecuencia)
        lfu_cache.put('d', 4)
        
        assert not lfu_cache.contains('c'), \
            "'c' debe ser desalojado (menor frecuencia)"
        assert lfu_cache.contains('a'), \
            "'a' debe sobrevivir (frecuencia 4)"
        assert lfu_cache.contains('b'), \
            "'b' debe sobrevivir (frecuencia 2)"
        assert lfu_cache.contains('d'), \
            "'d' debe estar presente (frecuencia 1)"
    
    def test_frequency_increments_correctly(self, lfu_cache):
        """
        Verifica que las frecuencias se incrementan correctamente.
        
        Cada acceso debe incrementar el contador de frecuencia en exactamente 1.
        """
        lfu_cache.put('elemento', 'valor')
        
        # Frecuencia inicial es 1 (la inserción cuenta)
        assert lfu_cache.get_key_frequency('elemento') == 1
        
        # Cada get debe incrementar la frecuencia
        lfu_cache.get('elemento')
        assert lfu_cache.get_key_frequency('elemento') == 2
        
        lfu_cache.get('elemento')
        assert lfu_cache.get_key_frequency('elemento') == 3
        
        lfu_cache.get('elemento')
        assert lfu_cache.get_key_frequency('elemento') == 4
        
        lfu_cache.get('elemento')
        assert lfu_cache.get_key_frequency('elemento') == 5
    
    def test_tie_breaking_with_fifo(self, lfu_cache):
        """
        Verifica que LFU usa FIFO para desempatar elementos con misma frecuencia.
        
        Cuando múltiples elementos tienen la misma frecuencia, LFU debe
        desalojar el que fue insertado primero. Este es un comportamiento
        crítico para mantener consistencia en el desalojo.
        """
        lfu_cache.put('a', 1)
        lfu_cache.put('b', 2)
        lfu_cache.put('c', 3)
        
        # Todos tienen frecuencia 1
        # 'a' fue insertado primero, por lo que es el próximo LFU
        assert lfu_cache.peek_lfu() == 'a'
        
        # Insertar 'd' desaloja 'a' (mismo freq, pero insertado primero)
        lfu_cache.put('d', 4)
        
        assert not lfu_cache.contains('a'), \
            "'a' debe ser desalojado (desempate FIFO)"
        assert lfu_cache.contains('b')
        assert lfu_cache.contains('c')
        
        # Ahora 'b' es el LFU (freq=1, insertado antes que 'c' y 'd')
        assert lfu_cache.peek_lfu() == 'b'
    
    def test_protects_popular_elements(self, lfu_cache):
        """
        Verifica que elementos con alta frecuencia están protegidos.
        
        Un elemento muy popular (accedido muchas veces) no debe ser
        desalojado incluso después de múltiples inserciones nuevas.
        """
        lfu_cache.put('popular', 'datos_importantes')
        lfu_cache.put('temp1', 'temporal')
        lfu_cache.put('temp2', 'temporal')
        
        # Hacer que 'popular' sea muy popular
        for _ in range(20):
            lfu_cache.get('popular')
        
        # 'popular' ahora tiene frecuencia 21 (1 inicial + 20 accesos)
        assert lfu_cache.get_key_frequency('popular') == 21
        
        # Insertar muchos elementos nuevos
        lfu_cache.put('temp3', 'temporal')  # Desaloja temp1 o temp2
        lfu_cache.put('temp4', 'temporal')  # Desaloja temp1 o temp2
        lfu_cache.put('temp5', 'temporal')  # Desaloja temp3 o temp4
        
        # 'popular' debe seguir en el caché
        assert lfu_cache.contains('popular'), \
            "'popular' debe sobrevivir por su alta frecuencia"
        assert lfu_cache.get_key_frequency('popular') == 21, \
            "La frecuencia debe mantenerse"
    
    def test_update_increments_frequency(self, lfu_cache):
        """
        Verifica que actualizar un elemento incrementa su frecuencia.
        
        En LFU, actualizar el valor se considera un acceso, por lo que
        debe incrementar el contador de frecuencia.
        """
        lfu_cache.put('clave', 'valor1')
        
        frecuencia_inicial = lfu_cache.get_key_frequency('clave')
        assert frecuencia_inicial == 1
        
        # Actualizar el valor
        lfu_cache.put('clave', 'valor2')
        
        # La frecuencia debe incrementar
        assert lfu_cache.get_key_frequency('clave') == 2, \
            "Actualizar debe incrementar la frecuencia"
        assert lfu_cache.get('clave') == 'valor2', \
            "El valor debe actualizarse"
    
    def test_frequency_distribution(self, lfu_cache):
        """
        Verifica que get_frequency_distribution retorna información correcta.
        
        Este método es útil para visualización y debe mostrar cuántos
        elementos hay en cada nivel de frecuencia.
        """
        lfu_cache.put('a', 1)
        lfu_cache.put('b', 2)
        lfu_cache.put('c', 3)
        
        # Todos comienzan con frecuencia 1
        dist = lfu_cache.get_frequency_distribution()
        assert dist == {1: 3}, \
            "Debe haber 3 elementos con frecuencia 1"
        
        # Acceder a 'a' dos veces (freq=3)
        lfu_cache.get('a')
        lfu_cache.get('a')
        
        dist = lfu_cache.get_frequency_distribution()
        assert dist == {1: 2, 3: 1}, \
            "2 elementos con freq=1, 1 elemento con freq=3"
        
        # Acceder a 'b' una vez (freq=2)
        lfu_cache.get('b')
        
        dist = lfu_cache.get_frequency_distribution()
        assert dist == {1: 1, 2: 1, 3: 1}, \
            "Distribución: 1 elemento en cada nivel"
    
    def test_elements_by_frequency(self, lfu_cache):
        """
        Verifica que get_elements_by_frequency agrupa correctamente.
        
        Este método muestra qué elementos específicos están en cada
        nivel de frecuencia, útil para debugging.
        """
        lfu_cache.put('a', 1)
        lfu_cache.put('b', 2)
        lfu_cache.put('c', 3)
        
        # Modificar frecuencias
        lfu_cache.get('a')  # a: freq=2
        lfu_cache.get('a')  # a: freq=3
        lfu_cache.get('b')  # b: freq=2
        
        elementos = lfu_cache.get_elements_by_frequency()
        
        assert 'c' in elementos[1], "'c' debe tener frecuencia 1"
        assert 'b' in elementos[2], "'b' debe tener frecuencia 2"
        assert 'a' in elementos[3], "'a' debe tener frecuencia 3"
    
    def test_delete_removes_frequency_tracking(self, lfu_cache):
        """
        Verifica que delete elimina el elemento del rastreo de frecuencias.
        
        Cuando eliminamos un elemento, debe limpiarse de todas las
        estructuras internas de LFU.
        """
        lfu_cache.put('a', 1)
        lfu_cache.put('b', 2)
        lfu_cache.put('c', 3)
        
        # Dar a 'b' una frecuencia alta
        for _ in range(5):
            lfu_cache.get('b')
        
        # Eliminar 'b'
        lfu_cache.delete('b')
        
        # 'b' no debe aparecer en la distribución
        dist = lfu_cache.get_frequency_distribution()
        elementos = lfu_cache.get_elements_by_frequency()
        
        for freq_list in elementos.values():
            assert 'b' not in freq_list, \
                "'b' no debe aparecer en ningún nivel de frecuencia"
    
    def test_clear_resets_frequency_tracking(self, lfu_cache):
        """
        Verifica que clear limpia completamente el rastreo de frecuencias.
        """
        lfu_cache.put('a', 1)
        lfu_cache.put('b', 2)
        
        # Dar frecuencias altas
        for _ in range(10):
            lfu_cache.get('a')
        
        lfu_cache.clear()
        
        # La distribución debe estar vacía
        assert lfu_cache.get_frequency_distribution() == {}
        assert lfu_cache.get_elements_by_frequency() == {}
        assert lfu_cache.peek_lfu() is None
        
        # Debe funcionar normalmente después de clear
        lfu_cache.put('x', 10)
        assert lfu_cache.get_key_frequency('x') == 1
    
    def test_lfu_with_realistic_workload(self, lfu_cache):
        """
        Verifica LFU con un patrón de acceso realista.
        
        Simula un escenario donde hay elementos claramente populares
        (alta frecuencia) y elementos ocasionales (baja frecuencia).
        """
        # Insertar diferentes tipos de datos
        lfu_cache.put('api_key', 'configuracion')      # Muy popular
        lfu_cache.put('user_session', 'datos_sesion')  # Popular
        lfu_cache.put('temp_data', 'temporal')         # Poco usado
        
        # Patrón de acceso realista
        # api_key se accede constantemente
        for _ in range(15):
            lfu_cache.get('api_key')
        
        # user_session se accede ocasionalmente
        for _ in range(5):
            lfu_cache.get('user_session')
        
        # temp_data nunca se accede después de inserción
        
        # Verificar frecuencias
        assert lfu_cache.get_key_frequency('api_key') == 16  # 1 + 15
        assert lfu_cache.get_key_frequency('user_session') == 6  # 1 + 5
        assert lfu_cache.get_key_frequency('temp_data') == 1  # Solo inserción
        
        # temp_data es el LFU
        assert lfu_cache.peek_lfu() == 'temp_data'
        
        # Insertar nuevo dato desaloja temp_data
        lfu_cache.put('cache_entry', 'nuevo_dato')
        
        assert not lfu_cache.contains('temp_data'), \
            "'temp_data' debe ser desalojado (menor frecuencia)"
        assert lfu_cache.contains('api_key'), \
            "'api_key' debe sobrevivir (alta frecuencia)"
        assert lfu_cache.contains('user_session'), \
            "'user_session' debe sobrevivir (frecuencia media)"
    
    def test_mixed_operations_maintain_consistency(self, lfu_cache):
        """
        Verifica que operaciones mezcladas mantienen consistencia.
        
        Este test combina inserciones, actualizaciones, accesos y
        eliminaciones para verificar que LFU mantiene consistencia
        en escenarios complejos.
        """
        # Operaciones iniciales
        lfu_cache.put('a', 1)
        lfu_cache.put('b', 2)
        lfu_cache.put('c', 3)
        
        # Patrón complejo
        lfu_cache.get('a')          # a: freq=2
        lfu_cache.put('a', 10)      # a: freq=3 (actualizar)
        lfu_cache.get('b')          # b: freq=2
        lfu_cache.delete('c')       # Eliminar c
        lfu_cache.put('d', 4)       # Insertar d: freq=1
        lfu_cache.get('a')          # a: freq=4
        lfu_cache.get('d')          # d: freq=2
        
        # Verificar estado final
        assert lfu_cache.get_key_frequency('a') == 4
        assert lfu_cache.get_key_frequency('b') == 2
        assert lfu_cache.get_key_frequency('d') == 2
        assert not lfu_cache.contains('c')
        
        # 'b' y 'd' tienen freq=2, pero 'b' fue insertado primero
        assert lfu_cache.peek_lfu() == 'b'


if __name__ == "__main__":
    """Permite ejecutar estos tests directamente con Python."""
    pytest.main([__file__, "-v"])