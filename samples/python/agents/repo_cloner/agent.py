from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from google.adk import Agent

from common.server.task_manager import TaskManager
from task_manager import AgentWithTaskManager

logger = logging.getLogger(__name__)


async def clone_repo(repo_url: str) -> str:
    """Clone a Git repository.
    
    This tool clones a Git repository from the provided URL to a temporary directory.
    
    Args:
        repo_url: The HTTPS URL of the repository to clone, e.g. https://github.com/user/repo
        
    Returns:
        A success message with the clone location or an error message
    """
    # Check if git exists
    from shutil import which
    if which("git") is None:
        return "Error: git executable not found in PATH."
    
    # Set up destination directory in tmp
    tmp_holder = tempfile.TemporaryDirectory(prefix="adk_clone_")
    dest_path = Path(tmp_holder.name) / "repo"
    
    # Build git command
    cmd = ["git", "clone", repo_url, str(dest_path)]
    
    try:
        # Execute clone command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Persist temporary directory
        tmp_holder._finalizer.detach()  # pylint: disable=protected-access
        
        return f"Repository successfully cloned to: {dest_path}"
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        return f"Error cloning repository: {error_msg}"


class RepoCloneAgent(AgentWithTaskManager):
    """An A2A agent that handles Git repository cloning."""
    
    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']
    
    def __init__(self):
        # Initialize the ADK agent
        self._agent = self._build_agent()
        self._runner = self._build_runner()
        self._user_id = 'remote_agent'
    
    def get_processing_message(self) -> str:
        return 'Processing the repository cloning request...'
    
    def invoke(self, query: str, session_id: str) -> Dict[str, Any]:
        """Process a user query and return a response.
        
        Args:
            query: The text query from the user
            session_id: Unique ID for the conversation
            
        Returns:
            Dict with response data
        """
        from google.genai import types
        
        try:
            # Get or create session
            session = self._runner.session_service.get_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                session_id=session_id,
            )
            
            if session is None:
                session = self._runner.session_service.create_session(
                    app_name=self._agent.name,
                    user_id=self._user_id,
                    state={},
                    session_id=session_id,
                )
            
            # Create user message
            content = types.Content(
                role='user', parts=[types.Part.from_text(text=query)]
            )
            
            # Run the agent
            events = list(
                self._runner.run(
                    user_id=self._user_id,
                    session_id=session.id,
                    new_message=content,
                )
            )
            
            # Extract response from events
            response_text = ""
            
            # Look through all events for text content
            for event in events:
                if hasattr(event, 'content') and event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text + '\n'
            
            # If no response text was collected, provide default
            if not response_text.strip():
                response_text = "The agent is processing your request to clone the repository."
            
            return {"text": response_text.strip()}
            
        except Exception as e:
            logger.error(f"Error in invoke method: {e}", exc_info=True)
            return {"text": f"An error occurred: {str(e)}"}
    
    def _build_agent(self) -> Agent:
        """Build the ADK agent with the repository cloning tool."""
        return Agent(
            model='gemini-2.0-flash-001',
            name='git_repo_cloner',
            description='A Git repository cloning assistant',
            instruction="""
            You are a Git repository cloning assistant. You have access to the clone_repo tool.
            
            When a user requests to clone a repository:
            1. Extract the repository URL from their message
            2. Call the clone_repo tool with the URL
            3. Report the result to the user
            
            Always use the clone_repo tool when a user asks you to clone a repository.
            If the user doesn't provide a repository URL clearly, ask them to provide one.
            """,
            tools=[clone_repo],
        )
    
    def _build_runner(self):
        """Build the ADK runner with necessary services."""
        from google.adk.runners import Runner
        from google.adk.artifacts import InMemoryArtifactService
        from google.adk.sessions import InMemorySessionService
        from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
        
        return Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )