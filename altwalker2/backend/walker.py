"""Test execution logic with direct GraphWalker integration

No AltWalker dependency - direct GraphWalker REST API usage.
"""

import json
import logging
import socket
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

from .graphwalker_client import GraphWalkerClient, GraphWalkerException
from .python_executor import PythonTestExecutor, TestExecutionException
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

    Direct GraphWalker integration without AltWalker dependency.

    Args:
        test_package: Path to test package
        models: List of (model_path, generator) tuples
        host: WebSocket server host
        port: WebSocket server port
        executor_type: Test executor type (only 'python' supported)
        executor_url: Optional executor URL (not used)
        start_element: Starting element in the model
        verbose: Verbose output
        unvisited: Report unvisited elements
        blocked: Filter blocked elements
        gw_host: GraphWalker host (not used, always localhost)
        gw_port: GraphWalker port
        report_path: Enable path reporting (not used)
        report_path_file: Path report file (not used)
        report_file: General report file (not used)
        report_xml: Enable XML reporting (not used)
        report_xml_file: XML report file (not used)
        import_mode: Python import mode (not used)
    """
    # Load model JSON data
    model_paths = [model[0] for model in models]
    models_json = load_models_json(model_paths)

    # Create reporter
    reporter = WebSocketReporter(host=host, port=port, models_data=models_json)

    # Create test executor
    if executor_type != "python":
        raise ValueError(
            f"Unsupported executor type: {executor_type}. Only 'python' is supported."
        )

    executor = PythonTestExecutor(tests_path=test_package)

    # Try to start GraphWalker on sequential ports
    graphwalker = None
    attempted_port = None
    max_retries = 10

    for attempt in range(max_retries):
        attempted_port = gw_port + attempt
        try:
            print(f"Attempting to start GraphWalker on port: {attempted_port}")

            # Create GraphWalker client
            graphwalker = GraphWalkerClient(
                models=models,
                port=attempted_port,
                blocked=blocked,
                start_element=start_element,
            )

            # Start GraphWalker process
            graphwalker.start()

            print(
                f"GraphWalker is ready and accepting connections on port: {attempted_port}"
            )
            break

        except GraphWalkerException as e:
            if "Address already in use" in str(e) or "bind" in str(e).lower():
                logger.warning(
                    f"Port {attempted_port} is in use, trying port {attempted_port + 1}..."
                )
                if graphwalker:
                    try:
                        graphwalker.kill()
                    except:
                        pass
                    graphwalker = None
                continue
            else:
                # Other GraphWalker errors should be raised
                if graphwalker:
                    try:
                        graphwalker.kill()
                    except:
                        pass
                raise
        except Exception as e:
            logger.warning(
                f"Unexpected error starting GraphWalker on port {attempted_port}: {e}"
            )
            if graphwalker:
                try:
                    graphwalker.kill()
                except:
                    pass
                graphwalker = None
            continue

    if graphwalker is None:
        raise RuntimeError(
            f"Failed to start GraphWalker after {max_retries} attempts. "
            f"Tried ports {gw_port}-{gw_port + max_retries - 1}."
        )

    # Execute tests
    try:
        print("Starting test execution with GraphWalker...")

        # Load test module
        executor.load()

        # Start reporting
        reporter.start()

        # Main execution loop
        step_count = 0
        has_failures = False

        while graphwalker.has_next():
            # Get next step from GraphWalker
            step = graphwalker.get_next()
            step_count += 1

            print(f"DEBUG [WALKER]: Received step from GraphWalker: {step}")

            # Validate step data
            if not isinstance(step, dict) or "name" not in step:
                logger.error(f"Invalid step data from GraphWalker: {step}")
                print(f"ERROR: Invalid step data - missing 'name' field")
                break

            # Get current model data
            step["data"] = graphwalker.get_data()

            # Report step start
            reporter.step_start(step)

            # Execute the step
            result = executor.execute_step(step)

            # Report step end
            reporter.step_end(step, result)

            # Check for errors
            if result.get("error"):
                has_failures = True

        # Get final statistics
        statistics = graphwalker.get_statistics()

        # Report end
        reporter.end(statistics=statistics, status=not has_failures)

        print(f"Test execution completed. Steps executed: {step_count}")
        print(f"Status: {'FAILED' if has_failures else 'PASSED'}")

    except Exception as e:
        logger.error(f"Error during test execution: {e}")
        try:
            reporter.end(statistics={}, status=False)
        except:
            pass
        raise
    finally:
        if executor:
            executor.kill()
        if graphwalker:
            graphwalker.kill()


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
        executor_type: Test executor type (only 'python' supported)
        executor_url: Optional executor URL (not used)
        report_path: Enable path reporting (not used)
        report_path_file: Path report file (not used)
        report_file: General report file (not used)
        report_xml: Enable XML reporting (not used)
        report_xml_file: XML report file (not used)
        import_mode: Python import mode (not used)
    """
    # Create reporter
    reporter = WebSocketReporter(host=host, port=port, models_data=[])

    # Create executor
    if executor_type != "python":
        raise ValueError(f"Unsupported executor type: {executor_type}")

    executor = PythonTestExecutor(tests_path=test_package)

    # Execute tests
    try:
        reporter.start()

        # Load executor
        executor.load()

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
