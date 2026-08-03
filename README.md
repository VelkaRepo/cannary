# 🐤 CanaryFile Engine

> **Lightweight Active Defense & Detection Engineering Canary Token Framework**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**CanaryFile Engine** is an open-source active defense security framework designed for cyber defense teams, SOC analysts, and detection engineers. It allows security teams to generate weaponized decoy files ("canary documents") and deploy a lightweight listener server that alerts instantly when unauthorized actors access or exfiltrate sensitive files.

---

## 🏗 System Architecture

```text
               +-------------------------------+
               |    Decoy Document (PDF, etc.) |
               |   [Contains /OpenAction URI]  |
               +---------------+---------------+
                               |
                               | (HTTP/S GET Request on file open)
                               v
               +---------------+---------------+
               |    CanaryFile Listener Server |
               |        (FastAPI App)          |
               +---------------+---------------+
                               |
            +------------------+------------------+
            |                                     |
            v                                     v
+-----------+-----------+             +-----------+-----------+
| SQLite Telemetry DB   |             | Webhook Alert System  |
| (IP, Headers, UA, TS) |             | (Slack / Discord)     |
+-----------------------+             +-----------------------+
```

---

## 📁 Repository Directory Structure

```text
Cannary/
├── server/
│   ├── __init__.py
│   ├── main.py          # FastAPI application & REST/Webhook endpoints
│   ├── config.py        # Settings management (Pydantic / Env vars)
│   ├── database.py      # Telemetry logging & SQLite database handler
│   └── notifier.py      # Asynchronous Webhook notification module
├── generator/
│   ├── __init__.py
│   ├── cli.py           # Command Line Interface for canary generation
│   └── pdf_injector.py  # PDF tracking payload injector
├── config/
│   └── config.example.yaml # Configuration settings template
├── tests/
│   ├── __init__.py
│   ├── test_server.py   # Listener API & database unit tests
│   └── test_generator.py# Generator payload injection unit tests
├── .gitignore
├── requirements.txt     # Dependency specifications
└── README.md            # Documentation & project manual
```

---

## 🚀 Quickstart Guide

### 1. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/your-org/canaryfile-engine.git
cd canaryfile-engine

# Create virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

---

### 2. Start the Listener Server

Launch the FastAPI listener server using `uvicorn`:

```bash
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

The listener server will be accessible at `http://127.0.0.1:8000`. You can view the automatic OpenAPI documentation at `http://127.0.0.1:8000/docs`.

---

### 3. Generate a Canary Document

Use the CLI generator to create a decoy PDF or MS Word (`.docx`) file embedded with a canary tracking token:

```bash
# Generate a new decoy PDF document
python -m generator.cli --server http://127.0.0.1:8000 --output Confidential_Q3_Report.pdf --label "Q3 Financial Decoy"

# Generate a new decoy MS Word (.docx) document
python -m generator.cli --server http://127.0.0.1:8000 --type docx --output Secret_Strategy.docx --label "Strategy Decoy"

# Or inject payload into an existing document
python -m generator.cli --server http://127.0.0.1:8000 --type docx --input sample.docx --output sample_canary.docx --label "Operations Manual"
```

---

### 4. Web Management Dashboard & Telemetry

Access the interactive, dark-mode Web Management Dashboard at `http://127.0.0.1:8000/dashboard` to view:
- Real-time trigger hits & GeoIP origin locations (Country, City, ISP/ASN).
- Total registered tokens & hit statistics.
- Interactive token registration modal.

---

### 5. Test Trigger Alert

Opening the generated PDF or MS Word document (or accessing the trigger URL directly) logs an enriched telemetry event:

```bash
curl -i http://127.0.0.1:8000/t/<TOKEN_ID>
```

#### Viewing Telemetry Logs & Analytics

Retrieve recorded trigger events and aggregate analytics via API:

```bash
# Get enriched trigger hits (Country, City, ISP, ASN)
curl http://127.0.0.1:8000/api/v1/hits

# Get dashboard analytics summary
curl http://127.0.0.1:8000/api/v1/stats
```

---

## 🔒 Security & API Authentication

Management endpoints (`/api/v1/tokens`, `/api/v1/hits`) can be secured using an API key (`X-API-Key` HTTP header).

```bash
# Enable API Key Authentication
export CANARY_API_KEY="your-secret-api-key"

# Set IP Rate Limiting threshold (default: 60 requests/minute)
export CANARY_RATE_LIMIT_PER_MINUTE=60
```

When API key authentication is enabled:
```bash
# Register token with API Key
curl -X POST http://127.0.0.1:8000/api/v1/tokens \
     -H "X-API-Key: your-secret-api-key" \
     -H "Content-Type: application/json" \
     -d '{"token_id": "secret-token", "label": "Decoy Doc"}'

# CLI generator with API key
python -m generator.cli --server http://127.0.0.1:8000 --api-key "your-secret-api-key" --output decoy.pdf
```

---

## 🔔 Webhook Alert Integration

CanaryFile Engine supports real-time alert notifications via **Slack**, **Discord**, and generic HTTP webhooks.

To configure alerts, set environment variables:

```bash
# Discord Example
export CANARY_WEBHOOK_ENABLED=true
export CANARY_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN"
export CANARY_WEBHOOK_PLATFORM="discord"
```

Or copy `config/config.example.yaml` to `config/config.yaml` and update configuration parameters.

---

## 🧪 Running Unit Tests

Run the test suite using `pytest`:

```bash
pytest -v
```

---

## 🗺 Project Roadmap

- [x] **Phase 1: Foundational Architecture**
  - Modular directory layout
  - FastAPI listener server with IP/User-Agent telemetry logging
  - SQLite persistent database storage
  - PDF OpenAction URI payload generator & CLI interface
  - Async webhook alert notifications (Slack / Discord)
- [ ] **Phase 2: Expanded File Format Injectors**
  - Microsoft Office (DOCX / XLSX / PPTX) template web bug injection
  - Windows Desktop.ini / Folder tracking tokens
  - AWS Key / API Credential decoy generators
- [ ] **Phase 3: Dashboard & Intelligence**
  - Web UI dashboard for token lifecycle management & geographical IP mapping
  - Threat Intelligence enrichment (IP reputation lookups & ASN analysis)

---

## 🛡 Security & Ethical Usage Notice

*CanaryFile Engine is designed exclusively for authorized defensive cyber operations, security research, internal deception networks, and active defense detection engineering. Ensure you have proper authorization prior to deploying decoy tokens in corporate environments.*
