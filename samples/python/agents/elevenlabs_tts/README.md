# ElevenLabs TTS Agent with A2A Protocol

This sample implements a text-to-speech agent using the [ElevenLabs API](https://elevenlabs.io/docs/api-reference/text-to-speech) exposed through the A2A protocol. It converts text messages into audio files that can be played by the client.

## Features

- **Text-to-Speech Conversion**: Converts input text to realistic speech audio
- **Streaming Responses**: Provides status updates during processing
- **Multiple Voice Options**: Configurable through environment variables
- **Caching**: Saves previously generated audio to avoid duplicate API calls
- **Error Handling**: Robust error handling with automatic retries

## Prerequisites

- Python 3.9 or higher
- [UV](https://docs.astral.sh/uv/) package manager (recommended)
- ElevenLabs API Key ([sign up here](https://elevenlabs.io/))

## Setup & Running

1. Navigate to the agent directory:

   ```bash
   cd samples/python/agents/elevenlabs_tts
   ```

2. Create an environment file with your API key:

   ```bash
   echo "ELEVENLABS_API_KEY=your_api_key_here" > .env
   ```

3. Optional: Configure additional settings in the .env file:

   ```bash
   # Optional settings with defaults shown
   ELEVENLABS_MODEL=eleven_multilingual_v2
   ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Rachel voice
   ELEVENLABS_STABILITY=0.5
   ELEVENLABS_SIMILARITY=0.75
   ```

4. Run the agent:

   ```bash
   # Basic run on default port 10005
   uv run .

   # On custom host/port
   uv run . --host 0.0.0.0 --port 8080
   ```

5. In a separate terminal, run an A2A client to test:

   ```bash
   cd samples/python/hosts/cli
   uv run . --agent http://localhost:10005
   ```

## Example Usage

When connected with an A2A client, you can send text messages that will be converted to speech.

Examples:
- "Convert this message to speech"
- "Hello world! This is a test of the ElevenLabs TTS agent."
- "Generate an audio file from this text"

The agent will return both the original text and an audio file that can be played.

## A2A Protocol Integration

This agent implements the A2A protocol for standardized agent communication. It supports:

- Synchronous requests via `tasks/send`
- Streaming requests via `tasks/sendSubscribe`
- Audio file artifacts in the response

## Voice Configuration

The default configuration uses the "Rachel" voice from ElevenLabs, but you can change the voice by setting the `ELEVENLABS_VOICE_ID` environment variable to another voice ID from your ElevenLabs account.

Popular ElevenLabs voice IDs:
- Rachel (female): `21m00Tcm4TlvDq8ikWAM`
- Adam (male): `pNInz6obpgDQGcFmaJgB`
- Sam (male): `yoZ06aMxZJJ28mfd3POQ`
- Elli (female): `MF3mGyEYCl7XYWbV9V6O`

## Limitations

- Only supports text-based input
- Requires a valid ElevenLabs API key with available credits
- Limited to ElevenLabs' voice options and models
- Audio files are stored in memory, which may cause memory issues with very large files

## Troubleshooting

- If you see API errors, check your ElevenLabs API key and remaining credits
- For streaming issues, verify that your client supports audio/mpeg content types
- If the agent starts but doesn't generate audio, check your environment variables

## Learn More

- [A2A Protocol Documentation](https://google.github.io/A2A/#/documentation)
- [ElevenLabs API Documentation](https://elevenlabs.io/docs/api-reference/text-to-speech)
- [ElevenLabs Voice Library](https://elevenlabs.io/voice-library)