"""
Tests for the database module.
"""

import csv
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.database import EmailDatabase
from src.models import ProcessedEmail, ActionType


class TestEmailDatabase:
    """Tests for EmailDatabase class."""

    def test_database_creation(self, temp_dir):
        """Test database file creation."""
        db_path = temp_dir / "test.csv"
        db = EmailDatabase(str(db_path))

        assert db_path.exists()

        # Check headers
        with open(db_path, 'r') as file:
            reader = csv.reader(file)
            headers = next(reader)
            expected_headers = [
                'id', 'original_message_id', 'original_subject', 'original_sender',
                'processed_at', 'action_taken', 'reason', 'sent_to_team',
                'success', 'error_message'
            ]
            assert headers == expected_headers

    def test_save_processed_email(self, temp_dir):
        """Test saving a processed email record."""
        db_path = temp_dir / "test.csv"
        db = EmailDatabase(str(db_path))

        processed_email = ProcessedEmail(
            original_message_id="msg_123",
            original_subject="Test Alert",
            original_sender="test@example.com",
            action_taken=ActionType.BACKEND,
            reason="Backend issue detected",
            sent_to_team="backend@company.com"
        )

        success = db.save_processed_email(processed_email)
        assert success is True

        # Verify record was saved
        records = db.get_processed_emails()
        assert len(records) == 1
        assert records[0].original_message_id == "msg_123"
        assert records[0].action_taken == ActionType.BACKEND

    def test_check_duplicate(self, temp_dir):
        """Test duplicate checking functionality."""
        db_path = temp_dir / "test.csv"
        db = EmailDatabase(str(db_path))

        # Initially no duplicates
        assert db.check_duplicate("msg_123") is False

        # Save a record
        processed_email = ProcessedEmail(
            original_message_id="msg_123",
            original_subject="Test Alert",
            original_sender="test@example.com",
            action_taken=ActionType.BACKEND,
            reason="Backend issue",
            sent_to_team="backend@company.com"
        )
        db.save_processed_email(processed_email)

        # Now should find duplicate
        assert db.check_duplicate("msg_123") is True
        assert db.check_duplicate("msg_456") is False

    def test_get_processing_stats(self, temp_dir):
        """Test processing statistics calculation."""
        db_path = temp_dir / "test.csv"
        db = EmailDatabase(str(db_path))

        # Save test records
        records = [
            ProcessedEmail(
                original_message_id="msg_1",
                original_subject="Alert 1",
                original_sender="test@example.com",
                action_taken=ActionType.BACKEND,
                reason="Backend issue",
                sent_to_team="backend@company.com",
                success=True
            ),
            ProcessedEmail(
                original_message_id="msg_2",
                original_subject="Alert 2",
                original_sender="test@example.com",
                action_taken=ActionType.CODE,
                reason="Code issue",
                sent_to_team="dev@company.com",
                success=False
            )
        ]

        for record in records:
            db.save_processed_email(record)

        stats = db.get_processing_stats()

        assert stats['total_processed'] == 2
        assert stats['successful'] == 1
        assert stats['failed'] == 1
        assert stats['success_rate'] == 50.0
        assert 'Backend' in stats['action_breakdown']
        assert 'Code' in stats['action_breakdown']

    def test_cleanup_old_records(self, temp_dir):
        """Test cleanup of old records."""
        db_path = temp_dir / "test.csv"
        db = EmailDatabase(str(db_path))

        # Create old and new records
        old_date = datetime.now() - timedelta(days=100)
        new_date = datetime.now()

        old_record = ProcessedEmail(
            original_message_id="old_msg",
            original_subject="Old Alert",
            original_sender="test@example.com",
            processed_at=old_date,
            action_taken=ActionType.BACKEND,
            reason="Old issue",
            sent_to_team="backend@company.com"
        )

        new_record = ProcessedEmail(
            original_message_id="new_msg",
            original_subject="New Alert",
            original_sender="test@example.com",
            processed_at=new_date,
            action_taken=ActionType.CODE,
            reason="New issue",
            sent_to_team="dev@company.com"
        )

        db.save_processed_email(old_record)
        db.save_processed_email(new_record)

        # Cleanup records older than 90 days
        removed_count = db.cleanup_old_records(90)

        assert removed_count == 1

        # Verify only new record remains
        records = db.get_processed_emails()
        assert len(records) == 1
        assert records[0].original_message_id == "new_msg"
