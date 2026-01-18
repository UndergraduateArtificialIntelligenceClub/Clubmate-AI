# Clubmate-AI

## Setup & Installation

### 1. Create a Virtual Environment
It's recommended to use a virtual environment to manage dependencies.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
Install the required packages using `pip`.

```bash
pip install -r requirements.txt
```

## Configuration

### Google Calendar API
1.  **Create OAuth Credentials**:
    *   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    *   Create a new project (or select an existing one).
    *   Enable the **Google Calendar API**.
    *   Go to **Credentials** -> **Create Credentials** -> **OAuth client ID**.
    *   Select **Desktop app**.
    *   Download the JSON file. (We have our own credentials.json for ClubeMateAI. Will be in repo)

2.  **Save Credentials**:
    *   Rename the downloaded JSON file to `credentials.json`.
    *   Place it in the root directory.

3.  **Authenticate**:
    Run the authentication script to generate your user token. This will open a browser window for you to log in.

    ```bash
    python src/authenticate.py
    ```
    
    *   Upon successful login, a `token.json` file will be created in the root directory.

### Discord Bot & Gemini
1.  **Environment Variables**:
    *   Copy `.env.example` to `.env`.
    *   Fill in your `DISCORD_TOKEN` and `GEMINI_API_KEY`.

    ```bash
    cp .env.example .env
    # Edit .env with your keys
    ```

## Running the Project

### Start the MCP Server (Standalone)
To start the Google Calendar MCP server manually (for testing via stdio):

```bash
python src/servers/calendar_integration.py
```

### Start the Discord Bot
The Discord bot acts as a client for the MCP server.

1.  Navigate to the `gemini` directory:
    ```bash
    cd gemini
    ```
2.  Run the bot:
    ```bash
    python discord_bot.py
    ```

The bot will automatically check for the calendar server script at `../src/servers/calendar_integration.py` and register it.

### Discord Commands
- `!chat <message>`: Chat with the bot (it can use tools).
- `!list_tools`: Show available tools.
- `!connect calendar`: Connect to the calendar server (auto-connected on startup).
- Mentioning the bot (`@Clubmate-AI <message>`) also works as a chat interface.