# AltWalker2 Live Viewer

A modern, FastAPI-based live viewer for AltWalker test execution with real-time graph visualization.

## Features

- **Real-time Visualization**: Watch your test execution in real-time with interactive graph visualization
- **Modern UI**: Clean, responsive interface built with Tailwind CSS
- **Graph Visualization**: Powered by AntV G6 for smooth, interactive graph rendering
- **WebSocket Communication**: Fast, bidirectional communication between test runner and viewer
- **Statistics Tracking**: Comprehensive test execution statistics including coverage metrics
- **Error Reporting**: Detailed error messages and stack traces

## Installation

### Prerequisites

- Python 3.8 or higher
- AltWalker installed and configured

### Install from source

```bash
cd altwalker2
pip install -e .
```

Or install dependencies directly:

```bash
pip install -r requirements.txt
```

## Usage

### Start the WebSocket Server

To start only the server:

```bash
cd altwalker2
python run_server.py --host localhost --port 5555
```

Or simply:

```bash
cd altwalker2
python run_server.py
```

Then open your browser at `http://localhost:5555`

### Run Tests with Live Viewer (Online Mode)

Execute tests with GraphWalker and view them live:

```bash
cd altwalker2
python run_online.py tests/ -m models/model.json "random(never)"
```

Example with actual paths:

```bash
cd altwalker2
python run_online.py ../example/tests -m ../example/models/default.json "random(never)"
```

Options:
- `-m, --model`: Model file path and generator (required, can be specified multiple times)
- `--host`: Server host (default: localhost)
- `--port`: Server port (default: 5555)
- `-x, --executor`: Test executor type (default: python)
- `--executor-url`: Executor URL (optional)
- `-e, --start-element`: Starting element in the model
- `--import-mode`: Python import mode (default: importlib)
- `--gw-host`: GraphWalker REST service host
- `--gw-port`: GraphWalker REST service port (default: 8888)
- `-b, --blocked`: Filter out blocked elements

### Run Tests from Predefined Path (Walk Mode)

Execute tests from a steps file:

```bash
altwalker2 walk tests/ steps.json --host localhost --port 5555
```

Options:
- `--host`: Server host (default: localhost)
- `--port`: Server port (default: 5555)
- `-x, --executor`: Test executor type (default: python)
- `--executor-url`: Executor URL (optional)
- `--import-mode`: Python import mode (default: importlib)

## Architecture

### Backend (FastAPI + WebSocket)

- **FastAPI Application**: Serves the frontend and handles WebSocket connections
- **WebSocket Manager**: Manages connections between reporter (test runner) and viewer (browser)
- **Reporter**: Integrates with AltWalker to send test execution events
- **Walker**: Executes tests using AltWalker's executor and planner

### Frontend (Vanilla JavaScript)

- **Graph Visualizer**: Uses AntV G6 for interactive graph visualization
- **WebSocket Client**: Handles real-time communication with the server
- **UI Manager**: Manages all UI components and user interactions
- **Main Application**: Coordinates all components and handles message flow

## Project Structure

```
altwalker2/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── websocket_manager.py # WebSocket connection management
│   ├── reporter.py          # AltWalker reporter implementation
│   ├── walker.py            # Test execution logic
│   └── cli.py              # CLI commands
├── frontend/
│   ├── index.html          # Main HTML page
│   └── js/
│       ├── graph.js        # G6 graph visualization
│       ├── websocket.js    # WebSocket client
│       ├── ui.js           # UI management
│       └── main.js         # Application entry point
├── pyproject.toml          # Project configuration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Development

### Running in Development Mode

1. Start the server:
```bash
python -m altwalker2.backend.main
```

2. Open `http://localhost:5555` in your browser

### Building and Testing

The frontend uses CDN-hosted libraries, so no build step is required for development.

## License

MIT License

## Credits

This project is inspired by AltWalker's Live Viewer but is a complete rewrite using modern technologies:

- **FastAPI**: Web framework
- **AntV G6**: Graph visualization
- **Tailwind CSS**: Styling
- **AltWalker**: Test execution framework

## Differences from Original

This implementation differs from the original altwalker-live-viewer:

1. **Framework**: FastAPI instead of websockets library directly
2. **Graph Library**: AntV G6 instead of model-visualizer
3. **Styling**: Tailwind CSS instead of Bootstrap
4. **Code**: Completely rewritten to avoid GPL license conflicts
5. **Architecture**: Modern, modular JavaScript instead of monolithic implementation



----


python -m altwalker2.backend.main
