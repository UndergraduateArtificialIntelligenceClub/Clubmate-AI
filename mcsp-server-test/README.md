# MCP Server Demo

A minimal **Model Context Protocol (MCP)** server built with the MCP Python SDK, demonstrating async tools, resources, Pydantic validation, and comprehensive logging.

## 📋 Project Overview

This project implements a fully functional MCP server that exposes:

- **4 Tools**: Functions the AI can invoke to perform actions

  - `get_current_time` - Returns current UTC timestamp
  - `echo_message` - Echoes and transforms text messages
  - `calculate` - Performs mathematical operations
  - `get_server_info` - Returns server diagnostics

- **2 Resources**: Read-only data endpoints

  - `config://server` - Server configuration
  - `status://{component}` - Component status information

- **1 Prompt**: Reusable interaction template
  - `assistant_greeting` - Personalized greeting for users

## 🏗️ Architecture

mcp-server-demo/
├── server.py # Main MCP server implementation
├── README.md # This file
├── .gitignore # Git ignore patterns
└── requirements.txt # Python dependencies (optional)

## 🚀 Installation & Setup

### Prerequisites

- Python 3.10 or higher
- pip or uv package manager
- Claude Desktop (for integration)

### Install Dependencies

Create virtual environment
python -m venv venv

Activate virtual environment
.\venv\Scripts\Activate.ps1

Install MCP SDK
pip install "mcp[cli]"

## ▶️ Running the Server

### Development Mode (with MCP Inspector)

Test your server interactively with the MCP Inspector:

mcp dev server.py

This will:

- Start the server on `http://127.0.0.1:6274`
- Open MCP Inspector in your browser
- Allow you to test tools, resources, and prompts interactively

### Production Mode (stdio)

Run the server in stdio mode for Claude Desktop integration:

python server.py

### Claude Desktop Integration

1. **Configure Claude Desktop**:

   - Edit `%APPDATA%\Claude\claude_desktop_config.json`
   - Add your server configuration (see Configuration section)

2. **Restart Claude Desktop**

3. **Verify Connection**:
   - Open Claude Desktop
   - Look for the 🔌 icon indicating MCP server connection
   - The server should appear in Claude's MCP settings

## ⚙️ Configuration

### Claude Desktop Config

File location: `%APPDATA%\Claude\claude_desktop_config.json`

{
"mcpServers": {
"demo-server": {
"command": "python",
"args": [
"C:\path\to\mcp-server-demo\server.py"
],
"env": {
"PYTHONUNBUFFERED": "1"
}
}
}
}

**Replace** `C:\\path\\to\\mcp-server-demo\\server.py` with your actual path.

## 🧪 Testing the Tools

### Using MCP Inspector

1. Start dev mode: `mcp dev server.py`
2. Open browser at `http://127.0.0.1:6274`
3. Test each tool through the UI

### Using Claude Desktop

Once configured, interact with the tools naturally:

You: "What time is it?"
Claude: [calls get_current_time tool]
"The current time (UTC) is 2025-10-29T19:16:45.123456"

You: "Calculate 15 \* 7"
Claude: [calls calculate tool with operation="multiply", a=15, b=7]
"15 multiplied by 7 equals 105"

You: "Echo 'Hello MCP' in uppercase 3 times"
Claude: [calls echo_message tool]
"HELLO MCP HELLO MCP HELLO MCP"

## 📚 Key Concepts

### Async Functions

The server uses `async/await` for non-blocking I/O operations:

@mcp.tool()
async def get_current_time(timezone: str = "UTC") -> str:

# Simulate async operation (e.g., API call)

await asyncio.sleep(0.01)
return f"Current time: {datetime.utcnow().isoformat()}"

**Benefits**:

- Handle multiple requests concurrently
- Don't block on I/O operations
- Scale better under load

### Pydantic Validation

Input validation using Pydantic ensures type safety:

class MessageInput(BaseModel):
message: str = Field(..., min_length=2, max_length=500)
uppercase: bool = Field(default=False)
repeat: int = Field(default=1, ge=1, le=10)

@validator('message')
def message_not_empty(cls, v):
if not v.strip():
raise ValueError('Message cannot be empty')
return v.strip()

**Benefits**:

- Automatic validation before tool execution
- Clear error messages for invalid inputs
- Type hints for IDE autocomplete
- Self-documenting code

### MCP Protocol Flow

Claude Desktop starts → Launches server.py via stdio

Server initializes → Registers tools, resources, prompts

Claude sends capabilities → Server responds with available features

User interacts → Claude decides which tools to call

Tool execution → Server processes, returns results

Response → Claude presents results to user

## 🔧 Example API Calls

### Tool Call: get_current_time

**Request**:
{
"method": "tools/call",
"params": {
"name": "get_current_time",
"arguments": {
"timezone": "UTC"
}
}
}

**Response**:
{
"content": [
{
"type": "text",
"text": "Current time (UTC): 2025-10-29T19:16:45.123456"
}
]
}

### Tool Call: calculate

**Request**:
{
    "method": "tools/call",
    "params": {
        "name": "calculate",
        "arguments": {
            "operation": "divide",
            "a": 100,
            "b": 5
        }
    }
}

**Response**:
{
}
}
