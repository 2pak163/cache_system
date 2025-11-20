import streamlit as st
import sys
from pathlib import Path
import plotly.graph_objects as go
import pandas as pd

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from cache_system.core import LRUCache, LFUCache, FIFOCache
from cache_system.multilevel import CacheHierarchy
from cache_system.simulator import create_workload

# Configuración

st.set_page_config(
    page_title="Comparación - Cache System",
    page_icon="🔬",
    layout="wide"
)

# Funciones

def run_comparison(configs, workload_config):
    #Ejecuta comparación de múltiples configuraciones.
    results = []
    
    for i, config in enumerate(configs):
        # Crear jerarquía
        hierarchy = CacheHierarchy(name=f"Config{i+1}")
        
        policy_classes = {
            'FIFO': FIFOCache,
            'LRU': LRUCache,
            'LFU': LFUCache
        }
        
        for level_cfg in config['levels']:
            policy_class = policy_classes[level_cfg['policy']]
            cache = policy_class(capacity=level_cfg['capacity'])
            hierarchy.add_level(
                cache=cache,
                name=level_cfg['name'],
                latency_ms=level_cfg['latency_ms']
            )
        
        # Crear y ejecutar workload
        workload = create_workload(**workload_config)
        
        hierarchy.reset_stats()
        operations = workload.generate()
        
        for op_type, key, value in operations:
            if op_type == 'get':
                hierarchy.get(key)
            else:
                hierarchy.put(key, value)
        
        stats = hierarchy.get_all_stats()
        results.append({
            'name': config['name'],
            'stats': stats
        })
    
    return results

# Página Principal

def main():
    st.title("Comparación de Políticas")
    st.markdown("Compara diferentes configuraciones lado a lado.")
    
    st.divider()
    
    # Configuración de comparación
    st.header("Configurar Comparación")
    
    comparison_type = st.selectbox(
        "Tipo de Comparación",
        ["Políticas en L1", "Todo LRU vs Todo LFU vs Mixto"],
        help="Qué aspectos comparar"
    )
    
    # Workload común
    col1, col2, col3 = st.columns(3)
    
    with col1:
        workload_type = st.selectbox(
            "Workload",
            ['zipfian', 'sequential', 'uniform']
        )
    
    with col2:
        num_keys = st.number_input(
            "Claves",
            min_value=50,
            max_value=1000,
            value=100
        )
    
    with col3:
        num_ops = st.number_input(
            "Operaciones",
            min_value=500,
            max_value=10000,
            value=2000
        )
    
    if st.button("Ejecutar Comparación", type="primary"):
        with st.spinner("Ejecutando comparación..."):
            # Configuraciones predefinidas
            if comparison_type == "Políticas en L1":
                configs = [
                    {
                        'name': 'FIFO en L1',
                        'levels': [
                            {'policy': 'FIFO', 'capacity': 50, 'name': 'L1', 'latency_ms': 1},
                            {'policy': 'LRU', 'capacity': 200, 'name': 'L2', 'latency_ms': 10}
                        ]
                    },
                    {
                        'name': 'LRU en L1',
                        'levels': [
                            {'policy': 'LRU', 'capacity': 50, 'name': 'L1', 'latency_ms': 1},
                            {'policy': 'LRU', 'capacity': 200, 'name': 'L2', 'latency_ms': 10}
                        ]
                    },
                    {
                        'name': 'LFU en L1',
                        'levels': [
                            {'policy': 'LFU', 'capacity': 50, 'name': 'L1', 'latency_ms': 1},
                            {'policy': 'LRU', 'capacity': 200, 'name': 'L2', 'latency_ms': 10}
                        ]
                    }
                ]
            else:
                configs = [
                    {
                        'name': 'Todo LRU',
                        'levels': [
                            {'policy': 'LRU', 'capacity': 50, 'name': 'L1', 'latency_ms': 1},
                            {'policy': 'LRU', 'capacity': 200, 'name': 'L2', 'latency_ms': 10},
                            {'policy': 'LRU', 'capacity': 1000, 'name': 'L3', 'latency_ms': 50}
                        ]
                    },
                    {
                        'name': 'Todo LFU',
                        'levels': [
                            {'policy': 'LFU', 'capacity': 50, 'name': 'L1', 'latency_ms': 1},
                            {'policy': 'LFU', 'capacity': 200, 'name': 'L2', 'latency_ms': 10},
                            {'policy': 'LFU', 'capacity': 1000, 'name': 'L3', 'latency_ms': 50}
                        ]
                    },
                    {
                        'name': 'Mixto (LRU+LFU)',
                        'levels': [
                            {'policy': 'LRU', 'capacity': 50, 'name': 'L1', 'latency_ms': 1},
                            {'policy': 'LRU', 'capacity': 200, 'name': 'L2', 'latency_ms': 10},
                            {'policy': 'LFU', 'capacity': 1000, 'name': 'L3', 'latency_ms': 50}
                        ]
                    }
                ]
            
            workload_config = {
                'workload_type': workload_type,
                'num_keys': num_keys,
                'num_operations': num_ops,
                'read_ratio': 0.8
            }
            
            results = run_comparison(configs, workload_config)
            st.session_state['comparison_results'] = results
            
            st.success("Comparación completada!")
    
    # Mostrar resultados
    st.divider()
    
    if 'comparison_results' in st.session_state:
        results = st.session_state['comparison_results']
        
        st.header("Resultados de Comparación")
        
        # Tabla comparativa
        comparison_data = []
        for result in results:
            global_stats = result['stats']['global']
            comparison_data.append({
                'Configuración': result['name'],
                'Hit Rate': f"{global_stats['global_hit_rate']:.2%}",
                'Latencia Prom (ms)': f"{global_stats['avg_latency_ms']:.2f}",
                'Promociones': global_stats['total_promotions'],
                'Total Hits': global_stats['total_hits']
            })
        
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, use_container_width=True, hide_index=True)
        
        # Gráfico comparativo
        st.subheader("Visualización Comparativa")
        
        fig = go.Figure()
        
        names = [r['name'] for r in results]
        hit_rates = [r['stats']['global']['global_hit_rate'] * 100 for r in results]
        latencies = [r['stats']['global']['avg_latency_ms'] for r in results]
        
        fig.add_trace(go.Bar(
            name='Hit Rate (%)',
            x=names,
            y=hit_rates,
            yaxis='y',
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='Latencia (ms)',
            x=names,
            y=latencies,
            yaxis='y2',
            marker_color='lightcoral'
        ))
        
        fig.update_layout(
            title='Comparación de Hit Rate y Latencia',
            yaxis=dict(title='Hit Rate (%)', side='left'),
            yaxis2=dict(title='Latencia (ms)', overlaying='y', side='right'),
            barmode='group',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Conclusiones automáticas
        st.subheader("Análisis Automático")
        
        # Mejor hit rate
        best_hit_rate = max(results, key=lambda x: x['stats']['global']['global_hit_rate'])
        st.success(f"Mejor Hit Rate: **{best_hit_rate['name']}** con "
                  f"{best_hit_rate['stats']['global']['global_hit_rate']:.2%}")
        
        # Mejor latencia
        best_latency = min(results, key=lambda x: x['stats']['global']['avg_latency_ms'])
        st.success(f"Menor Latencia: **{best_latency['name']}** con "
                  f"{best_latency['stats']['global']['avg_latency_ms']:.2f}ms")
    
    else:
        st.info("Configura y ejecuta una comparación para ver los resultados.")


if __name__ == "__main__":
    main()