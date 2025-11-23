"""
Simple example MCP server using FastMCP
Exposes basic tools for demonstration
"""

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    # Fallback if using a different package structure
    from fastmcp import FastMCP

import random
import json

# Create the MCP server
mcp = FastMCP(name="Example Server")


@mcp.tool()
def roll_dice(n_dice: int = 1, sides: int = 6) -> list[int]:
    """Roll n dice with specified number of sides"""
    return [random.randint(1, sides) for _ in range(n_dice)]


@mcp.tool()
def get_weather(city: str) -> dict:
    """Get weather information (simulated)"""
    cities = {
        "New York": {"temp": 72, "condition": "Sunny"},
        "London": {"temp": 59, "condition": "Rainy"},
        "Tokyo": {"temp": 68, "condition": "Cloudy"},
        "Sydney": {"temp": 77, "condition": "Sunny"},
    }
    return cities.get(city, {"temp": "Unknown", "condition": "No data"})


@mcp.tool()
def calculate(expression: str) -> float:
    """Evaluate a mathematical expression"""
    try:
        result = eval(expression)
        return float(result)
    except Exception as e:
        return float("nan")


@mcp.tool()
def json_format(data: dict) -> str:
    """Format JSON data nicely"""
    return json.dumps(data, indent=2)


@mcp.tool()
def reverse_text(text: str) -> str:
    """Reverse a string"""
    return text[::-1]


@mcp.tool()
def count_words(text: str) -> dict:
    """Count words in text"""
    words = text.split()
    unique_words = len(set(words))
    return {
        "total_words": len(words),
        "unique_words": unique_words,
        "characters": len(text),
        "avg_word_length": len(text) / len(words) if words else 0,
    }


if __name__ == "__main__":
    mcp.run()
