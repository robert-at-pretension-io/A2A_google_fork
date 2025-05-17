import logging
import os
import sys
import click
from dotenv import load_dotenv

from agent import VertexImageGenAgent
from common.server import A2AServer
from common.server.utils import get_service_hostname
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
@click.option("--port", default=10006, type=int, help="Port to run the server on")
def main(host, port):
    """Run the Vertex AI Image Generation A2A agent."""
    
    try:
        # Check for Google Cloud project
        if not os.getenv("GOOGLE_CLOUD_PROJECT"):
            raise MissingAPIKeyError("GOOGLE_CLOUD_PROJECT environment variable is not set")
            
        # Create the agent card
        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id="image-generation",
            name="Image Generation",
            description="Generates images from text prompts using Google Vertex AI",
            tags=["image", "ai", "generation", "vertex"],
            examples=[
                "Generate an image of a cat riding a rocket",
                "Create a picture of a mountain landscape at sunset",
                "Make an image of a futuristic city with flying cars"
            ]
        )
        
        # Use service hostname from environment if available (for Docker/Tilt)
        service_host = get_service_hostname(default_host=host)
        
        agent_card = AgentCard(
            name="Vertex AI Image Generator",
            description="Generates images from text prompts using Google Vertex AI",
            version="1.0.0",
            capabilities=capabilities,
            defaultInputModes=["text", "text/plain"],
            defaultOutputModes=["text", "text/plain", "image/png", "image/jpeg"],
            skills=[skill],
            url=f"http://{service_host}:{port}/"
        )
        
        # Create the agent and task manager
        image_gen_agent = VertexImageGenAgent()
        task_manager = AgentTaskManager(agent=image_gen_agent)
        
        # Create and run the server
        server = A2AServer(
            agent_card=agent_card,
            task_manager=task_manager,
            host=host,
            port=port,
        )
        
        logger.info(f"Starting Vertex AI Image Generator agent at http://{host}:{port}/")
        # Log the URL that will be used for agent discovery
        logger.info(f"Agent card URL set to http://{service_host}:{port}/")
        server.start()
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting the server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()