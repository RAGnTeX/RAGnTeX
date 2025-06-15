"""This module provides functionality to convert a JSON LLM output to LaTeX Beamer presentation."""

import json


def render_content(content: list[str], content_format: str) -> str:
    """Render content in LaTeX format depending is it si itemized list or plain text.
    Args:
        content (list[str]): List of content items.
        content_format (str): Format of the content, either "itemize" or "text".
    Returns:
        str: LaTeX formatted content.
    """
    # Remove blank or whitespace-only entries
    filtered_content = [c.strip() for c in content if c.strip()]
    if content_format == "text":
        return "\n\n".join(filtered_content)
    return (
        "\\begin{itemize}\n"
        + "\n".join(f"\\item {c}" for c in filtered_content)
        + "\n\\end{itemize}"
    )


def json_to_tex(
    presentation_json: str, theme: str, color_theme: str, aspect_ratio: str
) -> str:
    """Convert a JSON representation of a presentation to LaTeX Beamer format.
    Args:
        presentation (Dict[str, Any]): JSON LLM output of the presentation.
        theme (str): Beamer theme to use.
        color_theme (str): Beamer color theme to use.
        aspect_ratio (str): Aspect ratio for the presentation, e.g., "16:9", "4:3".
    Returns:
        str: LaTeX Beamer code as a string.
    """
    presentation = json.loads(presentation_json)
    aspect_ratio_num = 169 if aspect_ratio == "16:9" else 43
    header = f"""\\documentclass[aspectratio={aspect_ratio_num}]{{beamer}}
                \\usepackage[utf8]{{inputenc}}
                \\usetheme{{{theme}}}
                \\usecolortheme{{{color_theme}}}
                \\title{{{presentation["title"]}}}
                \\author{{{presentation["author"]}}}
                \\date{{\\today}}

                \\usepackage{{graphicx}}

                \\begin{{document}}

                \\frame{{\\titlepage}}"""

    slides = []

    for slide in presentation["slides"]:
        slide_type = slide["type"]
        content = slide.get("content", [])
        content_format = slide.get("content_format", "itemize")
        body = render_content(content, content_format)

        # if slide_type == "title":
        #     continue

        if slide_type in {"introduction", "summary"}:
            title = "Introduction" if slide_type == "introduction" else "Summary"
            slides.append(
                f"""\\begin{{frame}}
                \\frametitle{{{title}}}
                {body}
                \\end{{frame}}"""
            )

        elif slide_type == "core_idea":
            core_title = slide.get("title", "Core Idea")
            layout = slide.get("layout", "text_only")

            if layout == "text_only":
                slides.append(
                    f"""\\begin{{frame}}
                    \\frametitle{{{core_title}}}
                    {body}
                    \\end{{frame}}"""
                )

            elif layout == "two_column":
                img = slide["image"]
                slides.append(
                    f"""\\begin{{frame}}
                        \\frametitle{{{core_title}}}
                        \\begin{{columns}}
                        \\begin{{column}}{{0.5\\linewidth}}
                        {body}
                        \\end{{column}}
                        \\begin{{column}}{{0.5\\linewidth}}
                        \\center{{\\includegraphics[height=1.0\\textheight, width=1.0\\textwidth, keepaspectratio]{{{img["path"]}}} \\\\ {img["caption"]}}}
                        \\end{{column}}
                        \\end{{columns}}
                        \\end{{frame}}"""
                )

            elif layout == "single_image":
                img = slide["image"]
                slides.append(
                    f"""\\begin{{frame}}
                        \\frametitle{{{core_title}}}
                        \\center{{\\includegraphics[height=0.5\\textheight, width=0.8\\textwidth, keepaspectratio]{{{img["path"]}}} \\\\ {img["caption"]} \\\\}}
                        {body}
                        \\end{{frame}}"""
                )

    footer = "\\end{document}"

    return "\n\n".join([header] + slides + [footer])
