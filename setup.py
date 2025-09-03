#!/usr/bin/env python3
"""
Setup script for AlertIQ.
Creates necessary directories and files for first-time setup.
"""

import os
import sys
from pathlib import Path


def create_directories():
    """Create required directories."""
    directories = ["data", "logs", "tests"]

    for directory in directories:
        path = Path(directory)
        path.mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")


def create_env_file():
    """Create .env file from .env.example if it doesn't exist."""
    env_path = Path(".env")
    example_path = Path(".env.example")

    if env_path.exists():
        print("⚠️  .env file already exists")
        return False

    if not example_path.exists():
        print("❌ .env.example file not found")
        return False

    # Copy example to .env
    env_path.write_text(example_path.read_text())
    print("✓ Created .env file from .env.example")
    print("📝 Please edit .env file with your actual credentials")
    return True


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 12):
        print(f"❌ Python 3.12+ required, found {sys.version_info.major}.{sys.version_info.minor}")
        return False

    print(f"✓ Python version {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True


def main():
    """Main setup function."""
    print("🚀 Setting up AlertIQ...")
    print("=" * 50)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Create directories
    create_directories()

    # Create .env file
    env_created = create_env_file()

    print("\n" + "=" * 50)
    print("🎉 AlertIQ setup complete!")

    print("\n📋 Next steps:")
    if env_created:
        print("1. Edit .env file with your actual credentials:")
        print("   - Gmail API credentials")
        print("   - Gemini AI API key")
        print("   - SMTP settings")
        print("   - Team email addresses")

    print("2. Test the system:")
    print("   python -m src.main --test")

    print("3. Run processing once:")
    print("   python -m src.main --once")

    print("4. Run as daemon:")
    print("   python -m src.main --daemon")

    print("\n📚 Documentation:")
    print("   See README.md for detailed instructions")
    print("\n🧠⚡ Welcome to AlertIQ - Intelligent Alert Processing!")


if __name__ == "__main__":
    main()
