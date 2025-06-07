# interface/gradio_interface.py

import gradio as gr
from .upload_files import upload_files
from ..services import generate_presentation
import base64


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
    else:
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")
        # pdf_display = f'''
        #     <div style="position:relative; width:100%; padding-top:76.5%;">
        #     <iframe src="data:application/pdf;base64,{base64_pdf}#view=FitH" 
        #     style="position:absolute; top:0; left:0; width:100%; height:100%; border:none;">
        #     </iframe></div>
        # '''
        pdf_display = f'<iframe width="100%" height="auto" src="data:application/pdf;base64,{base64_pdf}"></iframe>'
    return pdf_display


theme = gr.themes.Monochrome(
    neutral_hue=gr.themes.Color(c50="#f8f4fe",  c100="#ede9fe", c200="#ddd6fe", c300="#c4b5fd",
                                c400="#a78bfa", c500="#8b5cf6", c600="#7c3aed", c700="#6d28d9",
                                c800="#5b21b6", c900="#4c1d95", c950="#181e44"),
).set(
    body_background_fill='*neutral_50',
    body_text_color='*neutral_950'
)

js_func = """
function refresh() {
    const url = new URL(window.location);

    if (url.searchParams.get('__theme') !== 'light') {
        url.searchParams.set('__theme', 'light');
        window.location.href = url.href;
    }
}
"""

def encode_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"

image_base64 = encode_image("gfx/long_logo.png")


with gr.Blocks(theme=theme,js=js_func) as demo:
    uploaded_files_state = gr.State([])

    gr.Markdown("<h1 style=\"text-align:center;\">AI-powered LaTeX Presentation Generator</h1>")
    with gr.Row():
        with gr.Column(scale=1):
            gr.HTML(f"""
                <div style="text-align:center;">
                <img src="{image_base64}" style="max-width: 100%; height: auto;" />
                </div>
            """)
        with gr.Column(scale=1):
            gr.Markdown("<div style=\"text-align:justify; margin-top: 15px;\">Turn your PDFs and ideas into beautiful LaTeX "
                        "presentations with AI. Built on top of the <a href=\"https://ragntex.github.io/lore/\">RAG\'n\'TeX</a>"
                        " engine, this tool automatically selects relevant content and compiles well-structured"
                        " slides. Ideal for students, researchers, and educators looking to save time and "
                        "create topic-focused presentations with minimal effort.</div>")
            gr.Markdown("<div style=\"text-align:justify; margin-top: 0px;\">Just upload your PDFs, click <b>Upload Files</b>, "
                        "choose a theme, enter your topic, and hit <b>Generate Presentation</b> — it's that easy!</div>")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## 📂 Step 1: Upload PDF Documents")
            file_input = gr.File(
                file_types=[".pdf"], file_count="multiple", label="Select PDF Files"
            )
            upload_button = gr.Button("Upload Files", variant="primary")

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
            submit_topic_button = gr.Button("Generate Presentation", variant="primary")

        with gr.Column(scale=1):
            gr.Markdown("## 📄 Uploaded Files")
            upload_output = gr.Textbox(
                label="Upload Status", lines=3, interactive=False
            )

            gr.Markdown("## 📝 Presentation Processing")
            topic_output = gr.Textbox(label="Compilation Status", lines=1, interactive=False)

            gr.Markdown("## 🎉 Final Presentation")
            pdf_output = gr.File(label="Download/View Presentation")
            pdf_output_viewer = gr.HTML(label="Presentation Preview")

    upload_button.click(
        fn=upload_and_update_list,
        inputs=[file_input, uploaded_files_state],
        outputs=[upload_output, uploaded_files_state],
    )

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

    pdf_output.change(
        fn=generate_iframe,
        inputs=pdf_output,
        outputs=pdf_output_viewer,
    )
