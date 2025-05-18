import time
import uuid
import mesop as me
from state.state import AppState, SettingsState, AudioRecorderState

def _gen_filename():
    """Generate a unique filename for audio recording"""
    timestamp = int(time.time())
    unique_id = uuid.uuid4().hex[:8]
    return f"audio_recording_{timestamp}_{unique_id}.wav"

def start_recording_click(e: me.ClickEvent):
    """Handle start recording button click"""
    state = me.state(AudioRecorderState)
    state.is_recording = True
    state.recording_duration = 0
    state.filename = _gen_filename()

def stop_recording_click(e: me.ClickEvent):
    """Handle stop recording button click"""
    state = me.state(AudioRecorderState)
    state.is_recording = False

@me.component
def audio_recorder():
    """Audio recorder component using HTML embedding for browser APIs"""
    state = me.state(AudioRecorderState)
    settings_state = me.state(SettingsState)
    
    # Only show if audio recording is enabled in settings
    if not getattr(settings_state, "audio_recording_enabled", True):
        return
    
    # Main container
    with me.box(
        style=me.Style(
            display='flex',
            flex_direction='column',
            align_items='center',
            padding=me.Padding(top=10, bottom=10),
            gap=10,
        )
    ):
        # Recording status and timer
        if state.is_recording:
            me.text(
                f"Recording... {state.recording_duration}s",
                style=me.Style(
                    color='red',
                    font_weight='bold',
                    font_size=14,
                ),
            )
        
        # Controls
        with me.box(
            style=me.Style(
                display='flex',
                flex_direction='row',
                gap=10,
                align_items='center',
            )
        ):
            # Embed the recorder's HTML/JavaScript
            me.html(
                f"""
                <div id="audio-recorder-container">
                    <script>
                        // Initialize variables for MediaRecorder
                        let mediaRecorder;
                        let audioChunks = [];
                        let recordingInterval;
                        
                        // Setup function to be called when buttons are clicked
                        function setupRecorder() {{
                            // Only setup once
                            if (typeof mediaRecorder !== 'undefined') return;
                            
                            navigator.mediaDevices.getUserMedia({{ audio: true }})
                            .then(function(stream) {{
                                mediaRecorder = new MediaRecorder(stream);
                                
                                mediaRecorder.addEventListener('dataavailable', function(e) {{
                                    audioChunks.push(e.data);
                                }});
                                
                                mediaRecorder.addEventListener('stop', function() {{
                                    const audioBlob = new Blob(audioChunks, {{ type: 'audio/wav' }});
                                    const reader = new FileReader();
                                    reader.readAsDataURL(audioBlob);
                                    reader.onloadend = function() {{
                                        const base64data = reader.result.split(',')[1];
                                        document.getElementById('audio-data-input').value = base64data;
                                        document.getElementById('audio-data-form').submit();
                                        audioChunks = [];
                                    }};
                                }});
                            }})
                            .catch(function(err) {{
                                console.error('Error accessing microphone:', err);
                                document.getElementById('audio-error-display').textContent = 
                                    'Error accessing microphone: ' + err.message;
                            }});
                        }}
                        
                        // Define start and stop functions to be called from buttons
                        function startRecording() {{
                            setupRecorder();
                            if (mediaRecorder && mediaRecorder.state !== 'recording') {{
                                audioChunks = [];
                                mediaRecorder.start();
                                
                                // Update duration counter
                                let duration = 0;
                                document.getElementById('recording-duration').textContent = duration;
                                recordingInterval = setInterval(function() {{
                                    duration += 1;
                                    document.getElementById('recording-duration').textContent = duration;
                                }}, 1000);
                            }}
                        }}
                        
                        function stopRecording() {{
                            if (mediaRecorder && mediaRecorder.state === 'recording') {{
                                mediaRecorder.stop();
                                clearInterval(recordingInterval);
                            }}
                        }}
                    </script>
                    
                    <!-- Hidden form to submit audio data -->
                    <form id="audio-data-form" method="post" action="/audio-upload" style="display:none;">
                        <input id="audio-data-input" type="hidden" name="audio_data" value="">
                        <input type="hidden" name="filename" value="{state.filename}">
                    </form>
                    
                    <!-- Invisible span for updating recording duration -->
                    <span id="recording-duration" style="display:none;">0</span>
                    
                    <!-- Error display -->
                    <div id="audio-error-display" style="color: red; font-size: 12px;"></div>
                </div>
                """,
                mode="sandboxed",
                style=me.Style(
                    width="0px",
                    height="0px",
                    overflow="hidden",
                )
            )
            
            # Record button
            if not state.is_recording:
                with me.box(
                    style=me.Style(
                        display='flex',
                        flex_direction='row',
                        align_items='center',
                        gap=5,
                    )
                ):
                    with me.content_button(
                        on_click=start_recording_click,
                        type='flat',
                        style=me.Style(
                            background='#f44336',
                            color='white',
                            border_radius=20,
                            padding=me.Padding(left=10, right=10),
                        ),
                    ):
                        me.icon(icon='mic')
                        me.text("Record")
                    
                    # Audio preview if available
                    if state.audio_blob:
                        me.audio(
                            src=f"data:{state.audio_mime_type};base64,{state.audio_blob}",
                            autoplay=False,
                        )
            else:
                # Stop button
                with me.content_button(
                    on_click=stop_recording_click,
                    type='flat',
                    style=me.Style(
                        background='#555',
                        color='white',
                        border_radius=20,
                        padding=me.Padding(left=10, right=10),
                    ),
                ):
                    me.icon(icon='stop')
                    me.text("Stop")