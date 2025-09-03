"""
Email reader module for connecting to Gmail and fetching alert emails.
Supports both Gmail API and IMAP connections.
"""

import base64
import email
import imaplib
import json
from datetime import datetime
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import config
from .models import EmailData


class EmailReader:
    """Email reader class for fetching emails from Gmail."""

    def __init__(self):
        self.service = None
        self.credentials = None
        self._setup_gmail_api()

    def _setup_gmail_api(self):
        """Set up Gmail API credentials and service."""
        try:
            # Create credentials from environment variables
            creds_info = {
                "client_id": config.gmail_client_id,
                "client_secret": config.gmail_client_secret,
                "refresh_token": config.gmail_refresh_token,
                "type": "authorized_user"
            }

            self.credentials = Credentials.from_authorized_user_info(creds_info)

            # Refresh credentials if needed
            if self.credentials.expired:
                self.credentials.refresh(Request())

            # Build the Gmail API service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            logger.info("Gmail API service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Gmail API: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def fetch_unread_emails(self, max_results: int = None) -> List[EmailData]:
        """
        Fetch unread emails from the inbox.

        Args:
            max_results: Maximum number of emails to fetch

        Returns:
            List of EmailData objects
        """
        try:
            if max_results is None:
                max_results = config.max_emails_per_batch

            # Search for unread emails in inbox
            query = "is:unread in:inbox"
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            logger.info(f"Found {len(messages)} unread emails")

            emails = []
            for message in messages:
                email_data = self._get_email_details(message['id'])
                if email_data:
                    emails.append(email_data)

            return emails

        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            raise

    def _get_email_details(self, message_id: str) -> Optional[EmailData]:
        """
        Get detailed information for a specific email.

        Args:
            message_id: Gmail message ID

        Returns:
            EmailData object or None if error
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            # Extract headers
            headers = message['payload'].get('headers', [])
            subject = self._get_header_value(headers, 'Subject') or "No Subject"
            sender = self._get_header_value(headers, 'From') or "Unknown Sender"
            date_str = self._get_header_value(headers, 'Date')

            # Parse date
            received_date = self._parse_email_date(date_str)

            # Extract body
            body = self._extract_email_body(message['payload'])

            # Get labels
            labels = message.get('labelIds', [])

            return EmailData(
                message_id=message_id,
                subject=subject,
                sender=sender,
                body=body,
                received_date=received_date,
                labels=labels
            )

        except Exception as e:
            logger.error(f"Error getting email details for {message_id}: {e}")
            return None

    def _get_header_value(self, headers: List[dict], name: str) -> Optional[str]:
        """Extract header value by name."""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return None

    def _parse_email_date(self, date_str: Optional[str]) -> datetime:
        """Parse email date string to datetime object."""
        if not date_str:
            return datetime.now()

        try:
            # Try parsing with email.utils
            import email.utils
            timestamp = email.utils.parsedate_tz(date_str)
            if timestamp:
                return datetime.fromtimestamp(email.utils.mktime_tz(timestamp))
        except Exception:
            pass

        # Fallback to current time
        return datetime.now()

    def _extract_email_body(self, payload: dict) -> str:
        """
        Extract email body from payload.

        Args:
            payload: Gmail message payload

        Returns:
            Email body text
        """
        body = ""

        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode('utf-8')
                elif part['mimeType'] == 'text/html' and not body:
                    # Fallback to HTML if no plain text
                    data = part['body'].get('data')
                    if data:
                        html_content = base64.urlsafe_b64decode(data).decode('utf-8')
                        # Simple HTML to text conversion
                        import re
                        body = re.sub(r'<[^>]+>', '', html_content)
        else:
            # Single part message
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')

        return body.strip()

    def mark_as_read(self, message_id: str) -> bool:
        """
        Mark an email as read.

        Args:
            message_id: Gmail message ID

        Returns:
            True if successful, False otherwise
        """
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()

            logger.info(f"Marked email {message_id} as read")
            return True

        except Exception as e:
            logger.error(f"Error marking email {message_id} as read: {e}")
            return False


class IMAPEmailReader:
    """Alternative IMAP-based email reader for non-Gmail providers."""

    def __init__(self, server: str, port: int, username: str, password: str):
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.connection = None

    def connect(self):
        """Connect to IMAP server."""
        try:
            self.connection = imaplib.IMAP4_SSL(self.server, self.port)
            self.connection.login(self.username, self.password)
            self.connection.select('INBOX')
            logger.info(f"Connected to IMAP server {self.server}")
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {e}")
            raise

    def fetch_unread_emails(self, max_results: int = None) -> List[EmailData]:
        """Fetch unread emails using IMAP."""
        if not self.connection:
            self.connect()

        try:
            # Search for unread emails
            status, messages = self.connection.search(None, 'UNSEEN')
            if status != 'OK':
                return []

            message_ids = messages[0].split()
            if max_results:
                message_ids = message_ids[:max_results]

            emails = []
            for msg_id in message_ids:
                email_data = self._get_imap_email_details(msg_id)
                if email_data:
                    emails.append(email_data)

            return emails

        except Exception as e:
            logger.error(f"Error fetching IMAP emails: {e}")
            return []

    def _get_imap_email_details(self, message_id: bytes) -> Optional[EmailData]:
        """Get email details using IMAP."""
        try:
            status, msg_data = self.connection.fetch(message_id, '(RFC822)')
            if status != 'OK':
                return None

            email_message = email.message_from_bytes(msg_data[0][1])

            subject = email_message.get('Subject', 'No Subject')
            sender = email_message.get('From', 'Unknown Sender')
            date_str = email_message.get('Date')

            # Parse date
            received_date = self._parse_email_date(date_str)

            # Extract body
            body = self._extract_imap_body(email_message)

            return EmailData(
                message_id=message_id.decode(),
                subject=subject,
                sender=sender,
                body=body,
                received_date=received_date
            )

        except Exception as e:
            logger.error(f"Error getting IMAP email details: {e}")
            return None

    def _extract_imap_body(self, email_message) -> str:
        """Extract body from IMAP email message."""
        body = ""

        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8')
                        break
                    except Exception:
                        continue
        else:
            try:
                body = email_message.get_payload(decode=True).decode('utf-8')
            except Exception:
                body = str(email_message.get_payload())

        return body.strip()

    def _parse_email_date(self, date_str: Optional[str]) -> datetime:
        """Parse email date string."""
        if not date_str:
            return datetime.now()

        try:
            import email.utils
            timestamp = email.utils.parsedate_tz(date_str)
            if timestamp:
                return datetime.fromtimestamp(email.utils.mktime_tz(timestamp))
        except Exception:
            pass

        return datetime.now()

    def disconnect(self):
        """Disconnect from IMAP server."""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
                logger.info("Disconnected from IMAP server")
            except Exception as e:
                logger.error(f"Error disconnecting from IMAP: {e}")
