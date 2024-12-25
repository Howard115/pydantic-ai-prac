from pydantic_ai import Agent, RunContext
import streamlit as st
import asyncio
from pydantic import BaseModel, Field
from jobs_getter import get_random_job
from personas_gen import persona_generator
from gameover_judge import gameover_judge, JudgeDeps


class GamePlayerDeps(BaseModel):
    user_forbidden_word: str = Field(description="The forbidden word of the user")
    your_forbidden_words: list[str] = Field(
        description="The list of words you should avoid in your response"
    )
    assistant_persona: str = Field(description="The persona of the assistant")
    user_persona: str = Field(description="The persona of the user")
    debate_topic: str = Field(description="The topic of the debate")
    assistant_position: str = Field(description="The position of the assistant")


class WordsDetectorResult(BaseModel):
    possible_words: list[str] = Field(
        description="The list of words ranked from high to low in terms of probability"
    )


class ForbiddenWordGame:
    def __init__(self):
        self.initialize_session_state()
        self.game_player = st.session_state["game_player"]
        self.words_detector = st.session_state["words_detector"]
        self.history = st.session_state["history"]
        self.detected_words = st.session_state["detected_words"]
        self.user_forbidden_word = st.session_state[
            "persona_related_stuff"
        ].most_common_word_1
        self.assistant_forbidden_word = st.session_state[
            "persona_related_stuff"
        ].most_common_word_2

    def initialize_session_state(self):
        if not st.session_state.get("history"):
            st.session_state["history"] = []
        if not st.session_state.get("detected_words"):
            st.session_state["detected_words"] = []
        if not st.session_state.get("persona_related_stuff"):
            st.session_state["persona_related_stuff"] = (
                self._get_persona_related_stuff()
            )

        if not st.session_state.get("game_player"):
            st.session_state["game_player"] = self._create_game_player()
        if not st.session_state.get("words_detector"):
            st.session_state["words_detector"] = self._create_words_detector()

    def _get_persona_related_stuff(self):
        with st.sidebar:
            with st.spinner("Generating personas..."):
                job_1 = get_random_job()
                job_2 = get_random_job()

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    persona_generator.run(f"{job_1}\n{job_2}")
                )
                loop.close()

                return result.data

    def _create_game_player(self):
        game_player = Agent("openai:gpt-4o-mini")

        @game_player.system_prompt
        def system_prompt(ctx: RunContext[GamePlayerDeps]):
            return f"""
            Your persona is: {ctx.deps.assistant_persona}
            User's persona is: {ctx.deps.user_persona}
            You are currently talking about the following topic with the user: {ctx.deps.debate_topic}
            Your position is: {ctx.deps.assistant_position}
            
            Your task is to guide user to say this word:{ctx.deps.user_forbidden_word}
            while responding to the user's input but don't mention the words in the your_forbidden_words list in your response.
            You can use `check_your_forbidden_words()` to see what words you should avoid in your response. 
            """

        @game_player.tool
        def check_your_forbidden_words(ctx: RunContext[GamePlayerDeps]):
            return f"your_forbidden_words:{ctx.deps.your_forbidden_words}"

        return game_player

    def _create_words_detector(self):
        words_detector = Agent(
            "openai:gpt-4o-mini",
            result_type=WordsDetectorResult,
        )

        @words_detector.system_prompt
        def system_prompt():
            return """
            Please analyze the input sentence and identify the words that the user is most likely referring to or the word that the user guides you to talk about.
            """

        return words_detector

    def display_chat_history(self):
        for message in self.history:
            if message.role == "user":
                st.chat_message("user").markdown(message.content)
            elif message.role == "model-text-response":
                st.chat_message("assistant").markdown(message.content)

    async def is_gameover(self, new_messages):
        for message in new_messages:
            if message.role == "user":
                deps = JudgeDeps(target_word=self.user_forbidden_word)
                result = await gameover_judge.run(message.content, deps=deps)
                if result.data.is_contain:
                    st.info(
                        f"Game Over - You lose! You said the forbidden word: {self.user_forbidden_word}",
                        icon="ℹ️",
                    )
                    return True
            if message.role == "model-text-response":
                deps = JudgeDeps(target_word=self.assistant_forbidden_word)
                result = await gameover_judge.run(message.content, deps=deps)
                if result.data.is_contain:
                    st.info(
                        f"Game Over - Assistant loses! Assistant said a forbidden word: {self.assistant_forbidden_word}",
                        icon="ℹ️",
                    )
                    return True
        return False

    async def process_user_input(self, prompt: str):
        result = await self.words_detector.run(prompt)

        deps = GamePlayerDeps(
            user_forbidden_word=self.user_forbidden_word,
            your_forbidden_words=[result.data.possible_words[0]],
            assistant_persona=st.session_state.persona_related_stuff.persona_2,
            user_persona=st.session_state.persona_related_stuff.persona_1,
            debate_topic=st.session_state.persona_related_stuff.debate_topic,
            assistant_position=st.session_state.persona_related_stuff.debate_position_2,
        )
        response = await self.game_player.run(
            prompt,
            message_history=self.history,
            deps=deps,
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

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.is_gameover(response.new_messages()))
        loop.close()

    def run(self):
        self.display_chat_history()

        if prompt := st.chat_input("What is up?"):
            self.update_chat(prompt)
            st.sidebar.write(st.session_state.history)
        st.sidebar.write(st.session_state.persona_related_stuff)


def main():
    game = ForbiddenWordGame()
    game.run()


if __name__ == "__main__":
    main()
