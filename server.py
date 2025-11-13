from mcp.server.fastmcp import FastMCP
from typing import Literal, Optional, Dict, Any
import os
from dotenv import load_dotenv
import requests

load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

mcp = FastMCP("mcp-server")

# Common elements from the periodic table
PERIODIC_TABLE = {
      "hydrogen": "H",
      "helium": "He",
      "lithium": "Li",
      "carbon": "C",
      "nitrogen": "N",
      "oxygen": "O",
      "fluorine": "F",
      "neon": "Ne",
      "sodium": "Na",
      "magnesium": "Mg",
      "aluminum": "Al",
      "silicon": "Si",
      "phosphorus": "P",
      "sulfur": "S",
      "chlorine": "Cl",
      "potassium": "K",
      "calcium": "Ca",
      "iron": "Fe",
      "copper": "Cu",
      "zinc": "Zn",
      "silver": "Ag",
      "gold": "Au",
  }



@mcp.tool()
def count_characters(text: str) -> str:
    """
    Count the number of characters in the input text
        Args:
          text: The text to count characters in

        Returns:
          A message with the character count
    """
    char_count = len(text)
    return f"The text contains {char_count} characters."


@mcp.tool()
def find_symbol(element: str) -> str:
    """
    Find the periodic table symbol for a given element name
    Args:
        element: The name of the chemical element (e.g., "hydrogen", "carbon")

    Returns:
        The chemical symbol or an error message if not found
    """
    element_lower = element.lower().strip()

    if element_lower in PERIODIC_TABLE:
        symbol = PERIODIC_TABLE[element_lower]
        return f"The symbol for {element.capitalize()} is: {symbol}"
    else:
        available = ", ".join(sorted(PERIODIC_TABLE.keys()))
        return f"Element '{element}' not found. Available elements: {available}"


@mcp.prompt()
def greet_user(tone: Literal["friendly", "professional", "casual"] = "friendly") -> str:
    """
    Generate a greeting prompt with a specific tone
    Args:
        tone: The tone of the greeting (friendly, professional, or casual)

    Returns:
        A prompt template for greeting the user
    """
    prompts = {
        "friendly": "You are a warm and welcoming assistant. Greet the user enthusiastically and make them feel at home. Use positive language and show genuine interest in helping them.",
        "professional": "You are a professional assistant. Greet the user courteously and maintain a business-like demeanor. Be polite, efficient, and respectful.",
        "casual": "You are a laid-back assistant. Greet the user casually like you're talking to a friend. Keep it relaxed and conversational."
    }

    return prompts.get(tone, prompts["friendly"])

@mcp.tool()
def geocode_city(city_name: str, country_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Decode city name to latitude and longitude coordinates using OpenWeather Geocoding API
    Because we need Lat/Lon for weather queries. The API has a built in decoder but is deprecated.
    So I figured why not just add this as well as a seperate tool.

    Returns:
        Dictionary with 'lat', 'lon', 'name', 'country' or None if not found
    """
    if not OPENWEATHER_API_KEY:
        raise ValueError("No Api Key")

    # Build query string
    query = f"{city_name}"
    if country_code:
        query += f",{country_code}"

    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": query,
        "appid": OPENWEATHER_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            location = data[0]
            return {
                "lat": location["lat"],
                "lon": location["lon"],
                "name": location["name"],
                "country": location["country"]
            }
        return None
    except requests.exceptions.RequestException as e:
        raise Exception(f"Geocoding API error: {str(e)}")

@mcp.tool()
def get_current_weather(city_name: str, country_code: Optional[str] = None, units: str = "metric") -> str:
    """
    Get current weather data for a specified city
    Args:
        city_name (str): Name of the city
        country_code (Optional[str]): Optional country code to narrow down the search
        units (str): Units for temperature ('metric', 'imperial', or 'standard')    

    Returns:
        str: Formatted string with current weather information just for testing
    """
    if not OPENWEATHER_API_KEY:
        return "No key"
    
    location = geocode_city(city_name, country_code)
    if not location:
        return f"Error: Could not find location for '{city_name}'"

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": location["lat"],
        "lon": location["lon"],
        "appid": OPENWEATHER_API_KEY,
        "units": units
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Since we're using metric, just use ignore imperial metrics and just use celsius and m/s by default 
        weather_info = f"""
            Current Weather for {location['name']}, {location['country']}:
            Temperature: {data['main']['temp']} C
            Feels Like: {data['main']['feels_like']} C
            Condition: {data['weather'][0]['description'].title()}
            Humidity: {data['main']['humidity']}%
            Wind Speed: {data['wind']['speed']} m/s
            Pressure: {data['main']['pressure']} hPa
            Visibility: {data.get('visibility', 'N/A')} meters
            Coordinates: ({location['lat']}, {location['lon']})
            """
        
        return weather_info

    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: {str(e)}"
    
@mcp.tool()
def get_5_day_forecast(city_name: str, country_code: Optional[str] = None, units: str = "metric") -> str:
    """
    Get 5 day weather forecast for a specified city
    Args:
        city_name (str): Name of the city
        country_code (Optional[str]): Optional country code to narrow down the search
        units (str): Units for temperature ('metric', 'imperial', or 'standard')

    Returns:
        str: String with 5 day weather forecast
    """
    if not OPENWEATHER_API_KEY:
        return "No key"

    location = geocode_city(city_name, country_code)
    if not location:
        return f"Could not find location for '{city_name}'"

    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": location["lat"],
        "lon": location["lon"],
        "appid": OPENWEATHER_API_KEY,
        "units": units
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        info = []
        for entry in data['list']:
            date_txt = entry['dt_txt']
            temp = entry['main']['temp']
            description = entry['weather'][0]['description'].title()
            info.append(f"{date_txt}: {temp} C, {description}\n")

        return f"5 Day Weather Forecast for {location['name']}, {location['country']}:\n" + "".join(info)

    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: {str(e)}"

def main():
    mcp.run()


if __name__ == "__main__":
    main()