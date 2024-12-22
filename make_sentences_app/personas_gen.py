from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field
from typing import Union
from make_sentences_app.jobs_getter import get_random_job


class PersonaGeneratorResponse(BaseModel):
    persona_1: str = Field(description="The first persona")
    persona_2: str = Field(description="The second persona")


persona_generator = Agent(
    "openai:gpt-4o-mini",
    result_type=PersonaGeneratorResponse,
    system_prompt=(
        "You are a persona generator, you will be given two job information"
        "You have to generate two persona based on the two job information"
        "The persona should contain the strengths, weaknesses, and personality traits."
        "The persona description within 50 words"
        "the two personas should better be in opposition regarding their interests"
    ),
)

job_1 = get_random_job()
job_2 = get_random_job()

result0 = persona_generator.run_sync(f"{job_1}\n{job_2}")
print(result0.data.persona_1)
print(result0.data.persona_2)
