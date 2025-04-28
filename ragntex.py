import os
import re
from datetime import datetime
from dotenv import load_dotenv

from src.database import db, embed_fn
from src.document_processing import process_documents
from src.images_processing import save_pdf_images, save_pdf_figures
from src.latex_compilation import CompilePresentation
from src.prompt import prompt
from src.google_client import client


load_dotenv()
load_dotenv("../.env")
MAIN_DIR = os.getenv("MAIN_DIR")

# Get all the existing papers in the database
all_entries = db.get(include=["metadatas"])
existing_pdfs = [meta.get("source_pdf") for meta in all_entries["metadatas"]]

# Dataset
dataset = MAIN_DIR + "dataset/"
files = os.listdir(dataset)

print("Looking for new PDFs to append to our database...")
# Look for new PDFs to append to our database
pdf_files = [
    os.path.join(dataset, f)
    for f in files
    if f.lower().endswith(".pdf") and f not in existing_pdfs
]

documents, metadatas = process_documents(pdf_files)
print("Adding new PDFs to the database...")
# Fill in the database
if documents:
    db.add(
        documents=documents,
        ids=[str(i) for i in range(len(documents))],
        metadatas=metadatas,
    )

# Prompting
print("Retrieving relevant documents...")
embed_fn.document_mode = False
query = "I need a presentation about AI agents."
query_oneline = query.replace(
    "\n", " "
)  # (Optional) For cleaner input in case of newlines
result = db.query(query_texts=[query], n_results=2)
[documents] = result["documents"]
[metadatas] = result["metadatas"]


for passage, metas in zip(documents, metadatas):
    passage_oneline = passage.replace("\n", " ")
    images_passage = metas["images_passage"]

    prompt += f"PASSAGE: {passage_oneline}\n"
    prompt += f"IMAGES: {images_passage}\n"

# Create a new subfolder
print("Creating new subfolder...")
base_path = MAIN_DIR + "output/"
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
work_dir = os.path.join(base_path, timestamp)
os.makedirs(work_dir, exist_ok=False)
print(f"📁 Created folder: {work_dir}")

# Generate the presentation code
model_name = "gemini-2.0-flash"
# model_name = "gemini-2.5-flash-preview-04-17"
print("Generating response...")
answer = client.models.generate_content(model=model_name, contents=prompt)
print(f"🎲 Generated the response using: {model_name}")

# Create a subfolder for graphics
graphics_dir = os.path.join(work_dir, "gfx")
os.makedirs(graphics_dir, exist_ok=True)
print(f"🌄 Images will be saved to: {graphics_dir}")

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

print("Compiling presentation...")
CompilePresentation(answer.text, work_dir)
