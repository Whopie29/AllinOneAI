"""Audio Operations: Audio to Text, Noise Reduction, Format Conversion"""
import os
import numpy as np
import soundfile as sf
import noisereduce as nr
import shutil
import subprocess


def _ffmpeg() -> str:
    ff = shutil.which("ffmpeg")
    if not ff:
        for p in [r"C:\ffmpeg\bin\ffmpeg.exe", r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"]:
            if os.path.isfile(p):
                return ff
        raise EnvironmentError("FFmpeg not found. Install it and add to PATH.")
    return ff


def audio_to_text(input_path: str, output_path: str, model_size: str = "base") -> str:
    """Transcribe audio file to text using Whisper."""
    import whisper
    model = whisper.load_model(model_size)
    result = model.transcribe(input_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result["text"].strip())
    return output_path


def reduce_noise(input_path: str, output_path: str) -> str:
    """Apply noise reduction to audio using noisereduce."""
    data, rate = sf.read(input_path)
    # Handle stereo by processing each channel
    if data.ndim == 2:
        reduced = np.stack([nr.reduce_noise(y=data[:, i], sr=rate) for i in range(data.shape[1])], axis=1)
    else:
        reduced = nr.reduce_noise(y=data, sr=rate)
    sf.write(output_path, reduced, rate)
    return output_path


def convert_audio(input_path: str, output_path: str) -> str:
    """Convert audio format using FFmpeg (format from output extension)."""
    ff = _ffmpeg()
    result = subprocess.run(
        [ff, "-y", "-i", input_path, output_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr[-500:]}")
    return output_path
