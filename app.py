from pydantic_ai import Agent
from pydantic import BaseModel, Field
from typing import Union

class LocationMapResponse(BaseModel):
    location: Union[str, None] = Field(description="The location you need to create a map for(also provide the country name)")
    response: str = Field(description="what you will say to the user")

agent = Agent(
    "openai:gpt-4o-mini",
    result_type=LocationMapResponse,
    system_prompt=(
        "You are a friendly location assistant helping users find and visualize places on maps by using the create_location_map() tool."
        "Primary Functions:"
        " • Provide brief location info with nearby attractions"
        " • Give concise location details"
        " • Never ask permission - just show the map"
    ),
)


def create_location_map(location: str) -> str:
    """Create a map of the location."""
    print(f"create_location_map: {location}")
    return "finished creating map for " + location

@agent.result_validator
def validate_result(result: LocationMapResponse):
    if result.location is not None:
        create_location_map(result.location)
    return result.response
    
result = agent.run_sync("Let's play a game to guess the city,do you know which city is the southernmost in Taiwan?(not Kaohsiung,)")
print(result.data)
