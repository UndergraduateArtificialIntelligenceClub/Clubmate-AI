"""
MCP Server Demo - A minimal Model Context Protocol server
Demonstrates tools, resources, async handlers, and Pydantic validation.

Author: DevOps Engineer
Date: October 2025
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from mcp.server.fastmcp import FastMCP, Context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "demo-server",
    dependencies=["pydantic"]
)

logger.info("MCP Server initialized: demo-server")


# ============================================================================
# PYDANTIC MODELS FOR INPUT VALIDATION
# ============================================================================

class MessageInput(BaseModel):
    """
    Pydantic model for validating echo_message tool input.
    
    Attributes:
        message: The message to echo (2-500 characters)
        uppercase: Whether to convert message to uppercase
        repeat: Number of times to repeat (1-10)
    """
    message: str = Field(
        ..., 
        min_length=2, 
        max_length=500,
        description="Message to echo"
    )
    uppercase: bool = Field(
        default=False,
        description="Convert message to uppercase"
    )
    repeat: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Number of times to repeat the message"
    )
    
    @validator('message')
    def message_not_empty(cls, v):
        """Ensure message contains non-whitespace characters."""
        if not v.strip():
            raise ValueError('Message cannot be empty or whitespace only')
        return v.strip()


class CalculationInput(BaseModel):
    """
    Pydantic model for mathematical calculations.
    
    Attributes:
        operation: Mathematical operation to perform
        a: First operand
        b: Second operand
    """
    operation: str = Field(
        ...,
        pattern="^(add|subtract|multiply|divide)$",
        description="Mathematical operation: add, subtract, multiply, or divide"
    )
    a: float = Field(..., description="First operand")
    b: float = Field(..., description="Second operand")
    
    @validator('b')
    def check_division_by_zero(cls, v, values):
        """Prevent division by zero."""
        if 'operation' in values and values['operation'] == 'divide' and v == 0:
            raise ValueError('Cannot divide by zero')
        return v


# ============================================================================
# TOOL IMPLEMENTATIONS (Model-controlled functions)
# ============================================================================

@mcp.tool()
async def get_current_time(timezone: str = "UTC") -> str:
    """
    Get the current time in ISO format.
    
    This is an async tool that simulates a lightweight time service.
    In production, this could query a time API or database.
    
    Args:
        timezone: Timezone name (currently only supports UTC)
        
    Returns:
        Current timestamp in ISO 8601 format
        
    Example:
        >>> await get_current_time("UTC")
        "2025-10-29T19:16:45.123456"
    """
    logger.info(f"Tool called: get_current_time(timezone={timezone})")
    
    # Simulate async operation (e.g., API call or database query)
    await asyncio.sleep(0.01)
    
    current_time = datetime.utcnow().isoformat()
    
    logger.info(f"Returning time: {current_time}")
    return f"Current time ({timezone}): {current_time}"


@mcp.tool()
async def echo_message(
    message: str,
    uppercase: bool = False,
    repeat: int = 1
) -> str:
    """
    Echo a message with optional transformations.
    
    This tool demonstrates:
    - Input validation using type hints (FastMCP uses these for Pydantic-style validation)
    - Async execution
    - String manipulation
    - Logging
    
    Args:
        message: The message to echo (2-500 characters)
        uppercase: If True, convert message to uppercase
        repeat: Number of times to repeat the message (1-10)
        
    Returns:
        The processed message
        
    Raises:
        ValueError: If message is empty or repeat count is invalid
        
    Example:
        >>> await echo_message("Hello", uppercase=True, repeat=2)
        "HELLO HELLO"
    """
    logger.info(f"Tool called: echo_message(message='{message}', uppercase={uppercase}, repeat={repeat})")
    
    # Validate using Pydantic model
    try:
        validated_input = MessageInput(
            message=message,
            uppercase=uppercase,
            repeat=repeat
        )
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise
    
    # Process message
    processed_message = validated_input.message
    
    if validated_input.uppercase:
        processed_message = processed_message.upper()
    
    # Simulate async processing (e.g., database write)
    await asyncio.sleep(0.02)
    
    result = " ".join([processed_message] * validated_input.repeat)
    
    logger.info(f"Echo result: '{result}'")
    return result


@mcp.tool()
async def calculate(operation: str, a: float, b: float) -> dict:
    """
    Perform mathematical calculations.
    
    This tool demonstrates:
    - Complex input validation with Pydantic
    - Error handling for edge cases (division by zero)
    - Returning structured data
    - Async computation
    
    Args:
        operation: One of 'add', 'subtract', 'multiply', 'divide'
        a: First operand
        b: Second operand
        
    Returns:
        Dictionary containing:
            - operation: The operation performed
            - operands: The input values
            - result: The calculated result
            - timestamp: When the calculation was performed
        
    Raises:
        ValueError: If operation is invalid or division by zero
        
    Example:
        >>> await calculate("add", 10, 5)
        {"operation": "add", "operands": [10, 5], "result": 15.0, ...}
    """
    logger.info(f"Tool called: calculate(operation={operation}, a={a}, b={b})")
    
    # Validate using Pydantic model
    try:
        calc_input = CalculationInput(operation=operation, a=a, b=b)
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise
    
    # Simulate async computation
    await asyncio.sleep(0.01)
    
    # Perform calculation
    operations_map = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y,
    }
    
    result = operations_map[calc_input.operation](calc_input.a, calc_input.b)
    
    response = {
        "operation": calc_input.operation,
        "operands": [calc_input.a, calc_input.b],
        "result": result,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.info(f"Calculation result: {response}")
    return response


@mcp.tool()
async def get_server_info(ctx: Context) -> dict:
    """
    Get information about the MCP server.
    
    This tool demonstrates:
    - Using the Context object to access server metadata
    - Logging with context
    - Returning server diagnostics
    
    Args:
        ctx: MCP Context object (automatically injected by FastMCP)
        
    Returns:
        Dictionary containing server information
        
    Example:
        >>> await get_server_info(ctx)
        {"server_name": "demo-server", "status": "running", ...}
    """
    logger.info("Tool called: get_server_info")
    
    # Log using context
    ctx.info("Fetching server information")
    
    # Simulate async data gathering
    await asyncio.sleep(0.01)
    
    info = {
        "server_name": "demo-server",
        "status": "running",
        "tools_count": 4,
        "timestamp": datetime.utcnow().isoformat(),
        "message": "MCP Server is operational"
    }
    
    logger.info(f"Server info: {info}")
    return info


# ============================================================================
# RESOURCE IMPLEMENTATIONS (Application-controlled data)
# ============================================================================

@mcp.resource("config://server")
async def get_server_config() -> str:
    """
    Expose server configuration as a resource.
    
    Resources are read-only data endpoints that provide context to the LLM.
    This is similar to a GET endpoint in a REST API.
    
    Returns:
        Server configuration as a formatted string
    """
    logger.info("Resource accessed: config://server")
    
    await asyncio.sleep(0.01)
    
    config = """
    Server Configuration
    ====================
    Name: demo-server
    Version: 1.0.0
    Protocol: MCP (Model Context Protocol)
    Transport: stdio
    Capabilities: tools, resources, prompts
    Dependencies: pydantic
    """
    
    return config.strip()


@mcp.resource("status://{component}")
async def get_component_status(component: str) -> str:
    """
    Get status of a specific server component.
    
    This demonstrates dynamic resource URIs with parameters.
    
    Args:
        component: Component name (e.g., 'tools', 'resources', 'logging')
        
    Returns:
        Component status information
    """
    logger.info(f"Resource accessed: status://{component}")
    
    await asyncio.sleep(0.01)
    
    status_map = {
        "tools": "All 4 tools are operational",
        "resources": "All 2 resources are available",
        "logging": "Logging is enabled at INFO level",
        "server": "Server is running normally"
    }
    
    return status_map.get(
        component,
        f"Unknown component: {component}. Available: tools, resources, logging, server"
    )


# ============================================================================
# PROMPT IMPLEMENTATIONS (User-controlled templates)
# ============================================================================

@mcp.prompt()
def assistant_greeting(user_name: str = "User") -> str:
    """
    Generate a personalized assistant greeting prompt.
    
    Prompts are reusable templates for LLM interactions.
    
    Args:
        user_name: Name of the user
        
    Returns:
        Formatted greeting prompt
    """
    logger.info(f"Prompt called: assistant_greeting(user_name={user_name})")
    
    return f"""
    Hello {user_name}! I'm an MCP-enabled AI assistant with access to:
    
    🔧 Tools:
       - get_current_time: Get the current UTC time
       - echo_message: Echo and transform messages
       - calculate: Perform mathematical operations
       - get_server_info: Get server diagnostics
    
    📊 Resources:
       - config://server: Server configuration
       - status://{{component}}: Component status
    
    How can I help you today?
    """


# ============================================================================
# SERVER ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting MCP Server...")
    logger.info("Server will communicate via stdio (standard input/output)")
    logger.info("Press Ctrl+C to stop the server")
    
    # Run the FastMCP server
    # This starts the stdio transport and handles all MCP protocol messages
    mcp.run()
