import pytest
import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al PYTHONPATH
# Esto permite importar cache_system desde cualquier test
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """
    Hook que se ejecuta al inicio de la sesión de tests.
    
    Registra markers personalizados que pueden usarse para categorizar tests.
    """
    config.addinivalue_line(
        "markers", "slow: marca tests que son lentos de ejecutar"
    )
    config.addinivalue_line(
        "markers", "integration: marca tests de integración"
    )


@pytest.fixture
def print_cache_state():
    """
    Fixture helper para imprimir el estado del caché durante debugging.
    
    Útil cuando los tests fallan y necesitas ver exactamente qué
    estado tiene el caché en ese momento.
    
    Uso:
        def test_algo(cache, print_cache_state):
            cache.put('a', 1)
            print_cache_state(cache, "Después de insertar 'a'")
    """
    def _print_state(cache, message=""):
        print(f"\n{'='*60}")
        if message:
            print(f"Estado del caché: {message}")
        print(f"{'='*60}")
        print(f"Tipo: {cache.__class__.__name__}")
        print(f"Capacidad: {cache.capacity}")
        print(f"Tamaño actual: {cache.current_size}")
        print(f"Lleno: {cache.is_full}")
        print(f"Claves: {cache.keys()}")
        print(f"\nEstadísticas:")
        for key, value in cache.stats.to_dict().items():
            print(f"  {key}: {value}")
        
        # Información específica de cada política
        if hasattr(cache, 'get_insertion_order'):
            print(f"\nOrden FIFO: {cache.get_insertion_order()}")
        
        if hasattr(cache, 'get_access_order'):
            print(f"\nOrden LRU: {cache.get_access_order()}")
        
        if hasattr(cache, 'get_frequency_distribution'):
            print(f"\nDistribución LFU: {cache.get_frequency_distribution()}")
        
        print(f"{'='*60}\n")
    
    return _print_state