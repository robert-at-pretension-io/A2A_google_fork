# Sample Agents

All the agents in this directory are samples built on different frameworks highlighting different capabilities. Each agent runs as a standalone A2A server.

> **Related Documentation**:
> - [Main A2A Protocol Documentation](https://google.github.io/A2A/)
> - [Main Project README](/README.md)
> - [Local Docker Deployment](/deploy/local/README.md)
> - [Kubernetes Deployment](/deploy/kubernetes/README.md)
> - [Host Apps Documentation](/samples/python/hosts/README.md)

Each agent can be run as its own A2A server with the instructions in its README. By default, each will run on a separate port on localhost (you can use command line arguments to override).

To interact with the servers, use an A2AClient in a host app (such as the [CLI](/samples/python/hosts/cli/README.md)).

## Creating a New Agent

This guide walks you through creating a new agent that works with the A2A protocol. For real-world examples, check out any of the [sample agents](#sample-agents-directory) listed below, particularly the [repo_cloner](/samples/python/agents/repo_cloner) for a simpler implementation or [google_adk](/samples/python/agents/google_adk) for a more comprehensive one.

### Step 1: Create Directory Structure

```
your_agent_name/
├── __init__.py         # Empty file to make the directory a package
├── __main__.py         # Entry point with click CLI
├── agent.py            # Main agent logic
├── task_manager.py     # A2A task handling
├── pyproject.toml      # Project configuration
└── README.md           # Documentation
```

### Step 2: Set Up Configuration Files

#### Create pyproject.toml:

```toml
[project]
name = "a2a-sample-agent-your-agent-name"
version = "0.1.0"
description = "Your agent description"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "a2a-samples",       # Core A2A protocol handling
    "click>=8.1.8",      # CLI argument parsing
    "python-dotenv>=1.0.0",  # Environment variable loading
    # Add framework-specific dependencies here
]

# Required for proper package building
[tool.hatch.build.targets.wheel]
packages = ["."]

# This enables using the local a2a-samples package
[tool.uv.sources]
a2a-samples = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### Update Root pyproject.toml:

Add your agent to the workspace members list in `/samples/python/pyproject.toml`:

```toml
[tool.uv.workspace]
members = [
    # Existing members...
    "agents/your_agent_name"
]
```

### Step 3: Implement Your Agent

#### agent.py:

```python
class YourAgent:
    """Your agent implementation."""
    
    # Content types your agent can process and return
    # Common types: 'text', 'text/plain', 'image', 'audio', 'data'
    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']
    
    def __init__(self):
        """Initialize your agent with any necessary configuration."""
        # Setup agent-specific resources (API clients, models, etc.)
        self._session_data = {}  # Optional: track session state
    
    def get_processing_message(self) -> str:
        """Return message shown during processing (for streaming updates)."""
        return "Processing your request..."
    
    def invoke(self, query: str, session_id: str) -> dict:
        """Process a request and return a response.
        
        Args:
            query: The text query from the user
            session_id: Unique ID for the conversation session
            
        Returns:
            Dict with response data, typically:
            {
                "text": "Your text response",
                # Optional: additional data based on content types
                "images": [...],  # For image content
                "audio": {...},   # For audio content
                "data": {...}     # For structured data
            }
        """
        # Your core agent logic goes here
        
        # Example: maintain session context
        if session_id not in self._session_data:
            self._session_data[session_id] = {"history": []}
        self._session_data[session_id]["history"].append(query)
        
        # Process the query with your agent implementation
        response = f"You said: {query}"
        
        return {"text": response}
```

#### task_manager.py:

For most agents, you can use one of these approaches:

1. **Basic implementation** - Import from common server module:
```python
from common.server.task_manager import AgentTaskManager, BaseAgentWithTaskManager as AgentWithTaskManager
```

2. **Advanced implementation** - Create custom task manager if needed (see google_adk or repo_cloner examples).

### Step 4: Create Entry Point

#### __main__.py:

```python
import os
import logging
import click
from dotenv import load_dotenv
from common.server import A2AServer
from common.server.utils import get_service_hostname  # For Docker/Kubernetes support
from common.types import AgentCapabilities, AgentCard, AgentSkill

from agent import YourAgent
from task_manager import AgentTaskManager

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option('--host', default='0.0.0.0', help="Host to run on (use 0.0.0.0 for Docker/Kubernetes)")
@click.option('--port', default=10010, help="Port to run on (choose a unique port)")
def main(host, port):
    """Run your agent as an A2A server."""
    try:
        # Create agent capabilities and skills
        capabilities = AgentCapabilities(
            streaming=True,            # Enable streaming responses 
            pushNotifications=False,   # Set to True if supported
            stateTransitionHistory=False
        )
        
        # Define the agent's skills
        skill = AgentSkill(
            id="your_skill_id",        # Unique identifier for this skill
            name="Your Skill Name",    # Display name
            description="Description of what your agent does",
            tags=["tag1", "tag2"],     # For categorization
            examples=[
                "Example query 1",      # Example prompts to show users
                "Example query 2"
            ]
        )
        
        # Get hostname for Docker/Kubernetes compatibility
        service_host = get_service_hostname(default_host=host)
        
        # Create the agent card (metadata)
        agent_card = AgentCard(
            name="Your Agent Name",
            description="Your agent description",
            url=f"http://{service_host}:{port}/",  # Used for discovery
            version="1.0.0",
            defaultInputModes=YourAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=YourAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )
        
        # Create agent instance and task manager
        your_agent = YourAgent()
        task_manager = AgentTaskManager(agent=your_agent)
        
        # Create and start the A2A server
        server = A2AServer(
            agent_card=agent_card,
            task_manager=task_manager,
            host=host,
            port=port,
        )
        
        logger.info(f"Starting your agent at http://{host}:{port}/")
        logger.info(f"Agent card URL set to http://{service_host}:{port}/")
        server.start()
        
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)

if __name__ == '__main__':
    main()
```

### Step 5: Create README.md

Create a comprehensive README.md that explains:
- What your agent does
- Prerequisites
- Setup and running instructions
- Example usage with sample prompts
- Any special configuration needed

### Step 6: Test Your Agent

```bash
# Install dependencies
cd samples/python
uv pip install -e .

# Run your agent
cd agents/your_agent_name
uv run .
```

### Step 7: Register with Deployment

#### For Local Docker Deployment:

Update the docker-compose.yaml file in `/deploy/local/`:
- Add a new service entry for your agent
- Set the correct port mapping
- Add any necessary environment variables

Also update the local README.md in `/deploy/local/README.md` to add your agent information.

#### For Kubernetes Deployment:

Add Kubernetes manifests in `/deploy/kubernetes/manifests/agents/your_agent_name/`:
- Create deployment.yaml
- Create service.yaml

Update the kustomization.yaml in `/deploy/kubernetes/kustomize/base/` to include your agent's manifests.

### Step 8: Integrate with Existing Documentation

Update the following documentation files:
- Main README.md to add your agent to the list
- This agents README.md to add to the Sample Agents Directory 
- Deployment README files to include your agent's information

For examples, look at how existing agents are documented and follow the same pattern.

## Sample Agents Directory

* [**Google ADK**](/samples/python/agents/google_adk/README.md)  
Sample agent to (mock) fill out expense reports. Showcases multi-turn interactions and returning/replying to webforms through A2A.

* [**AG2 MCP Agent with A2A Protocol**](/samples/python/agents/ag2/README.md)  
Demonstrates an MCP-enabled agent built with [AG2](https://github.com/ag2ai/ag2) that is exposed through the A2A protocol.

* [**LangGraph**](/samples/python/agents/langgraph/README.md)  
Sample agent which can convert currency using tools. Showcases multi-turn interactions, tool usage, and streaming updates. 

* [**CrewAI**](/samples/python/agents/crewai/README.md)  
Sample agent which can generate images. Showcases multi-turn interactions and sending images through A2A.

* [**LlamaIndex**](/samples/python/agents/llama_index_file_chat/README.md)  
Sample agent which can parse a file and then chat with the user using the parsed content as context. Showcases multi-turn interactions, file upload and parsing, and streaming updates. 

* [**Marvin Contact Extractor Agent**](/samples/python/agents/marvin/README.md)  
Demonstrates an agent using the [Marvin](https://github.com/prefecthq/marvin) framework to extract structured contact information from text, integrated with the Agent2Agent (A2A) protocol.

* [**Enterprise Data Agent**](/samples/python/agents/mindsdb/README.md)  
Sample agent which can answer questions from any database, datawarehouse, app. - Powered by Gemini 2.5 flash + MindsDB.

* [**Semantic Kernel Agent**](/samples/python/agents/semantickernel/README.md)  
Demonstrates how to implement a travel agent built on [Semantic Kernel](https://github.com/microsoft/semantic-kernel/) and exposed through the A2A protocol.

* [**ElevenLabs TTS Agent**](/samples/python/agents/elevenlabs_tts/README.md)  
Converts text to speech using the ElevenLabs API. Showcases handling and returning audio files through A2A.

* [**Vertex AI Image Generator**](/samples/python/agents/vertex_image_gen/README.md)  
Generates images from text prompts using Google Cloud Vertex AI. Showcases image generation and returning image files through A2A.

* [**Git Repository Cloner**](/samples/python/agents/repo_cloner/README.md)  
Clones Git repositories with support for authentication, branch selection, and depth control. Showcases system command execution and secure handling of credentials.