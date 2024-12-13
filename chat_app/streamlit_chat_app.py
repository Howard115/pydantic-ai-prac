"""Simple chat app example built with Streamlit.

Run with:
    streamlit run streamlit_chat_app.py
"""

import streamlit as st
from pathlib import Path
from dataclasses import dataclass
from typing import Iterator, Annotated
import json
from datetime import datetime
import asyncio

from pydantic import Field, TypeAdapter
from pydantic_ai import Agent
from pydantic_ai.messages import (
    Message,
    MessagesTypeAdapter,
    ModelTextResponse,
    UserPrompt,
)

# Initialize the agent
agent = Agent("openai:gpt-4")

@agent.tool_plain
def get_weather(location: str) -> str:
    """Get the weather for a given location."""
    return f"The weather in {location} is sunny."

THIS_DIR = Path(__file__).parent

@dataclass
class Database:
    """Very rudimentary database to store chat messages in a JSON lines file."""
    file: Path = THIS_DIR / "chat_app_messages.jsonl"

    def add_messages(self, messages: list[Message]):
        with self.file.open("a") as f:
            # Wrap messages in a list for MessagesTypeAdapter
            messages_json = MessagesTypeAdapter.dump_json(messages)
            f.write(messages_json.decode() + "\n")

    def get_messages(self) -> Iterator[Message]:
        if self.file.exists():
            with self.file.open("rb") as f:
                for line in f:
                    if line.strip():
                        try:
                            # Try to parse as a list of messages first
                            messages = MessagesTypeAdapter.validate_json(line)
                            yield from messages
                        except Exception:
                            # If that fails, try parsing as a single message
                            try:
                                message_data = json.loads(line)
                                if isinstance(message_data, list):
                                    messages = MessagesTypeAdapter.validate_json(line)
                                    yield from messages
                                else:
                                    messages = MessagesTypeAdapter.validate_json(json.dumps([message_data]).encode())
                                    yield from messages
                            except Exception as e:
                                print(f"Error parsing message: {e}")
                                continue

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Load existing messages from the database
        database = Database()
        st.session_state.messages.extend(database.get_messages())

async def process_response(prompt: str, message_placeholder):
    full_response = ""
    async with agent.run_stream(prompt, message_history=st.session_state.messages) as result:
        async for text in result.stream(debounce_by=0.01):
            full_response = text
            message_placeholder.markdown(full_response + "▌")
    message_placeholder.markdown(full_response)
    return full_response, result

def main():
    st.title("Chat App")
    st.write("Ask me anything...")

    initialize_session_state()

    # Display chat messages
    for message in st.session_state.messages:
        if message.role == "user":
            with st.chat_message("user"):
                st.write(message.content)
        elif message.role == "model-text-response":
            with st.chat_message("assistant"):
                st.write(message.content)

    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat
        user_message = UserPrompt(content=prompt)
        st.session_state.messages.append(user_message)
        
        with st.chat_message("user"):
            st.write(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            # Run async code in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            full_response, result = loop.run_until_complete(process_response(prompt, message_placeholder))
            loop.close()
            
            # Add AI response to chat history
            if full_response:
                ai_message = ModelTextResponse(content=full_response, timestamp=datetime.now().isoformat())
                st.session_state.messages.append(ai_message)
                
                # Save to database
                database = Database()
                database.add_messages([user_message, ai_message])

if __name__ == "__main__":
    main() 