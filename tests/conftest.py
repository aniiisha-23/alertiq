"""
Test configuration and fixtures for the Alert Email Processor test suite.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.models import EmailData, LLMAnalysis, ActionType


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_email_data():
    """Create sample email data for testing."""
    return EmailData(
        message_id="test_message_123",
        subject="Alert: Database Connection Failed",
        sender="monitoring@company.com",
        body="Database connection to prod-db-01 failed at 2025-09-03 10:30:00. Error: Connection timeout after 30 seconds.",
        received_date=datetime(2025, 9, 3, 10, 30, 0)
    )


@pytest.fixture
def sample_llm_analysis():
    """Create sample LLM analysis for testing."""
    return LLMAnalysis(
        action=ActionType.BACKEND,
        reason="Database connection timeout indicates infrastructure issue requiring backend team attention",
        confidence=0.85
    )


@pytest.fixture
def mock_gmail_service():
    """Create a mock Gmail service for testing."""
    mock_service = Mock()

    # Mock messages list response
    mock_service.users().messages().list().execute.return_value = {
        'messages': [
            {'id': 'msg_001'},
            {'id': 'msg_002'}
        ]
    }

    # Mock message get response
    mock_service.users().messages().get().execute.return_value = {
        'id': 'msg_001',
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Test Alert'},
                {'name': 'From', 'value': 'test@example.com'},
                {'name': 'Date', 'value': 'Mon, 3 Sep 2025 10:30:00 +0000'}
            ],
            'body': {
                'data': 'VGVzdCBlbWFpbCBib2R5'  # Base64 encoded "Test email body"
            },
            'mimeType': 'text/plain'
        },
        'labelIds': ['INBOX', 'UNREAD']
    }

    return mock_service


@pytest.fixture
def mock_gemini_model():
    """Create a mock Gemini model for testing."""
    mock_model = Mock()

    # Mock successful analysis response
    mock_response = Mock()
    mock_response.text = '''
    {
        "action": "Backend",
        "reason": "Database connection issue requires backend team attention",
        "confidence": 0.85
    }
    '''

    mock_model.generate_content.return_value = mock_response

    return mock_model


@pytest.fixture
def test_config():
    """Create test configuration with safe values."""
    test_env = {
        'GMAIL_CLIENT_ID': 'test_client_id',
        'GMAIL_CLIENT_SECRET': 'test_client_secret',
        'GMAIL_REFRESH_TOKEN': 'test_refresh_token',
        'GEMINI_API_KEY': 'test_api_key',
        'SMTP_USERNAME': 'test@example.com',
        'SMTP_PASSWORD': 'test_password',
        'BACKEND_TEAM_EMAIL': 'backend@company.com',
        'CODE_TEAM_EMAIL': 'dev@company.com',
        'REHIT_TEAM_EMAIL': 'ops@company.com',
        'DATABASE_PATH': 'test_data/processed_emails.csv',
        'LOG_FILE': 'test_logs/alert_processor.log',
        'CHECK_INTERVAL_MINUTES': '1',
        'MAX_EMAILS_PER_BATCH': '5'
    }

    # Temporarily set environment variables
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield test_env

    # Restore original environment
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value
