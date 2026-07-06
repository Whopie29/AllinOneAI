# 🚀 AllinOneAI

A powerful all-in-one Flask web application that combines **PDF tools**, **image processing**, **video & audio tools**, and **AI-powered PDF RAG querying** into a single unified interface.

---

## ✨ Features

### 📄 PDF Tools
| Feature | Description |
|---|---|
| Merge PDFs | Combine multiple PDF files into one |
| Split PDF | Split a PDF into chunks by page count |
| Compress PDF | Reduce PDF file size by compressing embedded images |
| Password Protect | Encrypt a PDF with AES-256 password protection |
| Remove Password | Decrypt and unlock a password-protected PDF |
| PDF → Word | Convert PDF to `.docx` using pdf2docx |
| PDF → Excel | Extract tables from PDF into `.xlsx` |
| PDF → PowerPoint | Convert PDF pages to `.pptx` slides |
| PDF → Images | Export each PDF page as a PNG image |
| Word → PDF | Convert `.docx` to PDF (MS Word on Windows / LibreOffice on Linux) |
| Excel → PDF | Convert `.xlsx` to PDF using ReportLab |
| PPT → PDF | Convert `.pptx` to PDF |
| Images → PDF | Combine multiple images into a single PDF |

### 🖼️ Image Tools
| Feature | Description |
|---|---|
| Resize | Resize with optional aspect ratio preservation |
| Crop | Crop to specified pixel coordinates |
| Compress | Reduce JPEG quality for smaller file size |
| Compress to Size | Binary-search compression to hit a target file size (KB) |
| Convert Format | Convert between JPG, PNG, and WEBP |
| Brightness & Contrast | Adjust image brightness and contrast |
| Watermark | Add tiled diagonal text watermark |
| Remove Background | AI-powered background removal using `rembg` |
| Change Background Color | Remove background and replace with a solid color |
| Image to Text (OCR) | Extract text from images using EasyOCR |

### 🎬 Video & Audio Tools
| Feature | Description |
|---|---|
| Mute Video | Strip audio track from a video file |
| Extract Audio | Extract audio from video as MP3 |
| Convert Video | Convert between video formats via FFmpeg |
| Compress Video | Compress video using H.264 CRF encoding |
| Audio to Text | Transcribe audio using OpenAI Whisper |
| Noise Reduction | Reduce background noise from audio using `noisereduce` |
| Convert Audio | Convert between audio formats via FFmpeg |
| Transcribe to TXT | Transcribe video/audio to a plain text file |
| Transcribe to SRT | Generate `.srt` subtitle file from video/audio |
| Speaker Identification | Basic speaker-turn detection from transcription segments |

### 🤖 PDF RAG (AI Q&A)
Powered by **LangChain + Groq (LLaMA 3.3 70B)** with **FAISS** vector search and **sentence-transformers** embeddings.

| Feature | Description |
|---|---|
| Ask Questions | Chat with your PDF using RAG retrieval |
| Summarize | Generate a concise summary of the document |
| Key Points | Extract the most important facts and conclusions |
| Topic Detection | Identify and describe main themes |
| Quiz Generator | Auto-generate multiple-choice quiz questions |
| Flashcard Generator | Create study flashcards from document content |

---

## 🗂️ Project Structure

```
aioai/
├── app.py                  # Main Flask application (unified entry point)
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker container configuration
├── .env                    # Environment variables (GROQ_API_KEY, etc.)
│
├── PDF/
│   └── operations/
│       ├── pdf_ops.py      # Merge, split, compress, password operations
│       └── convert.py      # PDF ↔ Word/Excel/PPT/Images conversions
│
├── Image/
│   └── operations/
│       ├── img_ops.py      # Resize, crop, compress, watermark, convert
│       └── ai_ops.py       # Background removal, color change, OCR
│
├── VIDEO/
│   └── operations/
│       ├── video_ops.py    # Mute, extract audio, convert, compress
│       ├── audio_ops.py    # Audio transcription, noise reduction, convert
│       └── transcript.py   # Whisper TXT/SRT/speaker transcription
│
├── PDF RAG/
│   └── rag/
│       ├── loader.py       # PDF loading and chunking
│       ├── embeddings.py   # FAISS vector store creation
│       └── chain.py        # LangChain LCEL chains (Q&A, summary, quiz, etc.)
│
├── templates/              # Jinja2 HTML templates
│   ├── layout.html
│   ├── index.html
│   ├── pdf.html
│   ├── image.html
│   ├── video.html
│   └── rag.html
│
└── static/
    ├── uploads/            # Temporary uploaded files
    └── outputs/            # Processed output files
```

---

## ⚙️ Prerequisites

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/download.html) installed and available in `PATH`
- LibreOffice (Linux only, for DOCX/PPTX → PDF conversion)
- A [Groq API key](https://console.groq.com/) for the PDF RAG feature

---

## 🚀 Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/aioai.git
cd aioai
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

> PyTorch is installed separately first to ensure CPU-only version compatibility.

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### 5. Run the application

```bash
python app.py
```

The app will be available at `http://localhost:5000`.

---

## 🐳 Docker

### Build and run locally

```bash
docker build -t aioai .
docker run -p 7860:7860 -e GROQ_API_KEY=your_key_here aioai
```

The app will be available at `http://localhost:7860`.

### What the Dockerfile does

- Base image: `python:3.12-slim`
- Installs system dependencies: `libreoffice`, `ffmpeg`, `libgl1`, `libglib2.0-0`
- Installs CPU PyTorch separately for compatibility
- Serves the app via **Gunicorn** with a 180-second timeout
- Exposes ports `7860` (Hugging Face Spaces) and `10000`

---

## ☁️ Deploy on Hugging Face Spaces

This project is ready to deploy on [Hugging Face Spaces](https://huggingface.co/spaces) using the Docker SDK.

1. Create a new Space with **Docker** as the SDK
2. Push this repository to the Space
3. Add your `GROQ_API_KEY` as a Space secret under **Settings → Repository secrets**

The `app_port: 7860` is already configured in the Space metadata.

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes (for RAG) | Groq API key for LLaMA 3.3 70B inference |
| `PORT` | No | Server port (defaults to `7860`) |

---

## 🛠️ Tech Stack

| Category | Libraries |
|---|---|
| Web Framework | Flask |
| PDF Processing | PyMuPDF (fitz), pdfplumber, pdf2docx, ReportLab |
| Office Conversion | python-pptx, openpyxl, docx2pdf, LibreOffice |
| Image Processing | Pillow, OpenCV, rembg, EasyOCR |
| Video & Audio | FFmpeg, MoviePy, OpenAI Whisper, noisereduce, soundfile |
| AI / RAG | LangChain, LangChain-Groq, FAISS, sentence-transformers |
| LLM | Groq (LLaMA 3.3 70B Versatile) |
| Server | Gunicorn |

---

## 📝 License

This project is open source and available under the [MIT License](LICENSE).
