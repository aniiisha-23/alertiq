"""
Main entry point for AlertIQ.
Provides command-line interface for running the system in different modes.
"""

import argparse
import sys
from pathlib import Path

from loguru import logger

from .scheduler import AlertEmailScheduler


def main():
    """Main entry point for AlertIQ."""
    parser = argparse.ArgumentParser(
        description="AlertIQ - Intelligent AI-powered alert email processing and routing system"
    )

    parser.add_argument(
        "--mode",
        choices=["once", "daemon", "test", "stats", "cleanup"],
        default="once",
        help="Operation mode (default: once)"
    )

    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as daemon process (shortcut for --mode daemon)"
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (shortcut for --mode once)"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Test connections and exit (shortcut for --mode test)"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Processing interval in minutes (for daemon mode)"
    )

    parser.add_argument(
        "--cleanup-days",
        type=int,
        default=90,
        help="Number of days to keep in cleanup mode (default: 90)"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="AlertIQ v0.1.0"
    )

    args = parser.parse_args()

    # Determine mode from arguments
    if args.daemon:
        mode = "daemon"
    elif args.once:
        mode = "once"
    elif args.test:
        mode = "test"
    else:
        mode = args.mode

    # Configure logging level
    logger.remove()
    logger.add(
        sys.stdout,
        level=args.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )

    try:
        scheduler = AlertEmailScheduler()

        if mode == "once":
            logger.info("Running alert processing once...")
            success = scheduler.run_once()
            sys.exit(0 if success else 1)

        elif mode == "daemon":
            logger.info("Starting alert processor in daemon mode...")
            scheduler.run_daemon(args.interval)

        elif mode == "test":
            logger.info("Testing system connections...")
            connections = scheduler.processor.test_connections()

            print("\nConnection Test Results:")
            print("=" * 30)
            for component, status in connections.items():
                status_symbol = "✓" if status else "✗"
                print(f"{status_symbol} {component.replace('_', ' ').title()}: {'OK' if status else 'FAILED'}")

            all_ok = all(connections.values())
            print(f"\nOverall Status: {'✓ ALL SYSTEMS OK' if all_ok else '✗ SOME SYSTEMS FAILED'}")
            sys.exit(0 if all_ok else 1)

        elif mode == "stats":
            logger.info("Retrieving processing statistics...")
            stats = scheduler.processor.get_processing_stats()

            if not stats:
                print("No processing statistics available.")
                sys.exit(0)

            print("\nProcessing Statistics:")
            print("=" * 30)
            print(f"Total Processed: {stats.get('total_processed', 0)}")
            print(f"Successful: {stats.get('successful', 0)}")
            print(f"Failed: {stats.get('failed', 0)}")
            print(f"Success Rate: {stats.get('success_rate', 0):.1f}%")
            print(f"Recent (24h): {stats.get('recent_24h', 0)}")

            if stats.get('action_breakdown'):
                print("\nAction Breakdown:")
                for action, count in stats['action_breakdown'].items():
                    print(f"  {action}: {count}")

            if stats.get('team_distribution'):
                print("\nTeam Distribution:")
                for team, count in stats['team_distribution'].items():
                    print(f"  {team}: {count}")

        elif mode == "cleanup":
            logger.info(f"Cleaning up records older than {args.cleanup_days} days...")
            removed_count = scheduler.processor.cleanup_old_records(args.cleanup_days)
            print(f"Cleaned up {removed_count} old records.")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


def create_sample_env():
    """Create a sample .env file with placeholder values."""
    env_path = Path(".env")

    if env_path.exists():
        print("⚠️  .env file already exists. Skipping creation.")
        return

    try:
        from .config import Config
        sample_config = Config.__new__(Config)

        # Copy from .env.example
        example_path = Path(".env.example")
        if example_path.exists():
            env_path.write_text(example_path.read_text())
            print("✓ Created .env file from .env.example")
            print("📝 Please edit .env file with your actual credentials")
        else:
            print("❌ .env.example file not found")

    except Exception as e:
        print(f"❌ Error creating .env file: {e}")


def setup_project():
    """Set up the project with required directories and files."""
    print("Setting up Alert Email Processor...")

    # Create required directories
    directories = ["data", "logs", "tests"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")

    # Create .env file if it doesn't exist
    create_sample_env()

    print("\n🎉 Project setup complete!")
    print("\nNext steps:")
    print("1. Edit the .env file with your credentials")
    print("2. Test the system: python -m src.main --test")
    print("3. Run once: python -m src.main --once")
    print("4. Run as daemon: python -m src.main --daemon")


if __name__ == "__main__":
    main()
