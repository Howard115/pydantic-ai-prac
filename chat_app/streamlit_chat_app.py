"""Streamlit Chat Application

A simple chat interface built with Streamlit that allows users to interact with an AI agent.
The app supports:
- Real-time chat with streaming responses
- Message history persistence
- Weather information queries

Run with:
    streamlit run streamlit_chat_app.py
"""

import streamlit as st
from pathlib import Path
from dataclasses import dataclass
from typing import Iterator, Union
import json
from datetime import datetime
import asyncio


from pydantic_ai import Agent
from pydantic_ai.messages import (
    Message,
    ModelTextResponse,
    UserPrompt,
    SystemPrompt,
    ToolReturn,
    RetryPrompt,
    ModelStructuredResponse,
)

# Constants
THIS_DIR = Path(__file__).parent
MODEL_NAME = "openai:gpt-4"

# Message Types
MessageTypes = Union[
    SystemPrompt,
    UserPrompt,
    ToolReturn,
    RetryPrompt,
    ModelTextResponse,
    ModelStructuredResponse,
]


class ChatAgent:
    """Handles AI agent initialization and tools."""

    def __init__(self):
        self.agent = Agent(MODEL_NAME)
        self._register_tools()

    def _register_tools(self):
        """Register all available tools for the agent."""

        @self.agent.tool_plain
        def get_weather(location: str) -> str:
            """Get the weather for a given location."""
            return f"The weather in {location} is sunny."


@dataclass
class MessageDatabase:
    """Handles persistence of chat messages using a JSONL file.

    Each line in the file contains a JSON array of message objects.
    Messages are stored with their type, content, and timestamp.
    """

    file: Path = THIS_DIR / "chat_app_messages.jsonl"

    def add_messages(self, messages: list[Message]) -> None:
        """Add new messages to the database.

        Args:
            messages: List of Message objects to store
        """
        with self.file.open("a") as f:
            messages_data = [self._serialize_message(msg) for msg in messages]
            json_data = json.dumps(messages_data)
            f.write(json_data + "\n")

    def _serialize_message(self, msg: Message) -> dict:
        """Convert a message object to a dictionary format.

        Handles both Pydantic v1 and v2 message objects.
        """
        if hasattr(msg, "model_dump"):
            return msg.model_dump()

        # Fallback for older message formats
        return {
            "content": msg.content,
            "role": msg.role,
            "timestamp": msg.timestamp.isoformat()
            if hasattr(msg, "timestamp")
            else datetime.now().isoformat(),
        }

    def get_messages(self) -> Iterator[Message]:
        """Retrieve all messages from the database.

        Yields:
            Message objects in chronological order
        """
        if not self.file.exists():
            return

        with self.file.open() as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    messages_data = json.loads(line)
                    if isinstance(messages_data, list):
                        yield from self._parse_messages(messages_data)
                except Exception as e:
                    print(f"Error parsing line: {e}")

    def _parse_messages(self, messages_data: list) -> Iterator[Message]:
        """Parse a list of message data into Message objects."""
        for msg_data in messages_data:
            try:
                # Parse timestamp if it's a string
                if isinstance(msg_data.get("timestamp"), str):
                    msg_data["timestamp"] = datetime.fromisoformat(
                        msg_data["timestamp"]
                    )

                # Create appropriate message type based on role
                yield self._create_message_by_role(msg_data)
            except Exception as e:
                print(f"Error parsing message: {e}")

    def _create_message_by_role(self, msg_data: dict) -> Message:
        """Create a message object of the appropriate type based on its role."""
        role_to_class = {
            "user": UserPrompt,
            "model-text-response": ModelTextResponse,
            "system": SystemPrompt,
            "tool-return": ToolReturn,
            "retry": RetryPrompt,
            "model-structured-response": ModelStructuredResponse,
        }

        role = msg_data.get("role")
        message_class = role_to_class.get(role)
        if message_class:
            return message_class(**msg_data)
        raise ValueError(f"Unknown message role: {role}")


class ChatUI:
    """Handles the Streamlit UI components and chat interaction logic."""

    def __init__(self):
        self.agent = ChatAgent()
        self.database = MessageDatabase()
        self._initialize_session()

    def _initialize_session(self):
        """Initialize or restore the chat session state."""
        if "messages" not in st.session_state:
            st.session_state.messages = []
            st.session_state.messages.extend(self.database.get_messages())

    async def _process_response(self, prompt: str, message_placeholder):
        """Process the AI response with streaming updates."""
        full_response = ""
        async with self.agent.agent.run_stream(
            prompt, message_history=st.session_state.messages
        ) as result:
            async for text in result.stream(debounce_by=0.01):
                full_response = text
                message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        return full_response, result

    def display_messages(self):
        """Display all messages in the chat history."""
        for message in st.session_state.messages:
            role = "user" if message.role == "user" else "assistant"
            with st.chat_message(role):
                st.write(message.content)

    def handle_user_input(self):
        """Process user input and generate AI response."""
        if prompt := st.chat_input("Type your message here..."):
            # Add and display user message
            user_message = UserPrompt(content=prompt)
            st.session_state.messages.append(user_message)
            with st.chat_message("user"):
                st.write(prompt)

            # Get and display AI response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()

                # Run async code in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                full_response, result = loop.run_until_complete(
                    self._process_response(prompt, message_placeholder)
                )
                loop.close()

                if full_response:
                    # Save response to chat history
                    ai_message = ModelTextResponse(
                        content=full_response, timestamp=datetime.now()
                    )
                    st.session_state.messages.append(ai_message)

                    # Persist messages
                    self.database.add_messages([user_message, ai_message])

    def run(self):
        """Run the chat application."""
        st.title("Chat App")
        st.write("Ask me anything...")

        self.display_messages()
        self.handle_user_input()


def main():
    """Main entry point for the application."""
    chat_ui = ChatUI()
    chat_ui.run()


if __name__ == "__main__":
    main()
