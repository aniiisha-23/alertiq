"""
Main processor module that orchestrates the entire alert email processing workflow.
Coordinates email reading, LLM analysis, email sending, and database logging.
"""

import sys
from datetime import datetime
from typing import List, Tuple

from loguru import logger

from .config import config
from .database import EmailDatabase
from .email_reader import EmailReader
from .email_sender import EmailSender
from .llm_analyzer import LLMAnalyzer
from .models import EmailData, LLMAnalysis, ProcessedEmail


class AlertEmailProcessor:
    """Main processor class that orchestrates the alert email processing workflow."""

    def __init__(self):
        self.email_reader = EmailReader()
        self.llm_analyzer = LLMAnalyzer()
        self.email_sender = EmailSender()
        self.database = EmailDatabase()
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging for the processor."""
        # Remove default logger
        logger.remove()

        # Add console logging
        logger.add(
            sys.stdout,
            level=config.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )

        # Add file logging
        logger.add(
            config.log_file,
            level=config.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="1 day",
            retention="30 days",
            compression="zip"
        )

        logger.info("Alert Email Processor initialized")

    def process_alerts(self) -> dict:
        """
        Main method to process alert emails.

        Returns:
            Dictionary with processing results and statistics
        """
        start_time = datetime.now()
        logger.info("Starting alert email processing cycle")

        results = {
            'processed_count': 0,
            'successful_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'errors': [],
            'start_time': start_time,
            'end_time': None,
            'duration_seconds': 0
        }

        try:
            # Step 1: Fetch unread emails
            logger.info("Fetching unread emails...")
            emails = self.email_reader.fetch_unread_emails(config.max_emails_per_batch)

            if not emails:
                logger.info("No unread emails found")
                results['end_time'] = datetime.now()
                results['duration_seconds'] = (results['end_time'] - start_time).total_seconds()
                return results

            logger.info(f"Found {len(emails)} unread emails to process")

            # Step 2: Filter out already processed emails
            emails_to_process = self._filter_unprocessed_emails(emails)
            results['skipped_count'] = len(emails) - len(emails_to_process)

            if not emails_to_process:
                logger.info("All emails have already been processed")
                results['end_time'] = datetime.now()
                results['duration_seconds'] = (results['end_time'] - start_time).total_seconds()
                return results

            logger.info(f"Processing {len(emails_to_process)} new emails")

            # Step 3: Process each email
            for email_data in emails_to_process:
                try:
                    success = self._process_single_email(email_data)
                    results['processed_count'] += 1

                    if success:
                        results['successful_count'] += 1
                        # Mark email as read
                        self.email_reader.mark_as_read(email_data.message_id)
                    else:
                        results['failed_count'] += 1

                except Exception as e:
                    error_msg = f"Error processing email {email_data.message_id}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['failed_count'] += 1

            # Step 4: Log summary
            self._log_processing_summary(results)

        except Exception as e:
            error_msg = f"Critical error in alert processing: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)

        finally:
            results['end_time'] = datetime.now()
            results['duration_seconds'] = (results['end_time'] - start_time).total_seconds()

        return results

    def _filter_unprocessed_emails(self, emails: List[EmailData]) -> List[EmailData]:
        """Filter out emails that have already been processed."""
        unprocessed_emails = []

        for email_data in emails:
            if not self.database.check_duplicate(email_data.message_id):
                unprocessed_emails.append(email_data)
            else:
                logger.info(f"Skipping already processed email: {email_data.subject}")

        return unprocessed_emails

    def _process_single_email(self, email_data: EmailData) -> bool:
        """
        Process a single email through the complete workflow.

        Args:
            email_data: EmailData object to process

        Returns:
            True if processing was successful, False otherwise
        """
        try:
            logger.info(f"Processing email: {email_data.subject}")

            # Step 1: Analyze email with LLM
            analysis = self.llm_analyzer.analyze_email(email_data)

            if not analysis:
                error_msg = "LLM analysis failed"
                logger.error(f"Failed to analyze email {email_data.message_id}: {error_msg}")

                # Send error notification
                self.email_sender.send_error_notification(error_msg, email_data)

                # Save failed record
                processed_record = ProcessedEmail(
                    original_message_id=email_data.message_id,
                    original_subject=email_data.subject,
                    original_sender=email_data.sender,
                    action_taken="Backend",  # Default for failed analysis
                    reason="LLM analysis failed",
                    sent_to_team=config.backend_team_email,
                    success=False,
                    error_message=error_msg
                )
                self.database.save_processed_email(processed_record)

                return False

            # Step 2: Determine recipient team
            recipient = config.get_team_email(analysis.action.value)

            # Step 3: Send summary email
            from .models import SummaryEmail
            summary_email = SummaryEmail.from_analysis(email_data, analysis, recipient)

            email_sent = self.email_sender.send_summary_email(summary_email)

            if not email_sent:
                error_msg = "Failed to send summary email"
                logger.error(f"Failed to send summary for email {email_data.message_id}")

                # Save failed record
                processed_record = ProcessedEmail(
                    original_message_id=email_data.message_id,
                    original_subject=email_data.subject,
                    original_sender=email_data.sender,
                    action_taken=analysis.action,
                    reason=analysis.reason,
                    sent_to_team=recipient,
                    success=False,
                    error_message=error_msg
                )
                self.database.save_processed_email(processed_record)

                return False

            # Step 4: Save successful processing record
            processed_record = ProcessedEmail(
                original_message_id=email_data.message_id,
                original_subject=email_data.subject,
                original_sender=email_data.sender,
                action_taken=analysis.action,
                reason=analysis.reason,
                sent_to_team=recipient,
                success=True
            )

            self.database.save_processed_email(processed_record)

            logger.info(f"Successfully processed email {email_data.message_id} - Action: {analysis.action}")
            return True

        except Exception as e:
            error_msg = f"Unexpected error processing email: {e}"
            logger.error(f"Error processing email {email_data.message_id}: {e}")

            # Send error notification
            self.email_sender.send_error_notification(error_msg, email_data)

            # Save failed record
            processed_record = ProcessedEmail(
                original_message_id=email_data.message_id,
                original_subject=email_data.subject,
                original_sender=email_data.sender,
                action_taken="Backend",  # Default for errors
                reason="Processing error",
                sent_to_team=config.backend_team_email,
                success=False,
                error_message=error_msg
            )
            self.database.save_processed_email(processed_record)

            return False

    def _log_processing_summary(self, results: dict):
        """Log a summary of the processing results."""
        logger.info("=" * 50)
        logger.info("PROCESSING SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total processed: {results['processed_count']}")
        logger.info(f"Successful: {results['successful_count']}")
        logger.info(f"Failed: {results['failed_count']}")
        logger.info(f"Skipped (duplicates): {results['skipped_count']}")
        logger.info(f"Duration: {results['duration_seconds']:.2f} seconds")

        if results['errors']:
            logger.info(f"Errors encountered: {len(results['errors'])}")
            for error in results['errors']:
                logger.error(f"  - {error}")

        logger.info("=" * 50)

    def test_connections(self) -> dict:
        """
        Test all external connections.

        Returns:
            Dictionary with connection test results
        """
        logger.info("Testing all connections...")

        results = {
            'email_reader': False,
            'llm_analyzer': False,
            'email_sender': False,
            'database': False
        }

        # Test email reader (Gmail API)
        try:
            emails = self.email_reader.fetch_unread_emails(1)
            results['email_reader'] = True
            logger.info("✓ Email reader connection successful")
        except Exception as e:
            logger.error(f"✗ Email reader connection failed: {e}")

        # Test LLM analyzer
        try:
            # Create a test email
            test_email = EmailData(
                message_id="test",
                subject="Test Alert",
                sender="test@example.com",
                body="This is a test alert for connection testing",
                received_date=datetime.now()
            )

            # Note: This will use actual API call, so we'll just check if the analyzer is initialized
            if self.llm_analyzer.model:
                results['llm_analyzer'] = True
                logger.info("✓ LLM analyzer connection successful")
            else:
                logger.error("✗ LLM analyzer not initialized")
        except Exception as e:
            logger.error(f"✗ LLM analyzer connection failed: {e}")

        # Test email sender
        try:
            sender_test = self.email_sender.test_connection()
            results['email_sender'] = sender_test
            if sender_test:
                logger.info("✓ Email sender connection successful")
            else:
                logger.error("✗ Email sender connection failed")
        except Exception as e:
            logger.error(f"✗ Email sender connection failed: {e}")

        # Test database
        try:
            stats = self.database.get_processing_stats()
            results['database'] = True
            logger.info("✓ Database connection successful")
        except Exception as e:
            logger.error(f"✗ Database connection failed: {e}")

        return results

    def get_processing_stats(self) -> dict:
        """Get processing statistics from the database."""
        return self.database.get_processing_stats()

    def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """Clean up old processing records."""
        return self.database.cleanup_old_records(days_to_keep)

    def run_health_check(self) -> bool:
        """
        Run a comprehensive health check of the system.

        Returns:
            True if all systems are healthy, False otherwise
        """
        logger.info("Running system health check...")

        connections = self.test_connections()
        all_healthy = all(connections.values())

        if all_healthy:
            logger.info("✓ All systems healthy")
        else:
            failed_components = [k for k, v in connections.items() if not v]
            logger.error(f"✗ Health check failed for: {', '.join(failed_components)}")

        return all_healthy
