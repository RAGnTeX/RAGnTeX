# interface/gradio_interface.py

import gradio as gr
from .upload_files import upload_files
from ..services import generate_presentation


def upload_and_update_list(files: list, uploaded_list) -> tuple[str, list[str]]:
    """Helper function to handle uploaded documents and update the list of uploaded files.
    Args:
        files (list): List of file-like objects to be uploaded.
        uploaded_list (list): Current list of uploaded file paths.
    Returns:
        tuple: A 2-element tuple:
            - str: Status message indicating the result of the upload operation.
            - list[str]: Updated list of uploaded file paths."""
    status, new_paths = upload_files(files)
    updated_list = uploaded_list + [p for p in new_paths if p not in uploaded_list]
    return status, updated_list


def generate_iframe(file_path):
    if not file_path:
        return ""
    return (
        f'<embed src="{file_path}" type="application/pdf" width="100%" height="600px">'
    )


with gr.Blocks() as demo:
    gr.Markdown("# 📚 RAGnTeX LaTeX Presentation Generator")

    uploaded_files_state = gr.State([])

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## 📂 Step 1: Upload PDF Documents")
            file_input = gr.File(
                file_types=[".pdf"], file_count="multiple", label="Select PDF Files"
            )
            upload_button = gr.Button("Upload Files")

            gr.Markdown("## 🎨 Step 2: Choose the presentation and color themes")
            presentation_theme_state = gr.State("default")
            theme_dropdown = gr.Dropdown(
                choices=[
                    "default",
                    "Darmstadt",
                    "Malmoe",
                    "AnnArbor",
                    "Dresden",
                    "Marburg",
                    "Antibes",
                    "Frankfurt",
                    "Montpellier",
                    "Bergen",
                    "Goettingen",
                    "PaloAlto",
                    "Berkeley",
                    "Hannover",
                    "Pittsburgh",
                    "Berlin",
                    "Ilmenau",
                    "Rochester",
                    "Boadilla",
                    "JuanLesPins",
                    "Singapore",
                    "CambridgeUS",
                    "Luebeck",
                    "Szeged",
                    "Copenhagen",
                    "Madrid",
                    "Warsaw",
                ],
                value="default",  # default option
                label="Choose a presentation theme",
            )
            # output = gr.Textbox()

            theme_dropdown.change(
                fn=lambda val: val,
                inputs=theme_dropdown,
                outputs=presentation_theme_state,
            )
            color_theme_state = gr.State("default")
            color_dropdown = gr.Dropdown(
                choices=[
                    "default",
                    "albatross",
                    "beetle",
                    "crane",
                    "dolphin",
                    "fly",
                    "lily",
                    "orchid",
                    "rose",
                    "seagull",
                    "seahorse",
                    "sidebartab",
                    "structure",
                    "whale",
                    "wolverine",
                ],
                value="default",  # default option
                label="Choose a color theme",
            )
            # output = gr.Textbox()
            color_dropdown.change(
                fn=lambda val: val,
                inputs=color_dropdown,
                outputs=color_theme_state,
            )

            gr.Markdown("## 🧠 Step 3: Enter Presentation Topic")
            topic_input = gr.Textbox(
                label="Presentation Topic",
                placeholder="e.g., Introduction to Quantum Computing",
                lines=1,
            )
            submit_topic_button = gr.Button("Generate Outline")

        with gr.Column(scale=1):
            gr.Markdown("## 📄 Uploaded Files (from State)")
            upload_output = gr.Textbox(
                label="Upload Status", lines=3, interactive=False
            )

            gr.Markdown("## 📝 Outline or Confirmation")
            topic_output = gr.Textbox(label="Topic Output", lines=6, interactive=False)

            gr.Markdown("## 🎉 Final Presentation")
            pdf_output = gr.File(label="Download/View Presentation")
            pdf_output_viewer = gr.HTML(label="Presentation Preview")

            submit_topic_button.click(
                fn=generate_presentation,
                inputs=[
                    presentation_theme_state,
                    color_theme_state,
                    topic_input,
                    uploaded_files_state,
                ],
                outputs=[topic_output, pdf_output, pdf_output_viewer],
            )

    upload_button.click(
        fn=upload_and_update_list,
        inputs=[file_input, uploaded_files_state],
        outputs=[upload_output, uploaded_files_state],
    )

    pdf_output.change(
        fn=generate_iframe,
        inputs=pdf_output,
        outputs=pdf_output_viewer,
    )
