# Importaciones convenientes de los módulos más usados
from .core import (
    CachePolicy,
    FIFOCache,
    LRUCache,
    LFUCache,
)

from .multilevel import (
    CacheHierarchy,
)

from .simulator import (
    MemoryBackend,
    SSDBackend,
    HDDBackend,
    ZipfianWorkload,
    SequentialWorkload,
    UniformWorkload,
)

# Información del paquete
__version__ = '0.1.0'
__author__ = 'Cache System Team'
__license__ = 'MIT'
__description__ = 'Sistema de caché multinivel con simulación y visualización'

# Exportar las clases más comunes para uso directo
__all__ = [
    # Políticas de caché
    'CachePolicy',
    'FIFOCache',
    'LRUCache',
    'LFUCache',
    
    # Sistema multinivel
    'CacheHierarchy',
    
    # Simulación
    'MemoryBackend',
    'SSDBackend',
    'HDDBackend',
    'ZipfianWorkload',
    'SequentialWorkload',
    'UniformWorkload',
]

# Mensajes de bienvenida para usuarios interactivos
def _show_welcome():
    """Muestra mensaje de bienvenida si se importa en sesión interactiva."""
    import sys
    if hasattr(sys, 'ps1'):  # Detectar si es sesión interactiva
        print(f"""
╔══════════════════════════════════════════════════════════╗
║  Cache System v{__version__}                                  ║
║  Sistema de Caché Multinivel                            ║
╚══════════════════════════════════════════════════════════╝

📚 Ejemplos rápidos:

  # Crear caché simple
  >>> from cache_system import LRUCache
  >>> cache = LRUCache(capacity=100)
  >>> cache.put('key', 'value')
  >>> cache.get('key')
  
  # Crear jerarquía multinivel
  >>> from cache_system import CacheHierarchy, LRUCache
  >>> hierarchy = CacheHierarchy()
  >>> hierarchy.add_level(LRUCache(10), "L1", latency_ms=1)
  
  # Ejecutar simulación
  >>> from cache_system import ZipfianWorkload
  >>> workload = ZipfianWorkload(100, 1000)
  >>> operations = workload.generate()

💡 Para ver el dashboard interactivo:
   $ streamlit run dashboard/app.py

📖 Documentación: README.md
🧪 Tests: pytest tests/unit/ -v
        """)