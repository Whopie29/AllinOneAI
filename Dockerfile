# Use an official lightweight Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=10000
ENV RENDER=true

# Set working directory
WORKDIR /app

# Install system dependencies
# - libreoffice: for converting DOCX/PPTX to PDF
# - ffmpeg: for Whisper audio transcribing & Video processing
# - libgl1-mesa-glx & libglib2.0-0: required for OpenCV and EasyOCR
# - build-essential: required for building some python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to leverage Docker cache
COPY requirements.txt .

# Install CPU version of PyTorch to keep image size small and avoid build timeouts
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install other Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn for a robust production server
RUN pip install --no-cache-dir gunicorn

# Copy the rest of the application code
COPY . .

# Expose ports
EXPOSE 10000 7860

# Run the Flask application with gunicorn using the PORT environment variable (default to 7860)
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-7860} --timeout 180 app:app"]
