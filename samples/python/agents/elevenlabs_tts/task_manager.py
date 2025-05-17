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
    FileContent,
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
                    try:
                        # Ensuring that artifact is properly formed before creating TaskArtifactUpdateEvent
                        # Creating a proper TaskArtifactUpdateEvent with validated artifact
                        artifact_update = TaskArtifactUpdateEvent(
                            id=task_send_params.id,
                            artifact=artifact,
                        )
                        yield SendTaskStreamingResponse(
                            id=request.id,
                            result=artifact_update,
                        )
                    except Exception as e:
                        logger.error(f"Error creating artifact update: {e}")
                        # Instead of failing, send an error message as a status update
                        error_status = TaskStatus(
                            state=TaskState.WORKING,
                            message=Message(
                                role="agent",
                                parts=[TextPart(text=f"Error creating artifact: {str(e)}")]
                            )
                        )
                        yield SendTaskStreamingResponse(
                            id=request.id,
                            result=TaskStatusUpdateEvent(
                                id=task_send_params.id,
                                status=error_status,
                                final=False,
                            )
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
            # Send a final status update with the failure state
            try:
                error_status = TaskStatus(
                    state=TaskState.FAILED,  # Using the correct TaskState enum value
                    message=Message(
                        role="agent",
                        parts=[TextPart(text=f"Error processing request: {str(e)}")]
                    )
                )
                yield SendTaskStreamingResponse(
                    id=request.id,
                    result=TaskStatusUpdateEvent(
                        id=task_send_params.id,
                        status=error_status,
                        final=True
                    )
                )
            except Exception as e2:
                # If even the error status fails, fall back to a basic JSONRPC error
                logger.error(f'Failed to create error status: {e2}')
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
            return [Artifact(name="Error Message", parts=parts, index=0, append=False)]
            
        # Create parts for the artifact
        parts = []
        
        # Add text part
        if "text" in result:
            parts.append(TextPart(text=result["text"]))
            
        # Add audio file part if present
        if "audio_file" in result:
            audio_file = result["audio_file"]
            
            try:
                # Make sure we're sending a proper structure with properly-formed FilePart
                # Note: we instantiate FilePart correctly using the FileContent model
                file_content = FileContent(
                    name=audio_file["filename"],
                    mimeType=audio_file["mime_type"],
                    bytes=audio_file["content"]  # This is already base64-encoded from agent.py
                )
                file_part = FilePart(file=file_content)
                
                # Add debugging log to inspect the file part
                logger.info(f"Creating file part with name: {file_content.name}, type: {file_content.mimeType}, bytes length: {len(file_content.bytes) if file_content.bytes else 0}")
                
                parts.append(file_part)
                
                # Add a debug text part to confirm audio was included
                parts.append(TextPart(text=f"[Audio file generated successfully. Type: {audio_file['mime_type']}]"))
            except Exception as e:
                logger.error(f"Error creating file part: {e}")
                logger.exception("Full exception details:")
                # Add error as text part instead
                parts.append(TextPart(text=f"Error creating audio file part: {str(e)}"))
        
        # Ensure we have a proper artifact name
        artifact_name = "Text to Speech Result"
        
        if not parts:
            # If we don't have any parts, add a placeholder text part
            parts = [TextPart(text="No content was generated.")]
            
        # Debug log for the final artifact
        logger.info(f"Created artifact with {len(parts)} parts: {[p.type for p in parts]}")
            
        return [Artifact(name=artifact_name, parts=parts, index=0, append=False)]