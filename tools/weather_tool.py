# tools/weather_tool.py

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_weather(location):
    """
    Fetches the current weather for a given location using OpenWeatherMap API.

    Args:
        location (str): The location to fetch weather for.

    Returns:
        dict or str: Weather data as a dictionary or an error message.
    """
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not api_key:
        return "OpenWeatherMap API key not found. Please set it in the .env file."

    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': location,
        'appid': api_key,
        'units': 'metric'
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        weather_info = {
            'Location': f"{data['name']}, {data['sys']['country']}",
            'Temperature (°C)': data['main']['temp'],
            'Weather': data['weather'][0]['description'].title(),
            'Humidity (%)': data['main']['humidity'],
            'Wind Speed (m/s)': data['wind']['speed']
        }
        return str(weather_info)
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err}"
    except Exception as err:
        return f"An error occurred: {err}"
