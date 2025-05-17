import os
import base64
import requests
import time
from typing import Any, Dict, List, Optional

from common.types import (
    Artifact,
    Message,
    Part,
    FilePart,
    TaskState,
    TaskStatus,
)


class ElevenLabsTTSAgent:
    """An agent that generates speech using ElevenLabs TTS API."""

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain', 'audio/mpeg']
    API_HOST = "https://api.elevenlabs.io"
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds

    def __init__(self):
        self._api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self._api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable is not set")
        
        # Default model and voice settings
        self._model = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")
        self._voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default voice - Rachel
        self._stability = float(os.getenv("ELEVENLABS_STABILITY", "0.5"))
        self._similarity_boost = float(os.getenv("ELEVENLABS_SIMILARITY", "0.75"))
        
        # Cache for storing generated audio
        self._cache = {}
        
        # Create output directory for saving audio files
        self._output_dir = os.path.join(os.getcwd(), "generated_audio")
        os.makedirs(self._output_dir, exist_ok=True)
        print(f"Generated audio will be saved to: {self._output_dir}")

    def get_processing_message(self) -> str:
        return "Generating audio from text..."

    def invoke(self, text: str, session_id: str) -> Dict[str, Any]:
        """Convert text to speech using ElevenLabs API."""
        try:
            # Check cache first
            cache_key = f"{text}_{self._voice_id}_{self._model}"
            if cache_key in self._cache:
                print(f"Using cached audio for: {text[:30]}...")
                return self._format_response(self._cache[cache_key], text)
            
            # Generate new audio
            print(f"Generating new audio for: {text[:30]}...")
            audio_data = self._generate_audio(text)
            
            # Cache the result
            self._cache[cache_key] = audio_data
            
            return self._format_response(audio_data, text)
            
        except Exception as e:
            # Return error message
            print(f"Error generating audio: {e}")
            return {
                "error": str(e),
                "text": text
            }

    def _generate_audio(self, text: str) -> bytes:
        """Generate audio from text using ElevenLabs API."""
        url = f"{self.API_HOST}/v1/text-to-speech/{self._voice_id}/stream"
        
        payload = {
            "text": text,
            "model_id": self._model,
            "voice_settings": {
                "stability": self._stability,
                "similarity_boost": self._similarity_boost,
            },
        }
        
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        for retry in range(self.MAX_RETRIES):
            try:
                with requests.post(url, headers=headers, json=payload, stream=True, timeout=300) as r:
                    if r.status_code != 200:
                        error_msg = f"API error: {r.status_code} - {r.text}"
                        if retry < self.MAX_RETRIES - 1:
                            time.sleep(self.RETRY_DELAY)
                            continue
                        raise Exception(error_msg)
                    
                    # Read the entire response into memory
                    audio_data = bytearray()
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            audio_data.extend(chunk)
                    
                    if len(audio_data) == 0:
                        error_msg = "Empty response from API"
                        if retry < self.MAX_RETRIES - 1:
                            time.sleep(self.RETRY_DELAY)
                            continue
                        raise Exception(error_msg)
                    
                    return bytes(audio_data)
                    
            except requests.exceptions.RequestException as e:
                if retry < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                else:
                    raise Exception(f"Network error: {str(e)}")
                    
        # If we get here, all retries failed
        raise Exception(f"Failed after {self.MAX_RETRIES} attempts")

    def _format_response(self, audio_data: bytes, text: str) -> Dict[str, Any]:
        """Format the API response as an A2A compatible structure."""
        # Encode audio data as base64
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Generate a filename based on first few words of text
        words = text.split()
        short_text = "_".join(words[:3]) if len(words) > 0 else "speech"
        # Replace characters that might cause issues in filenames
        short_text = "".join(c if c.isalnum() or c in "_- " else "_" for c in short_text)
        short_text = short_text[:40]  # Limit length
        
        filename = f"{short_text}_{hash(text) % 10000}.mp3"
        file_path = os.path.join(self._output_dir, filename)
        
        # Save the audio file to disk
        with open(file_path, "wb") as f:
            f.write(audio_data)
        
        print(f"Saved audio file to: {file_path}")
        print(f"Audio base64 length: {len(audio_b64)}, first 50 chars: {audio_b64[:50]}...")
        
        # Create response with both text and audio file
        # Make sure we're including the base64 encoded audio data
        response = {
            "text": text,
            "audio_file": {
                "filename": filename,
                "content": audio_b64,
                "mime_type": "audio/mpeg",
                "local_path": file_path  # Added for reference
            }
        }
        
        print(f"Response audio_file content type: {type(response['audio_file']['content'])}")
        return response