from agents import Runner
from my_agent import Gemini_agent

prompt = input("Enter your prompt: ")
result = Runner.run_sync(Gemini_agent,prompt)
print(result.final_output)