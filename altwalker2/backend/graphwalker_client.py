"""GraphWalker REST API Client

Direct implementation without AltWalker dependency.
GraphWalker is a standalone Java application with REST API.
"""

import json
import logging
import subprocess
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import requests

logger = logging.getLogger(__name__)


class GraphWalkerException(Exception):
    """Exception raised for GraphWalker errors."""

    pass


class GraphWalkerClient:
    """Client for GraphWalker REST API.

    GraphWalker is started as a subprocess and accessed via REST API.
    """

    def __init__(
        self,
        models: List[Tuple[str, str]],
        port: int = 8888,
        blocked: bool = False,
        start_element: Optional[str] = None,
    ):
        """Initialize GraphWalker client.

        Args:
            models: List of (model_path, generator) tuples
            port: Port for GraphWalker REST service
            blocked: Filter blocked elements
            start_element: Starting element in the model
        """
        self.models = models
        self.port = port
        self.blocked = blocked
        self.start_element = start_element
        self.process: Optional[subprocess.Popen] = None
        self.base_url = f"http://localhost:{port}/graphwalker"

    def start(self):
        """Start GraphWalker process."""
        # Find graphwalker.jar - try current directory and parent directory
        jar_paths = [
            Path("graphwalker.jar"),  # Current directory
            Path(__file__).parent / "graphwalker.jar",  # backend directory
            Path(__file__).parent.parent / "graphwalker.jar",  # altwalker2 directory
        ]

        jar_path = None
        for path in jar_paths:
            if path.exists():
                jar_path = str(path.resolve())
                break

        if not jar_path:
            raise GraphWalkerException(
                f"graphwalker.jar not found. Tried: {[str(p) for p in jar_paths]}"
            )

        print(f"DEBUG: Using GraphWalker JAR at: {jar_path}")

        # Build command
        cmd = ["java", "-jar", jar_path]

        # Add debug flag for all output
        cmd.extend(["-d", "all"])

        # Online mode with RESTFUL service
        cmd.append("online")

        # Service type - RESTFUL for REST API (not WebSocket)
        cmd.extend(["-s", "RESTFUL"])

        # Port
        cmd.extend(["-p", str(self.port)])

        # Models
        for model_path, generator in self.models:
            cmd.extend(["-m", model_path, generator])

        # Blocked elements
        if self.blocked:
            cmd.append("--blocked")

        # Start element
        if self.start_element:
            cmd.extend(["-e", self.start_element])

        logger.info(f"Starting GraphWalker: {' '.join(cmd)}")
        print(f"DEBUG: GraphWalker command: {' '.join(cmd)}")

        try:
            # Start process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            print(f"DEBUG: GraphWalker process started, PID: {self.process.pid}")

            # Check if process is still running
            import time
            import threading

            time.sleep(1)
            poll_result = self.process.poll()

            if poll_result is not None:
                # Process has already terminated
                stdout, stderr = self.process.communicate()
                print(f"DEBUG: GraphWalker process terminated immediately!")
                print(f"DEBUG: Exit code: {poll_result}")
                print(f"DEBUG: STDOUT: {stdout}")
                print(f"DEBUG: STDERR: {stderr}")
                raise GraphWalkerException(
                    f"GraphWalker process terminated immediately with code {poll_result}. "
                    f"STDERR: {stderr}"
                )

            print("DEBUG: GraphWalker process is running, waiting for REST service...")

            # Create event to signal when server is ready
            server_ready_event = threading.Event()

            # Try to read any output that might have been generated
            if self.process.stdout:

                def read_output(pipe, prefix, ready_event):
                    for line in iter(pipe.readline, ""):
                        if line:
                            print(f"{prefix}: {line.rstrip()}")
                            # Check if server has started
                            if "[HttpServer] Started" in line:
                                ready_event.set()

                stdout_thread = threading.Thread(
                    target=read_output,
                    args=(self.process.stdout, "GW-STDOUT", server_ready_event),
                )
                stderr_thread = threading.Thread(
                    target=read_output,
                    args=(self.process.stderr, "GW-STDERR", server_ready_event),
                )
                stdout_thread.daemon = True
                stderr_thread.daemon = True
                stdout_thread.start()
                stderr_thread.start()

            # Wait for service to be ready
            self._wait_for_ready(server_ready_event, timeout=10)

            logger.info(f"GraphWalker started on port {self.port}")

        except Exception as e:
            if self.process:
                self.process.kill()
                self.process = None
            raise GraphWalkerException(f"Failed to start GraphWalker: {e}")

    def _wait_for_ready(self, server_ready_event, timeout: int = 10):
        """Wait for GraphWalker REST service to be ready using event signaling."""
        print("DEBUG: Waiting for GraphWalker REST service to start...")
        print("DEBUG: Monitoring process output for '[HttpServer] Started' message")

        # Wait for the event with timeout
        if server_ready_event.wait(timeout):
            logger.info("GraphWalker REST service is ready")
            print("DEBUG: GraphWalker REST service is ready!")
            return

        # If we timed out, check if process is still running
        if self.process.poll() is not None:
            print("DEBUG: GraphWalker process has terminated!")
            raise GraphWalkerException("GraphWalker process terminated during startup")

        raise GraphWalkerException(
            f"GraphWalker REST service did not become ready within {timeout} seconds"
        )

    def _get_body(self, response):
        """Parse and validate GraphWalker response."""
        body = response.json()

        print(f"DEBUG [_get_body]: Full response body: {body}")
        print(f"DEBUG [_get_body]: Body keys: {list(body.keys())}")
        print(f"DEBUG [_get_body]: result = {body.get('result')}")

        if body.get("result") == "ok":
            body.pop("result")
            print(f"DEBUG [_get_body]: Result is 'ok', returning body: {body}")
            return body

        if body.get("result") == "nok":
            print(f"DEBUG [_get_body]: Result is 'nok'")
            if "error" in body:
                print(f"DEBUG [_get_body]: Error found: {body['error']}")
                raise GraphWalkerException(f"GraphWalker error: {body['error']}")
            print(f"DEBUG [_get_body]: No error field, raising generic nok exception")
            raise GraphWalkerException("GraphWalker responded with nok status")

        print(f"DEBUG [_get_body]: Result is neither 'ok' nor 'nok'")
        raise GraphWalkerException("GraphWalker did not respond with ok status")

    def has_next(self) -> bool:
        """Check if there are more steps to execute.

        Returns:
            True if there are more steps, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/hasNext")
            response.raise_for_status()
            # The hasNext endpoint returns {"hasNext":"true"} or {"hasNext":"false"}
            # without a "result" field, so we parse it directly
            body = response.json()
            has_next_value = body.get("hasNext")

            if has_next_value is None:
                raise GraphWalkerException(f"Unexpected response format: {body}")

            return has_next_value == "true"
        except requests.exceptions.RequestException as e:
            raise GraphWalkerException(f"Failed to check hasNext: {e}")
        except Exception as e:
            raise GraphWalkerException(f"Failed to check hasNext: {e}")

    def get_next(self) -> Dict[str, Any]:
        """Get the next step to execute.

        Returns:
            Step dictionary with id, name, modelName, etc.
        """
        try:
            response = requests.get(f"{self.base_url}/getNext")
            response.raise_for_status()
            raw_step = response.json()

            # Normalize the GraphWalker response format
            # GraphWalker returns: currentElementID, currentElementName, modelName
            # We need: id, name, modelName
            normalized_step = {
                "id": raw_step.get("currentElementID"),
                "name": raw_step.get("currentElementName"),
                "modelName": raw_step.get("modelName"),
            }

            # Include other fields if present
            if "data" in raw_step:
                normalized_step["data"] = raw_step["data"]
            if "properties" in raw_step:
                normalized_step["properties"] = raw_step["properties"]
            if "actions" in raw_step:
                normalized_step["actions"] = raw_step["actions"]

            return normalized_step
        except Exception as e:
            raise GraphWalkerException(f"Failed to get next step: {e}")

    def get_data(self) -> Dict[str, Any]:
        """Get current model data.

        Returns:
            Dictionary of current model data
        """
        try:
            response = requests.get(f"{self.base_url}/getData")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise GraphWalkerException(f"Failed to get data: {e}")

    def set_data(self, data: Dict[str, Any]):
        """Set model data.

        Args:
            data: Dictionary of data to set
        """
        try:
            response = requests.put(f"{self.base_url}/setData", json=data)
            response.raise_for_status()
        except Exception as e:
            raise GraphWalkerException(f"Failed to set data: {e}")

    def restart(self):
        """Restart the model execution."""
        try:
            response = requests.put(f"{self.base_url}/restart")
            response.raise_for_status()
        except Exception as e:
            raise GraphWalkerException(f"Failed to restart: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get execution statistics.

        Returns:
            Dictionary with statistics like totalNumberOfEdges, etc.
        """
        try:
            response = requests.get(f"{self.base_url}/getStatistics")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Failed to get statistics: {e}")
            return {}

    def load(self, model_data: Dict[str, Any]):
        """Load a model into GraphWalker via REST API.

        Args:
            model_data: The model JSON data to load
        """
        try:
            response = requests.post(
                f"{self.base_url}/load",
                data=json.dumps(model_data),
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            body = self._get_body(response)
            logger.info("Model loaded successfully")
            print("DEBUG: Model loaded into GraphWalker")
        except Exception as e:
            raise GraphWalkerException(f"Failed to load model: {e}")

    def kill(self):
        """Kill the GraphWalker process."""
        if self.process:
            logger.info("Killing GraphWalker process")
            self.process.kill()
            self.process.wait()
            self.process = None
