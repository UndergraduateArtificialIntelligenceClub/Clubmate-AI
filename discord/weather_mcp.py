import json
import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional

mcp = FastMCP("weather_mcp")

class GetWeatherInput(BaseModel):
    """Input for getting weather information."""
    location: str = Field(
        ...,
        description="City name or location (e.g., 'New York', 'London', 'Tokyo')",
        min_length=1,
        max_length=100
    )
    temperature_unit: Optional[str] = Field(
        default="celsius",
        description="Temperature unit: 'celsius' or 'fahrenheit'"
    )

async def get_coordinates(location: str) -> dict:
    """Get latitude and longitude for a location using Open-Meteo Geocoding API."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": location,
        "count": 1,
        "language": "en",
        "format": "json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("results"):
            raise ValueError(f"Location '{location}' not found")
        
        result = data["results"][0]
        return {
            "latitude": result["latitude"],
            "longitude": result["longitude"],
            "name": result.get("name", location),
            "country": result.get("country", "")
        }

@mcp.tool(
    name="get_weather",
    annotations={
        "title": "Get Weather Information",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_weather(params: GetWeatherInput) -> str:
    """Get current weather information for a specified location.
    
    This tool retrieves real-time weather data including temperature,
    weather conditions, wind speed, and humidity for any location worldwide.
    
    Args:
        params (GetWeatherInput): Contains:
            - location (str): City name or location to get weather for
            - temperature_unit (str): 'celsius' or 'fahrenheit'
    
    Returns:
        str: JSON-formatted weather information with temperature, conditions, and more
    """
    try:
        coords = await get_coordinates(params.location)
        
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": coords["latitude"],
            "longitude": coords["longitude"],
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "temperature_unit": params.temperature_unit.lower()
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(weather_url, params=weather_params)
            response.raise_for_status()
            weather_data = response.json()
        
        current = weather_data.get("current", {})
        
        weather_descriptions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        
        weather_code = current.get("weather_code", 0)
        weather_description = weather_descriptions.get(weather_code, "Unknown")
        
        result = {
            "location": f"{coords['name']}, {coords['country']}",
            "coordinates": {
                "latitude": coords["latitude"],
                "longitude": coords["longitude"]
            },
            "temperature": current.get("temperature_2m"),
            "temperature_unit": params.temperature_unit,
            "conditions": weather_description,
            "humidity": f"{current.get('relative_humidity_2m')}%",
            "wind_speed": f"{current.get('wind_speed_10m')} km/h"
        }
        
        return json.dumps(result, indent=2)
    
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except httpx.HTTPError as e:
        return json.dumps({"error": f"Weather API error: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}"})

if __name__ == "__main__":
    mcp.run()
