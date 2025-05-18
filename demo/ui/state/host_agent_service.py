import json
import os
import sys
import traceback
import uuid

import mesop as me
from state.state import AppState

from typing import Any

from common.types import Message, Part, Task, FilePart, FileContent, TextPart
from service.client.client import ConversationClient
from service.types import (
    Conversation,
    CreateConversationRequest,
    DeleteAgentRequest,
    DeleteConversationRequest,
    Event,
    GetEventRequest,
    ListAgentRequest,
    ListConversationRequest,
    ListMessageRequest,
    ListTaskRequest,
    PendingMessageRequest,
    RegisterAgentRequest,
    SendMessageRequest,
)

from .state import (
    AppState,
    SessionTask,
    StateConversation,
    StateEvent,
    StateMessage,
    StateTask,
)


server_url = 'http://localhost:12000'


async def ListConversations() -> list[Conversation]:
    client = ConversationClient(server_url)
    try:
        response = await client.list_conversation(ListConversationRequest())
        return response.result
    except Exception as e:
        print('Failed to list conversations: ', e)


async def ListMessages(conversation_id: str) -> list[Message]:
    client = ConversationClient(server_url)
    try:
        response = await client.list_message(
            ListMessageRequest(params=conversation_id)
        )
        return response.result
    except Exception as e:
        print('Failed to list messages: ', e)


async def ListTasks() -> list[Task]:
    client = ConversationClient(server_url)
    try:
        response = await client.list_task(ListTaskRequest())
        return response.result
    except Exception as e:
        print('Failed to list tasks: ', e)


async def GetPendingMessages() -> list[tuple[str, str]]:
    client = ConversationClient(server_url)
    try:
        response = await client.get_pending_messages(PendingMessageRequest())
        return response.result
    except Exception as e:
        print('Failed to get pending messages: ', e)
        return []


async def ListEvents() -> list[Event]:
    client = ConversationClient(server_url)
    try:
        response = await client.get_event(GetEventRequest())
        return response.result
    except Exception as e:
        print('Failed to list events: ', e)
        return []


async def SendMessage(message: Message) -> None:
    client = ConversationClient(server_url)
    try:
        await client.send_message(SendMessageRequest(params=message))
    except Exception as e:
        print('Failed to send message: ', e)
        traceback.print_exc(file=sys.stdout)


async def CreateConversation() -> Conversation:
    client = ConversationClient(server_url)
    try:
        response = await client.create_conversation(CreateConversationRequest())
        return response.result
    except Exception as e:
        print('Failed to create conversation: ', e)


async def DeleteConversation(conversation_id: str) -> bool:
    """Delete a conversation by ID."""
    client = ConversationClient(server_url)
    try:
        response = await client.delete_conversation(
            DeleteConversationRequest(params=conversation_id)
        )
        return response.result
    except Exception as e:
        print(f'Failed to delete conversation {conversation_id}: {e}')
        return False


async def RegisterAgent(url: str) -> None:
    client = ConversationClient(server_url)
    try:
        await client.register_agent(RegisterAgentRequest(params=url))
    except Exception as e:
        print('Failed to register agent: ', e)


async def DeleteAgent(url: str) -> bool:
    """Delete an agent by URL."""
    client = ConversationClient(server_url)
    try:
        response = await client.delete_agent(DeleteAgentRequest(params=url))
        return response.result
    except Exception as e:
        print(f'Failed to delete agent {url}: {e}')
        return False


async def UpdateApiKey(api_key: str) -> bool:
    """Update the API key in the server"""
    try:
        # Initialize a client we'll use for requests
        client = ConversationClient(server_url)
        
        # Update application environment variable
        os.environ['GOOGLE_API_KEY'] = api_key
        
        # If the server has agent_server with update_api_key,
        # we can call that method directly
        if 'agent_server' in globals() and hasattr(agent_server, 'update_api_key'):
            agent_server.update_api_key(api_key)
            return True
            
        # Otherwise, we'll just return success since we've updated the env var
        return True
    except Exception as e:
        print(f'Failed to update API key: {e}')
        return False


async def UpdateAppState(app_state: AppState, current_conversation_id: str) -> None:
    """Update app state with latest server data"""
    try:
        # Initialize client
        client = ConversationClient(server_url)
        
        # Get conversations
        conversations = await ListConversations()
        if conversations is not None:
            app_state.conversations = [convert_conversation_to_state(c) for c in conversations]
        
        # If we have a current conversation, update the messages for that conversation
        if current_conversation_id:
            messages = await ListMessages(current_conversation_id)
            if messages is not None:
                app_state.messages = [convert_message_to_state(m) for m in messages]
        
        # Get pending messages
        pending_messages = await GetPendingMessages()
        if pending_messages:
            app_state.background_tasks = dict(pending_messages)
            
        # Get tasks
        tasks = await ListTasks()
        if tasks is not None:
            app_state.task_list = [
                SessionTask(session_id=t.sessionId or '', task=convert_task_to_state(t))
                for t in tasks
            ]
    except Exception as e:
        print(f'Failed to update app state: {e}')
        # Don't propagate the error, just log it


async def ListAgents() -> list[Any]:
    client = ConversationClient(server_url)
    try:
        response = await client.list_agent(ListAgentRequest())
        return response.result
    except Exception as e:
        print('Failed to list agents: ', e)
        return []


def extract_message_id(message: Message) -> str:
    if not message or not message.metadata:
        return ''
    return message.metadata.get('message_id', '')


def extract_message_conversation(message: Message) -> str:
    if not message or not message.metadata:
        return ''
    return message.metadata.get('conversation_id', '')


def convert_message_to_state(message: Message) -> StateMessage:
    if not message:
        return StateMessage()

    return StateMessage(
        message_id=extract_message_id(message),
        role=message.role,
        content=extract_content(message.parts),
    )


def convert_conversation_to_state(
    conversation: Conversation,
) -> StateConversation:
    return StateConversation(
        conversation_id=conversation.conversation_id,
        conversation_name=conversation.name,
        is_active=conversation.is_active,
        message_ids=[extract_message_id(x) for x in conversation.messages],
    )


def convert_task_to_state(task: Task) -> StateTask:
    # Get the first message as the description
    message = task.history[0] if task.history else None
    last_message = task.history[-1] if task.history else None
    output = (
        [extract_content(a.parts) for a in task.artifacts]
        if task.artifacts
        else []
    )
    if last_message != message:
        output = [extract_content(last_message.parts)] + output
    return StateTask(
        task_id=task.id,
        session_id=task.sessionId,
        state=str(task.status.state),
        message=convert_message_to_state(message),
        artifacts=output,
    )


def convert_event_to_state(event: Event) -> StateEvent:
    return StateEvent(
        conversation_id=extract_message_conversation(event.content),
        actor=event.actor,
        role=event.content.role,
        id=event.id,
        content=extract_content(event.content.parts),
    )


def extract_content(
    message_parts: list[Part],
) -> list[tuple[str | dict[str, Any], str]]:
    parts = []
    if not message_parts:
        return []
    for p in message_parts:
        if p.type == 'text':
            parts.append((p.text, 'text/plain'))
        elif p.type == 'file':
            if p.file.bytes:
                # Make sure we're passing the actual bytes field
                # Add a debug print to see what kind of data we have
                print(f"Processing file part with mimeType: {p.file.mimeType}, bytes: {type(p.file.bytes)} length: {len(p.file.bytes) if p.file.bytes else 0}")
                
                # When served from server.py's _files method, we'll get back a URL like /message/file/{id}
                # But when coming directly from an agent, we need to handle the base64 content properly
                # Create a data URI for audio content to be played in the browser
                if p.file.mimeType and 'audio' in p.file.mimeType:
                    # Create a data URI format for audio that can be played directly
                    data_uri = f"data:{p.file.mimeType};base64,{p.file.bytes}"
                    parts.append((data_uri, p.file.mimeType))
                else:
                    # For other file types, pass the bytes as before
                    parts.append((p.file.bytes, p.file.mimeType))
            else:
                print(f"Processing file part with URI: {p.file.uri}")
                parts.append((p.file.uri, p.file.mimeType))
        elif p.type == 'data':
            # Some agents return file-like data wrapped in a DataPart
            if isinstance(p.data, dict) and p.data.get('type') == 'file':
                file_info = p.data.get('file', {})
                mime_type = file_info.get('mimeType', 'application/octet-stream')
                file_bytes = file_info.get('bytes')
                file_uri = file_info.get('uri')

                if file_bytes:
                    if 'audio' in mime_type:
                        data_uri = f"data:{mime_type};base64,{file_bytes}"
                        parts.append((data_uri, mime_type))
                    else:
                        parts.append((file_bytes, mime_type))
                elif file_uri:
                    parts.append((file_uri, mime_type))
                else:
                    try:
                        jsonData = json.dumps(p.data)
                        parts.append((jsonData, 'application/json'))
                    except Exception as e:  # pylint: disable=broad-except
                        print('Failed to dump data', e)
                        parts.append(('<data>', 'text/plain'))
            else:
                try:
                    jsonData = json.dumps(p.data)
                    if 'type' in p.data and p.data['type'] == 'form':
                        parts.append((p.data, 'form'))
                    else:
                        parts.append((jsonData, 'application/json'))
                except Exception as e:  # pylint: disable=broad-except
                    print('Failed to dump data', e)
                    parts.append(('<data>', 'text/plain'))
    
    # Debug print the content we extracted
    print(f"Extracted {len(parts)} parts: {[(type(p[0]), p[1]) for p in parts]}")
    return parts


async def check_audio_support() -> bool:
    """Check if any registered agents support audio input"""
    client = ConversationClient(server_url)
    try:
        response = await client.list_agent(ListAgentRequest())
        agents = response.result
        
        # Check if any agent supports audio input
        for agent in agents:
            for input_mode in agent.defaultInputModes:
                if input_mode.startswith('audio/'):
                    return True
        
        return False
    except Exception as e:
        print('Failed to check audio support: ', e)
        return False


async def send_audio_message(audio_data: str, mime_type: str, filename: str):
    """Send an audio message to the agent"""
    app_state = me.state(AppState)
    
    # Create a unique message ID
    message_id = str(uuid.uuid4())
    
    # Get the current conversation
    c = next(
        (
            x
            for x in await ListConversations()
            if x.conversation_id == app_state.current_conversation_id
        ),
        None,
    )
    
    if not c:
        print('Conversation id ', app_state.current_conversation_id, ' not found')
        return False
    
    # Create the FilePart with the audio data
    audio_part = FilePart(
        file=FileContent(
            name=filename,
            mimeType=mime_type,
            bytes=audio_data
        )
    )
    
    # Create a message with the audio part
    request = Message(
        id=message_id,
        role='user',
        parts=[audio_part],
        metadata={
            'conversation_id': c.conversation_id if c else '',
            'conversation_name': c.name if c else '',
        },
    )
    
    # Add a background task
    app_state.background_tasks[message_id] = ''
    
    # Convert to state message
    state_message = convert_message_to_state(request)
    
    # Update app state
    if not app_state.messages:
        app_state.messages = []
    app_state.messages.append(state_message)
    
    # Update conversation message IDs
    conversation = next(
        filter(
            lambda x: x.conversation_id == c.conversation_id,
            app_state.conversations,
        ),
        None,
    )
    if conversation:
        conversation.message_ids.append(state_message.message_id)
    
    # Check if any agents can handle audio
    supports_audio = await check_audio_support()
    
    if not supports_audio:
        # Create a system message indicating no audio support
        system_message = Message(
            id=str(uuid.uuid4()),
            role='agent',
            parts=[TextPart(text="Sorry, there are no agents currently available that can process audio input. Please try sending a text message instead.")],
            metadata={
                'conversation_id': c.conversation_id,
                'is_system_message': True
            }
        )
        
        # Convert to state message and add to the conversation
        system_state_message = convert_message_to_state(system_message)
        app_state.messages.append(system_state_message)
        
        # Update conversation
        if conversation:
            conversation.message_ids.append(system_state_message.message_id)
        
        # Remove the pending task
        if message_id in app_state.background_tasks:
            del app_state.background_tasks[message_id]
        
        return False
    
    # Send message to the agent
    await SendMessage(request)
    return True