# AlertIQ 🚨🤖

**Intelligent AI-powered alert email processing and routing system**

AlertIQ is an advanced email automation system that uses AI to intelligently process, analyze, and route alert emails to the appropriate teams. It leverages Google's Gemini AI for smart categorization and automated response generation.

## 📚 Documentation

- [🧪 **Testing Documentation**](TESTING.md) - Comprehensive test coverage report and API requirements
- [🏗️ **System Architecture**](ARCHITECTURE.md) - Detailed system design, data flow, and component interactions
- [⚙️ **Installation Guide**](#installation) - Step-by-step setup instructions
- [🔧 **Configuration**](#configuration) - Environment variables and settings

## 🌟 Features

- **AI-Powered Classification**: Uses Gemini AI to categorize alerts into backend, code, or rehit issues
- **Intelligent Routing**: Automatically forwards emails to the correct team based on AI analysis
- **Email Processing**: Connects to Gmail API for seamless email reading and sending
- **Batch Processing**: Handles multiple emails efficiently with configurable batch sizes
- **Flexible Modes**: Run once, as a daemon, or in test mode
- **Comprehensive Logging**: Detailed logging with configurable levels
- **Docker Support**: Easy deployment with Docker containerization
- **Retry Logic**: Built-in retry mechanisms for robust operation
- **Database Tracking**: CSV-based tracking of processed emails

## 📋 Prerequisites

- Python 3.12+
- UV package manager
- Gmail account with API access
- Google Cloud Console account (for Gemini AI API)

## 🛠️ Installation

### Step 1: Install UV Package Manager

UV is a fast Python package installer and resolver. Install it using one of these methods:

#### macOS/Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows:
```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Using pip (alternative):
```bash
pip install uv
```

### Step 2: Clone and Setup Project

```bash
# Clone the repository
git clone <repository-url>
cd AlertIQ

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all dependencies
uv pip install -e .
```

### Step 3: API Setup and Configuration

#### 3.1 Google Gemini AI API Setup

1. **Create Google Cloud Project:**
   ```bash
   # Visit: https://console.cloud.google.com/
   # Create new project or select existing one
   ```

2. **Enable Gemini AI API:**
   ```bash
   # Navigate to: APIs & Services > Library
   # Search for "Generative Language API"
   # Click "Enable"
   ```

3. **Create API Key:**
   ```bash
   # Go to: APIs & Services > Credentials
   # Click "Create Credentials" > "API Key"
   # Copy the generated API key
   ```

#### 3.2 Gmail API Setup

1. **Enable Gmail API:**
   ```bash
   # In same Google Cloud Console project
   # APIs & Services > Library
   # Search for "Gmail API" and enable it
   ```

2. **Create OAuth2 Credentials:**
   ```bash
   # APIs & Services > Credentials
   # Create Credentials > OAuth 2.0 Client IDs
   # Application type: Desktop application
   # Download the JSON file
   ```

3. **Generate Refresh Token:**
   ```python
   # Use the OAuth2 playground or run the auth script
   # https://developers.google.com/oauthplayground/
   # Scope: https://www.googleapis.com/auth/gmail.readonly
   ```

#### 3.3 Environment Configuration

Create a `.env` file in the project root:

```bash
# Copy the template
cp .env.example .env

# Edit with your credentials
nano .env
```

Add your API credentials:

```env
# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Gmail API Configuration
GMAIL_CLIENT_ID=your_gmail_client_id_here
GMAIL_CLIENT_SECRET=your_gmail_client_secret_here
GMAIL_REFRESH_TOKEN=your_gmail_refresh_token_here

# Email Configuration
BACKEND_TEAM_EMAIL=backend-team@company.com
CODE_TEAM_EMAIL=code-team@company.com
REHIT_TEAM_EMAIL=rehit-team@company.com

# SMTP Configuration (for sending emails)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_smtp_username@gmail.com
SMTP_PASSWORD=your_smtp_app_password

# Processing Configuration
MAX_EMAILS_PER_BATCH=10
PROCESSING_INTERVAL=300  # 5 minutes
LOG_LEVEL=INFO
```

### Step 4: Verify Installation

```bash
# Run basic tests (no API keys required)
python -m pytest tests/ -v

# Test configuration
python -c "from src.config import config; print('Config loaded successfully')"

# Test imports
python -c "import src.main; print('All modules imported successfully')"
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GEMINI_API_KEY` | Google Gemini AI API key | Yes | - |
| `GMAIL_CLIENT_ID` | Gmail OAuth2 client ID | Yes | - |
| `GMAIL_CLIENT_SECRET` | Gmail OAuth2 client secret | Yes | - |
| `GMAIL_REFRESH_TOKEN` | Gmail OAuth2 refresh token | Yes | - |
| `BACKEND_TEAM_EMAIL` | Backend team email address | Yes | - |
| `CODE_TEAM_EMAIL` | Code team email address | Yes | - |
| `REHIT_TEAM_EMAIL` | Rehit team email address | Yes | - |
| `SMTP_SERVER` | SMTP server hostname | No | smtp.gmail.com |
| `SMTP_PORT` | SMTP server port | No | 587 |
| `SMTP_USERNAME` | SMTP username | Yes | - |
| `SMTP_PASSWORD` | SMTP password/app password | Yes | - |
| `MAX_EMAILS_PER_BATCH` | Max emails per processing batch | No | 10 |
| `PROCESSING_INTERVAL` | Seconds between processing cycles | No | 300 |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | No | INFO |

### Team Configuration

The system routes emails to three predefined teams based on AI classification:

- **Backend Team**: Infrastructure, database, and server issues
- **Code Team**: Application bugs, code-related problems
- **Rehit Team**: Temporary issues requiring retry/reprocessing

## 🚀 Usage

### Basic Usage

```bash
# Run once (process all unread emails)
python -m src.main

# Run in daemon mode (continuous processing)
python -m src.main --daemon

# Test mode (dry run, no actual email sending)
python -m src.main --test

# Process specific number of emails
python -m src.main --max-emails 5

# Custom processing interval (seconds)
python -m src.main --daemon --interval 600
```

### Docker Usage

```bash
# Build the image
docker build -t alertiq .

# Run with environment file
docker run --env-file .env alertiq

# Run in daemon mode
docker run -d --env-file .env alertiq --daemon

# Using docker-compose
docker-compose up -d
```

### Advanced Usage

```python
# Programmatic usage
from src.processor import EmailProcessor
from src.config import config

processor = EmailProcessor()

# Process emails once
results = processor.process_emails()

# Process in daemon mode
processor.run_daemon(interval=300)
```

## 🧪 Testing

The project includes comprehensive test coverage. See [TESTING.md](TESTING.md) for detailed information about:

- ✅ **26 passing unit tests** (96.3% success rate)
- 🔑 **Missing integration tests** that require API keys
- 📊 **Test coverage analysis** and recommendations
- 🚀 **Running different test suites**

### Quick Test Commands

```bash
# Run all unit tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing

# Run specific test categories
python -m pytest tests/test_models.py -v          # Data models
python -m pytest tests/test_config.py -v         # Configuration
python -m pytest tests/test_database.py -v       # Database operations
python -m pytest tests/test_llm_analyzer.py -v   # AI analysis (mocked)
```

## 📝 Logging

The system provides comprehensive logging:

```bash
# Log files location
logs/
├── alertiq.log          # Main application log
├── email_processing.log # Email processing details
├── ai_analysis.log      # AI classification logs
└── error.log           # Error tracking
```

### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General operational messages
- **WARNING**: Important events that may need attention
- **ERROR**: Error conditions that need immediate attention

## 🐳 Docker Support

### Dockerfile

The project includes a multi-stage Dockerfile for efficient containerization:

```bash
# Development build
docker build --target development -t alertiq:dev .

# Production build
docker build --target production -t alertiq:prod .
```

### Docker Compose

```yaml
# docker-compose.yml included for easy deployment
docker-compose up -d
```

## 🔍 Monitoring

### Health Checks

```bash
# Check system status
python -m src.main --health-check

# View processing statistics
python -c "from src.database import EmailDatabase; db = EmailDatabase(); print(db.get_processing_stats())"
```

### Metrics

The system tracks:
- Emails processed per hour/day
- AI classification accuracy
- Team routing distribution
- Error rates and types
- Processing latency
---

**Built with ❤️ using Python, Google Gemini AI, and modern development practices**
