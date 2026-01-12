import os
import sys
import subprocess
import time
import requests
import webview
from dotenv import load_dotenv

# Load env from .env file explicitly
load_dotenv(".env")


class AppLauncher:
    """
    Launches the Discord Bot Panel application.
    
    Handles:
    - Installing Python dependencies
    - Starting the FastAPI backend
    - Starting the Vite frontend  
    - Opening a webview window
    """
    
    def __init__(self):
        self.processes = []
        self.backend_port = 8000
        self.frontend_port = 5173
        self.backend_url = f"http://127.0.0.1:{self.backend_port}"
        self.frontend_url = f"http://localhost:{self.frontend_port}"
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
    
    def install_dependencies(self):
        """Install Python dependencies if needed."""
        print("[LAUNCHER] Checking Python dependencies...")
        requirements_path = os.path.join(self.root_dir, "requirements.txt")
        
        try:
            # Check if key packages are installed
            import fastapi
            import uvicorn
            import sqlmodel
            print("[LAUNCHER] Dependencies already installed.")
        except ImportError:
            print("[LAUNCHER] Installing dependencies...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", requirements_path, "-q"],
                check=True
            )
            print("[LAUNCHER] Dependencies installed successfully.")
    
    def init_database(self):
        """Run database migrations."""
        print("[LAUNCHER] Initializing database...")
        backend_dir = os.path.join(self.root_dir, "backend")
        
        try:
            # Run alembic migrations using python -m
            result = subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=backend_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("[LAUNCHER] Database migrations applied.")
            else:
                # If alembic fails, the app will still create tables via SQLModel
                print(f"[LAUNCHER] Migration skipped (will use auto-create): {result.stderr[:100] if result.stderr else 'OK'}")
        except Exception as e:
            print(f"[LAUNCHER] Migration skipped: {e}")
    
    def start_backend(self):
        """Start the FastAPI backend server."""
        print(f"[LAUNCHER] Starting Backend on port {self.backend_port}...")
        
        backend_dir = os.path.join(self.root_dir, "backend")
        env = os.environ.copy()
        
        # Use python -m uvicorn for better compatibility
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "127.0.0.1",
            "--port", str(self.backend_port),
        ]
        
        # Start backend process - inherit stdout/stderr so we can see errors
        proc = subprocess.Popen(
            cmd,
            cwd=backend_dir,
            env=env,
        )
        self.processes.append(proc)
        
        # Give it a moment to start or fail
        time.sleep(2)
        
        # Check if process died immediately
        if proc.poll() is not None:
            print(f"[LAUNCHER] ❌ Backend failed to start! Exit code: {proc.returncode}")
            print("[LAUNCHER] Check the error output above.")
            return False
        
        # Wait for backend to be ready
        return self.wait_for_url(f"{self.backend_url}/health", "Backend")
    
    def start_frontend(self):
        """Start the Vite frontend dev server."""
        print(f"[LAUNCHER] Starting Frontend on port {self.frontend_port}...")
        
        frontend_dir = os.path.join(self.root_dir, "frontend")
        
        # Check if node_modules exists
        node_modules = os.path.join(frontend_dir, "node_modules")
        if not os.path.exists(node_modules):
            print("[LAUNCHER] Installing frontend dependencies...")
            subprocess.run(["pnpm", "install"], cwd=frontend_dir, shell=True, check=True)
        
        # Start frontend with pnpm
        cmd = ["pnpm", "dev", "--port", str(self.frontend_port)]
        
        proc = subprocess.Popen(
            cmd,
            cwd=frontend_dir,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        self.processes.append(proc)
        
        # Wait for frontend to be ready
        self.wait_for_url(self.frontend_url, "Frontend", status_code=None)
    
    def wait_for_url(self, url, name, timeout=60, status_code=200):
        """Wait for a URL to become available."""
        print(f"[LAUNCHER] Waiting for {name} ({url})...")
        start = time.time()
        
        while time.time() - start < timeout:
            try:
                r = requests.get(url, timeout=2)
                if status_code is None or r.status_code == status_code:
                    print(f"[LAUNCHER] ✓ {name} is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        
        print(f"[LAUNCHER] ⚠ {name} timed out, but continuing...")
        return False
    
    def cleanup(self):
        """Stop all child processes."""
        print("[LAUNCHER] Stopping processes...")
        for p in self.processes:
            try:
                p.terminate()
                # On Windows, terminate might not be enough for shell processes
                if sys.platform == 'win32':
                    subprocess.run(
                        f"taskkill /F /T /PID {p.pid}",
                        shell=True,
                        capture_output=True
                    )
            except Exception as e:
                print(f"[LAUNCHER] Error stopping process: {e}")
    
    def run(self):
        """Main entry point - starts everything and opens the window."""
        print("=" * 50)
        print("   Discord Bot Panel - Starting...")
        print("=" * 50)
        
        # Step 1: Install dependencies
        self.install_dependencies()
        
        # Step 2: Initialize database
        self.init_database()
        
        # Step 3: Start backend
        self.start_backend()
        
        # Step 4: Start frontend
        self.start_frontend()
        
        # Step 5: Open webview window
        print("[LAUNCHER] Opening application window...")
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
        print("[LAUNCHER] Application closed.")


if __name__ == "__main__":
    launcher = AppLauncher()
    try:
        launcher.run()
    except KeyboardInterrupt:
        print("\n[LAUNCHER] Interrupted by user.")
        launcher.cleanup()
    except Exception as e:
        print(f"[LAUNCHER] Error: {e}")
        launcher.cleanup()
        sys.exit(1)

