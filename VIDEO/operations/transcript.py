"""Transcription: SRT, TXT, Speaker Identification via Whisper"""
import whisper
import os


def _load_model(model_size: str = "base"):
    return whisper.load_model(model_size)


def _format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def transcribe_to_txt(input_path: str, output_path: str, model_size: str = "base") -> str:
    """Transcribe video/audio to plain text file."""
    model = _load_model(model_size)
    result = model.transcribe(input_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result["text"].strip())
    return output_path


def transcribe_to_srt(input_path: str, output_path: str, model_size: str = "base") -> str:
    """Transcribe video/audio and generate SRT subtitle file."""
    model = _load_model(model_size)
    result = model.transcribe(input_path, word_timestamps=False)
    lines = []
    for i, seg in enumerate(result["segments"], 1):
        start = _format_timestamp(seg["start"])
        end = _format_timestamp(seg["end"])
        text = seg["text"].strip()
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return output_path


def transcribe_with_speakers(input_path: str, output_path: str, model_size: str = "base") -> str:
    """
    Basic speaker identification using segment-level silence gaps.
    For true diarization, pyannote.audio requires a Hugging Face token.
    This implementation labels speaker turns based on pause detection.
    """
    model = _load_model(model_size)
    result = model.transcribe(input_path, word_timestamps=False)
    segments = result["segments"]

    lines = []
    speaker = 1
    prev_end = 0.0
    GAP_THRESHOLD = 1.5  # seconds gap = new speaker

    for seg in segments:
        if seg["start"] - prev_end > GAP_THRESHOLD and prev_end > 0:
            speaker = 2 if speaker == 1 else 1
        start = _format_timestamp(seg["start"])
        end = _format_timestamp(seg["end"])
        text = seg["text"].strip()
        lines.append(f"[Speaker {speaker}] {start} --> {end}\n{text}\n")
        prev_end = seg["end"]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return output_path
