from decouple import config
from agents import AsyncOpenAI, OpenAIChatCompletionsModel

API_KEY = config("GEMINI_API_KEY")
BASE_URL = config("GEMINI_BASE_URL")
MODEL_NAME = config("GEMINI_MODEL_NAME")

gemini_client = AsyncOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

model = OpenAIChatCompletionsModel(
    model=MODEL_NAME,
    openai_client=gemini_client
)
