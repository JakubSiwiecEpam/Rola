# simple_chat_memory.py

from typing import Any, Dict, List 
from langchain.memory.chat_memory import BaseChatMemory
from enum import Enum

class Role(Enum):
    USER = 'user'
    ASSISTANT = 'assistant'

class Message:
    def __init__(self, role: Role, content: str):
        self.role = role
        self.content = content

class SimpleChatMemory(BaseChatMemory):
    chat_memory: List[Dict[str, str]] = []

    def add_message(self, message: str, is_human: bool):
        self.chat_memory.append({"role": "user" if is_human else "assistant", "content": message})

    @property
    def memory_variables(self) -> List[str]:
        return ["chat_history"]

    def load_memory_variables(self, _: Dict[str, Any]) -> Dict[str, Any]:
        return {"chat_history": self.chat_memory}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        self.add_message(inputs.get("input", ""), is_human=True)
        self.add_message(outputs.get("output", ""), is_human=False)

    def clear(self) -> None:
        self.chat_memory = []

    @classmethod
    def from_messages(cls, messages: List[Message]) -> 'SimpleChatMemory':
        memory = cls()
        for message in messages:
            is_human = message.role == Role.USER
            memory.add_message(message.content, is_human)
        return memory
