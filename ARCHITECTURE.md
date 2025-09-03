# System Architecture Documentation

## 🏗️ AlertIQ System Architecture

This document provides comprehensive details about the AlertIQ system architecture, component interactions, and data flow patterns.

## Architecture Overview

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

## Component Flow Diagram

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

## Data Flow Architecture

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

## 🔄 Processing Flow Details

### 1. Email Collection Phase
```python
┌─ Scheduler starts processing cycle
├─ Email Reader authenticates with Gmail API
├─ Fetches unread emails from inbox
├─ Filters alerts based on configured criteria
└─ Queues emails for processing
```

**Key Operations:**
- OAuth2 authentication refresh
- Gmail API query execution (`is:unread in:inbox`)
- Email metadata extraction
- Content validation and sanitization

### 2. Content Analysis Phase
```python
┌─ Email content extraction and cleaning
├─ Subject line and body parsing
├─ Metadata extraction (sender, timestamp, etc.)
├─ Content preprocessing for AI analysis
└─ Gemini AI classification request
```

**Key Operations:**
- HTML content parsing and text extraction
- Email header analysis
- Content normalization for AI processing
- Prompt engineering for optimal classification

### 3. AI Decision Phase
```python
┌─ Gemini AI analyzes email content
├─ Determines alert category (backend/code/rehit)
├─ Assigns confidence score
├─ Generates routing recommendation
└─ Returns structured classification result
```

**AI Analysis Process:**
- Context-aware prompt generation
- Multi-factor classification analysis
- Confidence scoring based on content clarity
- Fallback handling for ambiguous cases

### 4. Routing & Delivery Phase
```python
┌─ Team assignment based on AI classification
├─ Email formatting for target team
├─ SMTP delivery to appropriate inbox
├─ Database logging of routing decision
└─ Status update and monitoring
```

**Key Operations:**
- Team email lookup based on classification
- Email template formatting
- SMTP authentication and delivery
- Audit trail creation

## Component Responsibilities

| Component | Primary Function | Key Technologies | Dependencies |
|-----------|------------------|------------------|--------------|
| **Email Reader** | Gmail API integration, OAuth authentication | Google APIs, OAuth2 | Gmail API, Config |
| **Processor** | Main processing logic, batch handling | Python asyncio, scheduling | Email Reader, AI Analyzer, Database |
| **AI Analyzer** | Content analysis, classification | Google Gemini AI API | Gemini API, Config |
| **Email Sender** | SMTP delivery, team routing | smtplib, email formatting | Config, SMTP Server |
| **Database** | Audit logging, processed email tracking | CSV, pandas | File System |
| **Scheduler** | Daemon mode, interval processing | APScheduler, threading | Processor |
| **Config** | Environment management, settings | Pydantic, dotenv | Environment Variables |

## Integration Points

### External Services
- **Gmail API**: Email reading and management
  - Authentication: OAuth2 with refresh tokens
  - Operations: Read, search, modify labels
  - Rate Limits: 1 billion quota units/day (default)

- **Gemini AI API**: Content analysis and classification
  - Authentication: API key
  - Operations: Text generation, content analysis
  - Rate Limits: 60 requests/minute (free tier)

- **SMTP Servers**: Email delivery to teams
  - Authentication: Username/password or app passwords
  - Operations: Send formatted alerts
  - Rate Limits: Provider-specific (Gmail: 500/day for free)

### Internal Interfaces
- **Config → All Components**: Centralized configuration management
- **Database → Processor**: Audit trail and deduplication
- **Scheduler → Processor**: Automated processing cycles
- **Models → All Components**: Shared data structures

## Data Models and Flow

### Core Data Structures

```python
EmailData:
├── message_id: str          # Unique Gmail message ID
├── subject: str             # Email subject line
├── body: str               # Email body content
├── sender: str             # Sender email address
├── timestamp: datetime     # Email received timestamp
└── labels: List[str]       # Gmail labels

LLMAnalysis:
├── action: ActionType      # Classification result (Backend/Code/Rehit)
├── reason: str            # AI reasoning for classification
├── confidence: float      # Confidence score (0.0-1.0)
└── metadata: Dict         # Additional analysis data

ProcessedEmail:
├── email_data: EmailData   # Original email information
├── analysis: LLMAnalysis  # AI classification result
├── status: str            # Processing status
├── error_message: str     # Error details (if any)
└── processed_at: datetime # Processing timestamp
```

### Data Transformation Pipeline

```
Raw Gmail Message → EmailData → LLMAnalysis → ProcessedEmail → Audit Log
                ↓              ↓             ↓              ↓
           Content Extract → AI Prompt → Classification → Team Routing
```

## Scalability Considerations

### Current Architecture Limitations
- **Single-threaded processing**: Sequential email handling
- **File-based database**: CSV storage not suitable for high volume
- **Synchronous AI calls**: Blocking operations during analysis
- **No load balancing**: Single instance processing

### Scaling Strategies

#### Horizontal Scaling
```
Load Balancer
├── AlertIQ Instance 1 (emails 1-100)
├── AlertIQ Instance 2 (emails 101-200)
└── AlertIQ Instance 3 (emails 201-300)
```

#### Database Scaling
```
CSV Files → SQLite → PostgreSQL → Distributed Database
```

#### Processing Optimization
```
Sequential → Batch Processing → Async Processing → Stream Processing
```

## Security Architecture

### Authentication Flow
```
User → OAuth2 → Google APIs → Gmail/Gemini
     ↓
   App Password → SMTP Server → Team Emails
```

### Data Protection
- **API Keys**: Environment variables, never committed
- **OAuth Tokens**: Encrypted storage, automatic refresh
- **Email Content**: Temporary processing, not permanently stored
- **Audit Logs**: Local file system, rotation policy

### Access Control
- **Gmail**: Read-only access to inbox
- **Gemini AI**: Content analysis only, no data retention
- **SMTP**: Send-only access to team inboxes
- **File System**: Local directory permissions

## Error Handling and Resilience

### Retry Strategies
```python
Email Reading: 3 retries with exponential backoff
AI Analysis: 2 retries with linear backoff
Email Sending: 3 retries with exponential backoff
Database Operations: No retries (fail fast)
```

### Failure Modes and Recovery

| Failure Type | Impact | Recovery Strategy |
|--------------|--------|------------------|
| **Gmail API Rate Limit** | Processing delay | Exponential backoff, queue management |
| **Gemini API Unavailable** | Classification failure | Fallback rules, manual review queue |
| **SMTP Server Down** | Delivery failure | Alternative SMTP, retry queue |
| **Network Connectivity** | Complete failure | Offline mode, batch retry |
| **Configuration Error** | Startup failure | Validation, default values |

### Monitoring and Alerting

```
System Health Checks:
├── API Connectivity Tests
├── Processing Rate Monitoring
├── Error Rate Tracking
├── Queue Length Monitoring
└── Resource Usage Alerts
```

## Future Architecture Enhancements

### Phase 1: Performance
- [ ] Async processing with asyncio
- [ ] Database migration to SQLite/PostgreSQL
- [ ] Batch AI analysis optimization
- [ ] Connection pooling for APIs

### Phase 2: Reliability
- [ ] Circuit breaker patterns
- [ ] Dead letter queues
- [ ] Health check endpoints
- [ ] Graceful shutdown handling

### Phase 3: Scalability
- [ ] Microservices architecture
- [ ] Message queue integration (Redis/RabbitMQ)
- [ ] Horizontal scaling support
- [ ] Load balancing strategies

### Phase 4: Intelligence
- [ ] Machine learning model training
- [ ] Custom classification models
- [ ] Feedback loop integration
- [ ] A/B testing framework

---

*Last Updated: September 3, 2025*  
*Architecture Version: 1.0*  
*For implementation details, see the main [README.md](README.md)*
