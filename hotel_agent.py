from agents import Agent,Runner
from agent_config import model


def dynamic_instructions(city: str, date: str) -> str:
    return f"""
    you are a hotel booking and information retrieval agent
    your task is to provide information about hotels.
    provide the list of hotels available in {city} on {date}
    hotel available on {date} in {city} are following
    - PC Hotel, 1 Night stay rent is 15000, Breakfast included, free parking
    - Marriott, 1 Night stay rent is 13000, Breakfast included, free parking
    - Movenpick, 1 Night stay rent is 14000, Breakfast included, free wifi
    """

hotel_agent = Agent(
    name="HotelAgent",
    instructions=dynamic_instructions,
    model=model,
)

prompt = input("Enter your prompt: ")
result = Runner.run_sync(hotel_agent,prompt)
print(result.final_output)