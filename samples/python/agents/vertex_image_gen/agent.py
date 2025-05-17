import os
import base64
import hashlib
import time
import pathlib
import logging
from typing import Any, Dict, List, Optional

import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from google.api_core.exceptions import ResourceExhausted
from tenacity import retry, stop_after_attempt, wait_exponential

from common.types import (
    Artifact,
    Message,
    Part,
    FilePart,
    TaskState,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class VertexImageGenAgent:
    """An agent that generates images using Google Cloud Vertex AI Imagen API."""

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain', 'image/png', 'image/jpeg']
    MAX_RETRIES = 5
    
    def __init__(self):
        self._project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not self._project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is not set")
        
        # Default model and generation settings
        self._model_name = os.getenv("VERTEX_MODEL", "imagen-3.0-generate-002")
        self._location = os.getenv("VERTEX_LOCATION", "us-central1")
        self._aspect_ratio = os.getenv("VERTEX_ASPECT_RATIO", "1:1")
        self._safety_filter = os.getenv("VERTEX_SAFETY_FILTER", "block_medium_and_above")
        self._language = os.getenv("VERTEX_LANGUAGE", "en")
        
        # Cache for storing generated images
        self._cache = {}
        
        # Create output directory for saving images
        self._output_dir = os.path.join(os.getcwd(), "generated_images")
        pathlib.Path(self._output_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Generated images will be saved to: {self._output_dir}")
        
        # Initialize Vertex AI
        try:
            vertexai.init(project=self._project_id, location=self._location)
            self._model = ImageGenerationModel.from_pretrained(self._model_name)
            logger.info(f"Initialized Vertex AI with model: {self._model_name}")
        except Exception as e:
            logger.error(f"Error initializing Vertex AI: {e}")
            raise

    def get_processing_message(self) -> str:
        return "Generating image from prompt..."

    def invoke(self, prompt: str, session_id: str) -> Dict[str, Any]:
        """Generate an image from a text prompt using Vertex AI."""
        try:
            # Sanitize prompt
            prompt = prompt.strip()
            if not prompt:
                return {"error": "Empty prompt. Please provide a description for the image you want to generate."}
            
            # Check cache first using hash of prompt and parameters
            cache_key = hashlib.md5(f"{prompt}_{self._model_name}_{self._aspect_ratio}_{self._safety_filter}".encode()).hexdigest()
            if cache_key in self._cache:
                logger.info(f"Using cached image for prompt: {prompt[:30]}...")
                return self._cache[cache_key]
            
            # Generate new image
            logger.info(f"Generating new image for prompt: {prompt[:30]}...")
            image_path, image_bytes = self._generate_image(prompt)
            
            # Create response
            response = self._format_response(image_path, image_bytes, prompt)
            
            # Cache the result
            self._cache[cache_key] = response
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return {
                "error": str(e),
                "prompt": prompt
            }

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(MAX_RETRIES),
        retry=lambda retry_state: isinstance(
            retry_state.outcome.exception(), ResourceExhausted
        ),
        reraise=True,
    )
    def _generate_image(self, prompt: str) -> tuple[str, bytes]:
        """Generate image from prompt using Vertex AI Imagen API."""
        try:
            # Generate the image
            images = self._model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio=self._aspect_ratio,
                language=self._language,
                safety_filter_level=self._safety_filter,
            )
            
            if not images:
                raise Exception("No images were generated")
            
            # Create a filename based on the prompt
            words = prompt.split()
            short_text = "_".join(words[:5]) if len(words) > 0 else "image"
            # Replace characters that might cause issues in filenames
            short_text = "".join(c if c.isalnum() or c in "_- " else "_" for c in short_text)
            short_text = short_text[:40]  # Limit length
            
            filename = f"{short_text}_{hashlib.md5(prompt.encode()).hexdigest()[:8]}.png"
            file_path = os.path.join(self._output_dir, filename)
            
            # Save the image file to disk
            images[0].save(location=file_path, include_generation_parameters=False)
            logger.info(f"Saved image to: {file_path}")
            
            # Read image bytes for response
            with open(file_path, "rb") as f:
                image_bytes = f.read()
            
            return file_path, image_bytes
            
        except ResourceExhausted as e:
            logger.warning(f"Resource exhausted error (will retry): {e}")
            raise
        except Exception as e:
            logger.error(f"Error in image generation: {e}")
            raise

    def _format_response(self, image_path: str, image_bytes: bytes, prompt: str) -> Dict[str, Any]:
        """Format the API response as an A2A compatible structure."""
        # Encode image data as base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Get the filename from the path
        filename = os.path.basename(image_path)
        
        # Create response with both prompt and image file
        return {
            "prompt": prompt,
            "image_file": {
                "filename": filename,
                "content": image_b64,
                "mime_type": "image/png",
                "local_path": image_path  # Added for reference
            }
        }