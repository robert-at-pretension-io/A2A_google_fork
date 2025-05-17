import json
import logging
import base64
from collections.abc import AsyncIterable
from typing import Any, Dict, List, Optional

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
    FilePart,
    Part,
)

logger = logging.getLogger(__name__)


class AgentTaskManager(InMemoryTaskManager):
    def __init__(self, agent):
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
            
            # Create artifacts from result
            artifacts = self._create_artifacts_from_result(result)
            
            # Send artifact update
            if artifacts:
                for artifact in artifacts:
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
                artifacts
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
            artifacts = self._create_artifacts_from_result(result)
            task = await self._update_store(
                task_send_params.id,
                TaskStatus(state=TaskState.COMPLETED),
                artifacts,
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
        
    def _create_artifacts_from_result(self, result: Dict[str, Any]) -> List[Artifact]:
        """Create A2A artifacts from agent result."""
        if "error" in result:
            # Return error message as text
            parts = [TextPart(text=f"Error: {result['error']}")]
            return [Artifact(parts=parts, index=0, append=False)]
            
        # Create parts for the artifact
        parts = []
        
        # Add text part
        if "text" in result:
            parts.append(TextPart(text=result["text"]))
            
        # Add audio file part if present
        if "audio_file" in result:
            audio_file = result["audio_file"]
            
            # Make sure we're sending a proper structure
            parts.append(
                FilePart(
                    file={
                        "name": audio_file["filename"],
                        "mimeType": audio_file["mime_type"],
                        "bytes": audio_file["content"]
                    }
                )
            )
            
        return [Artifact(parts=parts, index=0, append=False)]