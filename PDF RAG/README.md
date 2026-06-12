# AI PDF Assistant (RAG)

## Features
- Chat with PDF (Q&A)
- PDF Summarization
- Key Points Extraction
- Important Topics Detection
- Quiz Generation
- Flashcard Generation

## Workflow
PDF → Text Extraction → Chunking → Embeddings → FAISS Vector DB → Groq LLM

## Setup
```bash
pip install -r requirements.txt
```

## Run
```bash
python app.py
```

> First run downloads the sentence-transformer embedding model (~90MB, cached after that).
> Uses Groq API with llama3-8b-8192 for fast, free inference.
