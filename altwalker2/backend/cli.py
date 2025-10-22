"""Command-line interface for AltWalker2"""

import json
import logging
import multiprocessing
from pathlib import Path
from typing import List, Tuple

import click
import uvicorn

from . import __version__
from . import walker

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

CONTEXT_SETTINGS = dict(help_option_names=["--help", "-h"])


def run_server(host: str, port: int):
    """Run the FastAPI server in a separate process."""
    from .main import app

    uvicorn.run(app, host=host, port=port, log_level="info")


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__, "-v", "--version", prog_name="altwalker2")
def cli():
    """AltWalker2 - A FastAPI-based live viewer for test execution."""
    pass


@cli.command()
@click.option(
    "--host",
    "-h",
    "host",
    default="localhost",
    show_default=True,
    help="Set the binding host for the WebSocket server.",
)
@click.option(
    "--port",
    "-p",
    "port",
    default=5555,
    show_default=True,
    help="Set the port for the WebSocket server.",
)
def serve(host: str, port: int):
    """Start the WebSocket server."""
    click.secho(f"Starting server on {host}:{port}", fg="green", bold=True)
    run_server(host, port)


@cli.command()
@click.argument("test_package", type=click.Path(exists=True))
@click.option(
    "--model",
    "-m",
    "models",
    type=(click.Path(exists=True, dir_okay=False), str),
    required=True,
    multiple=True,
    help="The model as a graphml/json file followed by a generator with a stop condition.",
)
@click.option(
    "--host",
    "-h",
    "host",
    default="localhost",
    show_default=True,
    help="Set the binding host for the WebSocket server.",
)
@click.option(
    "--port",
    "-p",
    "port",
    default=5555,
    show_default=True,
    help="Set the port for the WebSocket server.",
)
@click.option(
    "--executor",
    "-x",
    "executor_type",
    default="python",
    show_default=True,
    help="Configure the executor to be used.",
)
@click.option("--executor-url", help="Sets the url for the executor.")
@click.option(
    "--start-element", "-e", help="Sets the starting element in the first model."
)
@click.option(
    "--import-mode",
    "import_mode",
    default="importlib",
    show_default=True,
    help="Sets the importing mode for the Python language.",
)
@click.option("--gw-host", help="Sets the host of the GraphWalker REST service.")
@click.option(
    "--gw-port",
    default=8887,
    show_default=True,
    help="Sets the port of the GraphWalker REST service.",
)
@click.option(
    "--blocked",
    "-b",
    default=False,
    is_flag=True,
    help="Will filter out elements with the blocked property.",
)
def online(
    test_package: str,
    models: List[Tuple[str, str]],
    host: str,
    port: int,
    executor_type: str,
    executor_url: str,
    start_element: str,
    import_mode: str,
    gw_host: str,
    gw_port: int,
    blocked: bool,
):
    """Execute tests online with GraphWalker and live viewer."""
    click.secho("Starting WebSocket server...", fg="green", bold=True)

    # Start server in separate process
    server_process = multiprocessing.Process(target=run_server, args=(host, port))
    server_process.start()

    try:
        # Give server time to start
        import time

        time.sleep(2)

        click.secho("Starting test execution...", fg="green", bold=True)
        click.secho(f"Open browser at: http://{host}:{port}", fg="cyan", bold=True)

        # Execute tests
        walker.online(
            test_package=test_package,
            models=models,
            host=host,
            port=port,
            executor_type=executor_type,
            executor_url=executor_url,
            start_element=start_element,
            import_mode=import_mode,
            gw_host=gw_host,
            gw_port=gw_port,
            blocked=blocked,
        )

        click.secho("Test execution completed!", fg="green", bold=True)

    except KeyboardInterrupt:
        click.secho("\nTest execution interrupted by user", fg="yellow")
    except Exception as e:
        click.secho(f"Error during test execution: {e}", fg="red", bold=True)
        raise
    finally:
        server_process.terminate()
        server_process.join()


@cli.command()
@click.argument("test_package", type=click.Path(exists=True))
@click.argument("steps_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--host",
    "-h",
    "host",
    default="localhost",
    show_default=True,
    help="Set the binding host for the WebSocket server.",
)
@click.option(
    "--port",
    "-p",
    "port",
    default=5555,
    show_default=True,
    help="Set the port for the WebSocket server.",
)
@click.option(
    "--executor",
    "-x",
    "executor_type",
    default="python",
    show_default=True,
    help="Configure the executor to be used.",
)
@click.option("--executor-url", help="Sets the url for the executor.")
@click.option(
    "--import-mode",
    "import_mode",
    default="importlib",
    show_default=True,
    help="Sets the importing mode for the Python language.",
)
def walk(
    test_package: str,
    steps_path: str,
    host: str,
    port: int,
    executor_type: str,
    executor_url: str,
    import_mode: str,
):
    """Execute tests from a predefined path with live viewer."""
    click.secho("Starting WebSocket server...", fg="green", bold=True)

    # Load steps from file
    with open(steps_path, "r") as f:
        steps = json.load(f)

    # Start server in separate process
    server_process = multiprocessing.Process(target=run_server, args=(host, port))
    server_process.start()

    try:
        # Give server time to start
        import time

        time.sleep(2)

        click.secho("Starting test execution...", fg="green", bold=True)
        click.secho(f"Open browser at: http://{host}:{port}", fg="cyan", bold=True)

        # Execute tests
        walker.walk(
            test_package=test_package,
            steps=steps,
            host=host,
            port=port,
            executor_type=executor_type,
            executor_url=executor_url,
            import_mode=import_mode,
        )

        click.secho("Test execution completed!", fg="green", bold=True)

    except KeyboardInterrupt:
        click.secho("\nTest execution interrupted by user", fg="yellow")
    except Exception as e:
        click.secho(f"Error during test execution: {e}", fg="red", bold=True)
        raise
    finally:
        server_process.terminate()
        server_process.join()


if __name__ == "__main__":
    cli()
