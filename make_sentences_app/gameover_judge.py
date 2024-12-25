from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field
from typing import Union

class JudgeDeps(BaseModel):
    target_word: str


class JudgeResult(BaseModel):
    is_contain: bool = Field(description="Whether the input sentence contains the word")
    related_part: Union[str, None] = Field(description="The related part in the input sentence")

gameover_judge = Agent(
    "openai:gpt-4o-mini",
    deps_type=JudgeDeps,
    result_type=JudgeResult,
)


@gameover_judge.system_prompt
def system_prompt(ctx: RunContext[JudgeDeps]):
    return f"""
    You are a highly intelligent language model. Your task is to determine if the input sentence contains "{ctx.deps.target_word}" or its direct word forms. Only consider:
    1. The exact word match
    2. Common conjugations of the word (for verbs)
    3. Direct plural/singular forms (for nouns)
    
    Respond with Yes only if the exact word or its direct grammatical variations are present, otherwise respond with No.
    """

if __name__ == "__main__":
    # Test case for noun with compound word
    deps_compound = JudgeDeps(target_word="view")
    result_compound = gameover_judge.run_sync("can toy give me seven views of the project that was excellent.", deps=deps_compound)
    print("Compound Word Test Result:", result_compound.data)

