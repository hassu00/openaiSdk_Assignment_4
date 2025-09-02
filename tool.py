import requests
from agents import function_tool

API_KEY = "432e8974576c4ed98fb102441250209"
BASE_URL = "http://api.weatherapi.com/v1/current.json"

@function_tool
def get_weather(city):
        url = f"{BASE_URL}?key={API_KEY}&q={city}"
        response = requests.get(url)
        return response.json()

@function_tool
def add_numbers(a, b):
    return a + b