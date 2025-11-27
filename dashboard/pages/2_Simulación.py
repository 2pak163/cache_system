import streamlit as st
import sys
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from cache_system.core import LRUCache, LFUCache, FIFOCache
from cache_system.multilevel import CacheHierarchy
from cache_system.simulator import (
    UniformWorkload,
    ZipfianWorkload,
    SequentialWorkload,
    create_workload
)

# Configuración de Página

st.set_page_config(
    page_title="Simulación - Cache System",
    page_icon="⚡",
    layout="wide"
)

# Funciones Auxiliares

def create_hierarchy_from_config(config):
    #Crea jerarquía a partir de configuración.
    hierarchy = CacheHierarchy(name="SimulationCache")
    
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


def run_simulation(hierarchy, workload):

    # Reiniciar estadísticas
    hierarchy.reset_stats()
    
    # Generar operaciones
    operations = workload.generate()
    
    # Ejecutar operaciones con progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_ops = len(operations)
    for i, (op_type, key, value) in enumerate(operations):
        if op_type == 'get':
            hierarchy.get(key)
        else:
            hierarchy.put(key, value)
        
        # Actualizar cada 10%
        if i % max(1, total_ops // 10) == 0:
            progress = (i + 1) / total_ops
            progress_bar.progress(progress)
            status_text.text(f"Ejecutando: {i+1}/{total_ops} operaciones ({progress:.0%})")
    
    progress_bar.progress(1.0)
    status_text.text(f"✅ Completado: {total_ops} operaciones")
    
    # Obtener estadísticas finales
    stats = hierarchy.get_all_stats()
    
    return {
        'stats': stats,
        'num_operations': total_ops,
        'workload_stats': workload.get_stats()
    }


def create_hit_rate_chart(stats):
    #Crea gráfico de hit rates por nivel.
    levels_data = []
    
    for level_stats in stats['levels']:
        levels_data.append({
            'Nivel': level_stats['name'],
            'Hit Rate': level_stats['hit_rate'] * 100,
            'Hits': level_stats['hits']
        })
    
    df = pd.DataFrame(levels_data)
    
    fig = px.bar(
        df,
        x='Nivel',
        y='Hit Rate',
        title='Hit Rate por Nivel (%)',
        labels={'Hit Rate': 'Hit Rate (%)'},
        color='Hit Rate',
        color_continuous_scale='Blues',
        text='Hit Rate'
    )
    
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(showlegend=False, height=400)
    
    return fig


def create_latency_chart(stats):
    #Crea gráfico de latencias por nivel.
    levels_data = []
    
    for level_stats in stats['levels']:
        if level_stats['avg_latency_ms'] > 0:
            levels_data.append({
                'Nivel': level_stats['name'],
                'Latencia Promedio (ms)': level_stats['avg_latency_ms'],
                'Accesos': level_stats['hits'] + level_stats['misses']
            })
    
    if not levels_data:
        return None
    
    df = pd.DataFrame(levels_data)
    
    fig = px.bar(
        df,
        x='Nivel',
        y='Latencia Promedio (ms)',
        title='Latencia Promedio por Nivel',
        color='Latencia Promedio (ms)',
        color_continuous_scale='Reds',
        text='Latencia Promedio (ms)'
    )
    
    fig.update_traces(texttemplate='%{text:.2f}ms', textposition='outside')
    fig.update_layout(showlegend=False, height=400)
    
    return fig


def create_distribution_chart(stats):
    #Crea gráfico de distribución de hits por nivel.
    global_stats = stats['global']
    total_hits = global_stats['total_hits']
    
    if total_hits == 0:
        return None
    
    levels_data = []
    
    for level_stats in stats['levels']:
        contribution = (level_stats['hits'] / total_hits * 100) if total_hits > 0 else 0
        levels_data.append({
            'Nivel': level_stats['name'],
            'Contribución (%)': contribution,
            'Hits': level_stats['hits']
        })
    
    df = pd.DataFrame(levels_data)
    
    fig = px.pie(
        df,
        values='Contribución (%)',
        names='Nivel',
        title='Distribución de Hits por Nivel',
        hole=0.4
    )
    
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(height=400)
    
    return fig

# Página Principal

def main():
    st.title("Simulación de Workloads")
    st.markdown("Ejecuta simulaciones con diferentes patrones de acceso y analiza los resultados.")
    
    # Verificar que exista jerarquía configurada
    if 'hierarchy_config' not in st.session_state:
        st.warning("No hay jerarquía configurada. Ve a la página de Overview para configurar una.")
        return
    
    st.divider()
    
    # Layout en dos columnas
    col_config, col_results = st.columns([1, 2])
    
    # Columna Izquierda: Configuración de Simulación
    
    with col_config:
        st.header("Configuración")
        
        # Tipo de workload
        st.subheader("Patrón de Acceso")
        
        workload_type = st.selectbox(
            "Tipo de Workload",
            options=['Zipfian (80/20)', 'Sequential', 'Uniform'],
            help="Patrón de acceso a simular"
        )
        
        # Mapear nombre amigable a nombre interno
        workload_map = {
            'Zipfian (80/20)': 'zipfian',
            'Sequential': 'sequential',
            'Uniform': 'uniform'
        }
        workload_internal = workload_map[workload_type]
        
        st.divider()
        
        # Parámetros del workload
        st.subheader("Parámetros")
        
        num_keys = st.slider(
            "Número de Claves Únicas",
            min_value=10,
            max_value=100000,
            value=100,
            step=100,
            help="Cuántas claves diferentes en el workload"
        )
        
        num_operations = st.slider(
            "Número de Operaciones",
            min_value=100,
            max_value=1000000,
            value=1000,
            step=100,
            help="Cuántas operaciones ejecutar"
        )
        
        read_ratio = st.slider(
            "Proporción de Lecturas",
            min_value=0.0,
            max_value=1.0,
            value=0.8,
            step=0.05,
            help="Porcentaje de operaciones GET vs PUT"
        )
        
        # Parámetros específicos por tipo
        if workload_internal == 'zipfian':
            st.divider()
            theta = st.slider(
                "Parámetro Theta (sesgo)",
                min_value=0.0,
                max_value=2.0,
                value=0.99,
                step=0.01,
                help="Mayor valor = más sesgado (más 80/20)"
            )
        elif workload_internal == 'sequential':
            st.divider()
            num_passes = st.number_input(
                "Número de Pasadas",
                min_value=1,
                max_value=100,
                value=1,
                help="Cuántas veces recorrer la secuencia"
            )
        
        # Botón de simulación
        st.divider()
        
        if st.button("Ejecutar Simulación", type="primary", use_container_width=True):
            # Crear jerarquía
            try:
                hierarchy = create_hierarchy_from_config(st.session_state.hierarchy_config)
                
                # Crear workload
                workload_kwargs = {
                    'num_keys': num_keys,
                    'num_operations': num_operations,
                    'read_ratio': read_ratio
                }
                
                if workload_internal == 'zipfian':
                    workload_kwargs['theta'] = theta
                elif workload_internal == 'sequential':
                    workload_kwargs['num_passes'] = num_passes
                
                workload = create_workload(workload_internal, **workload_kwargs)
                
                # Ejecutar simulación
                with st.spinner("Ejecutando simulación..."):
                    results = run_simulation(hierarchy, workload)
                
                # Guardar resultados en sesión
                st.session_state['last_simulation'] = results
                st.session_state['last_hierarchy'] = hierarchy
                
                st.success("✅ Simulación completada exitosamente!")
                
            except Exception as e:
                st.error(f"❌ Error en la simulación: {str(e)}")
    
    # Columna Derecha: Resultados
    
    with col_results:
        st.header("Resultados")
        
        if 'last_simulation' in st.session_state:
            results = st.session_state['last_simulation']
            stats = results['stats']
            global_stats = stats['global']
            
            # Métricas principales
            st.subheader("Métricas Principales")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Hit Rate Global",
                    f"{global_stats['global_hit_rate']:.1%}",
                    help="Porcentaje de accesos exitosos"
                )
            
            with col2:
                st.metric(
                    "Operaciones",
                    f"{global_stats['total_accesses']:,}",
                    help="Total de operaciones ejecutadas"
                )
            
            with col3:
                st.metric(
                    "Latencia Promedio",
                    f"{global_stats['avg_latency_ms']:.2f}ms",
                    help="Tiempo promedio por operación"
                )
            
            with col4:
                st.metric(
                    "Promociones",
                    f"{global_stats['total_promotions']:,}",
                    help="Elementos promovidos entre niveles"
                )
            
            st.divider()
            
            # Gráficos
            st.subheader("Visualizaciones")
            
            tab1, tab2, tab3 = st.tabs(["Hit Rates", "Latencias", "Distribución"])
            
            with tab1:
                fig_hits = create_hit_rate_chart(stats)
                st.plotly_chart(fig_hits, use_container_width=True)
            
            with tab2:
                fig_latency = create_latency_chart(stats)
                if fig_latency:
                    st.plotly_chart(fig_latency, use_container_width=True)
                else:
                    st.info("No hay datos de latencia disponibles")
            
            with tab3:
                fig_dist = create_distribution_chart(stats)
                if fig_dist:
                    st.plotly_chart(fig_dist, use_container_width=True)
                else:
                    st.info("No hay hits para mostrar distribución")
            
            # Tabla detallada por nivel
            st.divider()
            st.subheader("Detalles por Nivel")
            
            level_details = []
            for level_stats in stats['levels']:
                level_details.append({
                    'Nivel': level_stats['name'],
                    'Hits': level_stats['hits'],
                    'Misses': level_stats['misses'],
                    'Hit Rate': f"{level_stats['hit_rate']:.2%}",
                    'Promociones': level_stats['promotions'],
                    'Latencia Prom.': f"{level_stats['avg_latency_ms']:.2f}ms"
                })
            
            df_levels = pd.DataFrame(level_details)
            st.dataframe(df_levels, use_container_width=True, hide_index=True)
            
        else:
            st.info("Ejecuta una simulación para ver los resultados aquí.")
            
            # Mostrar configuración actual
            st.subheader("Configuración Actual")
            
            for level in st.session_state.hierarchy_config['levels']:
                st.markdown(f"**{level['name']}**: {level['policy']} "
                          f"(Cap: {level['capacity']}, Lat: {level['latency_ms']}ms)")
    
    # Información en sidebar
    with st.sidebar:
        st.header("Guía de Workloads")
        
        with st.expander("Zipfian (80/20)"):
            st.markdown("""
            **Más Realista**
            
            Simula el principio de Pareto:
            - 20% de las claves reciben 80% de accesos
            - Algunas claves son "calientes"
            - Otras claves son "frías"
            
            **Mejor para:**
            - Cachés web
            - Bases de datos
            - Sistemas con datos populares
            """)
        
        with st.expander("Sequential"):
            st.markdown("""
            **Acceso Ordenado**
            
            Accede a claves en orden:
            - Alta predictibilidad
            - Buena localidad espacial
            - Ideal para escaneos
            
            **Mejor para:**
            - Lectura de archivos
            - Escaneos de tablas
            - Procesamiento batch
            """)
        
        with st.expander("Uniform"):
            st.markdown("""
            **Aleatorio**
            
            Todas las claves igual probabilidad:
            - No hay patrón
            - Peor caso para cachés
            - Baseline para comparaciones
            
            **Mejor para:**
            - Testing de peor caso
            - Comparaciones base
            """)


if __name__ == "__main__":
    main()