from abc import ABC, abstractmethod

from common.types import AgentCard, Message, Task
from service.types import Conversation, Event


class ApplicationManager(ABC):
    @abstractmethod
    def create_conversation(self) -> Conversation:
        pass
        
    @abstractmethod
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation by ID."""
        pass
        
    @abstractmethod
    def delete_agent(self, agent_url: str) -> bool:
        """Delete an agent by URL."""
        pass

    @abstractmethod
    def sanitize_message(self, message: Message) -> Message:
        pass

    @abstractmethod
    async def process_message(self, message: Message):
        pass

    @abstractmethod
    def register_agent(self, url: str):
        pass

    @abstractmethod
    def get_pending_messages(self) -> list[str]:
        pass
        
    @abstractmethod
    def get_conversation(self, conversation_id: str) -> Conversation:
        """Get a conversation by ID."""
        pass

    @property
    @abstractmethod
    def conversations(self) -> list[Conversation]:
        pass

    @property
    @abstractmethod
    def tasks(self) -> list[Task]:
        pass

    @property
    @abstractmethod
    def agents(self) -> list[AgentCard]:
        pass

    @property
    @abstractmethod
    def events(self) -> list[Event]:
        pass
