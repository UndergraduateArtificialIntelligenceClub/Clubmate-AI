from mcp.server.fastmcp import FastMCP
from typing import Literal

print("Starting MCP server...")
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
    """Find the periodic table symbol for a given element name
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
    """Generate a greeting prompt with a specific tone
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

def main():
    mcp.run()


if __name__ == "__main__":
    main()