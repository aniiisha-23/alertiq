"""
Tests for the configuration module.
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.config import Config


class TestConfig:
    """Tests for Config class."""

    def test_config_creation_with_env(self, test_config):
        """Test creating config with environment variables."""
        config = Config()

        assert config.gmail_client_id == "test_client_id"
        assert config.gemini_api_key == "test_api_key"
        assert config.backend_team_email == "backend@company.com"
        assert config.check_interval_minutes == 1
        assert config.max_emails_per_batch == 5

    def test_get_team_email(self, test_config):
        """Test getting team email based on action."""
        config = Config()

        assert config.get_team_email("Re-hit") == "ops@company.com"
        assert config.get_team_email("Backend") == "backend@company.com"
        assert config.get_team_email("Code") == "dev@company.com"
        assert config.get_team_email("Unknown") == "backend@company.com"  # Default

    def test_directory_creation(self, test_config, temp_dir):
        """Test that directories are created for database and log files."""
        db_path = temp_dir / "data" / "test.csv"
        log_path = temp_dir / "logs" / "test.log"

        # Set environment variables to use temp directory
        os.environ["DATABASE_PATH"] = str(db_path)
        os.environ["LOG_FILE"] = str(log_path)

        config = Config()

        # Check that parent directories were created
        assert db_path.parent.exists()
        assert log_path.parent.exists()
        assert config.database_path == str(db_path)
        assert config.log_file == str(log_path)


class TestConfigDefaults:
    """Tests for Config default values."""

    def test_default_values(self, test_config):
        """Test that default values are set correctly."""
        config = Config()

        assert config.smtp_server == "smtp.gmail.com"
        assert config.smtp_port == 587
        assert config.log_level == "INFO"
        assert config.retry_attempts == 3
        assert config.retry_delay_seconds == 5
