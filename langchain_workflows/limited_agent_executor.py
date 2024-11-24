from langchain.agents import AgentExecutor
from pydantic import PrivateAttr


class LimitedAgentExecutor(AgentExecutor):
    """
    A custom agent executor with a limit on the number of tool calls.
    """

    # Define private attributes using Pydantic's PrivateAttr
    _tool_call_limit: int = PrivateAttr()
    _tool_call_count: int = PrivateAttr()

    def __init__(self, *args, tool_call_limit=10, **kwargs):
        """
        Initializes the LimitedAgentExecutor with a tool call limit.

        Args:
            tool_call_limit (int): The maximum number of tool calls allowed.
        """
        super().__init__(*args, **kwargs)
        self._tool_call_limit = tool_call_limit  # Set the tool call limit
        self._tool_call_count = 0  # Initialize the tool call counter

    def _call_tool(self, tool_name: str, tool_input: str):
        """
        Overrides the _call_tool method to track and limit tool calls.

        Args:
            tool_name (str): The name of the tool being called.
            tool_input (str): The input to the tool.

        Returns:
            Any: The result from the tool.
        """
        if self._tool_call_count >= self._tool_call_limit:
            raise Exception("Tool call limit exceeded.")
        self._tool_call_count += 1
        return super()._call_tool(tool_name, tool_input)

    def run(self, input: str):
        """
        Runs the agent with the given input. If the tool call limit is exceeded,
        returns a custom message.

        Args:
            input (str): The user's input.

        Returns:
            Any: The agent's response.
        """
        try:
            return super().run(input)
        except Exception:
            return "I'm sorry, but I cannot figure out how to respond to your request."
