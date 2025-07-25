# pylint: disable=no-member, line-too-long
"""Gradio UI for the RAG'n'TeX LaTeX Presentation Generator."""

import base64
from typing import Any

import gradio as gr
from gradio_pdf import PDF

from ..generator import generate_presentation
from ..telemetry import submit_feedback
from .manage_files import download_files, upload_files
from .session_manager import (check_session_status, create_session,
                              with_update_session)

SESSION_TIMEOUT = 900


def update_config(key, value, config) -> dict:
    """Helper function to update configuration settings.
    These settings will be later used for generate_presentation function.

    Args:
        key (str): Configuration key to update.
        value (str): New value for the configuration key.
        config (dict): Current configuration dictionary.

    Returns:
            dict: Updated configuration dictionary with the new key-value pair.
    """
    config[key] = value
    return config


def upload_and_update_list(
    files: list, uploaded_list, session_id
) -> tuple[str, list[str]]:
    """Helper function to handle uploaded documents and update the list of uploaded files.
    Args:
        files (list): List of file-like objects to be uploaded.
        uploaded_list (list): Current list of uploaded file paths.
        session_id (str): Unique identifier for the current session.
    Returns:
        tuple: A 2-element tuple:
            - str: Status message indicating the result of the upload operation.
            - list[str]: Updated list of uploaded file paths."""

    status, new_paths = upload_files(files, session_id)
    updated_list = uploaded_list + [p for p in new_paths if p not in uploaded_list]

    return status, updated_list


# def generate_iframe(folder_path) -> str:
#     """Generate an HTML iframe to display the PDF presentation.
#     Args:
#         folder_path (str): Path to the folder containing the generated PDF presentation.
#     Returns:
#         str: HTML string containing the iframe to display the PDF.
#     """

#     file_path = f"{folder_path}/presentation.pdf"
#     if not file_path:
#         return ""
#     with open(file_path, "rb") as f:
#         base64_pdf = base64.b64encode(f.read()).decode("utf-8")
#     pdf_display = f"""
#         <div style="position:relative; width:100%; padding-top:76.5%;">
#         <iframe src="data:application/pdf;base64,{base64_pdf}#view=FitH"
#         style="position:absolute; top:0; left:0; width:100%; height:100%; border:none;">
#         </iframe></div>
#     """


def activate_preview(
    browser_info: str, presentation_folder_state: str
) -> tuple[Any, Any]:
    """Activate the PDF preview in the viewer component.
    Args:
        browser_info (gr.State): State containing information about the user's browser.
        presentation_folder_state (str): Path to the folder containing the generated PDF presentation.
    Returns:
        tuple[gr.Update, gr.Update]: Tuple containing updates for the PDF viewer and alert box visibility.
    """
    if presentation_folder_state is None or not presentation_folder_state:
        return gr.update(visible=False), gr.update(visible=False)

    if "safari" in browser_info.lower() and "chrome" not in browser_info.lower():
        return gr.update(visible=False), gr.update(visible=True)
    else:
        return gr.update(visible=True), gr.update(visible=False)


def encode_image(image_path) -> str:
    """Encode an image file to a base64 data URL.
    Args:
        image_path (str): Path to the image file.
    Returns:
        str: Base64 data URL of the image.
    """
    with open(image_path, "rb") as f:
        data = f.read()
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"


banner_base64 = encode_image("gfx/long_logo.png")
logo_base64 = encode_image("gfx/icon_logo.png")
github_base64 = encode_image("gfx/github-mark-white.png")
favicon_base64 = encode_image("gfx/favicon.ico")


# Custom Gradio theme
theme = gr.themes.Monochrome(
    neutral_hue=gr.themes.Color(
        c50="#f8f4fe",
        c100="#ede9fe",
        c200="#ddd6fe",
        c300="#c4b5fd",
        c400="#a78bfa",
        c500="#8b5cf6",
        c600="#7c3aed",
        c700="#6d28d9",
        c800="#5b21b6",
        c900="#4c1d95",
        c950="#181e44",
    ),
).set(body_background_fill="*neutral_50", body_text_color="*neutral_950")


# Additional JavaScript to handle session management and UI updates
JS_FUNC = r"""
() => {
    // Force light theme
    const url = new URL(window.location);
    if (url.searchParams.get('__theme') !== 'light') {
        url.searchParams.set('__theme', 'light');
        window.location.href = url.href;
    }

    // Overlay for session expiration
    const overlayDiv = document.createElement("div");
    overlayDiv.id = "session-overlay";
    overlayDiv.style = `
        display: flex;
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        justify-content: center;
        align-items: center;
        background-color: rgba(0, 0, 0, 0.7);
        color: white;
        font-size: 1.5rem;
        text-align: center;
        z-index: 999999;
    `;
    overlayDiv.innerHTML = `
        ❌ Session expired.<br/>🔄 Please refresh the page to start over.
    `;

    const checker = setInterval(() => {
        const checkBtn = document.querySelector('#check-session-button');
        if (checkBtn) checkBtn.click();

        const statusBox = document.querySelector('#session-status textarea');
        if (!statusBox) return;

        const value = statusBox.value;

        if (value === "expired") {
            document.body.appendChild(overlayDiv);
            console.log("Session expired, please refresh the page.");

            clearInterval(checker);
        }
    }, 5000);

    const browser = navigator.userAgent.toLowerCase();
    const browser_element = document.querySelector('#browser_info textarea');
    if (browser_element) {
        browser_element.value = browser;
        setTimeout(() => {
            browser_element.dispatchEvent(new Event("input", { bubbles: true }));
            browser_element.dispatchEvent(new Event("change", { bubbles: true }));
        }, 1000);
    }
    }
"""


with gr.Blocks(theme=theme, js=JS_FUNC) as demo:
    # Session management
    session_id_state = gr.State()
    session_timeout = gr.State(SESSION_TIMEOUT)
    status_output = gr.Textbox(visible=False, elem_id="session-status")
    check_btn = gr.Button(visible=False, elem_id="check-session-button")
    check_btn.click(
        fn=check_session_status,
        inputs=[session_id_state],
        outputs=[status_output],
    )
    ###

    uploaded_files_state = gr.State([])
    presentation_folder_state = gr.State("")
    browser_info = gr.Textbox(visible=False, elem_id="browser_info")
    browser_info.change(fn=lambda x: None, inputs=browser_info, outputs=[])

    # Page title and favicon (doesn't work? Gradio is really agressive)
    gr.HTML(
        f"""
        <script>
        document.title = "RAG'n'TeX Presentation Generator";

        const links = document.querySelectorAll("link[rel*='icon']");
        links.forEach(link => link.parentNode.removeChild(link));

        const newFavicon = document.createElement('link');
        newFavicon.rel = 'icon';
        newFavicon.type = 'image/png';
        newFavicon.href = '{favicon_base64}';
        document.head.appendChild(newFavicon);
        </script>
        """,
        elem_id="custom-head-injection",
        visible=False,
    )

    # Mess with the download-box and preview-box
    gr.HTML(
        """
        <style>
        #download-box svg.feather-file {
            display: none !important;
        }
        </style>
        """,
        elem_id="custom-style-injection",
        visible=False,
    )

    gr.Markdown(
        '<h1 style="text-align:center;">AI-powered LaTeX Presentation Generator</h1>'
    )
    with gr.Row():
        with gr.Column(scale=1):
            gr.HTML(
                f"""
                <div style="text-align:center;">
                <img src="{banner_base64}" style="max-width: 100%; height: auto;" />
                </div>
                """
            )
        with gr.Column(scale=1):
            gr.Markdown(
                '<div style="text-align:justify; margin-top: 15px;">Turn your PDFs and ideas into beautiful LaTeX '
                "presentations with AI. Built on top of the <a href=\"https://ragntex.github.io/lore/\">RAG'n'TeX</a>"
                " engine, this tool automatically selects relevant content and compiles well-structured"
                " slides. Ideal for students, researchers, and educators looking to save time and "
                "create topic-focused presentations with minimal effort.</div>"
            )
            gr.Markdown(
                '<div style="text-align:justify; margin-top: 0px;">Just upload your PDFs, click <b>Upload Files</b>, '
                "choose a theme, enter your topic, and hit <b>Generate Presentation</b> — it's that easy!</div>"
            )
            gr.HTML(
                f"""
                    <div style="display: flex; flex-direction: row; align-items: center; justify-content: center; gap: 20px; margin-bottom: 12px;">
                        <p style="font-size: 16px; line-height: 1; margin: 0;">Please ⭐️ us on GitHub!</p>
                        <a href="https://github.com/RAGnTeX/RAGnTeX" target="_blank" style="
                            display: inline-flex;
                            align-items: center;
                            justify-content: center;
                            padding: 12px 16px;
                            background-color: #4c1d95;
                            color: white;
                            font-weight: 600;
                            font-size: 16px;
                            line-height: 1;
                            border-radius: 8px;
                            text-decoration: none;
                            gap: 8px;
                            transition: background-color 0.2s ease-in-out;
                            border: 2px solid transparent;
                            "
                            onmouseover="this.style.backgroundColor='#6d28d9'; this.style.border='2px solid #686868';"
                            onmouseout="this.style.backgroundColor='#4c1d95'; this.style.border='2px solid transparent';"
                        >
                            <img src="{github_base64}" alt="GitHub" style="height: 20px;">
                            RAG'n'TeX
                        </a>
                    </div>
                """
            )

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## 📂 Step 1: Upload PDF Documents")
            file_input = gr.File(
                file_types=[".pdf"], file_count="multiple", label="Select PDF Files"
            )
            upload_button = gr.Button("Upload Files", variant="primary")

            gr.Markdown("## 🎨 Step 2: Choose the parameters")
            config_state = gr.State({})
            model_state = gr.State("default")
            model_radio = gr.Radio(
                ["gemini-2.0-flash", "gemini-2.5-flash-preview-05-20"],
                label="LLM",
                info="Choose Gemini version",
                value="gemini-2.0-flash",
            )
            model_radio.change(
                fn=lambda value, config: update_config("model_name", value, config),
                inputs=[model_radio, config_state],  # only real components here
                outputs=config_state,
            )

            aspect_ratio_radio = gr.Radio(
                ["16:9", "4:3"],
                label="Aspect Ratio",
                info="Choose presentation aspect ratio",
                value="16:9",
            )

            aspect_ratio_radio.change(
                fn=lambda value, config: update_config("aspect_ratio", value, config),
                inputs=[aspect_ratio_radio, config_state],  # only real components here
                outputs=config_state,
            )
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

            theme_dropdown.change(
                fn=lambda value, config: update_config("theme", value, config),
                inputs=[theme_dropdown, config_state],  # only real components here
                outputs=config_state,
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

            color_dropdown.change(
                fn=lambda value, config: update_config("color_theme", value, config),
                inputs=[color_dropdown, config_state],  # only real components here
                outputs=config_state,
            )

            gr.Markdown("## 🧠 Step 3: Enter Presentation Topic")
            topic_input = gr.Textbox(
                label="Presentation Topic",
                placeholder="e.g., Introduction to Quantum Computing",
                lines=1,
            )
            topic_input.change(
                fn=lambda value, config: update_config("topic", value, config),
                inputs=[topic_input, config_state],  # only real components here
                outputs=config_state,
            )
            submit_topic_button = gr.Button("Generate Presentation", variant="primary")

        with gr.Column(scale=1):
            gr.Markdown("## 📄 Uploaded Files")
            upload_output = gr.Textbox(
                label="Upload Status", lines=3, interactive=False
            )

            gr.Markdown("## 📝 Presentation Processing")
            compilation_status = gr.Textbox(
                label="Compilation Status", lines=1, interactive=False
            )

            gr.Markdown("## 🎉 Final Presentation")
            pdf_output = gr.File(
                label="Download Presentation",
                interactive=False,
                elem_id="download-box",
                file_count="multiple",
            )
            pdf_output_viewer = PDF(
                label="Presentation Preview",
                elem_id="preview-box",
                visible=False,
            )
            browser_alert_box = gr.HTML(
                """
                <div style="
                    border: 1px solid #ddd6fe;
                    background-color: #ffffff;
                    color: #181e44;
                    padding: 15px;
                    border-radius: 4px;
                    font-weight: bold;
                    max-width: 100%;
                    margin: 0px;
                    text-align: center;
                ">
                    ⚠️ PDF preview is unavailable in Safari. Please download the PDF to view it.
                </div>
                """,
                visible=False,
            )
            # pdf_output_viewer = gr.HTML(label="Presentation Preview")
            trace_id_state = gr.State("")

    gr.Markdown("<br>")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## ⭐ Rate Us")
            rating = gr.Radio(
                choices=["⭐️", "⭐️⭐️", "⭐️⭐️⭐️", "⭐️⭐️⭐️⭐️", "⭐️⭐️⭐️⭐️⭐️"],
                label="How would you rate this app?",
                interactive=True,
                type="value",
                value=None,
                show_label=True,
                container=True,
            )
            feedback_comment = gr.Textbox(
                label="Give us a comment (optional)",
                placeholder="What did you like or what can be improved?",
                lines=3,
                max_lines=5,
                interactive=True,
            )
            submit_feedback_button = gr.Button("Submit Feedback", variant="secondary")
            feedback_output = gr.Textbox(
                label="Feedback Status", interactive=False, lines=2
            )

        with gr.Column(scale=1):
            gr.Markdown("## 🙌 Credits")
            gr.HTML(
                f"""
                <div style="display: flex; flex-direction: row; gap: 24px; margin-top: 0; align-items: flex-start;">

                <!-- Left Column -->
                <div style="flex: 1;">
                    <div style="text-align:justify; margin-top: 0px;">
                    <p> RAG'n'TeX is a collaborative effort by a team of developers and researchers driven
                    to make the everyday work of scientists and professionals easier. By combining LaTeX with AI,
                    we create smart tools that help you build polished, accurate presentations quickly and smoothly.
                    Our goal is to make the process simple and stress-free, so you can spend more time on what really matters.</p>
                    <br>
                    <p>📄 Licensed under the <a href="https://opensource.org/licenses/MIT" target="_blank" rel="noopener noreferrer">MIT License</a></p>
                    <br>
                    <h4>Authors:</h4>
                        <ul style="padding-left: 20px; margin-top: 4px;">
                        <li>👩🏻‍💻 <a href="https://github.com/AnnaErsh" target="_blank">Anna Ershova</a></li>
                        <li>👨🏼‍🔬 <a href="https://github.com/KajetanNiewczas" target="_blank">Kajetan Niewczas</a></li>
                        </ul>
                    </div>
                </div>

                <!-- Right Column -->
                <div style="flex: 1; display: flex; justify-content: flex-end; align-items: center;">
                    <img src="{logo_base64}" alt="Illustration" style="max-width: 100%; border-radius: 8px;">
                </div>
                </div>
                """
            )

    # Event handlers

    demo.load(
        fn=create_session,
        inputs=session_timeout,
        outputs=session_id_state,
    )

    upload_button.click(
        fn=with_update_session(upload_and_update_list),
        inputs=[file_input, uploaded_files_state, session_id_state],
        outputs=[upload_output, uploaded_files_state],
    )

    trace_id_state = gr.State("")
    submit_topic_button.click(
        fn=with_update_session(lambda x: ""),
        inputs=session_id_state,
        outputs=compilation_status,
    ).then(
        fn=with_update_session(generate_presentation),
        inputs=[
            config_state,
            session_id_state,
        ],
        outputs=[compilation_status, trace_id_state, presentation_folder_state],
    )

    compilation_status.change(
        fn=download_files,
        inputs=[
            compilation_status,
            presentation_folder_state,
            session_id_state,
        ],
        outputs=pdf_output,
    )

    browser_info.change(fn=lambda x: None, inputs=browser_info, outputs=[])

    pdf_output.change(
        fn=lambda folder: f"{folder}/presentation.pdf" if folder is not None else None,
        inputs=presentation_folder_state,
        outputs=pdf_output_viewer,
    ).then(
        fn=activate_preview,
        inputs=[browser_info, presentation_folder_state],
        outputs=[pdf_output_viewer, browser_alert_box],
    )

    # pdf_output.change(
    #     fn=generate_iframe,
    #     inputs=presentation_folder_state,
    #     outputs=pdf_output_viewer,
    # )

    submit_feedback_button.click(
        fn=with_update_session(submit_feedback),
        inputs=[
            rating,
            feedback_comment,
            trace_id_state,
            session_id_state,
        ],
        outputs=feedback_output,
    )
