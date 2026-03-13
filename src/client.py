#!/usr/bin/env python3
"""
HTTP thin client for Vault Intelligence System V2 daemon server.

This client communicates with the vis server running as a separate process,
automatically starting it if needed.
"""

import sys
import time
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

import httpx

from .server import DEFAULT_PORT, PID_FILE

logger = logging.getLogger(__name__)


class ServerNotRunning(Exception):
    """Exception raised when server is not running and auto_start=False"""
    pass


class VisClient:
    """HTTP client for vis daemon server"""

    def __init__(self, host: str = "127.0.0.1", port: int = DEFAULT_PORT):
        """
        Initialize VisClient.

        Args:
            host: Server host
            port: Server port
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"

    def is_server_running(self) -> bool:
        """
        Check if server is running by calling /health endpoint.

        Returns:
            True if server is running and responsive, False otherwise
        """
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError):
            return False

    def _start_server(self) -> None:
        """
        Start server as background process.

        Raises:
            RuntimeError: If server fails to start within 30 seconds
        """
        logger.info(f"Starting vis server on {self.host}:{self.port}...")

        # Start server process
        cmd = [
            sys.executable,
            "-m",
            "src.server_runner",
            "--host", self.host,
            "--port", str(self.port)
        ]

        try:
            # Start process in new session (detached)
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            logger.info(f"Server process started with PID: {process.pid}")

        except Exception as e:
            raise RuntimeError(f"Failed to start server process: {e}")

        # Wait for server to be ready (up to 30 seconds)
        max_wait = 30
        start_time = time.time()

        while time.time() - start_time < max_wait:
            if self.is_server_running():
                logger.info("✅ Server is ready")
                return

            time.sleep(0.5)

        raise RuntimeError(f"Server failed to start within {max_wait} seconds")

    def _ensure_server(self) -> None:
        """
        Ensure server is running, start if needed.

        Raises:
            RuntimeError: If server fails to start
        """
        if not self.is_server_running():
            self._start_server()

    def search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.0,
        search_method: str = "hybrid",
        rerank: bool = False,
        auto_start: bool = True
    ) -> List[Dict]:
        """
        Execute search query.

        Args:
            query: Search query
            top_k: Number of results to return
            threshold: Similarity threshold
            search_method: Search method (semantic, keyword, hybrid, colbert)
            rerank: Enable reranking
            auto_start: Auto-start server if not running

        Returns:
            List of search result dictionaries

        Raises:
            ServerNotRunning: If server is not running and auto_start=False
            httpx.HTTPError: If request fails
        """
        if not self.is_server_running():
            if not auto_start:
                raise ServerNotRunning("Server is not running. Start with auto_start=True or manually start the server.")
            self._ensure_server()

        # Build query parameters
        params = {
            "query": query,
            "top_k": top_k,
            "threshold": threshold,
            "search_method": search_method,
            "rerank": rerank
        }

        # Execute request
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{self.base_url}/search", params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])

    def reindex(self, force: bool = False) -> Dict:
        """
        Trigger reindexing.

        Args:
            force: Force rebuild index

        Returns:
            Reindex response dictionary

        Raises:
            httpx.HTTPError: If request fails
        """
        # Ensure server is running
        self._ensure_server()

        # Execute request
        params = {"force": force}
        with httpx.Client(timeout=300.0) as client:  # Long timeout for reindexing
            response = client.post(f"{self.base_url}/reindex", params=params)
            response.raise_for_status()
            return response.json()

    def health(self) -> Dict:
        """
        Get server health status.

        Returns:
            Health status dictionary

        Raises:
            httpx.HTTPError: If request fails
        """
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()

    @staticmethod
    def stop_server() -> None:
        """
        Stop running server by sending SIGTERM to PID from file.

        Raises:
            FileNotFoundError: If PID file doesn't exist
            ProcessLookupError: If process doesn't exist
        """
        import os
        import signal

        if not PID_FILE.exists():
            raise FileNotFoundError(f"PID file not found: {PID_FILE}")

        try:
            pid = int(PID_FILE.read_text().strip())
            logger.info(f"Stopping server process (PID: {pid})...")

            # Send SIGTERM
            os.kill(pid, signal.SIGTERM)

            # Wait for process to exit (up to 10 seconds)
            max_wait = 10
            start_time = time.time()

            while time.time() - start_time < max_wait:
                try:
                    # Check if process still exists
                    os.kill(pid, 0)
                    time.sleep(0.2)
                except ProcessLookupError:
                    logger.info("✅ Server stopped successfully")
                    return

            logger.warning("⚠️  Server did not stop gracefully, may still be running")

        except ValueError as e:
            raise ValueError(f"Invalid PID in file: {e}")
        except ProcessLookupError:
            logger.warning("Process not found, removing stale PID file")
            PID_FILE.unlink()
            raise
