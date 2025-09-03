"""
Configuration module for the Alert Email Processor.
Handles environment variables and application settings.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Config(BaseSettings):
    """Application configuration settings."""

    # Gmail API Configuration
    gmail_client_id: str
    gmail_client_secret: str
    gmail_refresh_token: str

    # Gemini AI Configuration
    gemini_api_key: str

    # Email Configuration
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str

    # Team Email Configuration
    backend_team_email: str
    code_team_email: str
    rehit_team_email: str

    # Database Configuration
    database_path: str = "data/processed_emails.csv"

    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/alert_processor.log"

    # Processing Configuration
    check_interval_minutes: int = 5
    max_emails_per_batch: int = 10
    retry_attempts: int = 3
    retry_delay_seconds: int = 5

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }

    @field_validator("database_path", "log_file")
    @classmethod
    def create_directories(cls, v):
        """Create directories for database and log files if they don't exist."""
        path = Path(v)
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)

    def get_team_email(self, action: str) -> str:
        """Get the appropriate team email based on action type."""
        action_mapping = {
            "Re-hit": self.rehit_team_email,
            "Backend": self.backend_team_email,
            "Code": self.code_team_email,
        }
        return action_mapping.get(action, self.backend_team_email)


# Global configuration instance
config = Config()
