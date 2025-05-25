"""Module for compiling LaTeX presentations into PDF format."""

import os
import subprocess
from ..telemetry import Logger, traced_block

LOGGER = Logger.get_logger()


def compile_presentation(latex_code, work_dir) -> None:
    """Compile LaTeX code into a PDF presentation.
    Args:
        latex_code (str): LaTeX code to be compiled.
        work_dir (str): Directory where the LaTeX file will be saved and compiled.
    """
    LOGGER.info("Compiling presentation...")
    # Remove possible Markdown wrapping around the output
    if latex_code.startswith("```latex"):
        latex_code = latex_code.split("\n", 1)[1]  # Remove the first line
    if latex_code.endswith("```"):
        latex_code = latex_code.rsplit("\n", 1)[0]

    # Save LaTeX code to file
    tex_file = os.path.join(work_dir, "presentation.tex")
    with open(tex_file, "w") as f:
        f.write(latex_code)

    LOGGER.info("📄 Files in the directory: %s", work_dir)

    # List files in the directory using Python (instead of `!ls`)
    for file in os.listdir(work_dir):
        LOGGER.info(file)

    # Compile with pdflatex (using subprocess instead of `!`)
    os.chdir(work_dir)  # Change working directory

    with traced_block("🧱 compile_presentation") as span:
        try:
            # Run pdflatex twice to ensure proper slide enumeration
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "presentation.tex"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "presentation.tex"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        except subprocess.CalledProcessError as e:
            # Handle error in case of failed LaTeX compilation
            span.set_attribute("pdf.success", False)
            span.set_attribute("pdf.error_log", e.stderr.decode())
            span.record_exception(e)
            LOGGER.error(
                "❌ PDF generation failed. Here's the log: %s", e.stderr.decode()
            )
        else:
            # Check for PDF output
            if not os.path.exists("presentation.pdf"):
                span.set_attribute("pdf.success", False)
                LOGGER.error("❌ PDF generation failed. No PDF file found.")
            else:
                span.set_attribute("pdf.success", True)
                LOGGER.info("💾 PDF generated successfully in: %s", work_dir)
