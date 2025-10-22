"""AltWalker Reporter implementation for WebSocket communication"""

import asyncio
import datetime
import json
import logging
from typing import Optional, Dict, Any
from websockets.sync.client import connect as sync_connect

logger = logging.getLogger(__name__)


class WebSocketReporter:
    """Reporter that sends test execution events via WebSocket."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5555,
        models_data: Optional[list] = None,
    ):
        """Initialize the WebSocket reporter.

        Args:
            host: WebSocket server host
            port: WebSocket server port
            models_data: List of model definitions (graphs)
        """
        self.host = host
        self.port = port
        self.models_data = models_data
        self.websocket = None
        self.connected = False

    def _connect(self):
        """Establish WebSocket connection."""
        try:
            print(f"DEBUG: Attempting to connect to ws://{self.host}:{self.port}/")
            self.websocket = sync_connect(f"ws://{self.host}:{self.port}/")
            print("DEBUG: WebSocket connected, sending init message")
            self.websocket.send(json.dumps({"type": "init", "client": "reporter"}))
            self.connected = True
            print(
                f"DEBUG: Successfully connected to WebSocket server at {self.host}:{self.port}"
            )
            logger.info(f"Connected to WebSocket server at {self.host}:{self.port}")
        except Exception as e:
            print(f"DEBUG: Failed to connect: {e}")
            logger.error(f"Failed to connect to WebSocket server: {e}")
            raise

    def _send_message(self, message: Dict[str, Any]):
        """Send a message through the WebSocket.

        Args:
            message: Dictionary message to send
        """
        if not self.connected or not self.websocket:
            logger.error("Not connected to WebSocket server")
            return

        try:
            self.websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

    def _receive_message(self, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Receive a message from the WebSocket.

        Args:
            timeout: Timeout in seconds

        Returns:
            Parsed message dictionary or None
        """
        if not self.connected or not self.websocket:
            return None

        try:
            data = self.websocket.recv(timeout=timeout)
            return json.loads(data)
        except TimeoutError:
            logger.warning("Timeout waiting for message")
            return None
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None

    def start(self, message: Optional[str] = None):
        """Report the start of a test run.

        Args:
            message: Optional start message
        """
        print("DEBUG: start() called")
        self._connect()

        start_message = {"type": "start", "models": self.models_data or []}
        print(f"DEBUG: Sending start message with {len(self.models_data or [])} models")

        if message:
            start_message["message"] = message

        self._send_message(start_message)
        print("DEBUG: Start message sent, waiting for viewer response...")

        # Wait for viewer acknowledgment
        logger.info("Waiting for viewer to connect...")
        response = self._receive_message()
        print(f"DEBUG: Received response: {response}")

        if response and response.get("type") == "start":
            print("DEBUG: Viewer acknowledged start")
            logger.info("Viewer connected and ready")
        else:
            print(f"DEBUG: Unexpected or no response from viewer: {response}")
            logger.warning("Unexpected response from viewer")

    def end(
        self,
        message: Optional[str] = None,
        statistics: Optional[Dict] = None,
        status: Optional[bool] = None,
    ):
        """Report the end of a test run.

        Args:
            message: Optional end message
            statistics: Test execution statistics
            status: Overall test status (True = passed, False = failed)
        """
        end_message = {
            "type": "end",
            "statistics": statistics or {},
            "status": status if status is not None else True,
        }

        if message:
            end_message["message"] = message

        self._send_message(end_message)

        if self.websocket:
            self.websocket.close()
            self.connected = False
            logger.info("WebSocket connection closed")

    def step_start(self, step: Dict[str, Any]):
        """Report the start of a step execution.

        Args:
            step: Step information dictionary
        """
        self._send_message({"type": "step-start", "step": step})

    def step_end(self, step: Dict[str, Any], result: Dict[str, Any]):
        print("asdfad----===", step)
        """Report the end of a step execution.

        Args:
            step: Step information dictionary
            result: Step execution result
        """
        # Add step ID to result
        result_copy = result.copy()
        result_copy["id"] = step.get("id")

        # Format output with timestamp and context
        output = result_copy.get("output", "")
        if step.get("modelName"):
            formatted_output = f"[{datetime.datetime.now()}] {step['modelName']}.{step['name']}:\n{output}"
        else:
            formatted_output = f"[{datetime.datetime.now()}] {step['name']}\n{output}"

        result_copy["output"] = formatted_output

        self._send_message({"type": "step-end", "result": result_copy})

    def error(self, step: Dict[str, Any], message: str, trace: Optional[str] = None):
        """Report an error during test execution.

        Args:
            step: Step information where error occurred
            message: Error message
            trace: Optional error traceback
        """
        error_message = {"type": "error", "step": step, "message": message}

        if trace:
            error_message["trace"] = trace

        self._send_message(error_message)
