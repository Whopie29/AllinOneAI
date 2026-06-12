# Video & Audio Toolkit

## Features

**Transcript**
- Video/Audio → TXT (plain transcript)
- Video/Audio → SRT (timestamped subtitles)
- Speaker Identification (turn-based labeling)

**Video Processing**
- Mute Video
- Extract Audio (MP3/WAV)
- Convert Video Format (MP4/MKV/AVI/WEBM/MOV)
- Compress Video (H.264 CRF control)

**Audio Processing**
- Audio to Text (Whisper)
- Noise Reduction (spectral gating)
- Audio Format Conversion (MP3/WAV/AAC/FLAC/OGG)

## Requirements

**FFmpeg** must be installed and on PATH:
- Download: https://ffmpeg.org/download.html
- Add `C:\ffmpeg\bin` to system PATH

**Python packages:**
```bash
pip install -r requirements.txt
```

## Run
```bash
python app.py
```

> First Whisper run downloads models (~150MB for base). Larger models are more accurate but slower.
> Whisper model sizes: tiny → base → small → medium → large
