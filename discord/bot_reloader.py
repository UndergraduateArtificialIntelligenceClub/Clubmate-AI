import subprocess
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class BotReloader(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_bot()
    
    def start_bot(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        print("Starting bot...")
        self.process = subprocess.Popen([sys.executable, "bot.py"])
    
    def on_modified(self, event):
        if event.src_path.endswith("bot.py"):
            print("bot.py changed! Restarting...")
            self.start_bot()

if __name__ == "__main__":
    event_handler = BotReloader()
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=False)
    observer.start()
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
