import os
import sys
import httpx
import sqlite3
import json
from datetime import datetime
from typing import Optional

# Add explicit import and initialization
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: mcp package not found. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

# WeatherAPI.com configuration
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_BASE_URL = "http://api.weatherapi.com/v1"

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), "weather_calls.db")

def init_database():
    """Initialize SQLite database for logging API calls"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            query_location TEXT NOT NULL,
            parameters TEXT,
            response_status INTEGER,
            response_data TEXT,
            error_message TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def log_api_call(
    tool_name: str,
    endpoint: str,
    location: str,
    params: dict,
    status: int,
    response_data: Optional[str] = None,
    error_msg: Optional[str] = None
):
    """Log API call to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO api_calls 
        (timestamp, tool_name, endpoint, query_location, parameters, 
         response_status, response_data, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        tool_name,
        endpoint,
        location,
        json.dumps(params),
        status,
        response_data,
        error_msg
    ))
    
    conn.commit()
    conn.close()

async def make_weather_request(endpoint: str, params: dict) -> Optional[dict]:
    """Make async request to WeatherAPI.com"""
    params['key'] = WEATHER_API_KEY
    url = f"{WEATHER_BASE_URL}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"error": str(e), "status_code": getattr(e.response, 'status_code', 500)}
        except Exception as e:
            return {"error": str(e)}

async def handle_get_current_weather(location: str, aqi: str = "yes") -> str:
    """Get current weather data"""
    params = {"q": location, "aqi": aqi}
    tool_name = "get_current_weather"
    
    try:
        data = await make_weather_request("current.json", params)
        
        if "error" in data:
            log_api_call(tool_name, "current.json", location, params, 
                        data.get("status_code", 500), error_msg=data["error"])
            return f"Error fetching weather: {data['error']}"
        
        log_api_call(tool_name, "current.json", location, params, 200, 
                    json.dumps(data))
        
        loc = data['location']
        current = data['current']
        
        result = f"""
🌍 Current Weather for {loc['name']}, {loc['region']}, {loc['country']}
📅 Local Time: {loc['localtime']}

🌡️ Temperature: {current['temp_c']}°C ({current['temp_f']}°F)
🌤️ Conditions: {current['condition']['text']}
🤚 Feels Like: {current['feelslike_c']}°C ({current['feelslike_f']}°F)
💨 Wind: {current['wind_kph']} km/h ({current['wind_mph']} mph) {current['wind_dir']}
💧 Humidity: {current['humidity']}%
☁️ Cloud Cover: {current['cloud']}%
👁️ Visibility: {current['vis_km']} km
🌡️ Pressure: {current['pressure_mb']} mb
☂️ Precipitation: {current['precip_mm']} mm
☀️ UV Index: {current['uv']}
        """
        
        if 'air_quality' in current:
            aqi_data = current['air_quality']
            result += f"""
💨 Air Quality:
   • US EPA Index: {aqi_data.get('us-epa-index', 'N/A')}
   • UK DEFRA Index: {aqi_data.get('gb-defra-index', 'N/A')}
   • PM2.5: {aqi_data.get('pm2_5', 'N/A')} μg/m³
   • PM10: {aqi_data.get('pm10', 'N/A')} μg/m³
        """
        
        return result.strip()
        
    except Exception as e:
        log_api_call(tool_name, "current.json", location, params, 500, 
                    error_msg=str(e))
        return f"Error: {str(e)}"

async def handle_get_forecast(location: str, days: int = 3) -> str:
    """Get weather forecast"""
    if days < 1 or days > 14:
        return "Error: days parameter must be between 1 and 14"
    
    params = {"q": location, "days": days, "aqi": "yes", "alerts": "yes"}
    tool_name = "get_forecast"
    
    try:
        data = await make_weather_request("forecast.json", params)
        
        if "error" in data:
            log_api_call(tool_name, "forecast.json", location, params,
                        data.get("status_code", 500), error_msg=data["error"])
            return f"Error fetching forecast: {data['error']}"
        
        log_api_call(tool_name, "forecast.json", location, params, 200,
                    json.dumps(data))
        
        loc = data['location']
        result = f"🌤️ {days}-Day Forecast for {loc['name']}, {loc['region']}, {loc['country']}\n\n"
        
        for day in data['forecast']['forecastday']:
            day_data = day['day']
            result += f"""
📅 {day['date']} - {day_data['condition']['text']}
   🌡️ High: {day_data['maxtemp_c']}°C / Low: {day_data['mintemp_c']}°C
   ☂️ Chance of Rain: {day_data.get('daily_chance_of_rain', 0)}%
   💧 Total Precip: {day_data['totalprecip_mm']} mm
   💨 Max Wind: {day_data['maxwind_kph']} km/h
   ☀️ UV Index: {day_data['uv']}
"""
        
        return result.strip()
        
    except Exception as e:
        log_api_call(tool_name, "forecast.json", location, params, 500,
                    error_msg=str(e))
        return f"Error: {str(e)}"

async def handle_get_history(location: str, date: str) -> str:
    """Get historical weather"""
    params = {"q": location, "dt": date}
    tool_name = "get_history"
    
    try:
        data = await make_weather_request("history.json", params)
        
        if "error" in data:
            log_api_call(tool_name, "history.json", location, params,
                        data.get("status_code", 500), error_msg=data["error"])
            return f"Error fetching history: {data['error']}"
        
        log_api_call(tool_name, "history.json", location, params, 200,
                    json.dumps(data))
        
        loc = data['location']
        forecast_day = data['forecast']['forecastday'][0]
        day_data = forecast_day['day']
        
        result = f"""
📜 Historical Weather for {loc['name']}, {loc['region']}, {loc['country']}
📅 Date: {forecast_day['date']}

🌡️ Temperature Range: {day_data['mintemp_c']}°C to {day_data['maxtemp_c']}°C
🌤️ Conditions: {day_data['condition']['text']}
💧 Total Precipitation: {day_data['totalprecip_mm']} mm
💨 Max Wind: {day_data['maxwind_kph']} km/h
        """
        
        return result.strip()
        
    except Exception as e:
        log_api_call(tool_name, "history.json", location, params, 500,
                    error_msg=str(e))
        return f"Error: {str(e)}"

async def main():
    """Main server entry point"""
    # Initialize database
    init_database()
    
    # Create MCP server
    server = Server("weather-mcp")
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="get_current_weather",
                description="Get current weather data for any location including air quality",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name, ZIP code, or coordinates (e.g., 'Edmonton', '53.5461,-113.4938')"
                        },
                        "aqi": {
                            "type": "string",
                            "description": "Include air quality data ('yes' or 'no')",
                            "enum": ["yes", "no"],
                            "default": "yes"
                        }
                    },
                    "required": ["location"]
                }
            ),
            Tool(
                name="get_forecast",
                description="Get weather forecast up to 14 days ahead",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name, ZIP code, or coordinates"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of forecast days (1-14)",
                            "minimum": 1,
                            "maximum": 14,
                            "default": 3
                        }
                    },
                    "required": ["location"]
                }
            ),
            Tool(
                name="get_history",
                description="Get historical weather data for a specific date",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name, ZIP code, or coordinates"
                        },
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format (after 2010-01-01)",
                            "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                        }
                    },
                    "required": ["location", "date"]
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name == "get_current_weather":
            result = await handle_get_current_weather(
                arguments["location"],
                arguments.get("aqi", "yes")
            )
        elif name == "get_forecast":
            result = await handle_get_forecast(
                arguments["location"],
                arguments.get("days", 3)
            )
        elif name == "get_history":
            result = await handle_get_history(
                arguments["location"],
                arguments["date"]
            )
        else:
            result = f"Unknown tool: {name}"
        
        return [TextContent(type="text", text=result)]
    
    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
