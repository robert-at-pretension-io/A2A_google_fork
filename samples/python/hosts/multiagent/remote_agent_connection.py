import uuid

from collections.abc import Callable

from common.client import A2AClient
from common.types import (
    AgentCard,
    Task,
    TaskArtifactUpdateEvent,
    TaskSendParams,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)


TaskCallbackArg = Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
TaskUpdateCallback = Callable[[TaskCallbackArg, AgentCard], Task]


class RemoteAgentConnections:
    """A class to hold the connections to the remote agents."""

    def __init__(self, agent_card: AgentCard):
        self.agent_client = A2AClient(agent_card)
        self.card = agent_card

        self.conversation_name = None
        self.conversation = None
        self.pending_tasks = set()

    def get_agent(self) -> AgentCard:
        return self.card

    async def send_task(
        self,
        request: TaskSendParams,
        task_callback: TaskUpdateCallback | None,
    ) -> Task | None:
        if self.card.capabilities.streaming:
            task = None
            # Create an initial task submission record
            submission_task = Task(
                id=request.id,
                sessionId=request.sessionId,
                status=TaskStatus(
                    state=TaskState.SUBMITTED,
                    message=request.message,
                ),
                history=[request.message],
            )
            
            if task_callback:
                task_callback(submission_task, self.card)
                
            try:
                async for response in self.agent_client.send_task_streaming(
                    request.model_dump()
                ):
                    # Handle response if we got one from the agent
                    if not hasattr(response, 'result'):
                        continue
                        
                    merge_metadata(response.result, request)
                    # For task status updates, we need to propagate metadata and provide
                    # a unique message id.
                    if (
                        hasattr(response.result, 'status')
                        and hasattr(response.result.status, 'message')
                        and response.result.status.message
                    ):
                        merge_metadata(
                            response.result.status.message, request.message
                        )
                        m = response.result.status.message
                        if not m.metadata:
                            m.metadata = {}
                        if 'message_id' in m.metadata:
                            m.metadata['last_message_id'] = m.metadata['message_id']
                        m.metadata['message_id'] = str(uuid.uuid4())
                    if task_callback:
                        task = task_callback(response.result, self.card)
                    if hasattr(response.result, 'final') and response.result.final:
                        break
                return task
            except Exception as e:
                error_msg = str(e)
                print(f"Error communicating with agent {self.card.name}: {error_msg}")
                
                # Log detailed connection error information
                import traceback
                print("Detailed error traceback:")
                traceback.print_exc()
                
                # Add specific logging for connection refused errors
                if "Connection refused" in error_msg:
                    print(f"DEBUG: Connection refused error detected for agent: {self.card.name}")
                    print(f"Agent URL: {self.card.url}")
                    print(f"This typically means the agent service is not running at {self.card.url}")
                    print(f"Check if the ElevenLabs TTS agent is running and accessible at this URL")
                    print(f"Agent capabilities: {self.card.capabilities}")
                    print(f"Supported content types: {self.card.defaultOutputModes}")
                
                # Create a failed task for the callback
                failed_task = Task(
                    id=request.id,
                    sessionId=request.sessionId,
                    status=TaskStatus(
                        state=TaskState.FAILED,
                        message=request.message,
                    ),
                    history=[request.message],
                )
                
                if task_callback:
                    print(f"Calling task_callback with failed task for agent: {self.card.name}")
                    task_callback(failed_task, self.card)
                    
                return failed_task
        # Non-streaming
        response = await self.agent_client.send_task(request.model_dump())
        merge_metadata(response.result, request)
        # For task status updates, we need to propagate metadata and provide
        # a unique message id.
        if (
            hasattr(response.result, 'status')
            and hasattr(response.result.status, 'message')
            and response.result.status.message
        ):
            merge_metadata(response.result.status.message, request.message)
            m = response.result.status.message
            if not m.metadata:
                m.metadata = {}
            if 'message_id' in m.metadata:
                m.metadata['last_message_id'] = m.metadata['message_id']
            m.metadata['message_id'] = str(uuid.uuid4())

        if task_callback:
            task_callback(response.result, self.card)
        return response.result


def merge_metadata(target, source):
    if not hasattr(target, 'metadata') or not hasattr(source, 'metadata'):
        return
    if target.metadata and source.metadata:
        target.metadata.update(source.metadata)
    elif source.metadata:
        target.metadata = dict(**source.metadata)
