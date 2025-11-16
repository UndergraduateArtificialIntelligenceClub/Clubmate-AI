import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import json
import httpx
import asyncio
import google.generativeai as genai
from google.generativeai.types import Tool

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Store conversation history per user
user_conversations = {}

# Define the weather tool for Gemini
weather_tool = Tool(
    function_declarations=[
        {
            "name": "get_weather",
            "description": "Get current weather information for a specified location. Returns temperature, conditions, humidity, and wind speed.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "location": {
                        "type": "STRING",
                        "description": "City name or location (e.g., 'London', 'Paris', 'Tokyo')"
                    },
                    "temperature_unit": {
                        "type": "STRING",
                        "description": "Temperature unit: 'celsius' or 'fahrenheit'",
                        "enum": ["celsius", "fahrenheit"]
                    }
                },
                "required": ["location"]
            }
        }
    ]
)

def get_user_conversation(user_id):
    """Get or create conversation history for a user."""
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    return user_conversations[user_id]

async def call_weather_api(location: str, temperature_unit: str = "celsius") -> dict:
    """Call the weather API to get weather data."""
    try:
        # Get coordinates for the location
        geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        geocoding_params = {
            "name": location,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(geocoding_url, params=geocoding_params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("results"):
                return {"error": f"Location '{location}' not found"}
            
            result = data["results"][0]
            latitude = result["latitude"]
            longitude = result["longitude"]
            location_name = result.get("name", location)
            country = result.get("country", "")
        
        # Get weather data
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "temperature_unit": temperature_unit.lower()
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(weather_url, params=weather_params)
            response.raise_for_status()
            weather_data = response.json()
        
        current = weather_data.get("current", {})
        
        weather_descriptions = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Depositing rime fog", 51: "Light drizzle",
            53: "Moderate drizzle", 55: "Dense drizzle", 61: "Slight rain",
            63: "Moderate rain", 65: "Heavy rain", 71: "Slight snow",
            73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
            80: "Slight rain showers", 81: "Moderate rain showers",
            82: "Violent rain showers", 85: "Slight snow showers",
            86: "Heavy snow showers", 95: "Thunderstorm",
            96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
        }
        
        weather_code = current.get("weather_code", 0)
        weather_description = weather_descriptions.get(weather_code, "Unknown")
        
        return {
            "location": f"{location_name}, {country}",
            "temperature": current.get("temperature_2m"),
            "temperature_unit": temperature_unit,
            "conditions": weather_description,
            "humidity": f"{current.get('relative_humidity_2m')}%",
            "wind_speed": f"{current.get('wind_speed_10m')} km/h",
            "success": True
        }
    
    except Exception as e:
        return {"error": str(e), "success": False}

async def get_gemini_response_with_tools(user_message: str, user_id: int) -> str:
    """Get response from Gemini with tool use."""
    try:
        conversation = get_user_conversation(user_id)
        
        # Format conversation for Gemini
        gemini_messages = []
        for msg in conversation:
            if msg["role"] == "user":
                gemini_messages.append({
                    "role": "user",
                    "parts": [{"text": msg["content"]}]
                })
            else:
                gemini_messages.append({
                    "role": "model",
                    "parts": [{"text": msg["content"]}]
                })
        
        # Add current user message
        gemini_messages.append({
            "role": "user",
            "parts": [{"text": user_message}]
        })
        
        # Add to conversation history
        conversation.append({
            "role": "user",
            "content": user_message
        })
        
        # Create model with tools
        model = genai.GenerativeModel(
            "gemini-2.0-flash",
            tools=[weather_tool]
        )
        
        # Generate response with tools
        response = model.generate_content(
            gemini_messages
        )
        
        # Handle tool calls in a loop
        while response.candidates[0].content.parts:
            last_part = response.candidates[0].content.parts[-1]
            
            # Check if it's a function call
            if hasattr(last_part, 'function_call'):
                func_call = last_part.function_call
                
                if func_call.name == "get_weather":
                    # Extract parameters
                    location = func_call.args.get("location")
                    temp_unit = func_call.args.get("temperature_unit", "celsius")
                    
                    # Call weather API
                    weather_data = await call_weather_api(location, temp_unit)
                    
                    if weather_data.get("success"):
                        tool_result = {
                            "location": weather_data["location"],
                            "temperature": f"{weather_data['temperature']}°{weather_data['temperature_unit'][0].upper()}",
                            "conditions": weather_data["conditions"],
                            "humidity": weather_data["humidity"],
                            "wind_speed": weather_data["wind_speed"]
                        }
                    else:
                        tool_result = {"error": weather_data.get("error", "Unknown error")}
                    
                    # Add tool result to conversation
                    gemini_messages.append({
                        "role": "user",
                        "parts": [
                            {
                                "function_response": {
                                    "name": "get_weather",
                                    "response": tool_result
                                }
                            }
                        ]
                    })
                    
                    # Get next response
                    response = model.generate_content(
                        gemini_messages
                    )
                else:
                    break
            else:
                break
        
        # Extract final text response
        final_response = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                final_response += part.text
        
        if final_response:
            # Add to conversation history
            conversation.append({
                "role": "assistant",
                "content": final_response
            })
            
            # Keep conversation manageable (last 20 messages)
            if len(conversation) > 20:
                conversation.pop(0)
                conversation.pop(0)
            
            return final_response
        else:
            return "I encountered an issue processing your request."
    
    except Exception as e:
        return f"❌ Error with Gemini API: {str(e)}"

@bot.event
async def on_ready():
    print(f"✓ Gemini AI Bot with MCP is online as {bot.user}")

@bot.event
async def on_message(message):
    # Don't respond to ourselves
    if message.author == bot.user:
        return
    
    # Check if bot is mentioned
    if bot.user.mentioned_in(message):
        # Remove bot mention from message
        user_message = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        
        if not user_message:
            await message.reply("Hi! What would you like to know? 👋")
            return
        
        # Show typing indicator
        async with message.channel.typing():
            # Get Gemini response with tools
            response = await get_gemini_response_with_tools(user_message, message.author.id)
            
            # Discord has 2000 character limit
            if len(response) > 2000:
                chunks = [response[i:i+1950] for i in range(0, len(response), 1950)]
                for chunk in chunks:
                    await message.reply(chunk)
            else:
                await message.reply(response)
    
    await bot.process_commands(message)

@bot.command(name="ask")
async def ask(ctx, *, question: str):
    """Ask Gemini AI a question with access to tools."""
    
    async with ctx.typing():
        response = await get_gemini_response_with_tools(question, ctx.author.id)
        
        if len(response) > 2000:
            chunks = [response[i:i+1950] for i in range(0, len(response), 1950)]
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(response)

@bot.command(name="reset")
async def reset(ctx):
    """Clear your conversation history with Gemini."""
    user_id = ctx.author.id
    if user_id in user_conversations:
        del user_conversations[user_id]
    await ctx.send(f"✓ {ctx.author.name}, your conversation history has been cleared!")

@bot.command(name="info")
async def info_command(ctx):
    """Show available commands."""
    embed = discord.Embed(
        title="🤖 Gemini AI Bot with MCP",
        description="An AI bot powered by Google Gemini with access to real-time data!",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="Chat Commands",
        value="**@bot message** - Chat with Gemini\n**!ask question** - Ask Gemini anything",
        inline=False
    )
    
    embed.add_field(
        name="Special Abilities",
        value="**Weather** - Ask \"What's the weather in [city]?\"",
        inline=False
    )
    
    embed.add_field(
        name="Utility",
        value="**!reset** - Clear conversation history\n**!info** - Show this message",
        inline=False
    )
    
    embed.add_field(
        name="Examples",
        value="• `@bot What's the weather in London?`\n• `!ask Compare weather in Paris and Tokyo`\n• `@bot Tell me about Rome and its weather`",
        inline=False
    )
    
    await ctx.send(embed=embed)

bot.run(DISCORD_TOKEN)
