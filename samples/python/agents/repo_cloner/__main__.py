import logging
import os

import click

from agent import RepoCloneAgent
from common.server import A2AServer
from common.server.utils import get_service_hostname
from common.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    MissingAPIKeyError,
)
from dotenv import load_dotenv
from task_manager import AgentTaskManager


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option('--host', default='0.0.0.0', help="Host to run the server on (use 0.0.0.0 for Docker/Kubernetes)")
@click.option('--port', default=10003, help="Port to run the server on (different from the existing agent)")
def main(host, port):
    try:
        # Check for API key only if Vertex AI is not configured
        if not os.getenv('GOOGLE_GENAI_USE_VERTEXAI') == 'TRUE':
            if not os.getenv('GOOGLE_API_KEY'):
                raise MissingAPIKeyError(
                    'GOOGLE_API_KEY environment variable not set and GOOGLE_GENAI_USE_VERTEXAI is not TRUE.'
                )

        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id='clone_git_repository',
            name='Clone Git Repository',
            description='Clone public or private Git repositories with optional branch, depth, and authentication',
            tags=['git', 'repository', 'clone'],
            examples=[
                'Clone the repository at https://github.com/user/repo.git',
                'Clone https://github.com/user/repo.git with branch main',
                'Clone the private repo at https://github.com/user/repo.git using my token'
            ],
        )
        # Use service hostname from environment if available (for Docker/Tilt)
        service_host = get_service_hostname(default_host=host)
        
        agent_card = AgentCard(
            name='Git Repository Cloner',
            description='This agent can clone public or private Git repositories from GitHub, GitLab, and other Git providers.',
            url=f'http://{service_host}:{port}/',
            version='1.0.0',
            defaultInputModes=RepoCloneAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=RepoCloneAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=RepoCloneAgent()),
            host=host,
            port=port,
        )
        
        logger.info(f"Starting Git Repository Cloner agent at http://{host}:{port}/")
        # Log the URL that will be used for agent discovery
        logger.info(f"Agent card URL set to http://{service_host}:{port}/")
        server.start()
    except MissingAPIKeyError as e:
        logger.error(f'Error: {e}')
        exit(1)
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        exit(1)


if __name__ == '__main__':
    main()