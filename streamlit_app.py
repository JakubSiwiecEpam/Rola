# streamlit_app.py

import json
from typing import Any, List
import streamlit as st
from agents.sql_rag_agent import SQLRAGAgent
import uuid
import pandas as pd
from dotenv import load_dotenv
from langchain_workflows.simple_chat_memory import Message, Role
from langchain_workflows.formatting import parse_tool_observetion, trim_agent_response
from langchain.globals import set_verbose

# Load environment variables
load_dotenv()

# Initialize the SQL RAG Agent
agent = SQLRAGAgent()
set_verbose(True)

# Initialize session state for conversations and memory
if 'conversations' not in st.session_state:
    st.session_state.conversations = {}

if 'current_conversation' not in st.session_state:
    # Create a default conversation
    default_conv_id = str(uuid.uuid4())
    st.session_state.conversations[default_conv_id] = {
        'name': 'Default Conversation',
        'messages': []
    }
    st.session_state.current_conversation = default_conv_id


def select_conversation():
    """
    Sidebar to select existing conversations or create a new one.
    """
    st.sidebar.title("Conversations")

    # List existing conversations
    for conv_id, conv in st.session_state.conversations.items():
        if st.sidebar.button(conv['name'], key=conv_id):
            st.session_state.current_conversation = conv_id

    st.sidebar.markdown("---")

    # Option to create a new conversation
    if st.sidebar.button("New Conversation"):
        new_conv_id = str(uuid.uuid4())
        st.session_state.conversations[new_conv_id] = {
            'name': f'Conversation {len(st.session_state.conversations) + 1}',
            'messages': []
        }
        st.session_state.current_conversation = new_conv_id


def get_current_messages() -> List[Message]:
    """
    Retrieve messages for the current conversation.
    """
    conv_id = st.session_state.current_conversation
    return [
        Message(role=Role.USER, content=m['content']) if m['sender'] == 'User' 
        else Message(role=Role.ASSISTANT, content=m['llm_history']) 
        for m in st.session_state.conversations[conv_id]['messages']
    ]


def add_message(sender: str, ui_content: Any, llm_history_content: Any):
    """
    Add a message to the current conversation.
    
    Args:
        sender (str): 'User' or 'Agent'.
        content (Any): The content of the message.
    """
    conv_id = st.session_state.current_conversation
    st.session_state.conversations[conv_id]['messages'].append({
        'sender': sender,
        'content': ui_content,
        'llm_history': llm_history_content
    })


def parse_agent_response(response) -> (List[str], str):
    """
    Parses the agent's response into individual steps and the final answer.

    Args:
        response (str): The raw response from the agent.

    Returns:
        Tuple[List[str], str]: A list of step messages and the final answer.
    """
    steps = []
    final_answer = ""
    markdown_bar_chart = ""
    print("Parsing response...")
    for stage in response:
        if not stage.get("output"):
            if stage.get("steps"):
                tool_step = stage.get("steps")[0]
                tool_name = tool_step.action.tool
                steps.append(f" **{tool_name} Tool:** {parse_tool_observetion(tool_name, tool_step.observation)}")
                # get the bar chart from data visualizer tool
                if tool_name == "Data Visualizer":
                    print(tool_step.observation)
                    try:
                        bar_chart_path = json.loads(tool_step.observation).get("chart")
                        with open(bar_chart_path, "r") as f:
                            bar_chart_base64 = f.read()
                            markdown_bar_chart = f"![Alt Text](data:image/png;base64,{bar_chart_base64})"
                    except:
                        markdown_bar_chart = "Sadly, I couldn't generate bar chart :((("
            else:
                steps.append(f" **Thinking...** {trim_agent_response(stage.get("messages")[0].content)}")
        if stage.get("output"):
            final_answer =  stage.get('output')
    return steps, final_answer, markdown_bar_chart


def display_agent_response(agent_response: dict):
    """
    Displays the agent's response in the UI.

    Args:
        agent_response (dict): The full response from the agent.
    """
    steps, final_answer, markdown_bar_chart = parse_agent_response(agent_response)

    # Build the formatted message with Markdown
    formatted_message = ""

    # Add steps
    for idx, step_text in enumerate(steps, start=1):
        formatted_message += f"**{idx}.** {step_text.strip()}\n\n"

    # Add the final answer
    if final_answer:
        formatted_message += f"**Final Answer:**\n\n{final_answer.strip()}"
    if markdown_bar_chart:
        formatted_message += f"\n**Requested chart:**\n\n{markdown_bar_chart}"

    # Display the formatted message in Markdown
    with st.chat_message("assistant"):
        print(formatted_message)
        st.markdown(formatted_message, unsafe_allow_html=True)

    # Add the raw message to the conversation for history
    add_message("Agent", formatted_message.strip(), final_answer.strip()) # to llm_history add only the final answer. Tool outputs are not needed here



def main():
    st.set_page_config(page_title="SQL RAG Agent for Farm Management", page_icon="🌾", layout="wide")
    st.title("🌾 SQL RAG Agent for Farm Management")

    # Sidebar for conversation selection
    select_conversation()

    # Main chat interface
    conv_id = st.session_state.current_conversation
    conv_name = st.session_state.conversations[conv_id]['name']
    st.header(conv_name)

    # Display conversation messages using st.chat_message
    for msg in st.session_state.conversations[conv_id]['messages']:
        with st.chat_message("user" if msg['sender'] == 'User' else "assistant"):
            if isinstance(msg['content'], pd.DataFrame):
                st.table(msg['content'])
            elif isinstance(msg['content'], dict):
                # Display weather information
                st.markdown("**Weather Information:**")
                weather_df = pd.DataFrame([msg['content']])
                st.table(weather_df)
            elif isinstance(msg['content'], str) and msg['content'].startswith('<img'):
                # Display visualization image
                st.markdown(msg['content'], unsafe_allow_html=True)
            else:
                st.write(msg['content'])

    st.markdown("---")

    # Input field for user instruction using st.chat_input
    user_input = st.chat_input("Type your instruction...")

    if user_input:
        # Add the user's input to the conversation
        add_message("User", user_input, user_input)

        # Retrieve the current conversation's messages
        conversation_messages = get_current_messages()
        print("conversation_messages", list(conversation_messages))

        # Display the user's message
        with st.chat_message("user"):
            st.write(user_input)

        # Run the agent synchronously and display the response
        try:
            # Run the agent and get the full response as a string
            agent_response = agent.run_agent(user_input, conversation_messages)

            # Display the full agent response
            display_agent_response(agent_response)

        except TimeoutError as e:
            with st.chat_message("assistant"):
                st.write(str(e))
            add_message("Agent", str(e), str(e))


if __name__ == "__main__":
    main()
