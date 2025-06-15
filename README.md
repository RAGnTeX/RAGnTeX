---
title: RAGnTeX
emoji: 📄
colorFrom: indigo
colorTo: pink
sdk: docker
pinned: false
---

# 📚 From Text to Visuals: Auto-Generating LaTeX Beamer Presentations with GenAI

In this project, we explore how generative AI can automate the creation of professional-looking presentation slides—directly from extensive collections of PDF documents.

---

## 🧠 Use Case

Creating slide decks from dense documents (like whitepapers or scientific articles) is a time-consuming and cognitively heavy task. Our goal is to streamline this process using generative AI.

We built an AI assistant that transforms document collections into LaTeX Beamer presentations—complete with structure, content, and visuals—based on a user-defined topic.

---

## 🔍 How It Works

### 💿 Database Creation
We start by creating a vector database from a collection of PDF documents (e.g., arXiv papers). Each document is processed to extract text chunks, and for each chunk, we store:
* **Embeddings** of the text from the file
* **Associated metadata** (like images, their captions, how many images there are)

### 🗣️ User Prompt

A user enters a natural language query like:

> "I need a presentation about AI agents."

### 📄 Document Retrieval

We use **Chroma** as our vector database to retrieve the most relevant PDF documents based on the query.

### 🧠 Content Understanding

Using **Gemini 2.0 Flash** (`google-genai==1.7.0`), the assistant analyzes the retrieved content and extracts the most relevant ideas and insights.

### 🎞️ Slide Generation (LaTeX Beamer)

The model outputs fully formatted compilable LaTeX code following a clear and consistent structure:

- **Introduction**: Topic overview and motivation  
- **Main Content**: 2–4 slides, each presenting a core idea  
- **Summary**: Key takeaways  

It also incorporates relevant images extracted from the documents, organizing them into LaTeX Beamer-friendly layouts (e.g., *Core Idea 2* and *Core Idea 3* slide formats).

### Prerequisites

This project requires the LaTeX toolchain, specifically `pdflatex`, to generate PDF presentations.

Please install it before running the project:

### On Debian/Ubuntu:

```bash
sudo apt-get update && sudo apt-get install -y texlive-latex-base texlive-fonts-recommended texlive-latex-extra


### Run docker:
```bash
docker run \
  --env-file .env \
  -e IN_DOCKER=true \
  -p 7860:7860 \
  -v /path/to/your/output:/app/output \
  ragntex
