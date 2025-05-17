import logging
import os
import sys
import click
from dotenv import load_dotenv

from agent import ElevenLabsTTSAgent
from common.server import A2AServer
from common.types import (
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    MissingAPIKeyError,
)
from task_manager import AgentTaskManager

load_dotenv()  # Load environment variables from .env file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="0.0.0.0", help="Host to run the server on (use 0.0.0.0 for Docker/Kubernetes)")
@click.option("--port", default=10005, type=int, help="Port to run the server on")
def main(host, port):
    """Run the ElevenLabs TTS A2A agent."""
    
    try:
        # Check for API key
        if not os.getenv("ELEVENLABS_API_KEY"):
            raise MissingAPIKeyError("ELEVENLABS_API_KEY environment variable is not set")
            
        # Create the agent card
        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id="text-to-speech",
            name="Text to Speech",
            description="Converts text to speech using ElevenLabs API",
            tags=["tts", "audio", "speech"],
            examples=[
                "Convert this text to speech",
                "Generate audio for this message",
                "Read this text aloud"
            ]
        )
        
        agent_card = AgentCard(
            name="ElevenLabs TTS Agent",
            description="Converts text to speech using ElevenLabs API",
            version="1.0.0",
            capabilities=capabilities,
            defaultInputModes=["text", "text/plain"],
            defaultOutputModes=["text", "text/plain", "audio/mpeg"],
            skills=[skill],
            url=f"http://{host}:{port}/"
        )
        
        # Create the agent and task manager
        tts_agent = ElevenLabsTTSAgent()
        task_manager = AgentTaskManager(agent=tts_agent)
        
        # Create and run the server
        server = A2AServer(
            agent_card=agent_card,
            task_manager=task_manager,
            host=host,
            port=port,
        )
        
        logger.info(f"Starting ElevenLabs TTS agent at http://{host}:{port}/")
        server.start()
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting the server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()