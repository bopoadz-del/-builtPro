import React from 'react';
import FileUpload from '../components/FileUpload.jsx';

/**
 * AudioPage wraps the FileUpload component to transcribe audio recordings.
 * Users can select any audio file and receive a placeholder transcript.
 */
export default function AudioPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Audio Transcription</h1>
      <p className="mb-4 text-gray-700">
        Upload an audio recording to receive a transcript. This demo uses a
        placeholder transcription engine and does not perform real
        speech‑to‑text.
      </p>
      <FileUpload
        title="Transcribe Audio Recording"
        endpoint="/api/v1/audio/transcribe"
        accept="audio/*"
      />
    </div>
  );
}