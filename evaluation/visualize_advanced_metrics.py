import json
import os
import webbrowser
import argparse
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List, Any

def load_advanced_results(base_dir: str) -> Dict[str, Any]:
    """Carga los resultados avanzados de evaluación."""
    datasets = {}
    
    # Buscar archivos de resultados avanzados
    dataset_names = ["fiqa", "squad_es"]
    
    for name in dataset_names:
        advanced_path = os.path.join(base_dir, f"{name}_advanced_results.json")
        
        if os.path.exists(advanced_path):
            with open(advanced_path, "r", encoding="utf-8") as f:
                datasets[name] = json.load(f)
        else:
            print(f"Advertencia: No se encontro el archivo de resultados avanzados para {name}")
    
    return datasets

def create_metrics_comparison_chart(datasets: Dict[str, Any]) -> go.Figure:
    """Crea un gráfico comparativo de métricas con intervalos de confianza."""
    if not datasets:
        return None
    
    # Preparar datos para el gráfico
    metrics_data = []
    
    for dataset_name, data in datasets.items():
        if 'bootstrap_confidence_intervals' not in data:
            continue
            
        for metric_name, stats in data['bootstrap_confidence_intervals'].items():
            metrics_data.append({
                'Dataset': dataset_name.upper(),
                'Metric': metric_name,
                'Mean': stats['mean'],
                'CI_Lower': stats['ci_lower'],
                'CI_Upper': stats['ci_upper'],
                'Std': stats['std']
            })
    
    if not metrics_data:
        return None
    
    df = pd.DataFrame(metrics_data)
    
    # Crear gráfico con barras y intervalos de confianza
    fig = go.Figure()
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, dataset in enumerate(df['Dataset'].unique()):
        dataset_data = df[df['Dataset'] == dataset]
        
        fig.add_trace(go.Bar(
            name=dataset,
            x=dataset_data['Metric'],
            y=dataset_data['Mean'],
            error_y=dict(
                type='data',
                array=dataset_data['Std'],
                visible=True
            ),
            marker_color=colors[i % len(colors)],
            text=[f"{val:.3f}" for val in dataset_data['Mean']],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>' +
                         'Mean: %{y:.4f}<br>' +
                         'Std: %{customdata:.4f}<br>' +
                         'CI: [%{customdata[1]:.4f}, %{customdata[2]:.4f}]<br>' +
                         '<extra></extra>',
            customdata=dataset_data[['Std', 'CI_Lower', 'CI_Upper']].values
        ))
    
    fig.update_layout(
        title="Comparacion de Metricas con Intervalos de Confianza (95%)",
        title_x=0.5,
        title_font_size=20,
        xaxis_title="Metricas",
        yaxis_title="Puntuacion",
        barmode='group',
        height=600,
        showlegend=True,
        font_family="Arial, sans-serif",
        plot_bgcolor='rgba(240, 240, 240, 0.95)',
        paper_bgcolor='white',
    )
    
    return fig

def create_confidence_intervals_chart(datasets: Dict[str, Any]) -> go.Figure:
    """Crea un gráfico específico para intervalos de confianza."""
    if not datasets:
        return None
    
    fig = go.Figure()
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, (dataset_name, data) in enumerate(datasets.items()):
        if 'bootstrap_confidence_intervals' not in data:
            continue
            
        for j, (metric_name, stats) in enumerate(data['bootstrap_confidence_intervals'].items()):
            fig.add_trace(go.Scatter(
                x=[f"{dataset_name.upper()}_{metric_name}"],
                y=[stats['mean']],
                error_y=dict(
                    type='data',
                    array=[stats['mean'] - stats['ci_lower']],
                    arrayminus=[stats['ci_upper'] - stats['mean']],
                    visible=True
                ),
                mode='markers+text',
                name=f"{dataset_name.upper()} - {metric_name}",
                marker=dict(
                    size=10,
                    color=colors[i % len(colors)]
                ),
                text=[f"{stats['mean']:.3f}"],
                textposition='top center',
                hovertemplate='<b>%{x}</b><br>' +
                             'Mean: %{y:.4f}<br>' +
                             'CI: [%{customdata[0]:.4f}, %{customdata[1]:.4f}]<br>' +
                             '<extra></extra>',
                customdata=[[stats['ci_lower'], stats['ci_upper']]]
            ))
    
    fig.update_layout(
        title="Intervalos de Confianza por Metrica y Dataset",
        title_x=0.5,
        title_font_size=20,
        xaxis_title="Dataset_Metrica",
        yaxis_title="Puntuacion",
        height=800,
        showlegend=False,
        font_family="Arial, sans-serif",
        plot_bgcolor='rgba(240, 240, 240, 0.95)',
        paper_bgcolor='white',
    )
    
    return fig

def create_retrieval_metrics_chart(datasets: Dict[str, Any]) -> go.Figure:
    """Crea un gráfico específico para métricas de recuperación."""
    if not datasets:
        return None
    
    fig = go.Figure()
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, (dataset_name, data) in enumerate(datasets.items()):
        if 'summary_statistics' not in data:
            continue
            
        # Extraer métricas de recuperación
        retrieval_metrics = {}
        for metric_name, value in data['summary_statistics']['average_metrics'].items():
            if 'hit_rate_at_' in metric_name:
                retrieval_metrics[metric_name] = value
        
        if retrieval_metrics:
            x_values = list(retrieval_metrics.keys())
            y_values = list(retrieval_metrics.values())
            
            fig.add_trace(go.Scatter(
                x=x_values,
                y=y_values,
                mode='lines+markers',
                name=dataset_name.upper(),
                marker=dict(
                    size=8,
                    color=colors[i % len(colors)]
                ),
                line=dict(width=3),
                hovertemplate='<b>%{x}</b><br>' +
                             'Hit Rate: %{y:.3f}<br>' +
                             '<extra></extra>'
            ))
    
    fig.update_layout(
        title="Metricas de Recuperacion por Dataset",
        title_x=0.5,
        title_font_size=20,
        xaxis_title="K (Numero de resultados)",
        yaxis_title="Hit Rate",
        height=500,
        showlegend=True,
        font_family="Arial, sans-serif",
        plot_bgcolor='rgba(240, 240, 240, 0.95)',
        paper_bgcolor='white',
    )
    
    return fig

def create_performance_dashboard(datasets: Dict[str, Any]) -> go.Figure:
    """Crea un dashboard de rendimiento del sistema."""
    if not datasets:
        return None
    
    # Crear subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "Tiempo de Procesamiento",
            "Chunks Recuperados",
            "Tasa de Éxito de Consultas",
            "Estadísticas Generales"
        ],
        specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "indicator"}, {"type": "table"}]]
    )
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, (dataset_name, data) in enumerate(datasets.items()):
        if 'summary_statistics' not in data:
            continue
            
        stats = data['summary_statistics']['retrieval_statistics']
        
        # Tiempo de procesamiento
        fig.add_trace(
            go.Bar(
                x=[dataset_name.upper()],
                y=[stats.get('avg_processing_time', 0)],
                name=f"Tiempo - {dataset_name.upper()}",
                marker_color=colors[i % len(colors)],
                showlegend=False
            ),
            row=1, col=1
        )
        
        # Chunks recuperados
        fig.add_trace(
            go.Bar(
                x=[dataset_name.upper()],
                y=[stats.get('avg_retrieved_chunks', 0)],
                name=f"Chunks - {dataset_name.upper()}",
                marker_color=colors[i % len(colors)],
                showlegend=False
            ),
            row=1, col=2
        )
        
        # Tasa de éxito
        success_rate = stats.get('successful_queries', 0) / max(stats.get('total_questions', 1), 1)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=success_rate * 100,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"Éxito {dataset_name.upper()}"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': colors[i % len(colors)]},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "gray"},
                        {'range': [80, 100], 'color': "darkgray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ),
            row=2, col=1
        )
    
    # Tabla de estadísticas
    table_data = []
    for dataset_name, data in datasets.items():
        if 'summary_statistics' in data:
            stats = data['summary_statistics']['retrieval_statistics']
            table_data.append([
                dataset_name.upper(),
                stats.get('total_questions', 0),
                stats.get('successful_queries', 0),
                f"{stats.get('avg_processing_time', 0):.3f}s",
                f"{stats.get('avg_retrieved_chunks', 0):.1f}"
            ])
    
    if table_data:
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['Dataset', 'Total Q', 'Éxitos', 'Tiempo Prom', 'Chunks Prom'],
                    fill_color='paleturquoise',
                    align='left'
                ),
                cells=dict(
                    values=list(zip(*table_data)),
                    fill_color='lavender',
                    align='left'
                )
            ),
            row=2, col=2
        )
    
    fig.update_layout(
        title="Dashboard de Rendimiento del Sistema RAG",
        title_x=0.5,
        title_font_size=20,
        height=800,
        showlegend=False,
        font_family="Arial, sans-serif",
        plot_bgcolor='rgba(240, 240, 240, 0.95)',
        paper_bgcolor='white',
    )
    
    return fig

def generate_advanced_report(datasets: Dict[str, Any], output_path: str) -> str:
    """Genera un informe HTML avanzado con múltiples visualizaciones."""
    if not datasets:
        return None
    
    # Crear todas las visualizaciones
    charts = []
    
    # 1. Comparación de métricas
    metrics_chart = create_metrics_comparison_chart(datasets)
    if metrics_chart:
        charts.append(("Comparación de Métricas", metrics_chart))
    
    # 2. Intervalos de confianza
    ci_chart = create_confidence_intervals_chart(datasets)
    if ci_chart:
        charts.append(("Intervalos de Confianza", ci_chart))
    
    # 3. Métricas de recuperación
    retrieval_chart = create_retrieval_metrics_chart(datasets)
    if retrieval_chart:
        charts.append(("Métricas de Recuperación", retrieval_chart))
    
    # 4. Dashboard de rendimiento
    performance_chart = create_performance_dashboard(datasets)
    if performance_chart:
        charts.append(("Dashboard de Rendimiento", performance_chart))
    
    if not charts:
        return None
    
    # Crear HTML con todas las visualizaciones
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Informe Avanzado de Evaluacion RAG</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --primary-color: #2563eb;
                --secondary-color: #64748b;
                --success-color: #10b981;
                --warning-color: #f59e0b;
                --danger-color: #ef4444;
                --background-color: #f8fafc;
                --surface-color: #ffffff;
                --border-color: #e2e8f0;
                --text-primary: #1e293b;
                --text-secondary: #64748b;
                --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
                --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
                --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            }}

            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background-color: var(--background-color);
                color: var(--text-primary);
                line-height: 1.6;
            }}

            .container {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 2rem;
            }}

            .header {{
                background: linear-gradient(135deg, var(--primary-color) 0%, #1d4ed8 100%);
                color: white;
                padding: 3rem 2rem;
                border-radius: 1rem;
                margin-bottom: 2rem;
                text-align: center;
                box-shadow: var(--shadow-lg);
            }}

            .header h1 {{
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
            }}

            .header p {{
                font-size: 1.125rem;
                opacity: 0.9;
                font-weight: 300;
            }}

            .summary-section {{
                background: var(--surface-color);
                border-radius: 1rem;
                padding: 2rem;
                margin-bottom: 2rem;
                box-shadow: var(--shadow-md);
                border: 1px solid var(--border-color);
            }}

            .summary-section h2 {{
                color: var(--text-primary);
                font-size: 1.5rem;
                font-weight: 600;
                margin-bottom: 1.5rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}

            .summary-section h2::before {{
                content: '';
                width: 4px;
                height: 24px;
                background: var(--primary-color);
                border-radius: 2px;
            }}

            .dataset-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1.5rem;
                margin-bottom: 1.5rem;
            }}

            .dataset-card {{
                background: var(--surface-color);
                border: 1px solid var(--border-color);
                border-radius: 0.75rem;
                padding: 1.5rem;
                box-shadow: var(--shadow-sm);
                transition: all 0.2s ease;
            }}

            .dataset-card:hover {{
                transform: translateY(-2px);
                box-shadow: var(--shadow-md);
            }}

            .dataset-card h3 {{
                color: var(--primary-color);
                font-size: 1.25rem;
                font-weight: 600;
                margin-bottom: 1rem;
            }}

            .metric-list {{
                list-style: none;
            }}

            .metric-item {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.5rem 0;
                border-bottom: 1px solid var(--border-color);
            }}

            .metric-item:last-child {{
                border-bottom: none;
            }}

            .metric-label {{
                font-weight: 500;
                color: var(--text-secondary);
            }}

            .metric-value {{
                font-weight: 600;
                color: var(--text-primary);
            }}

            .chart-section {{
                background: var(--surface-color);
                border-radius: 1rem;
                padding: 2rem;
                margin-bottom: 2rem;
                box-shadow: var(--shadow-md);
                border: 1px solid var(--border-color);
            }}

            .chart-title {{
                color: var(--text-primary);
                font-size: 1.25rem;
                font-weight: 600;
                margin-bottom: 1.5rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}

            .chart-title::before {{
                content: '';
                width: 3px;
                height: 20px;
                background: var(--primary-color);
                border-radius: 1.5px;
            }}

            .chart-container {{
                background: var(--surface-color);
                border-radius: 0.5rem;
                overflow: hidden;
            }}

            @media (max-width: 768px) {{
                .container {{
                    padding: 1rem;
                }}

                .header {{
                    padding: 2rem 1rem;
                }}

                .header h1 {{
                    font-size: 2rem;
                }}

                .dataset-grid {{
                    grid-template-columns: 1fr;
                }}
            }}

            .loading {{
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 2rem;
                color: var(--text-secondary);
            }}

            .error {{
                background: #fef2f2;
                border: 1px solid #fecaca;
                color: #dc2626;
                padding: 1rem;
                border-radius: 0.5rem;
                margin: 1rem 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Informe Avanzado de Evaluacion RAG</h1>
                <p>Analisis detallado de metricas con intervalos de confianza</p>
            </div>
            
            <div class="summary-section">
                <h2>Resumen de Datasets Evaluados</h2>
                <div class="dataset-grid">
    """
    
    # Añadir información de cada dataset
    for dataset_name, data in datasets.items():
        if 'summary_statistics' in data:
            stats = data['summary_statistics']['retrieval_statistics']
            html_content += f"""
                    <div class="dataset-card">
                        <h3>{dataset_name.upper()}</h3>
                        <ul class="metric-list">
                            <li class="metric-item">
                                <span class="metric-label">Preguntas evaluadas</span>
                                <span class="metric-value">{stats.get('total_questions', 0)}</span>
                            </li>
                            <li class="metric-item">
                                <span class="metric-label">Consultas exitosas</span>
                                <span class="metric-value">{stats.get('successful_queries', 0)}</span>
                            </li>
                            <li class="metric-item">
                                <span class="metric-label">Tiempo promedio</span>
                                <span class="metric-value">{stats.get('avg_processing_time', 0):.3f}s</span>
                            </li>
                            <li class="metric-item">
                                <span class="metric-label">Chunks recuperados</span>
                                <span class="metric-value">{stats.get('avg_retrieved_chunks', 0):.1f}</span>
                            </li>
                        </ul>
                    </div>
            """
    
    html_content += """
                </div>
            </div>
    """
    
    # Añadir cada gráfico
    for chart_title, chart in charts:
        html_content += f"""
            <div class="chart-section">
                <div class="chart-title">{chart_title}</div>
                <div class="chart-container">
                    {chart.to_html(full_html=False, include_plotlyjs='cdn')}
                </div>
            </div>
        """
    
    html_content += """
        </div>
        
        <script>
            // Funcionalidad adicional para mejorar la experiencia de usuario
            document.addEventListener('DOMContentLoaded', function() {
                // Animación suave al hacer scroll
                const observerOptions = {
                    threshold: 0.1,
                    rootMargin: '0px 0px -50px 0px'
                };
                
                const observer = new IntersectionObserver(function(entries) {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            entry.target.style.opacity = '1';
                            entry.target.style.transform = 'translateY(0)';
                        }
                    });
                }, observerOptions);
                
                // Aplicar animación a las secciones
                document.querySelectorAll('.chart-section, .dataset-card').forEach(el => {
                    el.style.opacity = '0';
                    el.style.transform = 'translateY(20px)';
                    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                    observer.observe(el);
                });
                
                // Mejorar la interactividad de las tarjetas
                document.querySelectorAll('.dataset-card').forEach(card => {
                    card.addEventListener('mouseenter', function() {
                        this.style.transform = 'translateY(-4px) scale(1.02)';
                    });
                    
                    card.addEventListener('mouseleave', function() {
                        this.style.transform = 'translateY(0) scale(1)';
                    });
                });
                
                // Función para exportar datos
                window.exportData = function() {
                    const data = {
                        timestamp: new Date().toISOString(),
                        datasets: {}
                    };
                    
                    // Recopilar datos de las tarjetas
                    document.querySelectorAll('.dataset-card').forEach(card => {
                        const datasetName = card.querySelector('h3').textContent;
                        const metrics = {};
                        
                        card.querySelectorAll('.metric-item').forEach(item => {
                            const label = item.querySelector('.metric-label').textContent;
                            const value = item.querySelector('.metric-value').textContent;
                            metrics[label] = value;
                        });
                        
                        data.datasets[datasetName] = metrics;
                    });
                    
                    // Crear y descargar archivo JSON
                    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'rag_evaluation_data.json';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                };
            });
        </script>
    </body>
    </html>
    """
    
    # Guardar el archivo HTML
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Informe avanzado generado en: {os.path.abspath(output_path)}")
    return os.path.abspath(output_path)

def main():
    """Función principal para generar el informe avanzado."""
    parser = argparse.ArgumentParser(description="Genera un informe HTML avanzado con métricas de evaluación del RAG.")
    parser.add_argument(
        "--dataset", 
        type=str, 
        choices=['fiqa', 'squad_es'], 
        help="Nombre del dataset para mostrar. Si no se especifica, se mostrarán todos."
    )
    args = parser.parse_args()

    # Obtener la ruta del directorio donde se encuentra este script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Cargar resultados avanzados
    all_datasets = load_advanced_results(base_dir=script_dir)
    
    if not all_datasets:
        print("Error: No se encontraron archivos de resultados avanzados.")
        print("Ejecute primero 'evaluate_advanced.py' para generar los resultados.")
        return

    # Filtrar el dataset si se ha especificado
    if args.dataset:
        if args.dataset in all_datasets:
            datasets_to_show = {args.dataset: all_datasets[args.dataset]}
        else:
            print(f"Error: No se encontraron resultados para el dataset '{args.dataset}'.")
            return
    else:
        datasets_to_show = all_datasets

    # Generar informe avanzado
    report_path = generate_advanced_report(
        datasets_to_show, 
        output_path=os.path.join(script_dir, "advanced_evaluation_report.html")
    )
    
    if report_path:
        # Abrir el informe en el navegador
        try:
            webbrowser.open(f"file://{report_path}")
        except Exception as e:
            print(f"Advertencia: No se pudo abrir el informe en el navegador: {e}")
            print("Por favor, abra el siguiente archivo manualmente en su navegador:")
            print(report_path)
    else:
        print("Error: No se pudo generar el informe avanzado")

if __name__ == "__main__":
    main() 