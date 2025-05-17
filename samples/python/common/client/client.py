import json

from collections.abc import AsyncIterable
from typing import Any

import httpx

from httpx._types import TimeoutTypes
from httpx_sse import connect_sse

from common.types import (
    A2AClientHTTPError,
    A2AClientJSONError,
    AgentCard,
    CancelTaskRequest,
    CancelTaskResponse,
    GetTaskPushNotificationRequest,
    GetTaskPushNotificationResponse,
    GetTaskRequest,
    GetTaskResponse,
    JSONRPCRequest,
    Message,
    SendTaskRequest,
    SendTaskResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    SetTaskPushNotificationRequest,
    SetTaskPushNotificationResponse,
    TaskStatus,
    TaskState,
    TaskStatusUpdateEvent,
    TextPart,
)


class A2AClient:
    def __init__(
        self,
        agent_card: AgentCard = None,
        url: str = None,
        timeout: TimeoutTypes = 60.0,
    ):
        if agent_card:
            self.url = agent_card.url
        elif url:
            self.url = url
        else:
            raise ValueError('Must provide either agent_card or url')
        self.timeout = timeout

    async def send_task(self, payload: dict[str, Any]) -> SendTaskResponse:
        request = SendTaskRequest(params=payload)
        return SendTaskResponse(**await self._send_request(request))

    async def send_task_streaming(
        self, payload: dict[str, Any]
    ) -> AsyncIterable[SendTaskStreamingResponse]:
        request = SendTaskStreamingRequest(params=payload)
        with httpx.Client(timeout=None) as client:
            try:
                with connect_sse(
                    client, 'POST', self.url, json=request.model_dump()
                ) as event_source:
                    try:
                        for sse in event_source.iter_sse():
                            try:
                                # Log the raw response data for debugging
                                print(f"DEBUG: Received SSE data: {sse.data[:200]}...") # Truncate to avoid huge logs
                                
                                # Parse the JSON data
                                json_data = json.loads(sse.data)
                                
                                # Check for key parts of the response that might cause validation issues
                                if "result" in json_data:
                                    result = json_data["result"]
                                    print(f"DEBUG: SSE result type: {type(result).__name__}")
                                    
                                    # Check for TaskStatusUpdateEvent validation issues
                                    if "status" in result and "state" in result["status"]:
                                        state = result["status"]["state"]
                                        print(f"DEBUG: Task state value: {state}")
                                        if state.upper() == "FAILED":
                                            print("WARNING: Task state 'FAILED' should be lowercase 'failed' to comply with TaskState enum")
                                    
                                    # Check for TaskArtifactUpdateEvent validation issues
                                    if "artifact" in result:
                                        print(f"DEBUG: Artifact data present with keys: {list(result['artifact'].keys()) if isinstance(result['artifact'], dict) else 'not a dict'}")
                                        
                                # Create and return the response object
                                yield SendTaskStreamingResponse(**json_data)
                                
                            except Exception as validation_error:
                                # Log detailed validation errors but still propagate them
                                print(f"ERROR: Validation error processing SSE data: {str(validation_error)}")
                                print(f"Raw data that caused the error: {sse.data}")
                                
                                # Re-raise to maintain original behavior
                                raise
                                
                    except json.JSONDecodeError as e:
                        print(f"ERROR: JSON decode error: {str(e)}")
                        print(f"Invalid JSON data: {sse.data if 'sse' in locals() else 'No SSE data available'}")
                        raise A2AClientJSONError(str(e)) from e
                    except httpx.RequestError as e:
                        print(f"ERROR: HTTP request error: {str(e)}")
                        raise A2AClientHTTPError(400, str(e)) from e
            except (httpx.ConnectError, ConnectionRefusedError) as e:
                # Handle connection errors more gracefully
                print(f"Connection to agent at {self.url} failed: {str(e)}")
                # Return a minimal response indicating connection failure
                # Create a properly formatted TaskStatusUpdateEvent
                yield SendTaskStreamingResponse(
                    jsonrpc="2.0",
                    id="connection_error",
                    result=TaskStatusUpdateEvent(
                        id=payload.get("id", "unknown"),
                        status=TaskStatus(
                            state=TaskState.FAILED,
                            message=Message(
                                role="agent",
                                parts=[TextPart(text=f"Could not connect to agent at {self.url}: {str(e)}")]
                            )
                        ),
                        final=True
                    )
                )

    async def _send_request(self, request: JSONRPCRequest) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                # Image generation could take time, adding timeout
                response = await client.post(
                    self.url, json=request.model_dump(), timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise A2AClientHTTPError(e.response.status_code, str(e)) from e
            except json.JSONDecodeError as e:
                raise A2AClientJSONError(str(e)) from e

    async def get_task(self, payload: dict[str, Any]) -> GetTaskResponse:
        request = GetTaskRequest(params=payload)
        return GetTaskResponse(**await self._send_request(request))

    async def cancel_task(self, payload: dict[str, Any]) -> CancelTaskResponse:
        request = CancelTaskRequest(params=payload)
        return CancelTaskResponse(**await self._send_request(request))

    async def set_task_callback(
        self, payload: dict[str, Any]
    ) -> SetTaskPushNotificationResponse:
        request = SetTaskPushNotificationRequest(params=payload)
        return SetTaskPushNotificationResponse(
            **await self._send_request(request)
        )

    async def get_task_callback(
        self, payload: dict[str, Any]
    ) -> GetTaskPushNotificationResponse:
        request = GetTaskPushNotificationRequest(params=payload)
        return GetTaskPushNotificationResponse(
            **await self._send_request(request)
        )
