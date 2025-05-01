import gradio as gr
from ..utils import (
    upload_files,
    process_presentation_topic,
    process_presentation_style,
    process_color_style,
)


def upload_and_update_list(files, uploaded_list):
    status = upload_files(files)
    new_files = [file.name for file in files if file.name not in uploaded_list]
    updated_list = uploaded_list + new_files
    return status, updated_list, "\n".join(updated_list)


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
            dropdown = gr.Dropdown(
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
            output = gr.Textbox()
            dropdown.change(
                fn=process_presentation_style, inputs=dropdown, outputs=output
            )
            dropdown = gr.Dropdown(
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
            output = gr.Textbox()
            dropdown.change(fn=process_color_style, inputs=dropdown, outputs=output)

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

    upload_button.click(
        fn=upload_and_update_list,
        inputs=[file_input, uploaded_files_state],
        outputs=[upload_output, uploaded_files_state],
    )

    submit_topic_button.click(
        fn=process_presentation_topic, inputs=[topic_input], outputs=[topic_output]
    )
