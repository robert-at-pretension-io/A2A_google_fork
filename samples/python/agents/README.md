# Sample Agents

All the agents in this directory are samples built on different frameworks highlighting different capabilities. Each agent runs as a standalone A2A server. 

Each agent can be run as its own A2A server with the instructions on its README. By default, each will run on a separate port on localhost (you can use command line arguments to override).

To interact with the servers, use an A2AClient in a host app (such as the CLI). See [Host Apps](/samples/python/hosts/README.md) for details.

## Creating a New Agent

To create a new agent that works with the A2A protocol, follow these steps:

1. **Create a Directory Structure**:
   ```
   your_agent_name/
   ├── __init__.py         # Empty file to make the directory a package
   ├── __main__.py         # Entry point with click CLI
   ├── agent.py            # Main agent logic
   ├── task_manager.py     # A2A task handling
   ├── pyproject.toml      # Project configuration
   └── README.md           # Documentation
   ```

2. **Create the pyproject.toml File**:
   ```toml
   [project]
   name = "a2a-sample-agent-your-agent-name"
   version = "0.1.0"
   description = "Your agent description"
   readme = "README.md"
   requires-python = ">=3.11"
   dependencies = [
       "a2a-samples",
       "click>=8.1.8",
       # Any other dependencies your agent needs
   ]

   [tool.hatch.build.targets.wheel]
   packages = ["."]

   [tool.uv.sources]
   a2a-samples = { workspace = true }

   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"
   ```

3. **Update the Root pyproject.toml File**:
   - Add your agent to the workspace members list in `/samples/python/pyproject.toml`:
   ```toml
   [tool.uv.workspace]
   members = [
       # Other members...
       "agents/your_agent_name"
   ]
   ```

4. **Implement agent.py**:
   ```python
   class YourAgent:
       """Your agent implementation."""
       
       SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']  # Add other types as needed
       
       def __init__(self):
           # Initialize your agent
           pass
           
       def get_processing_message(self) -> str:
           """Message shown during processing."""
           return "Processing your request..."
           
       def invoke(self, query: str, session_id: str) -> dict:
           """Process a request and return a response.
           
           Args:
               query: The text query from the user
               session_id: Unique ID for the conversation
               
           Returns:
               Dict with response data
           """
           # Your agent logic here
           return {"text": "Your response here"}
   ```

5. **Implement task_manager.py**:
   - Copy from an existing agent and adapt as needed
   - The task manager connects your agent to the A2A protocol

6. **Create __main__.py**:
   ```python
   import click
   import logging
   import os
   from dotenv import load_dotenv
   
   from common.server import A2AServer
   from common.types import AgentCard, AgentCapabilities, AgentSkill
   from agent import YourAgent
   from task_manager import AgentTaskManager
   
   load_dotenv()
   logging.basicConfig(level=logging.INFO)
   
   @click.command()
   @click.option('--host', default='localhost')
   @click.option('--port', default=10010)  # Choose a unique port
   def main(host, port):
       # Create agent card
       capabilities = AgentCapabilities(streaming=True)
       skill = AgentSkill(
           id="your_skill_id",
           name="Your Skill Name",
           description="Description of what your agent does",
           tags=["tag1", "tag2"],
           examples=["Example query 1", "Example query 2"]
       )
       
       agent_card = AgentCard(
           name="Your Agent Name",
           description="Your agent description",
           url=f"http://{host}:{port}/",
           version="1.0.0",
           defaultInputModes=YourAgent.SUPPORTED_CONTENT_TYPES,
           defaultOutputModes=YourAgent.SUPPORTED_CONTENT_TYPES,
           capabilities=capabilities,
           skills=[skill],
       )
       
       # Create the agent and server
       your_agent = YourAgent()
       task_manager = AgentTaskManager(agent=your_agent)
       
       server = A2AServer(
           agent_card=agent_card,
           task_manager=task_manager,
           host=host,
           port=port,
       )
       
       print(f"Starting your agent at http://{host}:{port}/")
       server.start()
   
   if __name__ == '__main__':
       main()
   ```

7. **Run Your Agent**:
   ```bash
   cd samples/python/agents/your_agent_name
   uv run .
   ```

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