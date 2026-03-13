#!/usr/bin/env python3
"""Entry point for running the server as a separate process."""

import argparse
from src.server import run_server, DEFAULT_PORT

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run Vault Intelligence Server as a daemon process"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to bind to (default: {DEFAULT_PORT})"
    )
    args = parser.parse_args()

    run_server(host=args.host, port=args.port)
