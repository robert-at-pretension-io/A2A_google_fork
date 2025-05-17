import mesop as me
import pandas as pd

from state.host_agent_service import CreateConversation, DeleteConversation
from state.state import AppState, StateConversation


@me.component
def conversation_list(conversations: list[StateConversation]):
    """Conversation list component"""
    df_data = {'ID': [], 'Name': [], 'Status': [], 'Messages': [], 'Actions': []}
    for conversation in conversations:
        df_data['ID'].append(conversation.conversation_id)
        df_data['Name'].append(conversation.conversation_name)
        df_data['Status'].append('Open' if conversation.is_active else 'Closed')
        df_data['Messages'].append(len(conversation.message_ids))
        df_data['Actions'].append("Delete")
    df = pd.DataFrame(
        pd.DataFrame(df_data), columns=['ID', 'Name', 'Status', 'Messages', 'Actions']
    )
    with me.box(
        style=me.Style(
            display='flex',
            justify_content='space-between',
            flex_direction='column',
        )
    ):
        me.table(
            df,
            on_click=on_click,
            header=me.TableHeader(sticky=True),
            columns={
                'ID': me.TableColumn(sticky=True),
                'Name': me.TableColumn(sticky=True),
                'Status': me.TableColumn(sticky=True),
                'Messages': me.TableColumn(sticky=True),
                'Actions': me.TableColumn(sticky=True),
            },
        )
        with me.content_button(
            type='raised',
            on_click=add_conversation,
            key='new_conversation',
            style=me.Style(
                display='flex',
                flex_direction='row',
                gap=5,
                align_items='center',
                margin=me.Margin(top=10),
            ),
        ):
            me.icon(icon='add')


async def add_conversation(e: me.ClickEvent):  # pylint: disable=unused-argument
    """Add conversation button handler"""
    response = await CreateConversation()
    me.state(AppState).messages = []
    me.navigate(
        '/conversation',
        query_params={'conversation_id': response.conversation_id},
    )
    yield


async def on_click(e: me.TableClickEvent):
    """Handle table click including navigation and delete actions"""
    # Get the current DataFrames columns and data
    df_data = {'ID': [], 'Name': [], 'Status': [], 'Messages': [], 'Actions': []}
    for conversation in me.state(AppState).conversations:
        df_data['ID'].append(conversation.conversation_id)
        df_data['Name'].append(conversation.conversation_name)
        df_data['Status'].append('Open' if conversation.is_active else 'Closed')
        df_data['Messages'].append(len(conversation.message_ids))
        df_data['Actions'].append("Delete")
    df = pd.DataFrame(df_data)
    
    # Get column name from index
    column_names = list(df.columns)
    if e.col_index < len(column_names):
        column_name = column_names[e.col_index]
    else:
        column_name = ""
        
    # Get row data based on index
    row_index = e.row_index
    conversation_id = df_data['ID'][row_index] if row_index < len(df_data['ID']) else None
    
    # Handle the click based on column
    if column_name == 'Actions':
        # Delete conversation
        if conversation_id:
            success = await DeleteConversation(conversation_id)
            if success:
                # Force state update to trigger re-render
                state = me.state(AppState)
                # Make a shallow copy of the conversations list to trigger a state change
                state.conversations = state.conversations.copy()
                # Yield to trigger render
                yield
    else:
        # Navigate to conversation
        state = me.state(AppState)
        if row_index < len(state.conversations):
            conversation = state.conversations[row_index]
            state.current_conversation_id = conversation.conversation_id
            me.query_params.update({'conversation_id': conversation.conversation_id})
            me.navigate('/conversation', query_params=me.query_params)
    yield
