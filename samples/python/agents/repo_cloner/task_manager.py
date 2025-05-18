import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterable
from typing import Dict, List, Any, Optional

from common.server.task_manager import InMemoryTaskManager
from common.server import utils
from common.types import (
    Artifact,
    InternalError,
    JSONRPCResponse,
    Message,
    SendTaskRequest,
    SendTaskResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskSendParams,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)

logger = logging.getLogger(__name__)


# Define AgentWithTaskManager interface
class AgentWithTaskManager(ABC):
    """Base class for agents that need task management capabilities."""
    
    @abstractmethod
    def get_processing_message(self) -> str:
        """Returns a message to show while processing."""
        pass
    
    @abstractmethod
    def invoke(self, query: str, session_id: str) -> Dict[str, Any]:
        """Process a query and return a response."""
        pass


# Define AgentTaskManager implementation
class AgentTaskManager(InMemoryTaskManager):
    def __init__(self, agent: AgentWithTaskManager):
        super().__init__()
        self.agent = agent

    async def _stream_generator(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        task_send_params: TaskSendParams = request.params
        query = self._get_user_query(task_send_params)
        try:
            # First, send a working status update
            task_state = TaskState.WORKING
            message = Message(
                role='agent', 
                parts=[TextPart(text=self.agent.get_processing_message())]
            )
            task_status = TaskStatus(state=task_state, message=message)
            yield SendTaskStreamingResponse(
                id=request.id,
                result=TaskStatusUpdateEvent(
                    id=task_send_params.id,
                    status=task_status,
                    final=False,
                )
            )
            
            # Now process the request
            result = self.agent.invoke(query, task_send_params.sessionId)
            
            # Create text response
            response_text = result.get("text", "Repository cloned successfully.")
            parts = [TextPart(text=response_text)]
            
            # Create artifact
            artifact = Artifact(parts=parts, index=0, append=False)
            
            # Send artifact update
            yield SendTaskStreamingResponse(
                id=request.id,
                result=TaskArtifactUpdateEvent(
                    id=task_send_params.id,
                    artifact=artifact,
                ),
            )
            
            # Send final status update
            yield SendTaskStreamingResponse(
                id=request.id,
                result=TaskStatusUpdateEvent(
                    id=task_send_params.id,
                    status=TaskStatus(
                        state=TaskState.COMPLETED,
                    ),
                    final=True,
                ),
            )
            
            # Update the task in memory
            await self._update_store(
                task_send_params.id, 
                TaskStatus(state=TaskState.COMPLETED), 
                [artifact]
            )
            
        except Exception as e:
            logger.error(f'An error occurred while streaming the response: {e}')
            yield JSONRPCResponse(
                id=request.id,
                error=InternalError(
                    message=f'An error occurred while streaming the response: {e}'
                ),
            )

    def _validate_request(
        self, request: SendTaskRequest | SendTaskStreamingRequest
    ) -> Optional[JSONRPCResponse]:
        task_send_params: TaskSendParams = request.params
        if not utils.are_modalities_compatible(
            task_send_params.acceptedOutputModes,
            self.agent.SUPPORTED_CONTENT_TYPES,
        ):
            logger.warning(
                'Unsupported output mode. Received %s, Support %s',
                task_send_params.acceptedOutputModes,
                self.agent.SUPPORTED_CONTENT_TYPES,
            )
            return utils.new_incompatible_types_error(request.id)
        return None

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        error = self._validate_request(request)
        if error:
            return error
        await self.upsert_task(request.params)
        return await self._invoke(request)

    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        error = self._validate_request(request)
        if error:
            return error
        await self.upsert_task(request.params)
        return self._stream_generator(request)

    async def _update_store(
        self, task_id: str, status: TaskStatus, artifacts: List[Artifact]
    ) -> Task:
        async with self.lock:
            try:
                task = self.tasks[task_id]
            except KeyError:
                logger.error(f'Task {task_id} not found for updating the task')
                raise ValueError(f'Task {task_id} not found')
            task.status = status
            if artifacts is not None:
                if task.artifacts is None:
                    task.artifacts = []
                task.artifacts.extend(artifacts)
            return task

    async def _invoke(self, request: SendTaskRequest) -> SendTaskResponse:
        task_send_params: TaskSendParams = request.params
        query = self._get_user_query(task_send_params)
        try:
            result = self.agent.invoke(query, task_send_params.sessionId)
            response_text = result.get("text", "Repository cloned successfully.")
            parts = [TextPart(text=response_text)]
            artifact = Artifact(parts=parts, index=0, append=False)
            
            task = await self._update_store(
                task_send_params.id,
                TaskStatus(state=TaskState.COMPLETED),
                [artifact],
            )
            return SendTaskResponse(id=request.id, result=task)
        except Exception as e:
            logger.error(f'Error invoking agent: {e}')
            raise ValueError(f'Error invoking agent: {e}')

    def _get_user_query(self, task_send_params: TaskSendParams) -> str:
        part = task_send_params.message.parts[0]
        if not isinstance(part, TextPart):
            raise ValueError('Only text parts are supported')
        return part.text