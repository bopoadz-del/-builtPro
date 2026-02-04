"""
Service functions to handle audio recording and transcription.

This module provides a placeholder implementation to accept an audio
file and return basic metadata along with a dummy transcript. It lays
the foundation for integrating real speech-to-text models (e.g. Whisper,
Google Speech-to-Text, AWS Transcribe) in future iterations.

The current implementation reads the raw bytes, attempts to detect
basic properties using the built-in `wave` module (when the audio is
WAV format), and returns the duration and file size. A dummy
transcription is included as a placeholder.
"""

from pathlib import Path
from typing import Any, Dict
import wave


def _get_wav_metadata(file_path: Path) -> Dict[str, Any]:
    """Try to extract metadata from a WAV file.

    Args:
        file_path: Path to the audio file.

    Returns:
        A dictionary with sample rate, channels and duration in seconds.
        If the file is not a valid WAV or cannot be parsed, returns an
        empty dict.
    """
    try:
        with wave.open(str(file_path), 'rb') as wav_file:
            params = wav_file.getparams()
            n_channels, sampwidth, framerate, n_frames = params[:4]
            duration = n_frames / float(framerate) if framerate > 0 else 0
            return {
                "sample_rate": framerate,
                "channels": n_channels,
                "duration_seconds": round(duration, 2),
            }
    except Exception:
        return {}


def transcribe_audio_file(file_path: Path) -> Dict[str, Any]:
    """
    Transcribe an uploaded audio file and return metadata and transcript.

    This placeholder implementation does not perform real speech-to-text.
    Instead, it reads basic audio metadata (if possible) and returns a
    hardcoded transcript message. This function should be replaced with
    actual transcription logic in production (e.g., calling a speech
    recognition library or external API).

    Args:
        file_path: Path to the uploaded audio file.

    Returns:
        A dictionary containing the filename, file size, extracted
        metadata and a dummy transcript.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file {file_path} does not exist")

    file_size = file_path.stat().st_size
    metadata: Dict[str, Any] = {}
    # Try WAV metadata extraction
    if file_path.suffix.lower() == '.wav':
        metadata = _get_wav_metadata(file_path)

    # Provide a placeholder transcript
    transcript = """
    [Transcription placeholder]
    This is a dummy transcript because the system does not yet
    implement real speech-to-text. In future iterations, this will
    contain the recognized words from the audio recording.
    """.strip()

    return {
        "filename": file_path.name,
        "file_size": file_size,
        "metadata": metadata,
        "transcript": transcript,
    }