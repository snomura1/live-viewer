"""FastAPI Application for AltWalker2 Live Viewer"""

import json
import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .websocket_manager import manager
from . import __version__

logger = logging.getLogger(__name__)

app = FastAPI(title="AltWalker2 Live Viewer", version=__version__)


# Get the frontend directory path
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


# Mount static files for frontend
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def root():
    """Serve the main HTML page."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(), status_code=200)
    return JSONResponse(content={"error": "Frontend not found"}, status_code=404)


@app.get("/index.html")
async def serve_html():
    """Serve the main HTML page (alternative route)."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(), status_code=200)
    return JSONResponse(content={"error": "Frontend not found"}, status_code=404)


@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(content={"status": "ok"}, status_code=200)


@app.get("/versionz")
async def version_check():
    """Version information endpoint."""
    return JSONResponse(
        content={
            "version": __version__,
            "reporter_connected": manager.is_reporter_connected(),
            "viewer_connected": manager.is_viewer_connected(),
        },
        status_code=200,
    )


@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for both reporter and viewer connections."""

    # Wait for initial message to determine client type
    await websocket.accept()

    try:
        # Receive initialization message
        data = await websocket.receive_text()
        message = json.loads(data)

        if message.get("type") != "init":
            await websocket.close(code=1008, reason="Invalid initialization")
            return

        client_type = message.get("client")

        if client_type == "reporter":
            await handle_reporter_connection(websocket)
        elif client_type == "viewer":
            await handle_viewer_connection(websocket)
        else:
            await websocket.close(code=1008, reason="Unknown client type")

    except WebSocketDisconnect:
        logger.info("Client disconnected during initialization")
    except Exception as e:
        logger.error(f"Error in WebSocket endpoint: {e}")
        try:
            await websocket.close(code=1011, reason="Server error")
        except:
            pass


async def handle_reporter_connection(websocket: WebSocket):
    """Handle reporter client connection."""
    try:
        # Already accepted in websocket_endpoint
        manager.reporter = websocket
        print("DEBUG [SERVER]: Reporter connected")
        logger.info("Reporter connected")

        # Forward messages from reporter to viewer
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                print(
                    f"DEBUG [SERVER]: Received from Reporter: {message.get('type', 'unknown')}"
                )

                # Buffer start message for later viewer connection
                if message.get("type") == "start":
                    print("DEBUG [SERVER]: Buffering start message for viewer")
                    manager.start_message = message

                # Send to viewer if connected
                if manager.viewer:
                    print(
                        f"DEBUG [SERVER]: Forwarding to Viewer: {message.get('type', 'unknown')}"
                    )
                    await manager.send_to_viewer(message)
                else:
                    print("DEBUG [SERVER]: No viewer connected, cannot forward message")

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in reporter loop: {e}")
                break

    except Exception as e:
        logger.error(f"Error handling reporter: {e}")
    finally:
        manager.reporter = None
        print("DEBUG [SERVER]: Reporter disconnected")
        logger.info("Reporter disconnected")


async def handle_viewer_connection(websocket: WebSocket):
    """Handle viewer client connection."""
    try:
        # Already accepted in websocket_endpoint
        manager.viewer = websocket
        print("DEBUG [SERVER]: Viewer connected")
        logger.info("Viewer connected")

        # Send buffered start message if available
        if manager.start_message:
            print("DEBUG [SERVER]: Sending buffered start message to Viewer")
            await manager.send_to_viewer(manager.start_message)

        # Send acknowledgment to reporter if connected
        if manager.reporter:
            print("DEBUG [SERVER]: Sending 'start' acknowledgment to Reporter")
            await manager.send_to_reporter({"type": "start"})
        else:
            print("DEBUG [SERVER]: No reporter connected, cannot send acknowledgment")

        # Forward messages from viewer to reporter (usually just acks)
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                print(
                    f"DEBUG [SERVER]: Received from Viewer: {message.get('type', 'unknown')}"
                )

                # Send to reporter if connected
                if manager.reporter:
                    print(
                        f"DEBUG [SERVER]: Forwarding to Reporter: {message.get('type', 'unknown')}"
                    )
                    await manager.send_to_reporter(message)
                else:
                    print(
                        "DEBUG [SERVER]: No reporter connected, cannot forward message"
                    )

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in viewer loop: {e}")
                break

    except Exception as e:
        logger.error(f"Error handling viewer: {e}")
    finally:
        manager.viewer = None
        print("DEBUG [SERVER]: Viewer disconnected")
        logger.info("Viewer disconnected")


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=5555)
