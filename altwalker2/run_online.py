"""
Direct Python script to run AltWalker2 online mode
Usage: python run_online.py <test_package> -m <model_path> <generator>
"""

import sys
import multiprocessing
import time
import webbrowser
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
    # if len(sys.argv) < 4:
    #     print(
    #         "Usage: python run_online.py <test_package> -m <model_path> <generator> [options]"
    #     )
    #     print("\nOptions:")
    #     print("  --host <host>        WebSocket server host (default: localhost)")
    #     print("  --port <port>        WebSocket server port (default: 5555)")
    #     print("  --gw-port <port>     GraphWalker REST service port (default: 8888)")
    #     print("\nExample:")
    #     print('  python run_online.py tests/ -m models/model.json "random(never)"')
    #     print(
    #         '  python run_online.py tests/ -m models/model.json "random(never)" --gw-port 8889'
    #     )
    #     sys.exit(1)
    test_package = "../example/tests"  # str(Path(sys.argv[1]).resolve())

    # Parse model arguments and options
    models = []
    host = "localhost"
    port = 5555
    gw_port = 8888  # GraphWalker port

    i = 2
    # str(Path(sys.argv[i + 1]).resolve())
    model_path = "../example/models/default.json"

    # generator = "random(edge_coverage(100))"  # sys.argv[i + 2]
    # generator = "a_star(edge_coverage(100))"  # sys.argv[i + 2]
    generator = "weighted_random(edge_coverage(100))"  # sys.argv[i + 2]
    # generator = "quick_random(edge_coverage(100))"  # sys.argv[i + 2]

    models.append((model_path, generator))

    # while i < len(sys.argv):
    #     if True:  # sys.argv[i] == "-m" and i + 2 < len(sys.argv):
    #         model_path = (
    #             "../example/models/default.json"  # str(Path(sys.argv[i + 1]).resolve())
    #         )
    #         generator = "random(edge_coverage(100))"  # sys.argv[i + 2]
    #         models.append((model_path, generator))
    #         i += 3
    #     elif sys.argv[i] == "--host" and i + 1 < len(sys.argv):
    #         host = sys.argv[i + 1]
    #         i += 2
    #     elif sys.argv[i] == "--port" and i + 1 < len(sys.argv):
    #         port = int(sys.argv[i + 1])
    #         i += 2
    #     elif sys.argv[i] == "--gw-port" and i + 1 < len(sys.argv):
    #         gw_port = int(sys.argv[i + 1])
    #         i += 2
    #     else:
    #         i += 1

    if not models:
        print("Error: No models specified. Use -m <model_path> <generator>")
        sys.exit(1)

    # Start server in separate process
    print(f"Starting WebSocket server on {host}:{port}...")
    server_process = multiprocessing.Process(target=run_server, args=(host, port))
    server_process.start()

    try:
        # Wait for server to be ready with health check
        import requests

        max_wait = 10
        wait_interval = 0.5
        waited = 0
        server_ready = False

        print("Waiting for server to start...")
        while waited < max_wait:
            try:
                response = requests.get(f"http://{host}:{port}/healthz", timeout=1)
                if response.status_code == 200:
                    server_ready = True
                    print(f"Server is ready after {waited:.1f}s")
                    break
            except:
                pass
            time.sleep(wait_interval)
            waited += wait_interval

        if not server_ready:
            print(
                f"WARNING: Server may not be ready after {max_wait}s, continuing anyway..."
            )
            time.sleep(1)  # Give it a bit more time

        print("Starting test execution...")
        browser_url = f"http://{host}:{port}"
        print(f"Opening browser at: {browser_url}")

        # Open browser automatically
        try:
            webbrowser.open(browser_url)
            # Wait a moment for browser to open and viewer to connect
            print("Waiting for viewer to connect...")
            time.sleep(3)
        except Exception as e:
            print(f"Could not open browser automatically: {e}")
            print(f"Please open manually: {browser_url}")
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
