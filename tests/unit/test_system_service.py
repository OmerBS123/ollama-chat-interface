"""
Unit tests for system_service module.

Tests system operations including app shutdown and Ollama daemon management.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from src.services.system_service import (
    check_ollama_running,
    get_ollama_pid,
    shutdown_app,
    stop_ollama_daemon,
)


class TestShutdownApp:
    """Tests for shutdown_app function."""

    @pytest.mark.asyncio
    async def test_shutdown_app_with_default_delay(self):
        """Test app shutdown with default delay."""
        with patch("sys.exit") as mock_exit:
            # Should exit with code 0 after delay
            asyncio.create_task(shutdown_app())
            await asyncio.sleep(1.1)  # Wait for default 1 second delay
            mock_exit.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test_shutdown_app_with_custom_delay(self):
        """Test app shutdown with custom delay."""
        with patch("sys.exit") as mock_exit:
            asyncio.create_task(shutdown_app(delay_seconds=0.5))
            await asyncio.sleep(0.6)  # Wait for custom delay
            mock_exit.assert_called_once_with(0)


class TestOllamaDaemonManagement:
    """Tests for Ollama daemon management functions."""

    @patch("subprocess.run")
    def test_get_ollama_pid_found(self, mock_run):
        """Test getting Ollama PID when daemon is running."""
        # Mock lsof output with PID
        mock_run.return_value = MagicMock(stdout="12345\n", returncode=0)

        pid = get_ollama_pid()

        assert pid == 12345
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_get_ollama_pid_not_found(self, mock_run):
        """Test getting Ollama PID when daemon is not running."""
        # Mock lsof output with no process
        mock_run.return_value = MagicMock(stdout="", returncode=1)

        pid = get_ollama_pid()

        assert pid is None

    @patch("subprocess.run")
    def test_check_ollama_running_true(self, mock_run):
        """Test checking if Ollama is running (returns True)."""
        mock_run.return_value = MagicMock(stdout="12345\n", returncode=0)

        is_running = check_ollama_running()

        assert is_running is True

    @patch("subprocess.run")
    def test_check_ollama_running_false(self, mock_run):
        """Test checking if Ollama is running (returns False)."""
        mock_run.return_value = MagicMock(stdout="", returncode=1)

        is_running = check_ollama_running()

        assert is_running is False

    @patch("src.services.system_service.get_ollama_pid")
    @patch("subprocess.run")
    def test_stop_ollama_daemon_success(self, mock_run, mock_get_pid):
        """Test successfully stopping Ollama daemon."""
        # Mock successful PID discovery and kill
        mock_get_pid.return_value = 12345
        mock_run.return_value = MagicMock(returncode=0)

        success, message = stop_ollama_daemon()

        assert success is True
        assert "12345" in message
        assert "stopped" in message.lower()

    @patch("src.services.system_service.get_ollama_pid")
    def test_stop_ollama_daemon_not_running(self, mock_get_pid):
        """Test stopping Ollama when it's not running."""
        mock_get_pid.return_value = None

        success, message = stop_ollama_daemon()

        assert success is False
        assert "not running" in message.lower()

    @patch("src.services.system_service.get_ollama_pid")
    @patch("subprocess.run")
    def test_stop_ollama_daemon_failure(self, mock_run, mock_get_pid):
        """Test failure when stopping Ollama daemon."""
        # Mock PID found but kill fails
        mock_get_pid.return_value = 12345
        mock_run.side_effect = Exception("Permission denied")

        success, message = stop_ollama_daemon()

        assert success is False
        assert "error" in message.lower() or "failed" in message.lower()


@pytest.mark.unit
def test_module_exports():
    """Test that all expected functions are exported."""
    from src.services import system_service

    assert hasattr(system_service, "shutdown_app")
    assert hasattr(system_service, "stop_ollama_daemon")
    assert hasattr(system_service, "check_ollama_running")
    assert hasattr(system_service, "get_ollama_pid")
