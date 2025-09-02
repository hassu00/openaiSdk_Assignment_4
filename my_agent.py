from agents import Agent, function_tool
from agent_config import model
from tool import get_weather

# def getWeather(city):
#     return f"The weather in {city} is sunny with a high of 25°C."

Gemini_agent = Agent(
    name="Gemini",
    instructions="A Gemini agent",
    model=model,
    tools=[get_weather]
)
