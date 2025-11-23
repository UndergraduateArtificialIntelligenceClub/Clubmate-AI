"""
Hello Word! file for mcp.
To start the mcp server you would have to edit your claude config file.
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional
import json


# Initializing the mcp-server
mcp = FastMCP("hello_mcp")


class greetingInput(BaseModel):
    "just wanted to mention pattern is a param which used regex operations"

    name: str = Field(..., description="The person's name", min_length=1, max_length=50)

    greetingStyle: Optional[str] = Field(
        default="friendly",
        description="Style of greeting: 'formal', 'friendly', or 'casual'",
        pattern="^(formal|friendly|casual)$",
    )


@mcp.tool(
    name="greet_person",
    annotations={
        "title": "Greet Someone",
        "readOnlyHint": True,
        "idempotentHint": True,
    },
)
async def greet_person(params: greetingInput) -> str:
    """
        Generate a personalized greeting based on the person's name and preference
    This tool creates friendly, formal or casual greeting for any person.

        Args:
        params(greetingInput):Contains:
            - name: Person's name (required, 1-50 chars)
            - greeting_style: Type of greeting (optional, default:"friendly")

        Returns:
            str: JSON response with the greeting message
    """

    greetings = {
        "formal": f"Greetings, {params.name}. I hope you're having a productive weekend.",
        "friendly": f"Hey {params.name}! Nice to meet you!",
        "casual": f"Yo {params.name}, what's good?",
    }

    greeting = greetings.get(params.greetingStyle, greetings["friendly"])

    response = {
        "greeting": greeting,
        "Style": params.greetingStyle,
        "name": params.name,
    }

    return json.dumps(response, indent=2)


if __name__ == "__main__":
    mcp.run()
