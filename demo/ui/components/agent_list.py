import mesop as me
import pandas as pd

from common.types import AgentCard
from state.agent_state import AgentState
from state.host_agent_service import DeleteRemoteAgent, ListRemoteAgents


@me.component
def agents_list(
    agents: list[AgentCard],
):
    """Agents list component."""
    df_data = {
        'Address': [],
        'Name': [],
        'Description': [],
        'Organization': [],
        'Input Modes': [],
        'Output Modes': [],
        'Streaming': [],
        'Actions': [],
    }
    for agent_info in agents:
        df_data['Address'].append(agent_info.url)
        df_data['Name'].append(agent_info.name)
        df_data['Description'].append(agent_info.description)
        df_data['Organization'].append(
            agent_info.provider.organization if agent_info.provider else ''
        )
        df_data['Input Modes'].append(', '.join(agent_info.defaultInputModes))
        df_data['Output Modes'].append(', '.join(agent_info.defaultOutputModes))
        df_data['Streaming'].append(agent_info.capabilities.streaming)
        df_data['Actions'].append("Delete")
    df = pd.DataFrame(
        pd.DataFrame(df_data),
        columns=[
            'Address',
            'Name',
            'Description',
            'Organization',
            'Input Modes',
            'Output Modes',
            'Streaming',
            'Actions',
        ],
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
            header=me.TableHeader(sticky=True),
            columns={
                'Address': me.TableColumn(sticky=True),
                'Name': me.TableColumn(sticky=True),
                'Description': me.TableColumn(sticky=True),
                'Actions': me.TableColumn(sticky=True),
            },
            on_click=on_table_click,
        )
        with me.content_button(
            type='raised',
            on_click=add_agent,
            key='new_agent',
            style=me.Style(
                display='flex',
                flex_direction='row',
                gap=5,
                align_items='center',
                margin=me.Margin(top=10),
            ),
        ):
            me.icon(icon='upload')


def add_agent(e: me.ClickEvent):  # pylint: disable=unused-argument
    """Import agent button handler."""
    state = me.state(AgentState)
    state.agent_dialog_open = True
    
    
async def on_table_click(e: me.TableClickEvent):
    """Handle table clicks including delete action."""
    try:
        # Get the current agents from the ListRemoteAgents function
        # Using explicit import to avoid any potential issues with closures
        from state.host_agent_service import ListRemoteAgents
        agents = await ListRemoteAgents()
        
        # Build data from current agents
        df_data = {
            'Address': [],
            'Name': [],
            'Description': [],
            'Organization': [],
            'Input Modes': [],
            'Output Modes': [],
            'Streaming': [],
            'Actions': [],
        }
    except Exception as exc:
        print(f"Error in on_table_click: {exc}")
        # Return early if we can't get agents
        return
    
    for agent_info in agents:
        df_data['Address'].append(agent_info.url)
        df_data['Name'].append(agent_info.name)
        df_data['Description'].append(agent_info.description)
        df_data['Organization'].append(
            agent_info.provider.organization if agent_info.provider else ''
        )
        df_data['Input Modes'].append(', '.join(agent_info.defaultInputModes))
        df_data['Output Modes'].append(', '.join(agent_info.defaultOutputModes))
        df_data['Streaming'].append(agent_info.capabilities.streaming)
        df_data['Actions'].append("Delete")
    
    # Get column name from index
    column_names = list(df_data.keys())
    if e.col_index < len(column_names):
        column_name = column_names[e.col_index]
    else:
        column_name = ""
    
    # Get row data based on index
    row_index = e.row_index
    
    # Only handle clicks on the Actions column (for delete)
    if column_name == 'Actions' and row_index < len(df_data['Address']):
        agent_url = df_data['Address'][row_index]
        try:
            # Import explicitly to avoid NameError
            from state.host_agent_service import DeleteRemoteAgent
            # Delete the agent
            success = await DeleteRemoteAgent(agent_url)
            print(f"Agent deletion {'succeeded' if success else 'failed'}: {agent_url}")
            # Yield to trigger UI update
            yield
        except Exception as e:
            print(f"Error deleting agent: {e}")
    yield
