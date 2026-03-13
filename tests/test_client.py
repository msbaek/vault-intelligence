#!/usr/bin/env python3
"""
Tests for VisClient - HTTP client for vis daemon server.
"""

import os
import signal
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import httpx

from src.client import VisClient, ServerNotRunning
from src.server import DEFAULT_PORT, PID_FILE


class TestVisClient:
    """Test cases for VisClient"""

    def test_init(self):
        """Test client initialization"""
        client = VisClient()
        assert client.host == "127.0.0.1"
        assert client.port == DEFAULT_PORT
        assert client.base_url == f"http://127.0.0.1:{DEFAULT_PORT}"

    def test_init_custom_port(self):
        """Test client initialization with custom port"""
        client = VisClient(port=9000)
        assert client.port == 9000
        assert client.base_url == "http://127.0.0.1:9000"

    def test_is_server_running_returns_false_when_no_server(self):
        """Test is_server_running returns False when no server is running"""
        # Use an unlikely port to ensure no server is running
        client = VisClient(port=59999)
        assert client.is_server_running() is False

    @patch('httpx.Client')
    def test_is_server_running_returns_true_when_server_responds(self, mock_client_class):
        """Test is_server_running returns True when server responds"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = VisClient()
        assert client.is_server_running() is True

    @patch('httpx.Client')
    def test_is_server_running_handles_connection_error(self, mock_client_class):
        """Test is_server_running handles connection errors gracefully"""
        # Mock connection error
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.side_effect = httpx.ConnectError("Connection refused")
        mock_client_class.return_value = mock_client

        client = VisClient()
        assert client.is_server_running() is False

    @patch('httpx.Client')
    def test_is_server_running_handles_timeout(self, mock_client_class):
        """Test is_server_running handles timeout gracefully"""
        # Mock timeout
        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client_class.return_value = mock_client

        client = VisClient()
        assert client.is_server_running() is False

    def test_search_raises_server_not_running_when_auto_start_false(self):
        """Test search raises ServerNotRunning when auto_start=False and no server"""
        client = VisClient(port=59999)  # Use unlikely port

        with pytest.raises(ServerNotRunning) as exc_info:
            client.search("test query", auto_start=False)

        assert "Server is not running" in str(exc_info.value)

    @patch('httpx.Client')
    def test_search_delegates_to_server(self, mock_client_class):
        """Test search delegates to server correctly"""
        # Mock server running check
        client = VisClient()

        # Mock successful search response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "path": "/vault/note1.md",
                    "score": 0.95,
                    "title": "Test Note",
                    "snippet": "Test content",
                    "rank": 1,
                    "match_type": "semantic"
                }
            ],
            "query": "test query",
            "search_method": "hybrid",
            "total": 1
        }

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Mock is_server_running to return True
        with patch.object(client, 'is_server_running', return_value=True):
            results = client.search(
                query="test query",
                top_k=5,
                threshold=0.5,
                search_method="hybrid",
                rerank=True,
                auto_start=False
            )

        # Verify results
        assert len(results) == 1
        assert results[0]["path"] == "/vault/note1.md"
        assert results[0]["score"] == 0.95

        # Verify request was made with correct parameters
        mock_client.__enter__.return_value.get.assert_called_once()
        call_args = mock_client.__enter__.return_value.get.call_args
        assert call_args[0][0].endswith("/search")
        assert call_args[1]["params"]["query"] == "test query"
        assert call_args[1]["params"]["top_k"] == 5
        assert call_args[1]["params"]["threshold"] == 0.5
        assert call_args[1]["params"]["search_method"] == "hybrid"
        assert call_args[1]["params"]["rerank"] is True

    @patch('httpx.Client')
    def test_reindex_delegates_to_server(self, mock_client_class):
        """Test reindex delegates to server correctly"""
        client = VisClient()

        # Mock successful reindex response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "document_count": 100,
            "message": "Successfully reindexed 100 documents"
        }

        mock_client = MagicMock()
        mock_client.__enter__.return_value.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Mock is_server_running and _ensure_server
        with patch.object(client, 'is_server_running', return_value=True):
            with patch.object(client, '_ensure_server'):
                result = client.reindex(force=True)

        # Verify result
        assert result["document_count"] == 100
        assert "Successfully reindexed" in result["message"]

        # Verify request was made with correct parameters
        mock_client.__enter__.return_value.post.assert_called_once()
        call_args = mock_client.__enter__.return_value.post.call_args
        assert call_args[0][0].endswith("/reindex")
        assert call_args[1]["params"]["force"] is True

    @patch('httpx.Client')
    def test_health_returns_status(self, mock_client_class):
        """Test health returns server status"""
        client = VisClient()

        # Mock successful health response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "indexed": True,
            "document_count": 100
        }

        mock_client = MagicMock()
        mock_client.__enter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = client.health()

        # Verify result
        assert result["status"] == "ok"
        assert result["indexed"] is True
        assert result["document_count"] == 100

    @patch('os.kill')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_stop_server_reads_pid_and_sends_sigterm(self, mock_read_text, mock_exists, mock_kill):
        """Test stop_server reads PID and sends SIGTERM"""
        # Mock PID file exists with PID 12345
        mock_exists.return_value = True
        mock_read_text.return_value = "12345"

        # Mock process not found after first SIGTERM (immediate success)
        mock_kill.side_effect = [None, ProcessLookupError()]

        VisClient.stop_server()

        # Verify SIGTERM was sent to correct PID
        assert mock_kill.call_count >= 1
        first_call = mock_kill.call_args_list[0]
        assert first_call[0][0] == 12345
        assert first_call[0][1] == signal.SIGTERM

    @patch('pathlib.Path.exists')
    def test_stop_server_raises_when_no_pid_file(self, mock_exists):
        """Test stop_server raises FileNotFoundError when PID file doesn't exist"""
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError):
            VisClient.stop_server()

    @patch('os.kill')
    @patch('pathlib.Path.unlink')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_stop_server_raises_when_process_not_found(self, mock_read_text, mock_exists, mock_unlink, mock_kill):
        """Test stop_server handles process not found"""
        mock_exists.return_value = True
        mock_read_text.return_value = "99999"
        mock_kill.side_effect = ProcessLookupError()

        with pytest.raises(ProcessLookupError):
            VisClient.stop_server()

        # Verify PID file was attempted to be removed
        mock_unlink.assert_called_once()

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_stop_server_raises_when_invalid_pid(self, mock_read_text, mock_exists):
        """Test stop_server raises ValueError when PID is invalid"""
        mock_exists.return_value = True
        mock_read_text.return_value = "not_a_number"

        with pytest.raises(ValueError):
            VisClient.stop_server()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
