from agents import Runner
from my_agent import Gemini_agent
from agents import enable_verbose_stdout_logging

enable_verbose_stdout_logging()

prompt = input("Enter your prompt: ")
result = Runner.run_sync(Gemini_agent,prompt)
print(result.final_output)