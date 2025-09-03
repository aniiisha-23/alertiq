"""
Email sender module for sending summary emails to appropriate teams.
Supports both SMTP and Gmail API for sending emails.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import config
from .models import SummaryEmail, LLMAnalysis, EmailData


class EmailSender:
    """Email sender class for sending summary emails to teams."""

    def __init__(self, use_gmail_api: bool = True):
        self.use_gmail_api = use_gmail_api
        self.service = None

        if use_gmail_api:
            self._setup_gmail_api()

    def _setup_gmail_api(self):
        """Set up Gmail API for sending emails."""
        try:
            # Create credentials from environment variables
            creds_info = {
                "client_id": config.gmail_client_id,
                "client_secret": config.gmail_client_secret,
                "refresh_token": config.gmail_refresh_token,
                "type": "authorized_user"
            }

            credentials = Credentials.from_authorized_user_info(creds_info)

            # Refresh credentials if needed
            if credentials.expired:
                credentials.refresh(Request())

            # Build the Gmail API service
            self.service = build('gmail', 'v1', credentials=credentials)
            logger.info("Gmail API service for sending initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Gmail API for sending: {e}")
            raise

    @retry(
        stop=stop_after_attempt(config.retry_attempts),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def send_summary_email(self, summary_email: SummaryEmail) -> bool:
        """
        Send summary email to the appropriate team.

        Args:
            summary_email: SummaryEmail object containing email details

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            if self.use_gmail_api:
                return self._send_via_gmail_api(summary_email)
            else:
                return self._send_via_smtp(summary_email)

        except Exception as e:
            logger.error(f"Error sending summary email: {e}")
            return False

    def _send_via_gmail_api(self, summary_email: SummaryEmail) -> bool:
        """Send email using Gmail API."""
        try:
            import base64

            # Create message
            message = MIMEMultipart()
            message['to'] = summary_email.recipient
            message['subject'] = summary_email.subject
            message['from'] = config.smtp_username

            # Add body
            body_part = MIMEText(summary_email.body, 'plain')
            message.attach(body_part)

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Send message
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"Summary email sent via Gmail API to {summary_email.recipient}")
            return True

        except Exception as e:
            logger.error(f"Error sending email via Gmail API: {e}")
            return False

    def _send_via_smtp(self, summary_email: SummaryEmail) -> bool:
        """Send email using SMTP."""
        try:
            # Create message
            message = MIMEMultipart()
            message['From'] = config.smtp_username
            message['To'] = summary_email.recipient
            message['Subject'] = summary_email.subject

            # Add body
            message.attach(MIMEText(summary_email.body, 'plain'))

            # Connect to SMTP server
            with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
                server.starttls()
                server.login(config.smtp_username, config.smtp_password)

                # Send email
                text = message.as_string()
                server.sendmail(config.smtp_username, summary_email.recipient, text)

            logger.info(f"Summary email sent via SMTP to {summary_email.recipient}")
            return True

        except Exception as e:
            logger.error(f"Error sending email via SMTP: {e}")
            return False

    def send_batch_summaries(
        self,
        original_emails: List[EmailData],
        analyses: dict[str, Optional[LLMAnalysis]]
    ) -> dict[str, bool]:
        """
        Send summary emails for a batch of analyzed emails.

        Args:
            original_emails: List of original EmailData objects
            analyses: Dictionary mapping message_id to LLMAnalysis results

        Returns:
            Dictionary mapping message_id to send success status
        """
        results = {}

        for email_data in original_emails:
            try:
                analysis = analyses.get(email_data.message_id)

                if not analysis:
                    logger.warning(f"No analysis found for email {email_data.message_id}")
                    results[email_data.message_id] = False
                    continue

                # Determine recipient team
                recipient = config.get_team_email(analysis.action.value)

                # Create summary email
                summary_email = SummaryEmail.from_analysis(
                    original_email=email_data,
                    analysis=analysis,
                    recipient=recipient
                )

                # Send summary email
                success = self.send_summary_email(summary_email)
                results[email_data.message_id] = success

            except Exception as e:
                logger.error(f"Error sending summary for email {email_data.message_id}: {e}")
                results[email_data.message_id] = False

        return results

    def send_error_notification(self, error_message: str, original_email: EmailData) -> bool:
        """
        Send error notification when processing fails.

        Args:
            error_message: Description of the error
            original_email: Original email that failed processing

        Returns:
            True if notification sent successfully
        """
        try:
            subject = f"Alert Processing Error - {original_email.subject}"

            body = f"""An error occurred while processing the following alert email:

Original Alert Subject: {original_email.subject}
Original Sender: {original_email.sender}
Received: {original_email.received_date}
Message ID: {original_email.message_id}

Error Details:
{error_message}

Please review the alert manually and take appropriate action.

---
This error notification was automatically generated by the Alert Email Processor.
"""

            # Send to backend team as default for errors
            error_notification = SummaryEmail(
                subject=subject,
                body=body,
                recipient=config.backend_team_email,
                action_type="Backend",  # Default for errors
                original_alert_subject=original_email.subject
            )

            success = self.send_summary_email(error_notification)

            if success:
                logger.info(f"Error notification sent for email {original_email.message_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
            return False

    def test_connection(self) -> bool:
        """
        Test email sending connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.use_gmail_api:
                # Test Gmail API by getting user profile
                if self.service:
                    profile = self.service.users().getProfile(userId='me').execute()
                    logger.info(f"Gmail API connection test successful for {profile.get('emailAddress')}")
                    return True
                else:
                    logger.error("Gmail API service not initialized")
                    return False
            else:
                # Test SMTP connection
                with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
                    server.starttls()
                    server.login(config.smtp_username, config.smtp_password)
                    logger.info("SMTP connection test successful")
                    return True

        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False
