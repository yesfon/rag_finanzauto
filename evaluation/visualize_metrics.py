import json
import os
import webbrowser
import argparse
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def generate_interactive_report(datasets, output_path):
    """Genera un informe HTML interactivo con Plotly."""
    
    if not datasets:
        return None

    fig = make_subplots(
        rows=len(datasets), 
        cols=1, 
        subplot_titles=[f"Métricas para el Dataset: <b>{name.upper()}</b>" for name in datasets.keys()],
        vertical_spacing=0.15 if len(datasets) > 1 else 0
    )

    color_palette = ['#005f73', '#0a9396', '#94d2bd', '#e9d8a6', '#ee9b00', '#ca6702', '#bb3e03', '#ae2012', '#9b2226']
    
    for i, (name, data) in enumerate(datasets.items()):
        if "summary" in data:
            avg_metrics = data["summary"].get("average_metrics", {})
            metrics_names = list(avg_metrics.keys())
            metrics_values = list(avg_metrics.values())
            
            bar_colors = color_palette[:len(metrics_names)]

            fig.add_trace(
                go.Bar(
                    x=metrics_names,
                    y=metrics_values,
                    text=[f"{v:.4f}" for v in metrics_values],
                    textposition='auto',
                    marker_color=bar_colors,
                    name='Métricas Promedio'
                ),
                row=i + 1,
                col=1
            )
            fig.update_yaxes(title_text="Puntuación", row=i + 1, col=1, range=[0, 1])

    fig.update_layout(
        title_text="📊 Informe Interactivo de Métricas de Evaluación RAG",
        title_x=0.5,
        title_font_size=24,
        font_family="Arial, sans-serif",
        showlegend=False,
        height=400 * len(datasets) + 100,
        margin=dict(t=100, b=80, l=80, r=80),
        plot_bgcolor='rgba(240, 240, 240, 0.95)',
        paper_bgcolor='white',
    )

    fig.write_html(output_path, full_html=True, include_plotlyjs='cdn')
    
    print(f"Informe interactivo generado en: {os.path.abspath(output_path)}")
    return os.path.abspath(output_path)


def find_and_load_results(base_dir):
    """Encuentra y carga los archivos de resultados de la evaluación."""
    datasets = {}
    
    # Asumiendo nombres de archivo fijos basados en el script de evaluación
    dataset_names = ["fiqa", "squad_es"]
    
    for name in dataset_names:
        summary_path = os.path.join(base_dir, f"{name}_results.json")
        
        dataset_data = {}
        if os.path.exists(summary_path):
            with open(summary_path, "r", encoding="utf-8") as f:
                # Cargamos solo el resumen, que es lo que necesitamos para los gráficos
                dataset_data["summary"] = json.load(f)
        else:
            # No imprimimos advertencia si no se encuentra, simplemente no se añade.
            pass

        if dataset_data:
            datasets[name] = dataset_data
            
    return datasets

def main():
    """Función principal para generar y mostrar el informe."""
    parser = argparse.ArgumentParser(description="Genera un informe HTML interactivo con las métricas de evaluación del RAG.")
    parser.add_argument(
        "--dataset", 
        type=str, 
        choices=['fiqa', 'squad_es'], 
        help="Nombre del dataset para mostrar. Si no se especifica, se mostrarán todos."
    )
    args = parser.parse_args()

    # Obtener la ruta del directorio donde se encuentra este script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    all_datasets = find_and_load_results(base_dir=script_dir)
    
    if not all_datasets:
        print("No se encontraron archivos de resultados. Ejecute primero 'evaluate.py'.")
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

    report_path = generate_interactive_report(datasets_to_show, output_path=os.path.join(script_dir, "evaluation_report.html"))
    
    if report_path:
        # Abrir el informe en el navegador
        try:
            webbrowser.open(f"file://{report_path}")
        except Exception as e:
            print(f"No se pudo abrir el informe en el navegador: {e}")
            print("Por favor, abra el siguiente archivo manualmente en su navegador:")
            print(report_path)

if __name__ == "__main__":
    main() 