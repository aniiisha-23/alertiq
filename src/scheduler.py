"""
Scheduler module for automated alert email processing.
Provides scheduling capabilities for running the processor at regular intervals.
"""

import signal
import sys
import time
from datetime import datetime
from threading import Event, Thread
from typing import Optional

import schedule
from loguru import logger

from .config import config
from .processor import AlertEmailProcessor


class AlertEmailScheduler:
    """Scheduler for automated alert email processing."""

    def __init__(self):
        self.processor = AlertEmailProcessor()
        self.is_running = False
        self.stop_event = Event()
        self.scheduler_thread: Optional[Thread] = None
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def start_scheduled_processing(self, interval_minutes: Optional[int] = None):
        """
        Start scheduled processing of alert emails.

        Args:
            interval_minutes: Processing interval in minutes (defaults to config value)
        """
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        interval = interval_minutes or config.check_interval_minutes

        logger.info(f"Starting scheduled alert processing every {interval} minutes")

        # Clear any existing scheduled jobs
        schedule.clear()

        # Schedule the processing job
        schedule.every(interval).minutes.do(self._run_processing_cycle)

        # Run health check on startup
        self.processor.run_health_check()

        # Run initial processing
        logger.info("Running initial processing cycle...")
        self._run_processing_cycle()

        # Start the scheduler thread
        self.is_running = True
        self.scheduler_thread = Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()

        logger.info("Alert email scheduler started successfully")

    def _scheduler_loop(self):
        """Main scheduler loop that runs scheduled jobs."""
        while self.is_running and not self.stop_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(5)  # Wait before retrying

    def _run_processing_cycle(self):
        """Run a single processing cycle."""
        try:
            logger.info("Starting scheduled processing cycle")
            start_time = datetime.now()

            results = self.processor.process_alerts()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.info(f"Processing cycle completed in {duration:.2f} seconds")
            logger.info(f"Results: {results['successful_count']} successful, {results['failed_count']} failed")

            # Log any errors
            if results['errors']:
                for error in results['errors']:
                    logger.error(f"Processing error: {error}")

        except Exception as e:
            logger.error(f"Error during processing cycle: {e}")

    def stop(self):
        """Stop the scheduler gracefully."""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return

        logger.info("Stopping alert email scheduler...")

        self.is_running = False
        self.stop_event.set()

        # Clear scheduled jobs
        schedule.clear()

        # Wait for scheduler thread to finish
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)

        logger.info("Alert email scheduler stopped")

    def run_once(self):
        """Run processing once without scheduling."""
        logger.info("Running one-time alert processing...")

        # Run health check first
        if not self.processor.run_health_check():
            logger.error("Health check failed, aborting processing")
            return False

        results = self.processor.process_alerts()

        logger.info(f"One-time processing completed:")
        logger.info(f"  Processed: {results['processed_count']}")
        logger.info(f"  Successful: {results['successful_count']}")
        logger.info(f"  Failed: {results['failed_count']}")
        logger.info(f"  Duration: {results['duration_seconds']:.2f} seconds")

        return results['successful_count'] > 0 or results['processed_count'] == 0

    def run_daemon(self, interval_minutes: Optional[int] = None):
        """
        Run as a daemon process with scheduled processing.

        Args:
            interval_minutes: Processing interval in minutes
        """
        try:
            self.start_scheduled_processing(interval_minutes)

            logger.info("Alert email processor is running as daemon")
            logger.info("Press Ctrl+C to stop...")

            # Keep the main thread alive
            while self.is_running:
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Error in daemon mode: {e}")
        finally:
            self.stop()

    def get_status(self) -> dict:
        """
        Get current scheduler status.

        Returns:
            Dictionary with scheduler status information
        """
        return {
            'is_running': self.is_running,
            'scheduled_jobs': len(schedule.jobs),
            'next_run': schedule.next_run().isoformat() if schedule.jobs else None,
            'processing_stats': self.processor.get_processing_stats()
        }

    def schedule_daily_cleanup(self, hour: int = 2, minute: int = 0, days_to_keep: int = 90):
        """
        Schedule daily cleanup of old records.

        Args:
            hour: Hour to run cleanup (0-23)
            minute: Minute to run cleanup (0-59)
            days_to_keep: Number of days of records to keep
        """
        def cleanup_job():
            logger.info("Running scheduled database cleanup...")
            try:
                removed_count = self.processor.cleanup_old_records(days_to_keep)
                logger.info(f"Database cleanup completed, removed {removed_count} old records")
            except Exception as e:
                logger.error(f"Error during database cleanup: {e}")

        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(cleanup_job)
        logger.info(f"Scheduled daily cleanup at {hour:02d}:{minute:02d}")

    def schedule_health_check(self, interval_hours: int = 6):
        """
        Schedule regular health checks.

        Args:
            interval_hours: Interval between health checks in hours
        """
        def health_check_job():
            logger.info("Running scheduled health check...")
            try:
                health_status = self.processor.run_health_check()
                if not health_status:
                    logger.warning("Health check failed - some components may need attention")
            except Exception as e:
                logger.error(f"Error during health check: {e}")

        schedule.every(interval_hours).hours.do(health_check_job)
        logger.info(f"Scheduled health checks every {interval_hours} hours")


def create_systemd_service_file(
    python_path: str = "/usr/bin/python3",
    project_path: str = "/opt/alert-email-processor",
    user: str = "alertprocessor"
) -> str:
    """
    Generate a systemd service file for the alert processor.

    Args:
        python_path: Path to Python executable
        project_path: Path to the project directory
        user: User to run the service as

    Returns:
        Systemd service file content
    """
    service_content = f"""[Unit]
Description=Alert Email Processor
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=5
User={user}
WorkingDirectory={project_path}
Environment=PYTHONPATH={project_path}
ExecStart={python_path} -m src.main --daemon
StandardOutput=journal
StandardError=journal
SyslogIdentifier=alert-email-processor

[Install]
WantedBy=multi-user.target
"""
    return service_content


def create_cron_entry(
    python_path: str = "/usr/bin/python3",
    project_path: str = "/opt/alert-email-processor",
    interval_minutes: int = 5
) -> str:
    """
    Generate a cron entry for the alert processor.

    Args:
        python_path: Path to Python executable
        project_path: Path to the project directory
        interval_minutes: Processing interval in minutes

    Returns:
        Cron entry string
    """
    if interval_minutes < 60:
        cron_schedule = f"*/{interval_minutes} * * * *"
    else:
        hours = interval_minutes // 60
        cron_schedule = f"0 */{hours} * * *"

    return f"{cron_schedule} cd {project_path} && {python_path} -m src.main --once >> /var/log/alert-processor.log 2>&1"
