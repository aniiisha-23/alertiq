# AlertIQ 🚨🤖

**Intelligent AI-powered alert email processing and routing system**

AlertIQ is an advanced email automation system that uses AI to intelligently process, analyze, and route alert emails to the appropriate teams. It leverages Google's Gemini AI for smart categorization and automated response generation.

## 🏗️ System Architecture

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                AlertIQ System                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────────┐  │
│  │   Gmail     │───▶│Email Reader  │───▶│ Processor   │───▶│   AI Analyzer   │  │
│  │   Inbox     │    │(Gmail API)   │    │ (Scheduler) │    │  (Gemini AI)    │  │
│  └─────────────┘    └──────────────┘    └─────────────┘    └─────────────────┘  │
│                                                │                       │        │
│                                                ▼                       ▼        │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────────┐  │
│  │   Team      │◀───│Email Sender  │◀───│  Database   │    │   Config        │  │
│  │  Inboxes    │    │   (SMTP)     │    │   (CSV)     │    │ Management      │  │
│  └─────────────┘    └──────────────┘    └─────────────┘    └─────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Component Flow

```
📧 INCOMING EMAIL
        │
        ▼
┌───────────────────┐
│   Email Reader    │ ──── Authenticates with Gmail OAuth
│   (Gmail API)     │ ──── Fetches unread emails
└───────────────────┘ ──── Marks emails as processed
        │
        ▼
┌───────────────────┐
│    Processor      │ ──── Validates email format
│   (Main Logic)    │ ──── Extracts relevant content
└───────────────────┘ ──── Batch processing
        │
        ▼
┌───────────────────┐
│   AI Analyzer     │ ──── Sends email to Gemini AI
│   (Gemini AI)     │ ──── Analyzes content & context
└───────────────────┘ ──── Returns classification
        │
        ▼
┌───────────────────┐
│    Database       │ ──── Logs processed emails
│     (CSV)         │ ──── Tracks routing decisions
└───────────────────┘ ──── Maintains audit trail
        │
        ▼
┌───────────────────┐
│   Email Sender    │ ──── Routes to appropriate team
│     (SMTP)        │ ──── Sends formatted alerts
└───────────────────┘ ──── Provides status updates
        │
        ▼
🎯 TEAM INBOXES
   (Backend/Code/Rehit)
```

### Data Flow Architecture

```
INPUT → PROCESSING → ANALYSIS → ROUTING → OUTPUT

┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Gmail     │──▶│ Validation  │──▶│ AI Analysis │──▶│   Team      │──▶│ Delivered   │
│   Emails    │   │ & Parsing   │   │ & Category  │   │ Assignment  │   │   Alerts    │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
                         │                   │                   │
                         ▼                   ▼                   ▼
                  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
                  │   Logging   │   │  Confidence │   │   Audit     │
                  │    & Audit  │   │   Scoring   │   │    Trail    │
                  └─────────────┘   └─────────────┘   └─────────────┘
```

## 🔄 Processing Flow

### 1. Email Collection Phase
```python
┌─ Scheduler starts processing cycle
├─ Email Reader authenticates with Gmail API
├─ Fetches unread emails from inbox
├─ Filters alerts based on configured criteria
└─ Queues emails for processing
```

### 2. Content Analysis Phase
```python
┌─ Email content extraction and cleaning
├─ Subject line and body parsing
├─ Metadata extraction (sender, timestamp, etc.)
├─ Content preprocessing for AI analysis
└─ Gemini AI classification request
```

### 3. AI Decision Phase
```python
┌─ Gemini AI analyzes email content
├─ Determines alert category (backend/code/rehit)
├─ Assigns confidence score
├─ Generates routing recommendation
└─ Returns structured classification result
```

### 4. Routing & Delivery Phase
```python
┌─ Team assignment based on AI classification
├─ Email formatting for target team
├─ SMTP delivery to appropriate inbox
├─ Database logging of routing decision
└─ Status update and monitoring
```

### Component Responsibilities

| Component | Primary Function | Key Technologies |
|-----------|------------------|------------------|
| **Email Reader** | Gmail API integration, OAuth authentication | Google APIs, OAuth2 |
| **Processor** | Main processing logic, batch handling | Python asyncio, scheduling |
| **AI Analyzer** | Content analysis, classification | Google Gemini AI API |
| **Email Sender** | SMTP delivery, team routing | smtplib, email formatting |
| **Database** | Audit logging, processed email tracking | CSV, pandas |
| **Scheduler** | Daemon mode, interval processing | APScheduler, threading |
| **Config** | Environment management, settings | Pydantic, dotenv |

### Integration Points

#### External Services
- **Gmail API**: Email reading and management
- **Gemini AI API**: Content analysis and classification
- **SMTP Servers**: Email delivery to teams
- **File System**: Local data storage and logging

#### Internal Interfaces
- **Config → All Components**: Centralized configuration
- **Database → Processor**: Audit trail and deduplication
- **Scheduler → Processor**: Automated processing cycles
- **Models → All Components**: Shared data structures

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

- Python 3.8+
- UV package manager
- Gmail account with API access
- Google Cloud Console account (for Gemini AI API)

## 🛠️ Installation

### 1. Install UV Package Manager

UV is a fast Python package installer and resolver. Install it using one of these methods:

#### macOS/Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows:
```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Using pip:
```bash
pip install uv
```

### 2. Clone the Repository

```bash
git clone <repository-url>
cd AlertIQ
```

### 3. Install Dependencies

```bash
# Install all dependencies using UV
uv sync

# Or if you prefer using pip
pip install -e .
```

## 🔐 API Configuration

### Gmail API Setup

1. **Enable Gmail API**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Gmail API for your project
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
   - Choose "Desktop application"
   - Download the credentials JSON file

2. **Get Refresh Token**:
   - Use the OAuth playground or run the initial authentication flow
   - Save the client ID, client secret, and refresh token

### Gemini AI API Setup

1. **Get API Key**:
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key for Gemini
   - Copy the API key for configuration

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with the following configuration:

```env
# Gmail API Configuration
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
GMAIL_REFRESH_TOKEN=your_refresh_token

# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key

# SMTP Configuration (for sending emails)
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Team Email Addresses
BACKEND_TEAM_EMAIL=backend-team@company.com
CODE_TEAM_EMAIL=dev-team@company.com
REHIT_TEAM_EMAIL=rehit-team@company.com

# Optional Configuration
LOG_LEVEL=INFO
CHECK_INTERVAL_MINUTES=5
MAX_EMAILS_PER_BATCH=10
```

### Gmail App Password

For SMTP authentication, you'll need to generate an App Password:

1. Go to your Google Account settings
2. Navigate to Security → 2-Step Verification
3. Generate an App Password for "Mail"
4. Use this password as `SMTP_PASSWORD`

## 🚀 Usage

### Command Line Interface

```bash
# Run once (process emails and exit)
python -m src.main

# Run as daemon (continuous monitoring)
python -m src.main --mode daemon

# Test mode (dry run without sending emails)
python -m src.main --mode test

# View processing statistics
python -m src.main --mode stats

# Cleanup old logs and data
python -m src.main --mode cleanup

# Run with specific options
python -m src.main --daemon --verbose
```

### Docker Deployment

```bash
# Build the Docker image
docker build -t alertiq .

# Run with environment file
docker run --env-file .env alertiq

# Run as daemon
docker run -d --env-file .env --name alertiq-daemon alertiq --mode daemon
```

### Using UV for Development

```bash
# Install in development mode
uv pip install -e .

# Run with UV
uv run python -m src.main

# Install additional development dependencies
uv add --dev pytest black flake8 mypy
```

## 📁 Project Structure

```
AlertIQ/
├── src/                    # Main source code
│   ├── main.py            # Entry point and CLI
│   ├── config.py          # Configuration management
│   ├── email_reader.py    # Gmail API integration
│   ├── email_sender.py    # SMTP email sending
│   ├── llm_analyzer.py    # Gemini AI integration
│   ├── processor.py       # Email processing logic
│   ├── scheduler.py       # Task scheduling
│   ├── database.py        # Data persistence
│   └── models.py          # Data models
├── tests/                 # Unit tests
├── data/                  # Data storage
├── logs/                  # Log files
├── test_data/            # Test data
├── pyproject.toml        # Project configuration
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose setup
└── README.md           # This file
```

## 🔍 Monitoring and Logs

AlertIQ provides comprehensive logging:

- **Log Location**: `logs/alert_processor.log`
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Structured Logging**: JSON format for easy parsing
- **Rotation**: Automatic log rotation to prevent disk space issues

Monitor the system:

```bash
# Watch logs in real-time
tail -f logs/alert_processor.log

# Check processing statistics
python -m src.main --mode stats
```

## 🧪 Testing

Run the test suite:

```bash
# Using UV
uv run pytest

# Using pytest directly
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## 🐛 Troubleshooting

### Common Issues

1. **Gmail API Authentication Errors**:
   - Verify OAuth credentials are correct
   - Ensure Gmail API is enabled in Google Cloud Console
   - Check refresh token hasn't expired

2. **Gemini AI API Errors**:
   - Verify API key is valid and active
   - Check API quotas and usage limits
   - Ensure billing is enabled for the project

3. **SMTP Errors**:
   - Use App Password instead of regular password
   - Enable 2-factor authentication
   - Check firewall settings for SMTP ports

4. **Permission Errors**:
   - Ensure proper file permissions for data/ and logs/ directories
   - Check Docker volume mounting permissions

## 📈 Performance Tuning

- **Batch Size**: Adjust `MAX_EMAILS_PER_BATCH` for optimal performance
- **Check Interval**: Modify `CHECK_INTERVAL_MINUTES` based on email volume
- **Retry Logic**: Configure retry attempts and delays for reliability
- **Logging Level**: Use INFO or WARNING in production for better performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the logs for detailed error information

---

**AlertIQ** - Making alert management intelligent and efficient! 🚨✨
