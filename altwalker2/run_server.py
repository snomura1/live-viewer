"""
Direct Python script to run AltWalker2 server only
Usage: python run_server.py [--host HOST] [--port PORT]
"""

import sys
import webbrowser
import time
import threading
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.main import app
import uvicorn


def main():
    """Main entry point for server only."""

    # Default configuration
    host = "localhost"
    port = 5555

    # Parse arguments
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--host" and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
            i += 2
        else:
            print(f"Unknown argument: {sys.argv[i]}")
            print("\nUsage: python run_server.py [--host HOST] [--port PORT]")
            sys.exit(1)

    print(f"Starting AltWalker2 Live Viewer server...")
    print(f"Server: http://{host}:{port}")
    print("Press Ctrl+C to stop")

    # Open browser after a short delay
    def open_browser():
        time.sleep(1.5)  # Wait for server to start
        browser_url = f"http://{host}:{port}"
        print(f"\nOpening browser at: {browser_url}")
        try:
            webbrowser.open(browser_url)
        except Exception as e:
            print(f"Could not open browser automatically: {e}")

    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
