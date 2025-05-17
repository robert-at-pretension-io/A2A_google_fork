import asyncio
import datetime
import uuid

from common.types import (
    AgentCard,
    Artifact,
    DataPart,
    Message,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
)
from service.server import test_image
from service.server.application_manager import ApplicationManager
from service.types import Conversation, Event
from utils.agent_card import get_agent_card


class InMemoryFakeAgentManager(ApplicationManager):
    """An implementation of memory based management with fake agent actions

    This implements the interface of the ApplicationManager to plug into
    the AgentServer. This acts as the service contract that the Mesop app
    uses to send messages to the agent and provide information for the frontend.
    """

    _conversations: list[Conversation]
    _messages: list[Message]
    _tasks: list[Task]
    _events: list[Event]
    _pending_message_ids: list[str]
    _next_message_idx: int
    _agents: list[AgentCard]

    def __init__(self):
        self._conversations = []
        self._messages = []
        self._tasks = []
        self._events = []
        self._pending_message_ids = []
        self._next_message_idx = 0
        self._agents = []
        self._task_map = {}

    def create_conversation(self) -> Conversation:
        conversation_id = str(uuid.uuid4())
        c = Conversation(conversation_id=conversation_id, is_active=True)
        self._conversations.append(c)
        return c

    def sanitize_message(self, message: Message) -> Message:
        if not message.metadata:
            message.metadata = {}
        message.metadata.update({'message_id': str(uuid.uuid4())})
        return message

    async def process_message(self, message: Message):
        self._messages.append(message)
        message_id = message.metadata['message_id']
        self._pending_message_ids.append(message_id)
        conversation_id = (
            message.metadata['conversation_id']
            if 'conversation_id' in message.metadata
            else None
        )
        # Now check the conversation and attach the message id.
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation.messages.append(message)
        self._events.append(
            Event(
                id=str(uuid.uuid4()),
                actor='host',
                content=message,
                timestamp=datetime.datetime.now(datetime.UTC).timestamp(),
            )
        )
        # Now actually process the message. If the response is async, return None
        # for the message response and the updated message information for the
        # incoming message (with ids attached).
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            sessionId=conversation_id,
            status=TaskStatus(
                state=TaskState.SUBMITTED,
                message=message,
            ),
            history=[message],
        )
        if self._next_message_idx != 0:
            self._task_map[message_id] = task_id
            self.add_task(task)
        await asyncio.sleep(self._next_message_idx)
        response = self.next_message()
        response.metadata = {
            **message.metadata,
            'message_id': str(uuid.uuid4()),
        }
        if conversation:
            conversation.messages.append(response)
        self._events.append(
            Event(
                id=str(uuid.uuid4()),
                actor='host',
                content=response,
                timestamp=datetime.datetime.now(datetime.UTC).timestamp(),
            )
        )
        self._pending_message_ids.remove(message.metadata['message_id'])
        # Now clean up the task
        if task:
            task.status.state = TaskState.COMPLETED
            task.artifacts = [Artifact(name='response', parts=response.parts)]
            task.history.append(response)
            self.update_task(task)

    def add_task(self, task: Task):
        self._tasks.append(task)

    def update_task(self, task: Task):
        for i, t in enumerate(self._tasks):
            if t.id == task.id:
                self._tasks[i] = task
                return

    def add_event(self, event: Event):
        self._events.append(event)

    def next_message(self) -> Message:
        message = _message_queue[self._next_message_idx]
        self._next_message_idx = (self._next_message_idx + 1) % len(
            _message_queue
        )
        return message

    def get_conversation(
        self, conversation_id: str | None
    ) -> Conversation | None:
        if not conversation_id:
            return None
        return next(
            filter(
                lambda c: c.conversation_id == conversation_id,
                self._conversations,
            ),
            None,
        )
        
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation by ID and all related messages and tasks."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
            
        # Remove conversation
        self._conversations = [c for c in self._conversations if c.conversation_id != conversation_id]
        
        # Remove related messages
        self._messages = [
            m for m in self._messages 
            if not (m.metadata and m.metadata.get("conversation_id") == conversation_id)
        ]
        
        # Remove related tasks
        related_task_ids = []
        for task in self._tasks:
            if task.metadata and task.metadata.get("conversation_id") == conversation_id:
                related_task_ids.append(task.id)
                
        self._tasks = [t for t in self._tasks if t.id not in related_task_ids]
        
        # Remove from task map
        for message_id, task_id in list(self._task_map.items()):
            if task_id in related_task_ids:
                del self._task_map[message_id]
                
        return True
        
    def delete_agent(self, agent_url: str) -> bool:
        """Delete an agent by URL."""
        original_count = len(self._agents)
        self._agents = [a for a in self._agents if a.url != agent_url]
        
        # Return True if an agent was actually removed
        return len(self._agents) < original_count

    def get_pending_messages(self) -> list[tuple[str, str]]:
        rval = []
        for message_id in self._pending_message_ids:
            if message_id in self._task_map:
                task_id = self._task_map[message_id]
                task = next(
                    filter(lambda x: x.id == task_id, self._tasks), None
                )
                if not task:
                    rval.append((message_id, ''))
                elif task.history and task.history[-1].parts:
                    if len(task.history) == 1:
                        rval.append((message_id, 'Working...'))
                    else:
                        part = task.history[-1].parts[0]
                        rval.append(
                            (
                                message_id,
                                part.text
                                if part.type == 'text'
                                else 'Working...',
                            )
                        )
            else:
                rval.append((message_id, ''))
            return rval
        return self._pending_message_ids

    def register_agent(self, url):
        agent_data = get_agent_card(url)
        if not agent_data.url:
            agent_data.url = url
        self._agents.append(agent_data)

    @property
    def agents(self) -> list[AgentCard]:
        return self._agents

    @property
    def conversations(self) -> list[Conversation]:
        return self._conversations

    @property
    def tasks(self) -> list[Task]:
        return self._tasks

    @property
    def events(self) -> list[Event]:
        return self._events


# This represents the pre-canned responses that will be returned in order.
# Extend this list to test more functionality of the UI
_message_queue: list[Message] = [
    Message(role='agent', parts=[TextPart(text='Hello')]),
    Message(
        role='agent',
        parts=[
            DataPart(
                data={
                    'type': 'form',
                    'form': {
                        'type': 'object',
                        'properties': {
                            'name': {
                                'type': 'string',
                                'description': 'Enter your name',
                                'title': 'Name',
                            },
                            'date': {
                                'type': 'string',
                                'format': 'date',
                                'description': 'Birthday',
                                'title': 'Birthday',
                            },
                        },
                        'required': ['date'],
                    },
                    'form_data': {
                        'name': 'John Smith',
                    },
                    'instructions': 'Please provide your birthday and name',
                }
            ),
        ],
    ),
    Message(role='agent', parts=[TextPart(text='I like cats')]),
    test_image.test_image,
    Message(role='agent', parts=[TextPart(text='And I like dogs')]),
]
