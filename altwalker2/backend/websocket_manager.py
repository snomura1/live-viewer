"""WebSocket Connection Manager for AltWalker2"""

import asyncio
import json
import logging
from typing import Optional
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections between reporter and viewer clients."""

    def __init__(self):
        self.reporter: Optional[WebSocket] = None
        self.viewer: Optional[WebSocket] = None
        self.reporter_lock = asyncio.Lock()
        self.viewer_lock = asyncio.Lock()
        self.start_message: Optional[dict] = None  # Buffer for start message

    async def connect_reporter(self, websocket: WebSocket):
        """Connect a reporter client."""
        async with self.reporter_lock:
            if self.reporter is not None:
                await websocket.close(code=1008, reason="Reporter already connected")
                raise ValueError("Reporter already connected")

            await websocket.accept()
            self.reporter = websocket
            logger.info("Reporter connected")

    async def connect_viewer(self, websocket: WebSocket):
        """Connect a viewer client."""
        async with self.viewer_lock:
            if self.viewer is not None:
                await websocket.close(code=1008, reason="Viewer already connected")
                raise ValueError("Viewer already connected")

            await websocket.accept()
            self.viewer = websocket
            logger.info("Viewer connected")

    async def disconnect_reporter(self):
        """Disconnect the reporter client."""
        async with self.reporter_lock:
            if self.reporter:
                try:
                    await self.reporter.close()
                except Exception as e:
                    logger.error(f"Error closing reporter connection: {e}")
                self.reporter = None
                logger.info("Reporter disconnected")

    async def disconnect_viewer(self):
        """Disconnect the viewer client."""
        async with self.viewer_lock:
            if self.viewer:
                try:
                    await self.viewer.close()
                except Exception as e:
                    logger.error(f"Error closing viewer connection: {e}")
                self.viewer = None
                logger.info("Viewer disconnected")

    async def send_to_viewer(self, message: dict):
        """Send a message to the viewer."""
        if self.viewer:
            try:
                await self.viewer.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to viewer: {e}")
                await self.disconnect_viewer()

    async def send_to_reporter(self, message: dict):
        """Send a message to the reporter."""
        if self.reporter:
            try:
                await self.reporter.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to reporter: {e}")
                await self.disconnect_reporter()

    async def wait_for_viewer(self, timeout: float = 60.0):
        """Wait for viewer to connect."""
        start_time = asyncio.get_event_loop().time()
        while self.viewer is None:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("Viewer connection timeout")
            await asyncio.sleep(0.1)

    async def wait_for_reporter(self, timeout: float = 60.0):
        """Wait for reporter to connect."""
        start_time = asyncio.get_event_loop().time()
        while self.reporter is None:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("Reporter connection timeout")
            await asyncio.sleep(0.1)

    def is_reporter_connected(self) -> bool:
        """Check if reporter is connected."""
        return self.reporter is not None

    def is_viewer_connected(self) -> bool:
        """Check if viewer is connected."""
        return self.viewer is not None


# Global connection manager instance
manager = ConnectionManager()
