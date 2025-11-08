"""
OpenWeatherAPI Tools for MCP Server
Provides weather data fetching capabilities including current weather and forecasts
"""

from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv
import requests
load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

def geocode_city(city_name: str, country_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Decode city name to latitude and longitude coordinates using OpenWeather Geocoding API
    Because we need Lat/Lon for weather queries. The API has a built in decoder but is deprecated.

    Returns:
        Dictionary with 'lat', 'lon', 'name', 'country' or None if not found
    """
    if not OPENWEATHER_API_KEY:
        raise ValueError("OPENWEATHER_API_KEY environment variable is not set")

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


def get_current_weather(
    city_name: str,
    country_code: Optional[str] = None,
    units: str = "metric"
) -> str:
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
        return "no key"
    
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

        temp_unit = "C" if units == "metric" else "F" if units == "imperial" else "K"
        speed_unit = "m/s" if units == "metric" else "mph" if units == "imperial" else "m/s"

        weather_info = f"""Current Weather for {location['name']}, {location['country']}:
            Temperature: {data['main']['temp']}{temp_unit}
            Feels Like: {data['main']['feels_like']}{temp_unit}
            Condition: {data['weather'][0]['description'].title()}
            Humidity: {data['main']['humidity']}%
            Wind Speed: {data['wind']['speed']} {speed_unit}
            Pressure: {data['main']['pressure']} hPa
            Visibility: {data.get('visibility', 'N/A')} meters
            Coordinates: ({location['lat']}, {location['lon']})"""

        return weather_info

    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: {str(e)}"



if __name__ == "__main__":
    location = geocode_city("London", "GB")
    print(f"Location: {location}\n")

    weather = get_current_weather("London", "GB")
    print(weather)
