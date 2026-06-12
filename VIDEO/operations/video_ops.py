"""Video Operations: Mute, Extract Audio, Convert, Compress via FFmpeg + MoviePy"""
import subprocess
import shutil
import os


def _ffmpeg() -> str:
    ff = shutil.which("ffmpeg")
    if not ff:
        # Common Windows install paths
        for p in [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        ]:
            if os.path.isfile(p):
                return p
        raise EnvironmentError("FFmpeg not found. Install it and add to PATH.")
    return ff


def _run(cmd: list[str]):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr[-500:]}")


def mute_video(input_path: str, output_path: str) -> str:
    """Remove audio track from video."""
    _run([_ffmpeg(), "-y", "-i", input_path, "-an", "-c:v", "copy", output_path])
    return output_path


def extract_audio(input_path: str, output_path: str) -> str:
    """Extract audio from video to MP3/WAV/etc based on output extension."""
    _run([_ffmpeg(), "-y", "-i", input_path, "-vn", "-acodec", "libmp3lame", "-q:a", "2", output_path])
    return output_path


def convert_video(input_path: str, output_path: str) -> str:
    """Convert video format using FFmpeg (format inferred from output extension)."""
    _run([_ffmpeg(), "-y", "-i", input_path, output_path])
    return output_path


def compress_video(input_path: str, output_path: str, crf: int = 28) -> str:
    """
    Compress video using H.264 with CRF quality control.
    crf: 18=high quality, 28=default, 40=low quality
    """
    _run([
        _ffmpeg(), "-y", "-i", input_path,
        "-vcodec", "libx264", "-crf", str(crf),
        "-preset", "medium", "-acodec", "aac",
        output_path
    ])
    return output_path
