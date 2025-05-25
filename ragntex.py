"""RAGnTex: A Retrieval-Augmented Generation for LaTeX Documents"""

from src import demo, init_telemetry

# Setup OpenTelemetry
init_telemetry()
# Run Gradio
demo.launch()
