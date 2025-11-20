import streamlit as st
import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from cache_system.core import LRUCache, LFUCache, FIFOCache
from cache_system.multilevel import CacheHierarchy


# Configuración de Página

st.set_page_config(
    page_title="Overview - Cache System",
    page_icon="📊",
    layout="wide"
)

# Funciones Auxiliares

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


def render_level_config(level_idx, level_config):
    with st.expander(f"{level_config['name']}", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            policy = st.selectbox(
                "Política",
                options=['FIFO', 'LRU', 'LFU'],
                index=['FIFO', 'LRU', 'LFU'].index(level_config['policy']),
                key=f"policy_{level_idx}",
                help="Política de reemplazo para este nivel"
            )
            
            capacity = st.number_input(
                "Capacidad",
                min_value=1,
                max_value=100000,
                value=level_config['capacity'],
                key=f"capacity_{level_idx}",
                help="Número máximo de elementos"
            )
        
        with col2:
            name = st.text_input(
                "Nombre",
                value=level_config['name'],
                key=f"name_{level_idx}",
                help="Nombre identificador del nivel"
            )
            
            latency = st.number_input(
                "Latencia (ms)",
                min_value=0.001,
                max_value=10000.0,
                value=float(level_config['latency_ms']),
                format="%.3f",
                key=f"latency_{level_idx}",
                help="Latencia simulada en milisegundos"
            )
        
        # Botón para eliminar nivel (solo si hay más de 1)
        if len(st.session_state.hierarchy_config['levels']) > 1:
            if st.button(f"Eliminar {level_config['name']}", key=f"delete_{level_idx}"):
                return None  
        
        return {
            'policy': policy,
            'capacity': capacity,
            'name': name,
            'latency_ms': latency
        }

# Página Principal

def main():
    st.title("Overview del Sistema")
    st.markdown("Configura y visualiza tu jerarquía de caché multinivel.")
    
    # Inicializar estado si no existe
    if 'hierarchy_config' not in st.session_state:
        st.session_state.hierarchy_config = {
            'levels': [
                {'policy': 'LRU', 'capacity': 10, 'name': 'L1', 'latency_ms': 1},
                {'policy': 'LRU', 'capacity': 100, 'name': 'L2', 'latency_ms': 10},
                {'policy': 'LFU', 'capacity': 1000, 'name': 'L3', 'latency_ms': 50},
            ]
        }
    
    st.divider()
    
    # Layout en dos columnas
    col_left, col_right = st.columns([1, 1])
    
    # Columna Izquierda: Configuración
    
    with col_left:
        st.header("Configuración de Jerarquía")
        
        # Configuración de cada nivel
        updated_levels = []
        for idx, level_config in enumerate(st.session_state.hierarchy_config['levels']):
            updated_level = render_level_config(idx, level_config)
            if updated_level is not None:
                updated_levels.append(updated_level)
        
        # Actualizar configuración
        st.session_state.hierarchy_config['levels'] = updated_levels
        
        # Botón para agregar nivel
        st.divider()
        if len(updated_levels) < 5:  # Límite de 5 niveles
            if st.button("Agregar Nivel", use_container_width=True):
                new_level = {
                    'policy': 'LRU',
                    'capacity': 100,
                    'name': f'L{len(updated_levels) + 1}',
                    'latency_ms': 10.0 * (len(updated_levels) + 1)
                }
                st.session_state.hierarchy_config['levels'].append(new_level)
                st.rerun()
        else:
            st.info("ℹMáximo 5 niveles permitidos")
        
        # Botones de acción
        st.divider()
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("Aplicar Configuración", type="primary", use_container_width=True):
                try:
                    # Crear nueva jerarquía
                    hierarchy = create_hierarchy_from_config(st.session_state.hierarchy_config)
                    st.session_state.hierarchy = hierarchy
                    st.success("Configuración aplicada correctamente")
                except Exception as e:
                    st.error(f"Error al crear jerarquía: {str(e)}")
        
        with col_btn2:
            if st.button("Resetear", use_container_width=True):
                st.session_state.hierarchy_config = {
                    'levels': [
                        {'policy': 'LRU', 'capacity': 10, 'name': 'L1', 'latency_ms': 1},
                        {'policy': 'LRU', 'capacity': 100, 'name': 'L2', 'latency_ms': 10},
                        {'policy': 'LFU', 'capacity': 1000, 'name': 'L3', 'latency_ms': 50},
                    ]
                }
                st.rerun()
    
    # Columna Derecha: Visualización
    
    with col_right:
        st.header("Estado del Sistema")
        
        # Si hay jerarquía activa, mostrar información
        if st.session_state.get('hierarchy'):
            hierarchy = st.session_state.hierarchy
            
            # Métricas generales
            st.subheader("Métricas Generales")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Niveles",
                    hierarchy.num_levels,
                    help="Número de niveles en la jerarquía"
                )
            
            with col2:
                st.metric(
                    "Capacidad Total",
                    f"{hierarchy.total_capacity:,}",
                    help="Suma de capacidades de todos los niveles"
                )
            
            with col3:
                st.metric(
                    "Elementos Totales",
                    f"{hierarchy.total_size:,}",
                    help="Elementos actualmente almacenados"
                )
            
            # Detalles de niveles
            st.divider()
            st.subheader("Detalles por Nivel")
            
            details = hierarchy.get_level_details()
            
            for detail in details:
                with st.container():
                    # Encabezado del nivel
                    col_name, col_policy = st.columns([2, 1])
                    
                    with col_name:
                        st.markdown(f"### {detail['name']}")
                    
                    with col_policy:
                        policy_color = {
                            'FIFOCache': '🔴',
                            'LRUCache': '🔵',
                            'LFUCache': '🟢'
                        }
                        st.markdown(f"{policy_color.get(detail['policy'], '⚪')} **{detail['policy']}**")
                    
                    # Métricas del nivel
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Capacidad", detail['capacity'])
                    
                    with col2:
                        st.metric("Uso", detail['current_size'])
                    
                    with col3:
                        utilization_pct = detail['utilization'] * 100
                        st.metric("Utilización", f"{utilization_pct:.1f}%")
                    
                    with col4:
                        st.metric("Latencia", f"{detail['latency_ms']}ms")
                    
                    # Barra de progreso de utilización
                    st.progress(detail['utilization'])
                    
                    st.divider()
            
            # Estadísticas de rendimiento
            stats = hierarchy.get_all_stats()
            global_stats = stats['global']
            
            if global_stats['total_accesses'] > 0:
                st.subheader("Estadísticas de Rendimiento")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Hit Rate Global",
                        f"{global_stats['global_hit_rate']:.2%}",
                        help="Porcentaje de accesos exitosos"
                    )
                
                with col2:
                    st.metric(
                        "Latencia Promedio",
                        f"{global_stats['avg_latency_ms']:.2f}ms",
                        help="Latencia promedio por acceso"
                    )
                
                with col3:
                    st.metric(
                        "Total Promociones",
                        f"{global_stats['total_promotions']:,}",
                        help="Elementos promovidos entre niveles"
                    )
        
        else:
            # Mostrar mensaje si no hay jerarquía
            st.info("Configura y aplica una jerarquía en el panel izquierdo para ver las métricas.")
            
            # Vista previa de configuración
            st.subheader("Configuración Actual")
            
            for level in st.session_state.hierarchy_config['levels']:
                with st.container():
                    st.markdown(f"**{level['name']}**: {level['policy']} | "
                              f"Capacidad: {level['capacity']} | "
                              f"Latencia: {level['latency_ms']}ms")
    
    # Información adicional en la barra lateral
    with st.sidebar:
        st.header("Ayuda")
        
        with st.expander("Políticas de Caché"):
            st.markdown("""
            **FIFO** (First-In-First-Out):
            - Desaloja el elemento más antiguo
            - Simple y predecible
            - Mejor para: patrones secuenciales
            
            **LRU** (Least Recently Used):
            - Desaloja el menos recientemente usado
            - Se adapta a patrones temporales
            - Mejor para: datos con localidad temporal
            
            **LFU** (Least Frequently Used):
            - Desaloja el menos frecuentemente usado
            - Protege elementos populares
            - Mejor para: datos con popularidad estable
            """)
        
        with st.expander("Configuración de Latencia"):
            st.markdown("""
            **Latencias Típicas:**
            - L1 (RAM): 0.1 - 1 ms
            - L2 (SSD): 1 - 10 ms
            - L3 (HDD): 10 - 100 ms
            - L4 (Red): 50 - 500 ms
            
            La latencia simula el tiempo de acceso
            real al hardware correspondiente.
            """)


if __name__ == "__main__":
    main()