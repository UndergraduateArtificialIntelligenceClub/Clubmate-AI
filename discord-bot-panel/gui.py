import os
import sys
import subprocess
import time
import socket
import requests
import webview
import threading
from dotenv import load_dotenv

# Load env from .env file explicitly
load_dotenv(".env")

class AppLauncher:
    def __init__(self):
        self.processes = []
        self.backend_port = 8000
        self.frontend_port = 5173
        self.backend_url = f"http://127.0.0.1:{self.backend_port}"
        self.frontend_url = f"http://localhost:{self.frontend_port}"

    def confirm_docker(self):
        print("[LAUNCHER] Checking Docker...")
        try:
            subprocess.run(["docker", "ps"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[LAUNCHER] Docker is running.")
            # Ensure DB is up
            print("[LAUNCHER] Starting Services...")
            subprocess.run(["docker-compose", "up", "-d"], check=True)
        except Exception:
            print("[LAUNCHER] Docker unreachable! Please ensure Docker Desktop is running.")
            # sys.exit(1) # Warn but continue? No, likely fatal.
    
    def start_backend(self):
        print(f"[LAUNCHER] Starting Backend on port {self.backend_port}...")
        # Use subprocess to isolate environment and use .env
        env = os.environ.copy()
        
        # We assume we are in root. Backend is in ./backend
        cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", str(self.backend_port), "--env-file", "../.env"]
        cwd = os.path.join(os.getcwd(), "backend")
        
        proc = subprocess.Popen(cmd, cwd=cwd, env=env) # Inherit output for debug
        self.processes.append(proc)
        
        # Wait for health
        self.wait_for_url(f"{self.backend_url}/health", "Backend")

    def start_frontend(self):
        print(f"[LAUNCHER] Starting Frontend on port {self.frontend_port}...")
        # Assume npm/pnpm
        cmd = ["pnpm", "dev", "--port", str(self.frontend_port)]
        cwd = os.path.join(os.getcwd(), "frontend")
        
        # Windows needs shell=True for pnpm sometimes if it's a batch file
        proc = subprocess.Popen(cmd, cwd=cwd, shell=True)
        self.processes.append(proc)
        
        self.wait_for_url(self.frontend_url, "Frontend", status_code=None) # Just connection

    def wait_for_url(self, url, name, timeout=30, status_code=200):
        print(f"[LAUNCHER] Waiting for {name} ({url})...")
        start = time.time()
        while time.time() - start < timeout:
            try:
                r = requests.get(url)
                if status_code is None or r.status_code == status_code:
                    print(f"[LAUNCHER] {name} is ready!")
                    return True
            except:
                pass
            time.sleep(1)
        print(f"[LAUNCHER] Warning: {name} timed out, but continuing...")

    def cleanup(self):
        print("[LAUNCHER] Stopping processes...")
        for p in self.processes:
            p.terminate()
            # on windows terminate might not be enough for shell=True
            if sys.platform == 'win32':
                subprocess.run(f"taskkill /F /T /PID {p.pid}", shell=True)

    def run(self):
        self.confirm_docker()
        self.start_backend()
        self.start_frontend()
        
        print("[LAUNCHER] Opening Window...")
        window = webview.create_window(
            "Discord Bot Panel", 
            url=self.frontend_url,
            width=1280,
            height=800,
            background_color='#e0e5ec'
        )
        webview.start()
        
        # Cleanup after window closes
        self.cleanup()

if __name__ == "__main__":
    launcher = AppLauncher()
    try:
        launcher.run()
    except KeyboardInterrupt:
        launcher.cleanup()
