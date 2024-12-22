from pydantic_ai import Agent
from pydantic_ai.messages import UserPrompt, ModelTextResponse
import streamlit as st
import asyncio


if st.session_state.get("agent") is None:
    st.session_state["agent"] = Agent("openai:gpt-4o-mini")
    st.session_state["history"] = []

agent = st.session_state["agent"]
history = st.session_state["history"]

for message in history:
    if message.role == "user":
        st.chat_message("user").markdown(message.content)
    elif message.role == "model-text-response":
        st.chat_message("assistant").markdown(message.content)

# React to user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.history.append(UserPrompt(content=prompt))

    

    # Run async code in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response = loop.run_until_complete(
        agent.run(prompt, message_history=history)
    )
    loop.close()
    
    
    # Display assistant response in chat message container
    st.chat_message("assistant").markdown(response.data)
    # Add assistant response to chat history
    st.session_state.history.append(ModelTextResponse(content=response.data))

st.write(st.session_state.history)