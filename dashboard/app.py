import streamlit as st
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar cache_system
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from cache_system.core import LRUCache, LFUCache, FIFOCache
from cache_system.multilevel import CacheHierarchy

st.set_page_config(
    page_title="App",
    page_icon="💾",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/2pak163/cache_system',
        'Report a bug': 'https://github.com/2pak163/cache-system/issues',
        'About': """    
        # Sistema de Caché Multinivel
        
        Simulador interactivo para políticas de caché y jerarquías multinivel.
        
        **Características:**
        - Múltiples políticas: FIFO, LRU, LFU
        - Sistema multinivel configurable
        - Workloads realistas (Zipfian, Sequential, Uniform)
        - Visualización en tiempo real
        - Comparación de rendimiento
        
        Desarrollado con Python y Streamlit
        """
    }
)

# Inicialización del Estado de Sesión

def init_session_state():
    # Configuración de la jerarquía
    if 'hierarchy_config' not in st.session_state:
        st.session_state.hierarchy_config = {
            'levels': [
                {'policy': 'LRU', 'capacity': 10, 'name': 'L1', 'latency_ms': 1},
                {'policy': 'LRU', 'capacity': 100, 'name': 'L2', 'latency_ms': 10},
                {'policy': 'LFU', 'capacity': 1000, 'name': 'L3', 'latency_ms': 50},
            ]
        }
    
    # Instancia de jerarquía actual
    if 'hierarchy' not in st.session_state:
        st.session_state.hierarchy = None
    
    # Resultados de simulaciones
    if 'simulation_results' not in st.session_state:
        st.session_state.simulation_results = []
    
    # Configuración de workload
    if 'workload_config' not in st.session_state:
        st.session_state.workload_config = {
            'type': 'zipfian',
            'num_keys': 100,
            'num_operations': 1000,
            'read_ratio': 0.8,
            'theta': 0.99
        }

# Funciones de Utilidad

def create_hierarchy_from_config(config):
    hierarchy = CacheHierarchy(name="DashboardCache")
    
    policy_classes = {
        'FIFO': FIFOCache,
        'LRU': LRUCache,
        'LFU': LFUCache
    }
    
    for level_config in config['levels']:
        policy_class = policy_classes[level_config['policy']]
        cache = policy_class(capacity=level_config['capacity'])
        
        hierarchy.add_level(
            cache=cache,
            name=level_config['name'],
            latency_ms=level_config['latency_ms']
        )
    
    return hierarchy


def get_policy_color(policy_name):
    colors = {
        'FIFO': '#FF6B6B',  # Rojo
        'LRU': '#4ECDC4',   # Turquesa
        'LFU': '#95E1D3',   # Verde agua
    }
    return colors.get(policy_name, '#95A5A6')

# Página Principal

def main():
    # Inicializar estado
    init_session_state()
    
    st.sidebar.title("App") 

    # Header con título y descripción
    st.title("Sistema de Caché Multinivel")
    st.markdown("""
    Bienvenido al simulador interactivo de sistemas de caché multinivel.
    Experimenta con diferentes políticas, configuraciones y patrones de acceso.
    """)
    
    # Línea divisoria
    st.divider()
    
    # Sección de inicio rápido
    st.header("Inicio Rápido")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Políticas Disponibles",
            value="3",
            help="FIFO, LRU, LFU"
        )
    
    with col2:
        st.metric(
            label="Tipos de Workload",
            value="3",
            help="Uniform, Zipfian, Sequential"
        )
    
    with col3:
        st.metric(
            label="Niveles Máximos",
            value="5",
            help="Configurable hasta 5 niveles"
        )
    
    st.divider()
    
    # Información sobre las páginas
    st.header("Páginas Disponibles")
    
    pages_info = [
        {
            "icon": "📊",
            "title": "Overview",
            "description": "Vista general del sistema con métricas clave y configuración básica."
        },
        {
            "icon": "⚡",
            "title": "Simulación",
            "description": "Ejecuta simulaciones con diferentes workloads y visualiza resultados en tiempo real."
        },
        {
            "icon": "🔬",
            "title": "Comparación",
            "description": "Compara diferentes políticas y configuraciones lado a lado."
        }
    ]
    
    for page in pages_info:
        with st.expander(f"{page['icon']} {page['title']}", expanded=False):
            st.markdown(page['description'])
    
    st.divider()
    
    # Guía rápida
    st.header("¿Cómo usar este dashboard?")
    
    st.markdown("""
    1. **Navega** por las diferentes páginas usando la barra lateral izquierda
    2. **Configura** tu jerarquía de caché en la página de Overview
    3. **Ejecuta** simulaciones en la página de Simulación
    4. **Compara** diferentes configuraciones en la página de Comparación
    """)
    
    # Información adicional en sidebar
    with st.sidebar:
        st.header("Información del Sistema")
        
        st.info("""
        **Estado del Sistema:**
        - ✅ Políticas cargadas
        - ✅ Simulador activo
        - ✅ Dashboard operativo
        """)
        
        # Configuración rápida
        st.divider()
        st.subheader("Acceso Rápido")
        
        if st.button("Reiniciar Sistema", use_container_width=True):
            # Limpiar estado de sesión
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        if st.button("Cargar Configuración Default", use_container_width=True):
            init_session_state()
            st.success("✅ Configuración cargada")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>Sistema de Caché Multinivel | Desarrollado con Streamlit</p>
        <p style='font-size: 0.8em;'>
            <a href='https://docs.python.org/3/'>Python</a> | 
            <a href='https://streamlit.io/'>Streamlit</a> | 
            Cache Simulator
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()