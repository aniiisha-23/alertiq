# AlertIQ 🧠⚡

An intelligent AI-powered system that automates the processing of alert emails using advanced Large Language Model (LLM) analysis. AlertIQ reads incoming alert emails, analyzes them with Gemini AI to determine appropriate actions, and automatically routes structured summaries to the correct teams.

## 🚀 Features

- **Smart Email Integration**: Connects to Gmail via API or IMAP for reading incoming alert emails
- **AI-Powered Analysis**: Uses Google Gemini AI to intelligently analyze alert content and determine actions
- **Intelligent Routing**: Automatically routes alerts to appropriate teams based on AI analysis
- **Action Classification**: Categorizes alerts into three intelligent action types:
  - `Re-hit`: Temporary issues that can be resolved by retrying
  - `Backend`: Infrastructure or configuration issues
  - `Code`: Software bugs requiring development intervention
- **Automated Notifications**: Sends structured summary emails to relevant teams
- **Complete Audit Trail**: Maintains comprehensive logs of all processed emails
- **Robust Error Handling**: Advanced error handling with retries and fallback notifications
- **Smart Scheduling**: Built-in scheduler for automated processing at regular intervals
- **Health Monitoring**: System health checks and intelligent status monitoring

## 📋 Requirements

- Python 3.12+
- Gmail API credentials (or IMAP access)
- Google Gemini AI API key
- SMTP access for sending emails

## 🛠️ Installation

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd alert-email-processor
   ```

2. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync
   
   # Or using pip
   pip install -e .
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

4. **Configure Gmail API** (if using Gmail)
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Gmail API
   - Create credentials (OAuth 2.0)
   - Download credentials and extract required fields for .env

5. **Get Gemini AI API Key**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create an API key
   - Add it to your .env file

## ⚙️ Configuration

Edit the `.env` file with your credentials:

```env
# Gmail API Configuration
GMAIL_CLIENT_ID=your_gmail_client_id_here
GMAIL_CLIENT_SECRET=your_gmail_client_secret_here
GMAIL_REFRESH_TOKEN=your_gmail_refresh_token_here

# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here

# Team Email Configuration
BACKEND_TEAM_EMAIL=backend-team@company.com
CODE_TEAM_EMAIL=dev-team@company.com
REHIT_TEAM_EMAIL=ops-team@company.com

# Processing Configuration
CHECK_INTERVAL_MINUTES=5
MAX_EMAILS_PER_BATCH=10
```

## 🚀 Usage

### Command Line Interface

The system provides several operation modes:

```bash
# Run once and exit
python -m src.main --once

# Run as daemon (continuous processing)
python -m src.main --daemon

# Test all connections
python -m src.main --test

# View processing statistics
python -m src.main --stats

# Clean up old records
python -m src.main --cleanup

# Set custom processing interval (daemon mode)
python -m src.main --daemon --interval 10
```

### Programmatic Usage

```python
from src.processor import AlertEmailProcessor
from src.scheduler import AlertEmailScheduler

# One-time processing
processor = AlertEmailProcessor()
results = processor.process_alerts()

# Scheduled processing
scheduler = AlertEmailScheduler()
scheduler.start_scheduled_processing(interval_minutes=5)
```

## 📊 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Email Inbox   │───▶│  Email Reader    │───▶│  LLM Analyzer   │
│   (Gmail API)   │    │                  │    │   (Gemini AI)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐              │
│     Database    │◀───│  Main Processor  │◀─────────────┘
│   (CSV Logs)    │    │                  │
└─────────────────┘    └──────────────────┘
                                │
┌─────────────────┐    ┌──────────────────┐
│  Team Emails    │◀───│  Email Sender    │
│   (SMTP/API)    │    │                  │
└─────────────────┘    └──────────────────┘
```

## 🔄 Workflow

1. **Email Fetching**: System connects to Gmail and fetches unread emails
2. **Duplicate Check**: Filters out already processed emails using database
3. **LLM Analysis**: Sends email content to Gemini AI for action determination
4. **Team Routing**: Routes to appropriate team based on analysis result
5. **Summary Generation**: Creates structured summary email
6. **Notification Sending**: Sends summary to relevant team
7. **Logging**: Records processing details in database
8. **Cleanup**: Marks original email as read

## 📧 Example Output

### Input Alert Email
```
Subject: Database Connection Failed
From: monitoring@company.com
Body: Database connection to prod-db-01 failed at 2025-09-03 10:30:00. 
Error: Connection timeout after 30 seconds.
```

### Generated Summary Email
```
Subject: Alert Analysis - Action Required: Backend
To: backend-team@company.com

Alert: Database Connection Failed
Action: Backend
Details: Database connection timeout indicates infrastructure issue requiring backend team attention

Original Alert Details:
- Sender: monitoring@company.com
- Received: 2025-09-03 10:30:00
- Message ID: msg_12345

Please take appropriate action based on the analysis above.
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_models.py

# Run with verbose output
pytest -v
```

## 📝 Logging

The system maintains comprehensive logs:

- **Application logs**: `logs/alert_processor.log`
- **Processing database**: `data/processed_emails.csv`
- **Rotation**: Daily log rotation with 30-day retention
- **Levels**: Configurable log levels (DEBUG, INFO, WARNING, ERROR)

## 🔧 Production Deployment

### As a Service (systemd)

```bash
# Create service file
sudo nano /etc/systemd/system/alert-processor.service

# Add content:
[Unit]
Description=Alert Email Processor
After=network.target

[Service]
Type=simple
Restart=always
User=alertprocessor
WorkingDirectory=/opt/alert-email-processor
ExecStart=/usr/bin/python3 -m src.main --daemon
Environment=PYTHONPATH=/opt/alert-email-processor

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable alert-processor
sudo systemctl start alert-processor
```

### Using Docker

```bash
# Build image
docker build -t alert-email-processor .

# Run container
docker run -d \
  --name alert-processor \
  --env-file .env \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  alert-email-processor
```

### Cron Job

```bash
# Add to crontab
*/5 * * * * cd /opt/alert-email-processor && python3 -m src.main --once >> /var/log/alert-processor.log 2>&1
```

## 🚨 Error Handling

The system includes comprehensive error handling:

- **Retry Logic**: Automatic retries with exponential backoff
- **Fallback Notifications**: Error alerts sent to backend team
- **Graceful Degradation**: Continues processing other emails if one fails
- **Connection Recovery**: Automatic reconnection to services
- **Logging**: Detailed error logging for troubleshooting

## 📈 Monitoring

Monitor system health:

```bash
# Check system status
python -m src.main --test

# View processing statistics
python -m src.main --stats

# Monitor logs
tail -f logs/alert_processor.log
```

## 🔐 Security

- **Environment Variables**: Sensitive data stored in environment variables
- **OAuth 2.0**: Secure Gmail API authentication
- **HTTPS**: All API communications over HTTPS
- **Validation**: Input validation and sanitization
- **Logging**: No sensitive data in logs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Gmail API Authentication**
   - Ensure OAuth 2.0 credentials are correct
   - Check refresh token validity
   - Verify Gmail API is enabled

2. **Gemini AI API**
   - Confirm API key is valid
   - Check API quotas and limits
   - Verify internet connectivity

3. **SMTP Issues**
   - Use app-specific passwords for Gmail
   - Check firewall settings
   - Verify SMTP server settings

4. **Database Issues**
   - Ensure write permissions to data directory
   - Check disk space
   - Verify CSV file format

### Getting Help

- Check the logs: `logs/alert_processor.log`
- Run system test: `python -m src.main --test`
- Review configuration: `.env` file
- Check dependencies: `pip list`

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the logs for error details
