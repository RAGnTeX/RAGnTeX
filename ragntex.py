"""RAGnTex: A Retrieval-Augmented Generation for LaTeX Documents"""

import os

from src import demo, init_telemetry

# Setup OpenTelemetry
_ = init_telemetry()
# Run Gradio
if os.getenv("IN_DOCKER") == "true":
    demo.launch(
        server_name="0.0.0.0",  # nosec: intentional bind all interfaces for HuggingFace Spaces
        server_port=7860,
    )
else:
    demo.launch()
