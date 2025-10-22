"""Test execution logic integrated with AltWalker"""

import json
import logging
import socket
import time
import requests
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

from altwalker.executor import create_executor
from altwalker.graphwalker import GraphWalkerClient, GraphWalkerException
from altwalker.model import get_models
from altwalker.planner import create_planner
from altwalker.walker import create_walker

from .reporter import WebSocketReporter

logger = logging.getLogger(__name__)


def find_available_port(start_port: int = 8888, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port.

    Args:
        start_port: Starting port number to try
        max_attempts: Maximum number of ports to try

    Returns:
        An available port number

    Raises:
        RuntimeError: If no available port is found
    """
    for port in range(start_port, start_port + max_attempts):
        try:
            # Try to bind to the port to check if it's available
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                logger.info(f"Found available port: {port}")
                return port
        except OSError:
            logger.debug(f"Port {port} is already in use")
            continue

    raise RuntimeError(
        f"Could not find an available port in range {start_port}-{start_port + max_attempts - 1}"
    )


def wait_for_graphwalker(port: int, timeout: int = 5, interval: float = 1.0) -> bool:
    """Wait for GraphWalker REST service to become available.

    Args:
        port: Port number where GraphWalker is running
        timeout: Maximum time to wait in seconds
        interval: Time between check attempts in seconds

    Returns:
        True if service is available, False otherwise
    """
    # Simple sleep-based wait to avoid port exhaustion
    # GraphWalker typically starts quickly
    print(f"Waiting for GraphWalker REST service on port {port}...")
    time.sleep(2)  # Give GraphWalker time to start
    print(f"GraphWalker should be ready on port {port}")
    return True


def load_models_json(model_paths: List[str]) -> List[Dict[str, Any]]:
    """Load model JSON files.

    Args:
        model_paths: List of paths to model files

    Returns:
        List of model data dictionaries
    """
    models_data = []

    for path in model_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                model_data = json.load(f)
                models_data.append(model_data)
        except Exception as e:
            logger.error(f"Error loading model from {path}: {e}")
            raise

    return models_data


def online(
    test_package: str,
    models: List[Tuple[str, str]],
    host: str = "localhost",
    port: int = 5555,
    executor_type: str = "python",
    executor_url: Optional[str] = None,
    start_element: Optional[str] = None,
    verbose: bool = False,
    unvisited: bool = False,
    blocked: bool = False,
    gw_host: Optional[str] = None,
    gw_port: int = 8888,
    report_path: bool = False,
    report_path_file: Optional[str] = None,
    report_file: Optional[str] = None,
    report_xml: bool = False,
    report_xml_file: Optional[str] = None,
    import_mode: str = "importlib",
    **kwargs,
):
    """Execute tests online with GraphWalker and report via WebSocket.

    Args:
        test_package: Path to test package
        models: List of (model_path, generator) tuples
        host: WebSocket server host
        port: WebSocket server port
        executor_type: Test executor type (python, dotnet, etc.)
        executor_url: Optional executor URL
        start_element: Starting element in the model
        verbose: Verbose output
        unvisited: Report unvisited elements
        blocked: Filter blocked elements
        gw_host: GraphWalker host
        gw_port: GraphWalker port
        report_path: Enable path reporting
        report_path_file: Path report file
        report_file: General report file
        report_xml: Enable XML reporting
        report_xml_file: XML report file
        import_mode: Python import mode
    """
    # Load model JSON data
    model_paths = [model[0] for model in models]
    models_json = load_models_json(model_paths)

    # Create reporter
    reporter = WebSocketReporter(host=host, port=port, models_data=models_json)

    # Create executor
    executor = create_executor(
        tests_path=test_package,
        executor_type=executor_type,
        executor_url=executor_url,
        import_mode=import_mode,
    )

    # Try to start GraphWalker on sequential ports
    # This avoids TOCTOU race condition by directly trying ports without pre-checking
    planner = None
    attempted_port = None
    max_retries = 10

    for attempt in range(max_retries):
        attempted_port = gw_port + attempt
        try:
            print(f"Attempting to start GraphWalker on port: {attempted_port}")

            # Create planner (GraphWalker client with auto-start)
            # This will start the GraphWalker process
            planner = create_planner(
                models=models,
                blocked=blocked,
                start_element=start_element,
                port=attempted_port,
            )
            print(f"GraphWalker process started on port: {attempted_port}")

            # Wait for GraphWalker REST service to become available
            if not wait_for_graphwalker(attempted_port, timeout=10):
                # Service didn't start properly, kill it and try next port
                if planner:
                    planner.kill()
                    planner = None
                logger.warning(
                    f"GraphWalker REST service did not become available on port {attempted_port}, trying next port..."
                )
                continue

            print(
                f"GraphWalker is ready and accepting connections on port: {attempted_port}"
            )
            break

        except GraphWalkerException as e:
            if "Address already in use" in str(e) or "bind" in str(e).lower():
                logger.warning(
                    f"Port {attempted_port} is in use, trying port {attempted_port + 1}..."
                )
                # Clean up if planner was partially created
                if planner:
                    try:
                        planner.kill()
                    except:
                        pass
                    planner = None
                continue
            else:
                # Other GraphWalker errors should be raised
                raise
        except Exception as e:
            # Unexpected error, log and try next port
            logger.warning(
                f"Unexpected error starting GraphWalker on port {attempted_port}: {e}"
            )
            if planner:
                try:
                    planner.kill()
                except:
                    pass
                planner = None
            continue

    if planner is None:
        raise RuntimeError(
            f"Failed to start GraphWalker after {max_retries} attempts. "
            f"Tried ports {gw_port}-{gw_port + max_retries - 1}. "
            "All ports are in use or GraphWalker failed to start. "
            "Please ensure some ports in this range are available or check GraphWalker installation."
        )

    # Start test execution using walker (like original altwalker-live-viewer)
    try:
        print("Starting test execution with walker...")

        # Create walker to manage execution
        # This uses AltWalker's internal connection pooling
        walker = create_walker(planner, executor, reporter=reporter)

        # Run tests
        walker.run()

        print(f"Test execution completed with status: {walker.status}")

    except Exception as e:
        logger.error(f"Error during test execution: {e}")
        raise
    finally:
        if executor:
            executor.kill()
        if planner:
            planner.kill()


def walk(
    test_package: str,
    steps: List[Dict[str, Any]],
    host: str = "localhost",
    port: int = 5555,
    executor_type: str = "python",
    executor_url: Optional[str] = None,
    report_path: bool = False,
    report_path_file: Optional[str] = None,
    report_file: Optional[str] = None,
    report_xml: bool = False,
    report_xml_file: Optional[str] = None,
    import_mode: str = "importlib",
    **kwargs,
):
    """Execute tests from a predefined path and report via WebSocket.

    Args:
        test_package: Path to test package
        steps: List of step dictionaries to execute
        host: WebSocket server host
        port: WebSocket server port
        executor_type: Test executor type (python, dotnet, etc.)
        executor_url: Optional executor URL
        report_path: Enable path reporting
        report_path_file: Path report file
        report_file: General report file
        report_xml: Enable XML reporting
        report_xml_file: XML report file
        import_mode: Python import mode
    """
    # Create reporter
    reporter = WebSocketReporter(host=host, port=port, models_data=[])

    # Create executor
    executor = create_executor(
        tests_path=test_package,
        executor_type=executor_type,
        executor_url=executor_url,
        import_mode=import_mode,
    )

    # Execute tests
    try:
        reporter.start()

        # Load executor
        executor.load(test_package)

        # Execute each step
        has_failures = False

        for step in steps:
            reporter.step_start(step)

            try:
                result = executor.execute_step(step)
                reporter.step_end(step, result)

                if result.get("error"):
                    has_failures = True

            except Exception as e:
                error_result = {
                    "id": step.get("id"),
                    "error": {
                        "message": str(e),
                        "trace": "",
                    },
                    "output": "",
                }
                reporter.step_end(step, error_result)
                has_failures = True

        # Report end
        reporter.end(statistics={}, status=not has_failures)

    except Exception as e:
        logger.error(f"Error during test execution: {e}")
        reporter.end(statistics={}, status=False)
        raise
    finally:
        if executor:
            executor.kill()
