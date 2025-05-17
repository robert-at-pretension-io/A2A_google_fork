# Vertex AI Image Generation Agent with A2A Protocol

This sample implements an image generation agent using the [Google Cloud Vertex AI Imagen API](https://cloud.google.com/vertex-ai/docs/generative-ai/image/image-generation-overview) exposed through the A2A protocol. It generates images based on text prompts provided by the user.

## Features

- **Text-to-Image Generation**: Converts text prompts into high-quality images
- **Streaming Responses**: Provides status updates during processing
- **Configurable Parameters**: Control image aspect ratio, safety filters, and more
- **Caching**: Saves previously generated images to avoid duplicate API calls
- **Error Handling**: Robust error handling with automatic retries

## Prerequisites

- Python 3.11 or higher
- [UV](https://docs.astral.sh/uv/) package manager (recommended)
- Google Cloud Vertex AI API access ([setup instructions](https://cloud.google.com/vertex-ai/docs/start/cloud-environment))
- Authentication setup with Application Default Credentials

## Setup & Running

1. Navigate to the agent directory:

   ```bash
   cd samples/python/agents/vertex_image_gen
   ```

2. Set up Google Cloud authentication:

   ```bash
   # Login with application default credentials
   gcloud auth application-default login
   
   # Set your project ID in an environment variable
   echo "GOOGLE_CLOUD_PROJECT=your-project-id-here" > .env
   ```

3. Optional: Configure additional settings in the .env file:

   ```bash
   # Optional settings with defaults shown
   VERTEX_MODEL=imagen-3.0-generate-002
   VERTEX_LOCATION=us-central1
   VERTEX_ASPECT_RATIO=1:1
   VERTEX_SAFETY_FILTER=block_medium_and_above
   VERTEX_LANGUAGE=en
   ```

4. Run the agent:

   ```bash
   # Basic run on default port 10006
   uv run .
   
   # On custom host/port
   uv run . --host 0.0.0.0 --port 8080
   ```

5. In a separate terminal, run an A2A client to test:

   ```bash
   cd samples/python/hosts/cli
   uv run . --agent http://localhost:10006
   ```

## Example Usage

When connected with an A2A client, you can send text prompts that will be converted to images.

Examples:
- "Generate an image of a cat riding a rocket"
- "Create a picture of a mountain landscape at sunset"
- "Make an image of a futuristic city with flying cars"

The agent will return both the original prompt and the generated image.

## A2A Protocol Integration

This agent implements the A2A protocol for standardized agent communication. It supports:

- Synchronous requests via `tasks/send`
- Streaming requests via `tasks/sendSubscribe`
- Image file artifacts in the response

## Image Configuration

You can configure the image generation parameters by setting environment variables:

- `VERTEX_MODEL`: The model ID to use (default: "imagen-3.0-generate-002")
- `VERTEX_LOCATION`: The GCP region to use (default: "us-central1")
- `VERTEX_ASPECT_RATIO`: Image aspect ratio (default: "1:1", options include "16:9", "4:3", etc.)
- `VERTEX_SAFETY_FILTER`: Safety filter level (default: "block_medium_and_above")
- `VERTEX_LANGUAGE`: Prompt language code (default: "en")

## Limitations

- Only supports text-based prompts
- Requires Google Cloud Vertex AI API access and proper authentication
- Subject to Google Cloud Vertex AI quotas and pricing
- Generated images are stored locally, consuming disk space over time

## Troubleshooting

- If you see API errors, check your Google Cloud authentication and project setup
- For quota issues, review your Google Cloud Vertex AI quota limits
- If the agent starts but doesn't generate images, check your environment variables and permissions

## Learn More

- [A2A Protocol Documentation](https://google.github.io/A2A/#/documentation)
- [Vertex AI Imagen Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/image/overview)
- [Google Cloud Authentication](https://cloud.google.com/docs/authentication/application-default-credentials)