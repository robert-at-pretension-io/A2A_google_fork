import mesop as me
from state.state import AppState, AudioRecorderState

async def send_audio_click(e: me.ClickEvent):
    """Handle send audio button click"""
    recorder_state = me.state(AudioRecorderState)
    
    if not recorder_state.audio_blob:
        return
    
    # Import here to avoid circular imports
    from state.host_agent_service import send_audio_message
    
    # Send the audio message
    await send_audio_message(
        audio_data=recorder_state.audio_blob,
        mime_type=recorder_state.audio_mime_type,
        filename=recorder_state.filename
    )
    
    # Reset recorder state after sending
    recorder_state.audio_blob = ""
    recorder_state.recording_duration = 0

@me.component
def send_audio_button():
    """Button to send recorded audio"""
    recorder_state = me.state(AudioRecorderState)
    
    # Only show if we have audio data
    if not recorder_state.audio_blob:
        return
    
    with me.content_button(
        on_click=send_audio_click,
        type='flat',
        style=me.Style(
            background='#4CAF50',
            color='white',
            border_radius=20,
            padding=me.Padding(left=10, right=10),
        ),
    ):
        me.icon(icon='send')
        me.text("Send Audio")