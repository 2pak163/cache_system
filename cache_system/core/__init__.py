from .base import (
    CachePolicy,
    CacheEntry,
    CacheStats
)

from .fifo import FIFOCache
from .lru import LRUCache
from .lfu import LFUCache

__all__ = [
    # Clase base y estructuras
    'CachePolicy',
    'CacheEntry',
    'CacheStats',
    
    # Políticas de caché
    'FIFOCache',
    'LRUCache',
    'LFUCache',
]

# Información de versión
__version__ = '0.1.0'

# Metadata del paquete
__author__ = 'Cache System Team'
__description__ = 'Implementaciones de políticas de caché con interfaz común'