import mesop as me

from state.state import AppState, StateMessage


@me.component
def chat_bubble(message: StateMessage, key: str):
    """Chat bubble component"""
    app_state = me.state(AppState)
    show_progress_bar = (
        message.message_id in app_state.background_tasks
        or message.message_id in app_state.message_aliases.values()
    )
    progress_text = ''
    if show_progress_bar:
        progress_text = app_state.background_tasks[message.message_id]
    if not message.content:
        print('No message content')
    for pair in message.content:
        chat_box(
            pair[0],
            pair[1],
            message.role,
            key,
            progress_bar=show_progress_bar,
            progress_text=progress_text,
        )


def _render_audio(audio_src: str):
    """Renders an HTML5 audio player for the given audio source."""
    me.html(
        f'''
        <div style="display: flex; flex-direction: column; align-items: center;">
            <audio controls src="{audio_src}" style="max-width: 300px; margin: 5px 0;">
                Your browser does not support the audio element.
            </audio>
            <span style="font-size: 12px; color: #666;">Audio message</span>
        </div>
        ''',
        style=me.Style(
            margin=me.Margin(top=5, left=0, right=0, bottom=5),
            padding=me.Padding(top=1, left=15, right=15, bottom=1),
            background=me.theme_var('secondary-container'),
            border_radius=15,
            box_shadow='0 1px 2px 0 rgba(60, 64, 67, 0.3), 0 1px 3px 1px rgba(60, 64, 67, 0.15)',
        ),
        mode='sandboxed',
    )


def chat_box(
    content: str | dict,
    media_type: str,
    role: str,
    key: str,
    progress_bar: bool,
    progress_text: str,
):
    with me.box(
        style=me.Style(
            display='flex',
            justify_content=('space-between' if role == 'agent' else 'end'),
            min_width=500,
        ),
        key=key,
    ):
        with me.box(
            style=me.Style(display='flex', flex_direction='column', gap=5)
        ):
            if media_type == 'image/png':
                if '/message/file' not in content:
                    content = 'data:image/png;base64,' + content
                me.image(
                    src=content,
                    style=me.Style(
                        width='50%',
                        object_fit='contain',
                    ),
                )
            elif media_type == 'audio/mpeg':
                # Handle both string and dictionary content types for audio
                audio_src = ""
                
                # If content is a dictionary (like from the JSON response)
                if isinstance(content, dict):
                    print(f"Received audio content as dictionary: {content.keys() if content else 'empty'}")
                    
                    # Extract the file data from dictionary structure
                    if content.get('type') == 'file' and isinstance(content.get('file'), dict):
                        file_data = content['file']
                        mime_type = file_data.get('mimeType', 'audio/mpeg')
                        
                        if file_data.get('bytes'):
                            # Convert bytes to data URI
                            audio_src = f"data:{mime_type};base64,{file_data['bytes']}"
                            print(f"Created data URI from bytes, starts with: {audio_src[:50]}...")
                        elif file_data.get('uri'):
                            audio_src = file_data['uri']
                            print(f"Using URI from file data: {audio_src}")
                    else:
                        # Try to convert the dictionary to a readable format
                        import json
                        error_msg = f"Unsupported audio format: {json.dumps(content)[:100]}..."
                        print(error_msg)
                        me.text(error_msg)
                        return
                else:
                    # For string content
                    print(f"Processing audio content: {'Data URI' if isinstance(content, str) and content.startswith('data:') else 'Base64' if isinstance(content, str) and '/message/file' not in content else 'File URL'}")
                    
                    # Ensure proper data URI format for string content
                    if isinstance(content, str):
                        if '/message/file' not in content and not content.startswith('data:'):
                            # This is a base64 string that needs a data URI prefix
                            audio_src = 'data:audio/mpeg;base64,' + content
                            print(f"Converted to data URI, starts with: {audio_src[:50]}...")
                        else:
                            audio_src = content
                
                if not audio_src:
                    print("Could not extract audio source from content")
                    me.text("Error: Could not process audio content")
                    return
                
                _render_audio(audio_src)
            else:
                # Handle other content types (text, JSON, or potentially complex dicts with audio)
                if isinstance(content, dict):
                    # Attempt to find and render audio if present in a generic dict structure
                    audio_data_extracted = None
                    if 'response' in content and isinstance(content['response'], dict):
                        response_data = content['response']
                        if 'result' in response_data and isinstance(response_data['result'], list):
                            for part in response_data['result']:
                                if isinstance(part, dict) and part.get('type') == 'file':
                                    file_obj = part.get('file')
                                    if isinstance(file_obj, dict) and \
                                       file_obj.get('bytes') and \
                                       isinstance(file_obj.get('mimeType'), str) and \
                                       file_obj['mimeType'].startswith('audio/'):
                                        audio_data_extracted = (file_obj['bytes'], file_obj['mimeType'])
                                        print(f"Extracted audio from generic dict: {file_obj['mimeType']}")
                                        break 
                    
                    if audio_data_extracted:
                        audio_bytes, audio_mime_type = audio_data_extracted
                        audio_src_extracted = f"data:{audio_mime_type};base64,{audio_bytes}"
                        _render_audio(audio_src_extracted)
                    else:
                        # Original behavior: display dict as JSON code
                        import json
                        try:
                            formatted_content = json.dumps(content, indent=2)
                            me.code(
                                formatted_content,
                                language="json",
                            style=me.Style(
                                font_family='Roboto Mono, monospace',
                                box_shadow=(
                                    '0 1px 2px 0 rgba(60, 64, 67, 0.3), '
                                    '0 1px 3px 1px rgba(60, 64, 67, 0.15)'
                                ),
                                padding=me.Padding(top=5, left=15, right=15, bottom=5),
                                margin=me.Margin(top=5, left=0, right=0, bottom=5),
                                background=(
                                    me.theme_var('primary-container')
                                    if role == 'user'
                                    else me.theme_var('secondary-container')
                                ),
                                border_radius=15,
                                max_height="400px",
                                overflow="auto",
                            ),
                        )
                    except Exception as e:
                        print(f"Error formatting dictionary content: {e}")
                        me.text(f"Error displaying content: {str(e)}")
                else:
                    # Regular string content 
                    me.markdown(
                        content,
                        style=me.Style(
                            font_family='Google Sans',
                            box_shadow=(
                                '0 1px 2px 0 rgba(60, 64, 67, 0.3), '
                                '0 1px 3px 1px rgba(60, 64, 67, 0.15)'
                            ),
                            padding=me.Padding(top=1, left=15, right=15, bottom=1),
                            margin=me.Margin(top=5, left=0, right=0, bottom=5),
                            background=(
                                me.theme_var('primary-container')
                                if role == 'user'
                                else me.theme_var('secondary-container')
                            ),
                            border_radius=15,
                        ),
                    )
    if progress_bar:
        with me.box(
            style=me.Style(
                display='flex',
                justify_content=('space-between' if role == 'user' else 'end'),
                min_width=500,
            ),
            key=key,
        ):
            with me.box(
                style=me.Style(display='flex', flex_direction='column', gap=5)
            ):
                with me.box(
                    style=me.Style(
                        font_family='Google Sans',
                        box_shadow=(
                            '0 1px 2px 0 rgba(60, 64, 67, 0.3), '
                            '0 1px 3px 1px rgba(60, 64, 67, 0.15)'
                        ),
                        padding=me.Padding(top=1, left=15, right=15, bottom=1),
                        margin=me.Margin(top=5, left=0, right=0, bottom=5),
                        background=(
                            me.theme_var('primary-container')
                            if role == 'agent'
                            else me.theme_var('secondary-container')
                        ),
                        border_radius=15,
                    ),
                ):
                    if not progress_text:
                        progress_text = 'Working...'
                    me.text(
                        progress_text,
                        style=me.Style(
                            padding=me.Padding(
                                top=1, left=15, right=15, bottom=1
                            ),
                            margin=me.Margin(top=5, left=0, right=0, bottom=5),
                        ),
                    )
                    me.progress_bar(color='accent')
