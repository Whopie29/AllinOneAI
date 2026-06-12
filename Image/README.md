# Image Processing Suite

## Features
- Resize (with/without aspect ratio)
- Crop (pixel coordinates)
- Compress (JPEG quality control)
- Convert JPG ↔ PNG ↔ WEBP
- Brightness & Contrast adjustment
- Watermark (tiled text, custom color/opacity)
- Background Removal (AI via rembg)
- Background Color Change (AI + color fill)
- Image to Text OCR (EasyOCR)

## Setup
```bash
pip install -r requirements.txt
```

## Run
```bash
python app.py
```

> First OCR run downloads EasyOCR models (~100MB). Background removal also downloads a model on first use.
