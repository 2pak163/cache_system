# Sistema de Caché Multinivel

Simulador interactivo de políticas de caché y jerarquías multinivel desarrollado con Python y Streamlit.

## Descripción

Este proyecto implementa un sistema completo de simulación de cachés que permite:
- Experimentar con diferentes políticas de reemplazo (FIFO, LRU, LFU)
- Configurar jerarquías multinivel con hasta 5 niveles
- Simular patrones de acceso realistas con diferentes tipos de workloads
- Visualizar métricas de rendimiento en tiempo real
- Comparar el comportamiento de diferentes configuraciones

## Características Principales

### Políticas de Caché Implementadas

**FIFO (First In First Out)**
- Desaloja el elemento más antiguo en el caché
- Implementación simple y predecible
- Ideal para datos con acceso uniforme

**LRU (Least Recently Used)**
- Desaloja el elemento menos recientemente usado
- Implementación con lista doblemente enlazada para O(1)
- Excelente para patrones con localidad temporal

**LFU (Least Frequently Used)**
- Desaloja el elemento menos frecuentemente usado
- Mantiene contador de accesos por elemento
- Protege elementos "calientes" de ser desalojados

### Sistema Multinivel

El sistema permite crear jerarquías de caché con múltiples niveles, cada uno con:
- Política de reemplazo configurable
- Capacidad específica
- Latencia simulada
- Promoción automática entre niveles

### Tipos de Workload

**Uniform**: Distribución uniforme donde todas las claves tienen igual probabilidad de acceso

**Zipfian**: Distribución realista que simula el principio 80/20, donde pocas claves reciben la mayoría de accesos

**Sequential**: Acceso secuencial a las claves, útil para simular escaneos de datos

## Instalación

### Requisitos Previos
- Python 3.9 o superior
- pip (gestor de paquetes de Python)
- Git (para clonar el repositorio)

### Pasos de Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/2pak163/cache_system
cd cache-system
```

2. Crear un entorno virtual (recomendado):
```bash
python -m venv venv

# En Windows:
venv\Scripts\activate

# En Linux/Mac:
source venv/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Ejecutar la aplicación:
```bash
streamlit run dashboard/app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## Uso del Sistema

### Interfaz del Dashboard

El dashboard está organizado en tres páginas principales:

#### 1. Overview (Vista General)

Esta página permite configurar la jerarquía de caché:

- **Agregar Niveles**: Define cada nivel de la jerarquía especificando:
  - Nombre del nivel (ej: L1, L2, L3)
  - Política de reemplazo (FIFO, LRU o LFU)
  - Capacidad (número de elementos)
  - Latencia simulada en milisegundos

- **Visualización**: Muestra la configuración actual de la jerarquía con métricas básicas

**Ejemplo de configuración típica**:
- L1: LRU, capacidad 10, latencia 1ms (caché rápido)
- L2: LRU, capacidad 100, latencia 10ms (caché intermedio)
- L3: LFU, capacidad 1000, latencia 50ms (caché grande)

#### 2. Simulación

Ejecuta simulaciones con diferentes patrones de acceso:

- **Configurar Workload**:
  - Tipo: Uniform, Zipfian o Sequential
  - Número de claves únicas
  - Número total de operaciones
  - Ratio de lectura/escritura
  - Parámetros específicos (ej: theta para Zipfian)

- **Ejecutar Simulación**: Procesa el workload y muestra resultados

- **Métricas Disponibles**:
  - Hit rate global y por nivel
  - Miss rate
  - Número de evictions
  - Latencia promedio
  - Utilización de capacidad
  - Número de promociones entre niveles

- **Visualizaciones**:
  - Gráfico de hits vs misses por nivel
  - Evolución temporal del hit rate
  - Distribución de latencias
  - Comparación de utilización

#### 3. Comparación

Permite comparar diferentes configuraciones lado a lado:

- Ejecuta múltiples simulaciones con diferentes políticas
- Compara métricas de rendimiento
- Identifica la mejor configuración para un workload específico

### Uso Programático

El sistema también puede usarse directamente desde código Python:

#### Ejemplo Básico

```python
from cache_system.core import LRUCache

# Crear un caché LRU de 100 elementos
cache = LRUCache(capacity=100, name="MiCache")

# Insertar datos
cache.put('usuario_1', {'nombre': 'Juan', 'edad': 25})
cache.put('usuario_2', {'nombre': 'María', 'edad': 30})

# Recuperar datos
usuario = cache.get('usuario_1')
print(usuario)  # {'nombre': 'Juan', 'edad': 25}

# Verificar estadísticas
stats = cache.stats.to_dict()
print(f"Hit rate: {stats['hit_rate']:.2%}")
print(f"Utilización: {stats['utilization']:.2%}")
```

#### Ejemplo de Jerarquía Multinivel

```python
from cache_system.core import LRUCache, LFUCache
from cache_system.multilevel import CacheHierarchy

# Crear jerarquía
hierarchy = CacheHierarchy(name="SistemaMemoria")

# Agregar niveles
hierarchy.add_level(
    cache=LRUCache(capacity=10),
    name="L1",
    latency_ms=1
)

hierarchy.add_level(
    cache=LRUCache(capacity=100),
    name="L2",
    latency_ms=10
)

hierarchy.add_level(
    cache=LFUCache(capacity=1000),
    name="L3",
    latency_ms=50
)

# Usar el caché
hierarchy.put('clave', 'valor')
resultado = hierarchy.get('clave')  # Hit en L1

# Obtener estadísticas detalladas
stats = hierarchy.get_all_stats()
print(f"Hit rate global: {stats['global']['global_hit_rate']:.2%}")
print(f"Latencia promedio: {stats['global']['avg_latency_ms']:.2f}ms")

# Ver estadísticas por nivel
for level_stats in stats['levels']:
    print(f"\n{level_stats['name']}:")
    print(f"  Hits: {level_stats['hits']}")
    print(f"  Misses: {level_stats['misses']}")
    print(f"  Hit rate: {level_stats['hit_rate']:.2%}")
```

#### Ejemplo de Simulación con Workload

```python
from cache_system.simulator.workload import ZipfianWorkload
from cache_system.core import LRUCache

# Crear workload Zipfian (80/20)
workload = ZipfianWorkload(
    num_keys=100,
    num_operations=10000,
    read_ratio=0.8,
    theta=0.99
)

# Generar operaciones
operations = workload.generate()

# Crear caché
cache = LRUCache(capacity=20)

# Ejecutar simulación
for op_type, key, value in operations:
    if op_type == 'get':
        cache.get(key)
    else:  # put
        cache.put(key, value)

# Analizar resultados
stats = cache.stats.to_dict()
print(f"Total de operaciones: {len(operations)}")
print(f"Hit rate: {stats['hit_rate']:.2%}")
print(f"Evictions: {stats['evictions']}")
```

## Arquitectura del Proyecto

```
cache-system/
├── cache_system/              # Paquete principal
│   ├── core/                 # Implementación de políticas
│   │   ├── base.py          # Clase base abstracta CachePolicy
│   │   ├── fifo.py          # Implementación FIFO
│   │   ├── lru.py           # Implementación LRU
│   │   └── lfu.py           # Implementación LFU
│   ├── multilevel/           # Sistema multinivel
│   │   └── cache_hierarchy.py
│   ├── simulator/            # Simulación y workloads
│   │   ├── backend.py       # Modelado de backends de almacenamiento
│   │   └── workload.py      # Generadores de patrones de acceso
│   └── utils/               # Utilidades auxiliares
├── dashboard/                # Aplicación Streamlit
│   ├── app.py               # Página principal
│   └── pages/               # Páginas del dashboard
│       ├── 1_Overview.py
│       ├── 2_Simulacion.py
│       └── 3_Comparacion.py
├── tests/                    # Suite de tests
│   ├── unit/                # Tests unitarios
│   ├── integration/         # Tests de integración
│   └── performance/         # Benchmarks
├── examples/                 # Ejemplos de uso
├── requirements.txt          # Dependencias del proyecto
└── README.md                # Este archivo
```

## Métricas y Estadísticas

El sistema recopila y presenta las siguientes métricas:

### Métricas Básicas
- **Hits**: Número de accesos que encontraron el dato en caché
- **Misses**: Número de accesos que no encontraron el dato
- **Hit Rate**: Porcentaje de hits sobre el total de accesos
- **Miss Rate**: Porcentaje de misses (complemento del hit rate)
- **Evictions**: Número de elementos desalojados del caché

### Métricas de Capacidad
- **Current Size**: Número actual de elementos en caché
- **Max Size**: Capacidad máxima del caché
- **Utilization**: Porcentaje de capacidad utilizada

### Métricas Multinivel
- **Promotions**: Número de elementos promovidos a niveles superiores
- **Latency**: Latencia promedio de acceso considerando todos los niveles
- **Level Hit Rate**: Hit rate individual de cada nivel

## Testing

El proyecto incluye una suite completa de tests:

```bash
# Ejecutar todos los tests
pytest tests/

# Ejecutar con reporte de cobertura
pytest --cov=cache_system tests/

# Ejecutar solo tests unitarios
pytest tests/unit/

# Ejecutar tests de una política específica
pytest tests/unit/test_lru.py -v
```

## Casos de Uso

### 1. Análisis de Políticas de Caché

Usar el dashboard para comparar cómo se comportan FIFO, LRU y LFU con diferentes workloads y determinar cuál es más apropiada para tu caso de uso.

### 2. Dimensionamiento de Caché

Experimentar con diferentes capacidades para encontrar el punto óptimo entre memoria utilizada y hit rate obtenido.

### 3. Educación

Herramienta didáctica para entender cómo funcionan los sistemas de caché y las diferentes estrategias de reemplazo.

### 4. Prototipado

Validar el diseño de un sistema de caché antes de implementarlo en producción.

### 5. Benchmarking

Comparar el rendimiento de diferentes configuraciones con workloads realistas.

## Limitaciones Conocidas

- El sistema simula comportamiento de caché pero no implementa persistencia real
- Las latencias son simuladas y no reflejan hardware real
- El sistema está optimizado para simulación educativa, no para producción a escala

## Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Realiza tus cambios y agrega tests
4. Asegúrate de que todos los tests pasen
5. Commit tus cambios (`git commit -m 'Agrega nueva funcionalidad'`)
6. Push a la rama (`git push origin feature/nueva-funcionalidad`)
7. Abre un Pull Request

### Áreas donde Contribuir

- Implementación de nuevas políticas (ARC, CLOCK, 2Q)
- Mejoras en visualizaciones del dashboard
- Optimizaciones de rendimiento
- Documentación y ejemplos adicionales
- Tests y casos de prueba

## Contacto

Para preguntas, sugerencias o reportar problemas, por favor abre un issue en el repositorio de GitHub.

## Agradecimientos

Inspirado por sistemas de caché reales utilizados en:
- Arquitecturas de CPU (L1, L2, L3 cache)
- Sistemas operativos (page cache)
- Bases de datos (buffer pool)
- Aplicaciones web (Redis, Memcached)

Desarrollado con:
- Python 3.x
- Streamlit para el dashboard interactivo
- Plotly para visualizaciones
- Pandas y NumPy para procesamiento de datos