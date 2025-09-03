"""
Tests for the models module.
"""

import pytest
from datetime import datetime

from src.models import EmailData, LLMAnalysis, ActionType, ProcessedEmail, SummaryEmail


class TestEmailData:
    """Tests for EmailData model."""

    def test_email_data_creation(self):
        """Test creating EmailData object."""
        email = EmailData(
            message_id="test_123",
            subject="Test Alert",
            sender="test@example.com",
            body="Test body content",
            received_date=datetime.now()
        )

        assert email.message_id == "test_123"
        assert email.subject == "Test Alert"
        assert email.sender == "test@example.com"
        assert email.body == "Test body content"
        assert isinstance(email.received_date, datetime)

    def test_email_data_with_labels(self):
        """Test EmailData with optional labels."""
        email = EmailData(
            message_id="test_123",
            subject="Test Alert",
            sender="test@example.com",
            body="Test body content",
            received_date=datetime.now(),
            labels=["INBOX", "UNREAD"]
        )

        assert email.labels == ["INBOX", "UNREAD"]


class TestLLMAnalysis:
    """Tests for LLMAnalysis model."""

    def test_llm_analysis_creation(self):
        """Test creating LLMAnalysis object."""
        analysis = LLMAnalysis(
            action=ActionType.BACKEND,
            reason="Database connection issue",
            confidence=0.85
        )

        assert analysis.action == ActionType.BACKEND
        assert analysis.reason == "Database connection issue"
        assert analysis.confidence == 0.85

    def test_llm_analysis_without_confidence(self):
        """Test LLMAnalysis without confidence score."""
        analysis = LLMAnalysis(
            action=ActionType.RE_HIT,
            reason="Temporary network issue"
        )

        assert analysis.action == ActionType.RE_HIT
        assert analysis.reason == "Temporary network issue"
        assert analysis.confidence is None

    def test_reason_validation(self):
        """Test reason field validation."""
        with pytest.raises(ValueError):
            LLMAnalysis(
                action=ActionType.CODE,
                reason=""  # Empty reason should fail
            )

        with pytest.raises(ValueError):
            LLMAnalysis(
                action=ActionType.CODE,
                reason="   "  # Whitespace-only reason should fail
            )

    def test_confidence_validation(self):
        """Test confidence field validation."""
        with pytest.raises(ValueError):
            LLMAnalysis(
                action=ActionType.BACKEND,
                reason="Valid reason",
                confidence=1.5  # Too high
            )

        with pytest.raises(ValueError):
            LLMAnalysis(
                action=ActionType.BACKEND,
                reason="Valid reason",
                confidence=-0.1  # Too low
            )


class TestProcessedEmail:
    """Tests for ProcessedEmail model."""

    def test_processed_email_creation(self):
        """Test creating ProcessedEmail object."""
        processed = ProcessedEmail(
            original_message_id="msg_123",
            original_subject="Test Alert",
            original_sender="test@example.com",
            action_taken=ActionType.BACKEND,
            reason="Backend issue detected",
            sent_to_team="backend@company.com"
        )

        assert processed.original_message_id == "msg_123"
        assert processed.action_taken == ActionType.BACKEND
        assert processed.success is True  # Default value
        assert processed.error_message is None
        assert isinstance(processed.processed_at, datetime)

    def test_processed_email_with_error(self):
        """Test ProcessedEmail with error information."""
        processed = ProcessedEmail(
            original_message_id="msg_123",
            original_subject="Test Alert",
            original_sender="test@example.com",
            action_taken=ActionType.BACKEND,
            reason="Failed to process",
            sent_to_team="backend@company.com",
            success=False,
            error_message="LLM analysis failed"
        )

        assert processed.success is False
        assert processed.error_message == "LLM analysis failed"


class TestSummaryEmail:
    """Tests for SummaryEmail model."""

    def test_summary_email_from_analysis(self, sample_email_data, sample_llm_analysis):
        """Test creating SummaryEmail from analysis."""
        recipient = "backend@company.com"

        summary = SummaryEmail.from_analysis(
            original_email=sample_email_data,
            analysis=sample_llm_analysis,
            recipient=recipient
        )

        assert summary.recipient == recipient
        assert summary.action_type == sample_llm_analysis.action
        assert summary.original_alert_subject == sample_email_data.subject
        assert "Alert Analysis - Action Required: Backend" in summary.subject
        assert sample_email_data.subject in summary.body
        assert sample_llm_analysis.reason in summary.body
        assert sample_email_data.sender in summary.body


class TestActionType:
    """Tests for ActionType enum."""

    def test_action_type_values(self):
        """Test ActionType enum values."""
        assert ActionType.RE_HIT.value == "Re-hit"
        assert ActionType.BACKEND.value == "Backend"
        assert ActionType.CODE.value == "Code"

    def test_action_type_from_string(self):
        """Test creating ActionType from string."""
        assert ActionType("Re-hit") == ActionType.RE_HIT
        assert ActionType("Backend") == ActionType.BACKEND
        assert ActionType("Code") == ActionType.CODE
