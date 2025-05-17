import os
import uuid
from typing import List, Dict, Any, Optional

from common.types import (
    AgentCard,
    Message,
    Task
)
from service.types import Conversation, Event
from service.server.adk_host_manager import ADKHostManager
from service.server.persistent_storage import PersistentStorage, serialize_list

class PersistentADKHostManager(ADKHostManager):
    """ADKHostManager with persistence for conversations and agents."""

    def __init__(self, api_key: str = "", uses_vertex_ai: bool = False):
        """Initialize the manager with persistence.
        
        Args:
            api_key: API key for Google Gemini
            uses_vertex_ai: Whether to use Vertex AI
        """
        # Initialize storage before parent class
        self._storage = PersistentStorage()
        
        # Call parent constructor
        super().__init__(api_key=api_key, uses_vertex_ai=uses_vertex_ai)
        
        # Load saved data
        self._load_state()
        
        print(f"Loaded {len(self._agents)} agents and {len(self._conversations)} conversations from storage")

    def _load_state(self):
        """Load conversations and agents from storage."""
        # Load agents
        agents_data = self._storage.load("agents")
        if agents_data and "agents" in agents_data:
            for agent_data in agents_data["agents"]:
                # Create AgentCard from data
                try:
                    agent = AgentCard(**agent_data)
                    # Add only if not already in list
                    if agent.url not in [a.url for a in self._agents]:
                        self._agents.append(agent)
                        # Register with host agent
                        self.host_agent.register_agent_card(agent)
                except Exception as e:
                    print(f"Error loading agent: {e}")
        
        # Load conversations
        convs_data = self._storage.load("conversations")
        if convs_data and "conversations" in convs_data:
            for conv_data in convs_data["conversations"]:
                try:
                    # Create conversation and add if not in list
                    conv = Conversation(**conv_data)
                    if conv.conversation_id not in [c.conversation_id for c in self._conversations]:
                        self._conversations.append(conv)
                        
                        # Load messages for this conversation
                        msgs_data = self._storage.load(f"messages_{conv.conversation_id}")
                        if msgs_data and "messages" in msgs_data:
                            for msg_data in msgs_data["messages"]:
                                try:
                                    msg = Message(**msg_data)
                                    self._messages.append(msg)
                                except Exception as e:
                                    print(f"Error loading message: {e}")
                except Exception as e:
                    print(f"Error loading conversation: {e}")

    def _save_agents(self):
        """Save agents to storage."""
        try:
            agents_data = {
                "agents": serialize_list(self._agents)
            }
            self._storage.save("agents", agents_data)
        except Exception as e:
            print(f"Error saving agents: {e}")

    def _save_conversations(self):
        """Save conversations to storage."""
        try:
            # Save conversation list
            convs_data = {
                "conversations": serialize_list(self._conversations)
            }
            self._storage.save("conversations", convs_data)
            
            # Save messages for each conversation
            for conv in self._conversations:
                conv_messages = [msg for msg in self._messages 
                               if msg.metadata and msg.metadata.get("conversation_id") == conv.conversation_id]
                msgs_data = {
                    "messages": serialize_list(conv_messages)
                }
                self._storage.save(f"messages_{conv.conversation_id}", msgs_data)
        except Exception as e:
            print(f"Error saving conversations: {e}")

    def register_agent(self, url):
        """Register an agent and save to storage."""
        super().register_agent(url)
        self._save_agents()

    def create_conversation(self) -> Conversation:
        """Create a conversation and save to storage."""
        conversation = super().create_conversation()
        self._save_conversations()
        return conversation

    async def process_message(self, message):
        """Process message and save updates to storage."""
        await super().process_message(message)
        self._save_conversations()