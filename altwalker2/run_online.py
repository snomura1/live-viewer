"""
Direct Python script to run AltWalker2 online mode
Usage: python run_online.py <test_package> -m <model_path> <generator>
"""

import sys
import multiprocessing
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.main import app
from backend import walker
import uvicorn


def run_server(host: str, port: int):
    """Run the FastAPI server in a separate process."""
    uvicorn.run(app, host=host, port=port, log_level="info")


def main():
    """Main entry point for online test execution."""

    # Parse arguments
    if len(sys.argv) < 4:
        print(
            "Usage: python run_online.py <test_package> -m <model_path> <generator> [options]"
        )
        print("\nOptions:")
        print("  --host <host>        WebSocket server host (default: localhost)")
        print("  --port <port>        WebSocket server port (default: 5555)")
        print("  --gw-port <port>     GraphWalker REST service port (default: 8888)")
        print("\nExample:")
        print('  python run_online.py tests/ -m models/model.json "random(never)"')
        print(
            '  python run_online.py tests/ -m models/model.json "random(never)" --gw-port 8889'
        )
        sys.exit(1)

    test_package = str(Path(sys.argv[1]).resolve())

    # Parse model arguments and options
    models = []
    host = "localhost"
    port = 5555
    gw_port = 8888  # Changed from 8887 to avoid common conflicts

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "-m" and i + 2 < len(sys.argv):
            model_path = str(Path(sys.argv[i + 1]).resolve())
            generator = sys.argv[i + 2]
            models.append((model_path, generator))
            i += 3
        elif sys.argv[i] == "--host" and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--gw-port" and i + 1 < len(sys.argv):
            gw_port = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    if not models:
        print("Error: No models specified. Use -m <model_path> <generator>")
        sys.exit(1)

    # Start server in separate process
    print(f"Starting WebSocket server on {host}:{port}...")
    server_process = multiprocessing.Process(target=run_server, args=(host, port))
    server_process.start()

    try:
        # Give server time to start
        time.sleep(2)

        print("Starting test execution...")
        print(f"Open browser at: http://{host}:{port}")
        print(f"\nGraphWalker port: {gw_port}")
        print("Test package:", test_package)
        print("Models:")
        for model_path, generator in models:
            print(f"  - {model_path}: {generator}")
        print()

        # Execute tests
        walker.online(
            test_package=test_package,
            models=models,
            host=host,
            port=port,
            executor_type="python",
            executor_url=None,
            start_element=None,
            verbose=False,
            unvisited=False,
            blocked=False,
            gw_host=None,
            gw_port=gw_port,
            report_path=False,
            report_path_file=None,
            report_file=None,
            report_xml=False,
            report_xml_file=None,
            import_mode="importlib",
        )

        print("\nTest execution completed!")

    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
    except Exception as e:
        print(f"\nError during test execution: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print("\nStopping server...")
        server_process.terminate()
        server_process.join()


if __name__ == "__main__":
    main()
