# langchain_workflows/workflow_definitions.py

import os
import sqlite3
import tempfile
from typing import Any, List

from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.schema import HumanMessage
from langchain_openai import AzureChatOpenAI
from sqlalchemy import create_engine, text
import pandas as pd

from tools.visualization_tool import draw_bar_chart
from tools.weather_tool import get_weather
from .simple_chat_memory import SimpleChatMemory, Message
from .prompts import react_agent_prompt_template

class SQLRAGWorkflow:
    def __init__(self, db_path: str = 'database/farm_management.db'):
        """
        Initializes the SQL RAG Workflow with Azure OpenAI and database connection.

        Args:
            db_path (str): Path to the SQLite database.
        """

        self.llm = AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_API_BASE"),
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            temperature=0
        )

        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        self.tools = self.initialize_tools()

    def initialize_tools(self) -> List[Tool]:
        """
        Defines and returns the tools available to the agent.

        Returns:
            List[Tool]: The tools for SQL query generation, execution, visualization, and weather checking.
        """
        # Tool to generate SQL queries
        sql_query_tool = Tool(
            name="SQL Query Generator",
            func=self.generate_sql_query,
            description="Generates SQL queries for the Crops (with their yields) and Wages (from years 2022 - 2024 for employees) tables based on natural language instructions. Wages are in PLN"
        )

        # Tool to execute SQL queries
        sql_execute_tool = Tool(
            name="SQL Executor",
            func=self.execute_sql_query,
            description="Executes provided SQL queries on the Crops and Wages tables and returns the results."
        )

        # Tool to visualize data
        visualization_tool = Tool(
            name="Data Visualizer",
            func=self.visualize_data,
            description="Creates bar charts from provided data tuples. Input should be a list of (label, value) tuples."
        )

        # Tool to fetch weather information
        weather_tool = Tool(
            name="Weather Checker",
            func=self.fetch_weather,
            description="Fetches current weather information for a specified location."
        )

        return [sql_query_tool, sql_execute_tool, visualization_tool, weather_tool]

    def initialize_agent(self, messages: List[Message]) -> AgentExecutor:
        """
        Initializes the LangChain agent with the defined tools and memory.

        Args:
            messages (List[Message]): List of Message objects to initialize memory.

        Returns:
            AgentExecutor: The configured agent executor with memory and tool call limit.
        """
        # Initialize memory from messages
        memory = SimpleChatMemory.from_messages(messages)

        # Initialize the agent with tools and custom prompt
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=react_agent_prompt_template,
        )

        # Create a AgentExecutor with a tool call limit
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            memory=memory,
            handle_parsing_errors=True,
            verbose=True
        )

        return agent_executor

    def run_agent(self, user_input: str, messages: List[Message]) -> str:
        """
        Runs the agent with the given user input and memory.

        Args:
            user_input (str): The user's natural language instruction.
            messages (List[Message]): The existing conversation history.

        Returns:
            str: The full response from the agent.
        """
        # Initialize the agent with current messages
        agent_executor = self.initialize_agent(messages)

        # Execute the agent synchronously and get the response
        response = agent_executor.stream({"input": user_input})

        return response

    def generate_sql_query(self, instruction: str) -> str:
        """
        Generates an SQL query based on the user's instruction.

        Args:
            instruction (str): Natural language instruction for SQL query.

        Returns:
            str: Generated SQL query.
        """
        # Create a prompt for generating the SQL query
        messages = [
            HumanMessage(content=(
                f"You are an SQL assistant. Generate a valid SQLite query based on the user's instruction.\n\n"
                f"Available tables and columns:\n"
                f"- Crops: crop_name (TEXT), year (INTEGER), month (TEXT), yield_amount (REAL), target (REAL)\n"
                f"- Wages: employee_name (TEXT), wage (REAL), year (INTEGER), month (TEXT), time_worked (REAL)\n\n"
                f"Key Notes:\n"
                f"- Always format 'month' as a capitalized string (e.g., 'July').\n"
                f"- The year is an INTEGER.\n"
                f"- Ensure SQLite compatibility. Do not use unsupported syntax.\n"
                f"- Do not include semicolons or stray quotation marks.\n\n"
                f"Instruction: {instruction}\n\nSQL Query:"
            ))
        ]

        # Generate query with the chat model
        response = self.llm(messages)
        sql_query = response.content.strip()

        # Sanitize output
        return sql_query


    def execute_sql_query(self, sql_query: str) -> Any:
        """
        Executes the provided SQL query on the SQLite database.

        Args:
            sql_query (str): The SQL query to execute.

        Returns:
            pd.DataFrame or str: Query results as a DataFrame or success/error message.
        """
        try:
            # Sanitize query by removing any trailing or leading characters
            cleaned_query = sql_query.strip().strip(";").strip('"').strip("'")
            
            # Execute query with SQLAlchemy
            with self.engine.connect() as connection:
                result = connection.execute(text(cleaned_query))
                
                # Handle SELECT queries
                if cleaned_query.lower().startswith("select"):
                    rows = result.fetchall()
                    if not rows:
                        return "Query returned no results."
                    df = pd.DataFrame(rows, columns=result.keys())
                    return df.to_string()
                
                # Handle other queries
                connection.commit()
                return "Query executed successfully."
        except sqlite3.OperationalError as oe:
            return f"SQLite OperationalError: {str(oe)}"
        except Exception as e:
            return f"An error occurred: {str(e)}"



    def visualize_data(self, data: str) -> str:
        """
        Creates a bar chart from the provided data and saves it to a temporary file.

        Args:
            data (str): A string representation of a list of tuples, e.g., "[('Wheat', 1500), ('Corn', 1800)]".

        Returns:
            str: Path to the saved bar chart image or an error message.
        """
        try:
            # Evaluate the string to convert it into a list of tuples
            data_tuples = eval(data)
            if not isinstance(data_tuples, list) or not all(isinstance(t, tuple) and len(t) == 2 for t in data_tuples):
                return "Invalid data format. Please provide a list of 2-element tuples."

            # Create a temporary file to save the bar chart
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", prefix="bar_chart_", dir="temp") as tmp_file:
                img_path = tmp_file.name

            # Ensure the temporary directory exists
            os.makedirs(os.path.dirname(img_path), exist_ok=True)

            # Draw and save the bar chart
            draw_bar_chart(data_tuples, title="Bar Chart", xlabel="Category", ylabel="Value", save_path=img_path)

            # Leave some trace to the agent that it should return the final answer now
            return f'{{"chart": "{img_path.replace("\\", "\\\\")}", "Thought": "I should now return the Final Answer."}}'  # Return the path to the saved image

        except Exception as e:
            return f"An error occurred while visualizing data: {str(e)}"

    def fetch_weather(self, location: str) -> Any:
        """
        Fetches current weather information for a given location.

        Args:
            location (str): The location to fetch weather for.

        Returns:
            dict or str: Weather data as a dictionary or an error message.
        """
        weather_info = get_weather(location)
        return weather_info
