import pytest
from cache_system.core.fifo import FIFOCache
from cache_system.core.lru import LRUCache
from cache_system.core.lfu import LFUCache


class TestBaseCacheBehavior:
    """
    Tests del comportamiento común que todas las políticas deben cumplir.
    
    Estos tests usan un fixture parametrizado que ejecuta cada test tres veces,
    una vez con cada política de caché. Esto garantiza que FIFO, LRU y LFU todas
    implementan correctamente la interfaz base definida en CachePolicy.
    
    Si alguno de estos tests falla para cualquier política, indica un problema
    fundamental en la implementación que debe corregirse antes de continuar.
    """
    
    @pytest.fixture(params=[FIFOCache, LRUCache, LFUCache])
    def cache(self, request):
        """
        Fixture parametrizado que crea instancias de cada política.
        
        Este fixture es la magia que hace que cada test se ejecute tres veces.
        Pytest automáticamente ejecutará cada test que use este fixture una vez
        con FIFOCache, otra con LRUCache, y otra con LFUCache.
        """
        cache_class = request.param
        return cache_class(capacity=3)
    
    def test_initialization(self, cache):
        """
        Verifica que el caché se inicializa en un estado válido.
        
        Un caché recién creado debe estar completamente vacío, con todas sus
        estadísticas en cero, y debe reportar correctamente su capacidad.
        Este es el estado fundamental del cual parten todos los demás tests.
        """
        assert cache.current_size == 0, "El caché debe iniciar vacío"
        assert cache.capacity == 3, "La capacidad debe ser la especificada en construcción"
        assert cache.is_empty, "Un caché vacío debe reportar is_empty como True"
        assert not cache.is_full, "Un caché vacío no puede estar lleno"
        
        # Verificar que las estadísticas inician en cero
        assert cache.stats.hits == 0, "No puede haber hits antes de cualquier operación"
        assert cache.stats.misses == 0, "No puede haber misses antes de cualquier operación"
        assert cache.stats.evictions == 0, "No puede haber desalojos en un caché vacío"
    
    def test_invalid_capacity_rejected(self):
        """
        Verifica que capacidades inválidas se rechazan apropiadamente.
        
        Intentar crear un caché con capacidad cero o negativa debe fallar
        inmediatamente con ValueError. Este test previene la creación de
        cachés en estados inconsistentes que causarían problemas difíciles
        de debuggear más adelante.
        """
        with pytest.raises(ValueError):
            FIFOCache(capacity=0)
        
        with pytest.raises(ValueError):
            LRUCache(capacity=-1)
        
        with pytest.raises(ValueError):
            LFUCache(capacity=-10)
    
    def test_single_put_and_get(self, cache):
        """
        Verifica la operación más básica: insertar un elemento y recuperarlo.
        
        Este test valida el camino feliz más simple. Si este test falla,
        hay un problema fundamental en la implementación que debe resolverse
        antes de probar cualquier cosa más compleja.
        """
        cache.put('mi_clave', 'mi_valor')
        
        assert cache.current_size == 1, "Insertar un elemento debe incrementar el tamaño a 1"
        assert cache.get('mi_clave') == 'mi_valor', "Debe retornar exactamente el valor insertado"
        
        # Verificar que las estadísticas se actualizaron correctamente
        assert cache.stats.hits == 1, "Un get exitoso debe contar como hit"
        assert cache.stats.misses == 0, "No debe haber misses en este escenario"
    
    def test_get_nonexistent_key_returns_none(self, cache):
        """
        Verifica el comportamiento cuando buscamos una clave que no existe.
        
        Buscar una clave inexistente debe retornar None y contar como miss,
        sin causar errores o excepciones. Este es un caso que ocurre
        constantemente en uso real del caché.
        """
        result = cache.get('clave_inexistente')
        
        assert result is None, "Buscar una clave inexistente debe retornar None"
        assert cache.stats.misses == 1, "Debe contarse como un miss"
        assert cache.stats.hits == 0, "No debe contarse como hit"
        assert cache.current_size == 0, "El tamaño no debe cambiar"
    
    def test_multiple_insertions(self, cache):
        """
        Verifica que podemos insertar múltiples elementos hasta la capacidad.
        
        Este test valida que el caché puede llenarse completamente sin problemas
        y que el indicador is_full funciona correctamente.
        """
        cache.put('a', 1)
        cache.put('b', 2)
        cache.put('c', 3)
        
        assert cache.current_size == 3, "Después de 3 inserciones, el tamaño debe ser 3"
        assert cache.is_full, "El caché debe reportarse como lleno al alcanzar capacidad"
        assert not cache.is_empty, "Un caché lleno no puede estar vacío"
        
        # Verificar que todos los elementos están accesibles
        assert cache.get('a') == 1
        assert cache.get('b') == 2
        assert cache.get('c') == 3
    
    def test_update_existing_key(self, cache):
        """
        Verifica que actualizar una clave existente funciona correctamente.
        
        Cuando hacemos put con una clave que ya existe, debe actualizar el valor
        sin cambiar el tamaño del caché. Este comportamiento es fundamental
        para usar el caché como almacenamiento temporal.
        """
        cache.put('clave', 'valor_original')
        tamano_original = cache.current_size
        
        cache.put('clave', 'valor_actualizado')
        
        assert cache.current_size == tamano_original, "Actualizar no debe cambiar el tamaño"
        assert cache.get('clave') == 'valor_actualizado', "Debe retornar el nuevo valor"
    
    def test_contains_method(self, cache):
        """
        Verifica que contains verifica existencia sin afectar estadísticas.
        
        El método contains es importante porque permite verificar si una clave
        existe sin contaminar las estadísticas de hits y misses. Es como
        "mirar sin tocar".
        """
        cache.put('existe', 'valor')
        
        assert cache.contains('existe'), "Debe retornar True para claves existentes"
        assert not cache.contains('no_existe'), "Debe retornar False para claves inexistentes"
        
        # Lo crítico: contains NO debe afectar estadísticas
        assert cache.stats.hits == 0, "contains no debe contar como hit"
        assert cache.stats.misses == 0, "contains no debe contar como miss"
    
    def test_delete_existing_key(self, cache):
        """
        Verifica que eliminar una clave existente funciona correctamente.
        
        Delete debe eliminar la clave, reducir el tamaño, y retornar True
        para indicar éxito. Las demás claves no deben verse afectadas.
        """
        cache.put('a', 1)
        cache.put('b', 2)
        cache.put('c', 3)
        
        result = cache.delete('b')
        
        assert result is True, "delete debe retornar True cuando elimina con éxito"
        assert cache.current_size == 2, "El tamaño debe reducirse en 1"
        assert not cache.contains('b'), "La clave eliminada no debe existir"
        assert cache.contains('a'), "Las otras claves no deben verse afectadas"
        assert cache.contains('c'), "Las otras claves no deben verse afectadas"
    
    def test_delete_nonexistent_key(self, cache):
        """
        Verifica que eliminar una clave inexistente se maneja correctamente.
        
        Intentar eliminar algo que no existe debe retornar False y no causar
        errores. El estado del caché no debe cambiar.
        """
        cache.put('existe', 'valor')
        tamano_original = cache.current_size
        
        result = cache.delete('no_existe')
        
        assert result is False, "delete debe retornar False si la clave no existe"
        assert cache.current_size == tamano_original, "El tamaño no debe cambiar"
    
    def test_clear_empties_cache(self, cache):
        """
        Verifica que clear vacía completamente el caché.
        
        Después de clear, el caché debe volver al mismo estado que tenía
        después de la inicialización: completamente vacío.
        """
        # Llenar el caché
        cache.put('a', 1)
        cache.put('b', 2)
        cache.put('c', 3)
        
        cache.clear()
        
        assert cache.current_size == 0, "El caché debe estar vacío después de clear"
        assert cache.is_empty, "is_empty debe retornar True"
        assert not cache.contains('a'), "Todas las claves deben haber sido eliminadas"
        assert not cache.contains('b'), "Todas las claves deben haber sido eliminadas"
        assert not cache.contains('c'), "Todas las claves deben haber sido eliminadas"
    
    def test_keys_returns_all_keys(self, cache):
        """
        Verifica que keys() retorna todas las claves presentes.
        
        Este método es importante para inspeccionar el contenido del caché
        y será útil para el sistema multinivel.
        """
        cache.put('x', 1)
        cache.put('y', 2)
        cache.put('z', 3)
        
        keys = cache.keys()
        
        assert len(keys) == 3, "Debe retornar todas las claves"
        assert 'x' in keys, "Debe incluir todas las claves insertadas"
        assert 'y' in keys, "Debe incluir todas las claves insertadas"
        assert 'z' in keys, "Debe incluir todas las claves insertadas"
    
    def test_eviction_when_full(self, cache):
        """
        Verifica que insertar en un caché lleno causa desalojo.
        
        Este test no verifica QUÉ elemento se desaloja (eso es específico
        de cada política), sino que ALGÚN elemento se desaloja y que las
        estadísticas se actualizan correctamente.
        """
        # Llenar el caché
        cache.put('a', 1)
        cache.put('b', 2)
        cache.put('c', 3)
        
        # Verificar que está lleno
        assert cache.is_full
        assert cache.stats.evictions == 0
        
        # Insertar un cuarto elemento debe causar desalojo
        cache.put('d', 4)
        
        assert cache.current_size == 3, "El tamaño debe mantenerse en la capacidad"
        assert cache.is_full, "Debe seguir lleno"
        assert cache.stats.evictions == 1, "Debe registrar exactamente 1 desalojo"
        
        # El nuevo elemento debe estar presente
        assert cache.contains('d'), "El nuevo elemento debe estar en el caché"
    
    def test_statistics_consistency(self, cache):
        """
        Verifica que las estadísticas se mantienen consistentes.
        
        Las métricas derivadas como hit_rate deben calcularse correctamente
        a partir de los contadores básicos.
        """
        # Realizar operaciones conocidas
        cache.put('a', 1)
        cache.put('b', 2)
        
        cache.get('a')     # Hit
        cache.get('b')     # Hit
        cache.get('c')     # Miss
        cache.get('a')     # Hit
        
        # Verificar contadores
        assert cache.stats.hits == 3, "Debe contar exactamente 3 hits"
        assert cache.stats.misses == 1, "Debe contar exactamente 1 miss"
        
        # Verificar hit_rate calculado
        expected_hit_rate = 3 / 4  # 3 hits de 4 accesos totales = 0.75
        assert abs(cache.stats.hit_rate - expected_hit_rate) < 0.01, \
            "El hit_rate debe calcularse correctamente"
    
    def test_capacity_one_edge_case(self, cache):
        """
        Verifica que un caché con capacidad 1 funciona correctamente.
        
        Este es un edge case importante porque muchas optimizaciones asumen
        capacidad mayor a 1. Un caché de tamaño 1 debe funcionar correctamente
        aunque desaloje en cada inserción después de la primera.
        """
        # Crear un caché con capacidad 1
        cache_class = cache.__class__
        small_cache = cache_class(capacity=1)
        
        small_cache.put('a', 1)
        assert small_cache.get('a') == 1
        assert small_cache.is_full
        
        # Insertar segundo elemento desaloja el primero inmediatamente
        small_cache.put('b', 2)
        assert not small_cache.contains('a'), "'a' debe haber sido desalojado"
        assert small_cache.get('b') == 2, "'b' debe estar presente"
        assert small_cache.stats.evictions == 1, "Debe registrar el desalojo"


if __name__ == "__main__":
    """Permite ejecutar estos tests directamente con Python."""
    pytest.main([__file__, "-v"])