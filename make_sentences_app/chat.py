from pydantic_ai import Agent, RunContext
import streamlit as st
import asyncio
from pydantic import BaseModel, Field


class ForbiddenWordGameDeps(BaseModel):
    user_forbidden_word: str = Field(description="The forbidden word of the user")


class ForbiddenWordGame:
    def __init__(self):
        self.initialize_session_state()
        self.game_player = st.session_state["game_player"]
        self.history = st.session_state["history"]

    def initialize_session_state(self):
        if not st.session_state.get("game_player"):
            game_player = self._create_game_player()
            st.session_state["game_player"] = game_player
            st.session_state["history"] = []

    def _create_game_player(self):
        game_player = Agent("openai:gpt-4o-mini")

        @game_player.system_prompt
        def system_prompt(ctx: RunContext[ForbiddenWordGameDeps]):
            return f"""
            Your task is to do everything you can to guide user to say this word: "{ctx.deps.user_forbidden_word}".
            when user says the word, you say "You lose!" and the game is over.
            """

        return game_player

    def display_chat_history(self):
        for message in self.history:
            if message.role == "user":
                st.chat_message("user").markdown(message.content)
            elif message.role == "model-text-response":
                st.chat_message("assistant").markdown(message.content)

    async def process_user_input(self, prompt: str):
        deps = ForbiddenWordGameDeps(user_forbidden_word="cat")
        response = await self.game_player.run(
            prompt, message_history=self.history, deps=deps
        )
        return response

    def update_chat(self, prompt: str):
        st.chat_message("user").markdown(prompt)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(self.process_user_input(prompt))
        loop.close()

        st.chat_message("assistant").markdown(response.data)
        st.session_state.history = response.all_messages()

    def run(self):
        self.display_chat_history()

        if prompt := st.chat_input("What is up?"):
            self.update_chat(prompt)
            st.sidebar.write(st.session_state.history)


def main():
    game = ForbiddenWordGame()
    game.run()


if __name__ == "__main__":
    main()
