from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field
from typing import Union
from jobs_getter import get_random_job


class PersonaGeneratorResponse(BaseModel):
    persona_1: str = Field(description="The first persona description within 30 words.")
    persona_2: str = Field(description="The second persona description within 30 words.")
    most_common_word_1: str = Field(description="The most common word spoken by the first persona")
    most_common_word_2: str = Field(description="The most common word spoken by the second persona")
    debate_topic: str = Field(description="The debate topic description between the two personas")
    debate_position_1: str = Field(description="The position of the first persona in the debate")
    debate_position_2: str = Field(description="The position of the second persona in the debate")
persona_generator = Agent(
    "openai:gpt-4o-mini",
    result_type=PersonaGeneratorResponse,
    system_prompt=(
        """
        You are a creative persona description generator. Your primary task is to craft two compelling personas, each showcasing unique strengths and weaknesses derived from the provided job titles.
        
        Additionally, you should:
        - Identify and highlight the most frequently used word by each persona based on their descriptions.
        - Create an detailed debate topic(must be yes/no question) that both the two personas can discuss.
        
        NOTE:
        Ensure that both personas are centered around the same debate topic but represent contrasting viewpoints to foster an engaging discussion.
        """
    ),
)

job_1 = get_random_job()
job_2 = get_random_job()

result0 = persona_generator.run_sync(f"{job_1}\n{job_2}")
print(result0.data.persona_1+"\n")
print(result0.data.persona_2+"\n")
print(result0.data.most_common_word_1+"\n")
print(result0.data.most_common_word_2+"\n")
print(result0.data.debate_topic+"\n")
print(result0.data.debate_position_1+"\n")
print(result0.data.debate_position_2+"\n")
