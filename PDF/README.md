# PDF Utility Suite

A desktop app for all common PDF tasks.

## Features

**PDF Operations**
- Merge PDFs
- Split PDFs (configurable pages per file)
- Compress PDFs (image optimization)
- Password protect / remove password (AES-256)

**PDF → Other Formats**
- PDF → Word (DOCX) via LibreOffice
- PDF → Excel (XLSX) via pdfplumber (table extraction)
- PDF → PPT (PPTX) via python-pptx
- PDF → Images (PNG/JPG) via PyMuPDF

**Other Formats → PDF**
- Word → PDF via LibreOffice
- Excel → PDF via LibreOffice
- PPT → PDF via LibreOffice
- Images → PDF via PyMuPDF

## Setup

```bash
pip install -r requirements.txt
```

> LibreOffice must be installed and on PATH for Word/Excel/PPT conversions.
> Download: https://www.libreoffice.org/download/download/

## Run

```bash
python app.py
```
