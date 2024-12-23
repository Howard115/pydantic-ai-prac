from pydantic_ai import Agent, RunContext
import streamlit as st
import asyncio
from pydantic import BaseModel, Field


class ForbiddenWordGameDeps(BaseModel):
    user_forbidden_word: str = Field(description="The forbidden word of the user")


if not st.session_state.get("game_player"):
    game_player = Agent(
        "openai:gpt-4o-mini",
    )

    # add a system prompt to the game_player
    @game_player.system_prompt
    def system_prompt(ctx: RunContext[ForbiddenWordGameDeps]):
        return f"""
        Your task is to do everything you can to guide user to say this word: "{ctx.deps.user_forbidden_word}".
        when user says the word, you say "You lose!" and the game is over.
        """

    st.session_state["game_player"] = game_player
    st.session_state["history"] = []


game_player = st.session_state["game_player"]
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

    deps = ForbiddenWordGameDeps(user_forbidden_word="cat")

    # Run async code in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response = loop.run_until_complete(
        game_player.run(prompt, message_history=history, deps=deps)
    )
    loop.close()

    # Display assistant response in chat message container
    st.chat_message("assistant").markdown(response.data)
    # Add assistant response to chat history
    st.session_state.history = response.all_messages()

st.write(st.session_state.history)
