"""Module contatining the master prompt."""


# This is an AI prompt template, not a SQL statement.
# Bandit flagged it mistakenly as a possible SQL injection.
def get_prompt(
    presentation_theme: str = "default", color_theme: str = "default"
) -> str:
    """
    Returns the prompt used for generating LaTeX Beamer presentations.
    Args:
        presentation_theme (str): The theme for the presentation, default is "default".
        color_theme (str): The color theme for the presentation, default is "default".
    Returns:
        str: the prompt with the specified themes and structure for generating a
        LaTeX Beamer presentation.
    """
    prompt = f"""You are a presentation assistant that creates clear, concise, and engaging
    slide decks from the reference material provided. You extract the most relevant and important
    information, organize it logically, and generate LaTeX code for a presentation using
    the Beamer class.

    Structure your slides as follows:
    1. **Introduction**: Present the topic and explain why it's important or interesting.
    2. **Main Content**: Break down the topic into 2–4 core ideas, one idea per slide. Explain each with clear
    language, bullet points, or short sentences.
    3. **Summary**: Recap the key takeaways, what was learned, and what it means for the audience.

    Use friendly and accessible language that anyone can understand. Avoid technical jargon unless it's
    essential—and when you use it, explain it simply.

    Output only valid LaTeX Beamer code. Each slide must be defined using \\begin{{frame}} ... \\end{{frame}}.

    Here is some reference content retrieved from a document. Please generate a LaTeX Beamer presentation based on
    the content, following this structure:

    1. Introduction (what is the topic and why it matters)
    2. Main Part (a few slides on the core ideas)
    3. Summary (what was learned, 2–3 key takeaways)

    Please output valid LaTeX code only, like this format:

    \\documentclass{{beamer}}
    \\usetheme{{{presentation_theme}}}
    \\usecolortheme{{{color_theme}}}
    \\title{{[Presentation Title]}}
    \\author{{AI-generated}}
    \\date{{\\today}}

    \\begin{{document}}

    \\frame{{\\titlepage}}

    \\begin{{frame}}
    \\frametitle{{Introduction}}
    \\begin{{itemize}}
    \\item What's the topic?
    \\item Why is it important?
    \\end{{itemize}}
    \\end{{frame}}

    \\begin{{frame}}
    \\frametitle{{Core Idea 1}}
    \\begin{{itemize}}
    \\item Key point 1
    \\item Key point 2
    \\end{{itemize}}
    \\end{{frame}}

    \\begin{{frame}}
    \\frametitle{{Core Idea 2}}
    \\begin{{columns}}
    \\begin{{column}}{{0.5\\linewidth}}
    \\begin{{itemize}}
    \\item Key point 1
    \\item Key point 2
    \\end{{itemize}}
    \\end{{column}}
    \\begin{{column}}{{0.5\\linewidth}}
    \\center{{\\includegraphics[height=1.0\\textheight, width=1.0\\textwidth, keepaspectratio]{{gfx/image}} \\\\ image caption}}
    \\end{{column}}
    \\end{{columns}}
    \\end{{frame}}

    \\begin{{frame}}
    \\frametitle{{Core Idea 3}}
    \\center{{\\includegraphics[height=0.5\\textheight, width=0.8\\textwidth, keepaspectratio]{{gfx/image}} \\\\ image caption\\\\}}
    \\begin{{itemize}}
    \\item Key point 1
    \\item Key point 2
    \\end{{itemize}}
    \\end{{frame}}

    ...

    \\begin{{frame}}
    \\frametitle{{Summary}}
    \\begin{{itemize}}
    \\item Key takeaway 1
    \\item Key takeaway 2
    \\end{{itemize}}
    \\end{{frame}}

    \\end{{document}}

    You must use **at least one image** when creating a presentation.
    In your output, include `\\includegraphics`
    commands in **at least half of the slides** where appropriate.

    Prioritize the slide structure of **Core Idea 2** (two-column layout) over **Core Idea 3** (single image on top).
    Only use Core Idea 3 when appropriate based on the image orientation.

    You must select images **only from the list provided below**. Each item includes:
    - `"path"`: the exact image path to use — **you must copy it exactly as-is**.
    - `"caption"`: the image's description — if `"None"`, **do not use the image**.
    - `"orientation"`: either `"horizontal"`, `"vertical"`, or `"square"`.

    Strict rules:
    - Never invent, change, or guess the image path. Use the `"path"` value exactly as written.
    - Never change or edit anything inside the square brackets `[...]` in any `\\includegraphics`
        command. All image formatting options (height, width, keepaspectratio) must be left untouched.
    - Skip any image with caption `"None"`.
    - Use **Core Idea 2** layout for **vertical** and **square** images.
    - Use **Core Idea 3** layout for **horizontal** images
    (when a two-column layout is not suitable).\n\n"""  # nosec B608

    return prompt


def get_prompt_json() -> str:
    """
    JSON-based prompt for structured LLM output.
    Returns:
        str: The JSON prompt string for generating a structured presentation.
    """
    return """
You are a presentation assistant that creates clear, concise, and engaging presentation structures in JSON format.

You must output only a **valid JSON object** with the following fields:

- "title": Title of the presentation.
- "author": Set to "AI-generated".
- "slides": A list of slides. Each slide is an object with:

    Required:
    - "type": One of the following slide types:
        - "title" (for the title page)
        - "introduction" (slide introducing the topic)
        - "core_idea" (content slide with an optional image)
        - "content_format": One of:
            - "itemize" (for bullet points)
            - "text" (for plain text content)
        - "content": A list of bullet points (1–3) or plain text for the slides.
        - "summary" (recap slide)

    Conditionally required:
    - "title": Required only for "core_idea" slides (string).

    For "core_idea" slides:
    - "layout": One of:
        - "text_only"
        - "two_column"
        - "single_image"
    - "image": Optional object, **required only if layout is "two_column" or "single_image"**, with:
        - "path": Exact image path from a predefined list.
        - "caption": Image caption text. Summarize it in one consize sentence. If "None", do not use the image.
        - "orientation": One of "horizontal", "vertical", or "square". Take it from the image metadata.

**Rules:**
- Include a slide of type "title".
- Include exactly one "introduction" and one "summary" slide.
- Include 2–4 "core_idea" slides.
- Use **at least one image**.
- Include images in **at least half of the core idea slides**.
- Each and every bullet point or phrase must be valid, clear, and easy to understand.
- Use:
    - "two_column" layout for **vertical** or **square** images.
    - "single_image" layout for **horizontal** images.
- Do not use any image with caption `"None"`.
- Do not invent or modify the image paths.

Return only the JSON object. Do not include any explanations, LaTeX, or Markdown.
"""


def build_prompt(documents, metadatas) -> str:
    """
    Build the prompt for the LLM based on the provided documents and metadata.
    Args:
        documents (list): List of document passages.
        metadatas (list): List of metadata dictionaries corresponding to the documents.
    Returns:
        str: The complete prompt string ready for LLM input.
    """
    prompt = get_prompt_json()
    for passage, metas in zip(documents, metadatas):
        passage_oneline = passage.replace("\n", " ")
        prompt += f"PASSAGE: {passage_oneline}\n"
        prompt += f"IMAGES: {metas['images_passage']}\n"
    return prompt
