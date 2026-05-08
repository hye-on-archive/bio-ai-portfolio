# Bio Paper Summarizer

## 1. Project Overview

Bio Paper Summarizer is a generative AI-based prototype designed to help users understand biomedical research papers more efficiently.

This project takes a biomedical paper abstract or research text as input and summarizes it into structured sections such as background, purpose, methods, key results, limitations, and future research ideas.

The main goal of this project is to explore how generative AI can support biomedical literature understanding.

---

## 2. Problem

Biomedical papers are often difficult to read because they contain complex terminology, experimental methods, and dense results.

For biology students, biomedical researchers, and pharmaceutical job applicants, it is important to quickly understand the core message of a paper.

However, reading papers can be time-consuming, especially for beginners or people who need to review many papers in a short time.

---

## 3. Solution

This project aims to use generative AI to summarize biomedical papers into clear and structured outputs.

Planned output sections include:

- One-sentence summary
- Research background
- Research purpose
- Experimental methods
- Key results
- Limitations
- Future research ideas
- Beginner-friendly explanation
- Important keywords

---

## 4. Target Users

- Biology students
- Biomedical researchers
- Pharmaceutical and biotechnology job applicants
- Beginners studying biomedical AI
- People who need to review biomedical papers efficiently

---

## 5. Current Features

Current implemented features:

- Basic Streamlit app interface
- Biomedical abstract input box
- Generate Summary button
- Structured summary output layout
- Prompt template for paper summarization
- Sample input and output documentation

Current status: Prototype UI / Planning stage

---

## 6. Project Structure

```text
bio-paper-summarizer/
├── README.md
├── app.py
├── requirements.txt
├── prompts/
│   └── paper_summary_prompt.md
└── examples/
    └── sample_output.md
