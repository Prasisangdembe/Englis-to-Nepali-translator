import argparse
import subprocess
import sys

from api.app import app
from config.settings import config
from scripts.init_db import main as init_db_main


def run_dev_server() -> None:
    """Run Flask development server."""
    app.run(host=config.API_HOST, port=config.API_PORT, debug=config.DEBUG)


def run_prod_server() -> None:
    """Run production server using gunicorn."""
    command = [
        "gunicorn",
        "--bind",
        f"{config.API_HOST}:{config.API_PORT}",
        "api.app:app",
    ]
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print("Error: gunicorn is not installed or not available in PATH.")
        print("Install dependencies with: pip install -r requirements.txt")
        raise SystemExit(1)
    except subprocess.CalledProcessError as exc:
        print(f"Gunicorn exited with code {exc.returncode}.")
        raise SystemExit(exc.returncode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="English to Limbu translation system entry point."
    )
    parser.add_argument(
        "command",
        choices=["init-db", "run-dev", "run-prod"],
        help="Command to execute.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.command == "init-db":
        init_db_main()
    elif args.command == "run-dev":
        run_dev_server()
    elif args.command == "run-prod":
        run_prod_server()
    else:
        print(f"Unknown command: {args.command}")
        raise SystemExit(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(130)
