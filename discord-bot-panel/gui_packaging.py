import os
import sys
import socket
import time
import threading
import uvicorn
import requests
import webview
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

# 2. Add backend to path so imports work
sys.path.append(os.path.abspath("backend"))

from app.main import app

# Constants
TITLE = "Discord Bot Panel"
MIN_WIDTH = 1024
MIN_HEIGHT = 768
FRONTEND_DIR = os.path.join(os.path.abspath("frontend"), "dist")

# 3. Mount Frontend Static Files (Production Mode)
# This tells FastAPI to serve the React Build files
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

if os.path.exists(FRONTEND_DIR):
    # Mount assets (JS/CSS)
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")
    
    # Catch-all route to serve index.html for React Router
    @app.get("/{full_path:path}")
    async def serve_react(full_path: str):
        # Don't catch API routes
        if full_path.startswith("api") or full_path.startswith("health"):
            return {"error": "API route not found"}
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
else:
    print(f"WARNING: Frontend build not found at {FRONTEND_DIR}")
    print("Please run 'pnpm build' in the frontend folder first.")

class ApiThread(threading.Thread):
    def __init__(self, port):
        super().__init__()
        self.port = port
        self.daemon = True

    def run(self):
        uvicorn.run(app, host="127.0.0.1", port=self.port, log_level="info")

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

def wait_for_server(port, timeout=10):
    start_time = time.time()
    health_url = f"http://127.0.0.1:{port}/health"
    while time.time() - start_time < timeout:
        try:
            if requests.get(health_url).status_code == 200:
                return True
        except:
            pass
        time.sleep(0.1)
    return False

def start_app():
    port = get_free_port()
    os.environ["API_PORT"] = str(port)

    # Start Backend
    api_thread = ApiThread(port)
    api_thread.start()

    # Wait for Backend
    if not wait_for_server(port):
        print("Failed to start API server")
        sys.exit(1)

    # Launch Window pointing to the LOCAL PYTHON SERVER (not vite)
    window = webview.create_window(
        TITLE, 
        url=f"http://127.0.0.1:{port}", 
        width=1200, 
        height=800, 
        min_size=(MIN_WIDTH, MIN_HEIGHT),
        background_color='#e0e5ec'
    )
    webview.start()

if __name__ == '__main__':
    start_app()
