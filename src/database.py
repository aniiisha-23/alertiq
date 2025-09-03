"""
Database module for logging processed emails and maintaining audit trail.
Uses CSV files for simple storage and pandas for data manipulation.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from loguru import logger

from .config import config
from .models import ProcessedEmail, EmailData, LLMAnalysis


class EmailDatabase:
    """Database class for managing processed email records."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or config.database_path)
        self._ensure_database_exists()

    def _ensure_database_exists(self):
        """Create database file and directory if they don't exist."""
        try:
            # Create directory if it doesn't exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Create CSV file with headers if it doesn't exist
            if not self.db_path.exists():
                headers = [
                    'id', 'original_message_id', 'original_subject', 'original_sender',
                    'processed_at', 'action_taken', 'reason', 'sent_to_team',
                    'success', 'error_message'
                ]

                with open(self.db_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(headers)

                logger.info(f"Created database file: {self.db_path}")

        except Exception as e:
            logger.error(f"Error creating database: {e}")
            raise

    def save_processed_email(self, processed_email: ProcessedEmail) -> bool:
        """
        Save a processed email record to the database.

        Args:
            processed_email: ProcessedEmail object to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(self.db_path, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    processed_email.id,
                    processed_email.original_message_id,
                    processed_email.original_subject,
                    processed_email.original_sender,
                    processed_email.processed_at.isoformat(),
                    processed_email.action_taken.value,
                    processed_email.reason,
                    processed_email.sent_to_team,
                    processed_email.success,
                    processed_email.error_message or ""
                ])

            logger.info(f"Saved processed email record: {processed_email.id}")
            return True

        except Exception as e:
            logger.error(f"Error saving processed email: {e}")
            return False

    def save_batch_processed_emails(self, processed_emails: List[ProcessedEmail]) -> int:
        """
        Save multiple processed email records.

        Args:
            processed_emails: List of ProcessedEmail objects

        Returns:
            Number of successfully saved records
        """
        saved_count = 0

        for processed_email in processed_emails:
            if self.save_processed_email(processed_email):
                saved_count += 1

        logger.info(f"Saved {saved_count}/{len(processed_emails)} processed email records")
        return saved_count

    def get_processed_emails(
        self,
        limit: Optional[int] = None,
        action_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[ProcessedEmail]:
        """
        Retrieve processed email records with optional filtering.

        Args:
            limit: Maximum number of records to return
            action_filter: Filter by action type
            date_from: Filter records from this date
            date_to: Filter records to this date

        Returns:
            List of ProcessedEmail objects
        """
        try:
            if not self.db_path.exists():
                return []

            # Read CSV file
            df = pd.read_csv(self.db_path)

            if df.empty:
                return []

            # Apply filters
            if action_filter:
                df = df[df['action_taken'] == action_filter]

            if date_from:
                df['processed_at'] = pd.to_datetime(df['processed_at'])
                df = df[df['processed_at'] >= date_from]

            if date_to:
                if 'processed_at' not in df.columns or df['processed_at'].dtype == 'object':
                    df['processed_at'] = pd.to_datetime(df['processed_at'])
                df = df[df['processed_at'] <= date_to]

            # Apply limit
            if limit:
                df = df.tail(limit)

            # Convert to ProcessedEmail objects
            processed_emails = []
            for _, row in df.iterrows():
                try:
                    processed_email = ProcessedEmail(
                        id=str(row['id']),
                        original_message_id=str(row['original_message_id']),
                        original_subject=str(row['original_subject']),
                        original_sender=str(row['original_sender']),
                        processed_at=pd.to_datetime(row['processed_at']).to_pydatetime(),
                        action_taken=str(row['action_taken']),
                        reason=str(row['reason']),
                        sent_to_team=str(row['sent_to_team']),
                        success=bool(row['success']),
                        error_message=str(row['error_message']) if pd.notna(row['error_message']) else None
                    )
                    processed_emails.append(processed_email)
                except Exception as e:
                    logger.warning(f"Error parsing row: {e}")
                    continue

            return processed_emails

        except Exception as e:
            logger.error(f"Error retrieving processed emails: {e}")
            return []

    def get_processing_stats(self) -> dict:
        """
        Get statistics about processed emails.

        Returns:
            Dictionary with processing statistics
        """
        try:
            if not self.db_path.exists():
                return {}

            df = pd.read_csv(self.db_path)

            if df.empty:
                return {}

            # Calculate statistics
            total_processed = len(df)
            successful = len(df[df['success'] == True])
            failed = len(df[df['success'] == False])

            # Action breakdown
            action_counts = df['action_taken'].value_counts().to_dict()

            # Team distribution
            team_counts = df['sent_to_team'].value_counts().to_dict()

            # Recent activity (last 24 hours)
            df['processed_at'] = pd.to_datetime(df['processed_at'])
            recent_cutoff = datetime.now() - pd.Timedelta(days=1)
            recent_processed = len(df[df['processed_at'] >= recent_cutoff])

            return {
                'total_processed': total_processed,
                'successful': successful,
                'failed': failed,
                'success_rate': (successful / total_processed * 100) if total_processed > 0 else 0,
                'action_breakdown': action_counts,
                'team_distribution': team_counts,
                'recent_24h': recent_processed
            }

        except Exception as e:
            logger.error(f"Error calculating processing stats: {e}")
            return {}

    def check_duplicate(self, message_id: str) -> bool:
        """
        Check if an email has already been processed.

        Args:
            message_id: Email message ID to check

        Returns:
            True if email has been processed, False otherwise
        """
        try:
            if not self.db_path.exists():
                return False

            df = pd.read_csv(self.db_path)

            if df.empty:
                return False

            return message_id in df['original_message_id'].values

        except Exception as e:
            logger.error(f"Error checking for duplicate: {e}")
            return False

    def create_processed_email_record(
        self,
        original_email: EmailData,
        analysis: LLMAnalysis,
        sent_to_team: str,
        success: bool,
        error_message: Optional[str] = None
    ) -> ProcessedEmail:
        """
        Create a ProcessedEmail record from components.

        Args:
            original_email: Original EmailData object
            analysis: LLMAnalysis result
            sent_to_team: Team email that received the summary
            success: Whether processing was successful
            error_message: Error message if processing failed

        Returns:
            ProcessedEmail object
        """
        return ProcessedEmail(
            original_message_id=original_email.message_id,
            original_subject=original_email.subject,
            original_sender=original_email.sender,
            action_taken=analysis.action,
            reason=analysis.reason,
            sent_to_team=sent_to_team,
            success=success,
            error_message=error_message
        )

    def export_to_excel(self, output_path: str) -> bool:
        """
        Export processed emails to Excel file.

        Args:
            output_path: Path for the Excel file

        Returns:
            True if export successful, False otherwise
        """
        try:
            if not self.db_path.exists():
                logger.warning("Database file does not exist")
                return False

            df = pd.read_csv(self.db_path)
            df.to_excel(output_path, index=False)

            logger.info(f"Exported processed emails to: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return False

    def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """
        Remove old processed email records.

        Args:
            days_to_keep: Number of days of records to keep

        Returns:
            Number of records removed
        """
        try:
            if not self.db_path.exists():
                return 0

            df = pd.read_csv(self.db_path)

            if df.empty:
                return 0

            # Calculate cutoff date
            cutoff_date = datetime.now() - pd.Timedelta(days=days_to_keep)

            # Filter records
            df['processed_at'] = pd.to_datetime(df['processed_at'])
            initial_count = len(df)
            df_filtered = df[df['processed_at'] >= cutoff_date]

            # Save filtered data
            df_filtered.to_csv(self.db_path, index=False)

            removed_count = initial_count - len(df_filtered)
            logger.info(f"Cleaned up {removed_count} old records (older than {days_to_keep} days)")

            return removed_count

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0
