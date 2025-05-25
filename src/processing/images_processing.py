"""Module handling images exrtraction and processing from the uploaded PDF documents."""

import re
import os
import hashlib
from collections import defaultdict
import fitz
from rtree import index

from ..telemetry import Logger

LOGGER = Logger.get_logger()


def find_image_caption(page, image_bbox, max_distance=100):
    """Method to find and extract image caption based on the image bounding box."""
    # Get all text blocks on the page
    blocks = page.get_text("dict")["blocks"]
    image_bottom = image_bbox.y1
    image_x_center = (image_bbox.x0 + image_bbox.x1) / 2

    best_match_caption = None
    fallback_caption = None
    closest_distance = float("inf")

    for block in blocks:
        if block["type"] != 0:
            continue

        block_bbox = block["bbox"]
        x0, y0, x1, y1 = block_bbox
        vertical_distance = y0 - image_bottom

        # Merge all spans' text into one string
        block_text = " ".join(
            span["text"]
            for line in block.get("lines", [])
            for span in line.get("spans", [])
        ).strip()

        if (
            y0 >= image_bottom
            and abs(image_x_center - (x0 + x1) / 2) < image_bbox.width / 2
        ):
            if (
                vertical_distance < max_distance
                and vertical_distance < closest_distance
            ):
                if re.match(r"^(Fig(ure)?\.?\s*\d+[:\-])", block_text, re.IGNORECASE):
                    best_match_caption = block_text
                    break
                else:
                    fallback_caption = block_text
                    closest_distance = vertical_distance

    if best_match_caption and len(best_match_caption.strip()) > 10:
        return best_match_caption.strip()
    elif fallback_caption and len(fallback_caption.strip()) > 10:
        return fallback_caption.strip()
    else:
        return None


def extract_images(pdf, doc, page, page_num):
    """Extract images from a PDF page and classify them based on their aspect ratio."""
    images = page.get_images(full=True)

    imgs = []
    for img_index, img in enumerate(images):
        # Extract the image
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        image_hash = hashlib.md5(image_bytes).hexdigest()
        image_name = f"doc{pdf}_page{page_num}_img{img_index}_hash{image_hash[:8]}.png"

        # Find the bbox
        image_bbox = None
        for img_info in page.get_image_info(xrefs=True):
            if img_info["xref"] == xref:
                image_bbox = fitz.Rect(img_info["bbox"])
                break

        # Get the image ratio
        width = image_bbox.width
        height = image_bbox.height
        ratio = width / height if height != 0 else None

        # Classify the image based on the ratio
        if ratio >= 1.5:
            image_type = "horizontal"
        elif ratio <= 0.67:
            image_type = "vertical"
        else:
            image_type = "square"

        # Get caption based on bbox
        caption = find_image_caption(page, image_bbox) if image_bbox else None

        # Append an image
        imgs.append(
            {
                "name": image_name,
                "caption": caption,
                "ratio": image_type,
                "hash": image_hash,
            }
        )

    return imgs


def are_bounding_boxes_close(bbox1, bbox2, threshold=50):
    # Extracting the four edges of each bounding box
    left1, top1, right1, bottom1 = bbox1
    left2, top2, right2, bottom2 = bbox2

    # Check if any of the borders are within the threshold distance
    return (
        abs(left1 - right2) < threshold
        or abs(right1 - left2) < threshold
        or abs(top1 - bottom2) < threshold
        or abs(bottom1 - top2) < threshold
    )


def merge_bounding_boxes(bboxes):
    if not bboxes:
        return None
    # Start with the first bounding box
    combined_bbox = bboxes[0]
    for bbox in bboxes[1:]:
        combined_bbox = combined_bbox | bbox  # Combine the bounding boxes (union)
    return combined_bbox


def group_bounding_boxes(bboxes, max_drawings=2000, threshold=50):
    # R-tree index setup
    idx = index.Index()
    for i, rect in enumerate(bboxes):
        expanded = rect + (-threshold, -threshold, threshold, threshold)
        idx.insert(i, expanded)

    # Graph connectivity
    adj_list = defaultdict(list)
    for i, rect in enumerate(bboxes):
        expanded = rect + (-threshold, -threshold, threshold, threshold)
        for j in idx.intersection(expanded):
            if i != j:
                adj_list[i].append(j)

    # Perform DFS to find connected components (groups of connected bounding boxes)
    visited = [False] * len(bboxes)
    components = []

    def dfs(node, component):
        visited[node] = True
        component.append(bboxes[node])
        for neighbor in adj_list[node]:
            if not visited[neighbor]:
                dfs(neighbor, component)

    # Find all connected components using DFS
    for i in range(len(bboxes)):
        if not visited[i]:
            component = []
            dfs(i, component)
            components.append(component)

    # Return grouped and merged bboxes
    return [merge_bounding_boxes(group) for group in components]


def process_large_drawing(drawings, max_drawings=1000, threshold=50):
    bboxes = [fitz.Rect(d["rect"]) for d in drawings if d.get("rect")]

    if len(bboxes) < max_drawings:
        return group_bounding_boxes(bboxes, threshold=threshold)

    # Split the data into smaller chunks
    num_chunks = (len(bboxes) // max_drawings) + 1
    all_results = []

    for chunk_index in range(num_chunks):
        chunk = bboxes[chunk_index * max_drawings : (chunk_index + 1) * max_drawings]
        results = group_bounding_boxes(chunk, threshold=threshold)
        all_results.extend(results)

    # Return the combined results
    return group_bounding_boxes(all_results, threshold=threshold)


def find_surrounding_text(page, group, threshold=50):
    text_blocks = page.get_text("dict")["blocks"]
    expanded = group + (-threshold, -threshold, threshold, threshold)
    surrounding = []

    for block in text_blocks:
        if block["type"] != 0:
            continue

        block_rect = fitz.Rect(block["bbox"])
        if expanded.intersects(block_rect):
            surrounding.append(block_rect)

    return surrounding


def extract_vector(pdf, doc, page, page_num):
    MAX_DRAWINGS = 1000
    MIN_SIZE = 0.05
    MAX_SIZE = 0.30
    THRESHOLD = 5
    ZOOM = 4

    page_size = page.rect.width * page.rect.height
    min_size = page_size * MIN_SIZE
    max_size = page_size * MAX_SIZE

    drawings = page.get_drawings()

    # Group drawings into figures
    grouped = process_large_drawing(
        drawings, max_drawings=MAX_DRAWINGS, threshold=THRESHOLD
    )

    figs = []
    for group_num, group in enumerate(grouped):
        # Try to include any text labels around
        surrounding = find_surrounding_text(page, group, threshold=THRESHOLD)
        if surrounding:
            figure_bbox = merge_bounding_boxes([group] + surrounding)
        else:
            figure_bbox = group

        # Filter by minimal plot size
        width = figure_bbox[2] - figure_bbox[0]
        height = figure_bbox[3] - figure_bbox[1]
        area = width * height
        if area > min_size and area < max_size:
            scale_mat = fitz.Matrix(ZOOM, ZOOM)
            figure_pix = page.get_pixmap(matrix=scale_mat, clip=figure_bbox)
            figure_bytes = figure_pix.tobytes("png")
            figure_hash = hashlib.md5(figure_bytes).hexdigest()
            figure_name = (
                f"doc{pdf}_page{page_num}_fig{group_num}_hash{figure_hash[:8]}.png"
            )

            # Get the figure ratio
            ratio = width / height if height != 0 else None

            # Classify the image based on the ratio
            if ratio >= 1.5:
                figure_type = "horizontal"
            elif ratio <= 0.67:
                figure_type = "vertical"
            else:
                figure_type = "square"

            # Get caption based on bbox
            caption = find_image_caption(page, figure_bbox) if figure_bbox else None

            # Append an image
            figs.append(
                {
                    "name": figure_name,
                    "caption": caption,
                    "ratio": figure_type,
                    "hash": figure_hash,
                }
            )

    return figs


def save_pdf_images(pdf_path: str, req_imgs: list, images_dir: str):
    """Save images used in the presentation to the specified directory."""
    doc = fitz.open(pdf_path)
    pdf = os.path.splitext(os.path.basename(pdf_path))[0]

    # Create a set of page to process
    pages_to_inspect = set()
    for img in req_imgs:
        if pdf == img["doc"]:
            pages_to_inspect.add(img["page"])

    for page_num, page in enumerate(doc):
        if page_num in pages_to_inspect:

            # Extract images
            images_info = page.get_images(full=True)
            for img_index, img in enumerate(images_info):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_hash = hashlib.md5(image_bytes).hexdigest()

                image_found = any(
                    pdf == img["doc"]
                    and page_num == img["page"]
                    and img_index == img["img"]
                    and image_hash.startswith(img["hash"])
                    for img in req_imgs
                )

                # Save the image
                if image_found:
                    image_name = f"doc{pdf}_page{page_num}_img{img_index}_hash{image_hash[:8]}.png"
                    image_path = os.path.join(images_dir, image_name)
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)

    return True


def save_pdf_figures(pdf_path: str, req_figs: list, figures_dir: str):
    doc = fitz.open(pdf_path)
    pdf = os.path.splitext(os.path.basename(pdf_path))[0]

    # Create a set of page to process
    pages_to_inspect = set()
    for fig in req_figs:
        if pdf == fig["doc"]:
            pages_to_inspect.add(fig["page"])

    for page_num, page in enumerate(doc):
        if page_num in pages_to_inspect:
            MAX_DRAWINGS = 1000
            MIN_SIZE = 0.05
            MAX_SIZE = 0.30
            THRESHOLD = 5
            ZOOM = 4

            page_size = page.rect.width * page.rect.height
            min_size = page_size * MIN_SIZE
            max_size = page_size * MAX_SIZE

            drawings = page.get_drawings()

            # Group drawings into figures
            grouped = process_large_drawing(
                drawings, max_drawings=MAX_DRAWINGS, threshold=THRESHOLD
            )

            for group_num, group in enumerate(grouped):
                # Try to include any text labels around
                surrounding = find_surrounding_text(page, group, threshold=THRESHOLD)
                if surrounding:
                    figure_bbox = merge_bounding_boxes([group] + surrounding)
                else:
                    figure_bbox = group

                # Filter by minimal plot size
                width = figure_bbox[2] - figure_bbox[0]
                height = figure_bbox[3] - figure_bbox[1]
                area = width * height
                if area > min_size and area < max_size:
                    scale_mat = fitz.Matrix(ZOOM, ZOOM)
                    figure_pix = page.get_pixmap(matrix=scale_mat, clip=figure_bbox)
                    figure_bytes = figure_pix.tobytes("png")
                    figure_hash = hashlib.md5(figure_bytes).hexdigest()

                    figure_found = any(
                        pdf == fig["doc"]
                        and page_num == fig["page"]
                        and group_num == fig["fig"]
                        and figure_hash.startswith(fig["hash"])
                        for fig in req_figs
                    )

                    # Save the figure
                    if figure_found:
                        figure_name = f"doc{pdf}_page{page_num}_fig{group_num}_hash{figure_hash[:8]}.png"
                        figure_path = os.path.join(figures_dir, figure_name)
                        with open(figure_path, "wb") as f:
                            f.write(figure_bytes)

    return True


def find_used_fgx(answer, work_dir: str, metadatas: list):
    """Finds and saves the figures used in the LLM output to the gfx directory
    where the presentation will be compiled.
    Args:
        answer (str): The LLM answer containing names of the figures.
        work_dir (str): The working directory where the presentation will be compiled.
        metadatas (list): List of metadata dictionaries containing PDF paths.
    """
    graphics_dir = os.path.join(work_dir, "gfx")
    os.makedirs(graphics_dir, exist_ok=True)
    LOGGER.info("🌄 Images will be saved to: %s", graphics_dir)

    # Find images, which are used in the presentation
    pattern_img = re.compile(
        r"doc(?P<doc>[a-zA-Z0-9_]+)_page(?P<page>\d+)_img(?P<img>\d+)_hash(?P<hash>[a-fA-F0-9]{8})\.png"
    )
    matches_img = pattern_img.finditer(answer.text)

    req_imgs = []
    for match in matches_img:
        req_img = {
            "doc": match.group("doc"),
            "page": int(match.group("page")),
            "img": int(match.group("img")),
            "hash": match.group("hash"),
        }
        req_imgs.append(req_img)

    # Find figures, which are used in the presentation
    pattern_fig = re.compile(
        r"doc(?P<doc>[a-zA-Z0-9_]+)_page(?P<page>\d+)_fig(?P<fig>\d+)_hash(?P<hash>[a-fA-F0-9]{8})\.png"
    )
    matches_fig = pattern_fig.finditer(answer.text)

    req_figs = []
    for match in matches_fig:
        req_fig = {
            "doc": match.group("doc"),
            "page": int(match.group("page")),
            "fig": int(match.group("fig")),
            "hash": match.group("hash"),
        }
        req_figs.append(req_fig)

    # Save the required graphics
    for metadata in metadatas:
        save_pdf_images(metadata["pdf_path"], req_imgs, graphics_dir)
        save_pdf_figures(metadata["pdf_path"], req_figs, graphics_dir)
