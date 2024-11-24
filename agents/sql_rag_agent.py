# agents/sql_rag_agent.py

import os
from langchain_workflows.workflow_definitions import SQLRAGWorkflow
from dotenv import load_dotenv
from typing import Any, List
from langchain_workflows.simple_chat_memory import Message


# Load environment variables from .env file
load_dotenv()


class SQLRAGAgent:
    def __init__(self):
        """
        Initializes the SQL RAG Agent by setting up the LangChain workflow.
        """
        
        self.workflow = SQLRAGWorkflow()
    
    def run_agent(self, user_input: str, messages: List[Message]) -> str:
        """
        Runs the LangChain agent with the given user input and memory.

        Args:
            user_input (str): The user's natural language instruction.
            messages (List[Message]): The existing conversation history.

        Returns:
            str: The full response from the agent.
        """
        response = self.workflow.run_agent(user_input, messages)
        return response
