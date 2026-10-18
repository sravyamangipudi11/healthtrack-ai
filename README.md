# HealthTrack AI — Patient Symptom Analysis Tool

HealthTrack AI is a web application that helps healthcare professionals review patient-reported symptoms and receive preliminary, LLM-generated insights, including possible conditions, recommended next steps, red flags, and urgency.

**Disclaimer:** This application provides preliminary decision support, not a diagnosis. It has not been clinically validated and must not replace professional medical judgment or emergency care. Use synthetic data only.

## Features

- **Symptom assessment UI:** Enter symptoms and relevant patient details through a browser-based interface.
- **LLM integration:** Generate structured preliminary insights using Groq, with provider alternatives supported by the code.
- **Input validation:** Validate symptom input and patient fields using Pydantic schemas.
- **Safety escalation:** Deterministic red-flag rules can raise urgency when potentially serious symptoms are detected.
- **Interaction logging:** Record operational metadata and assessment results while excluding free-text notes.
- **Caching:** Use an in-memory TTL cache to avoid repeated LLM calls for eligible requests.
- **Role-based access control:** Restrict assessment and log access using API keys assigned to clinician and admin roles.
- **Automated tests:** Test validation, caching, safety escalation, logging, error handling, and access control.

## Technology Stack

- Python
- FastAPI
- Pydantic
- Groq LLM API
- HTTPX
- Pytest
- HTML, CSS, and vanilla JavaScript

## Architecture

```text
Browser UI
    |
    v
FastAPI routes (app/main.py)
    |
    +--> API-key authentication (app/auth.py)
    |
    v
InsightService (app/service.py)
    |
    +--> Input/output validation (app/schemas.py)
    |
    +--> TTL cache (app/cache.py)
    |
    +--> LLM provider (app/llm.py)
    |
    +--> Red-flag safety rules (app/safety.py)
    |
    +--> Interaction logger (app/logging_utils.py)
```

The application separates HTTP handling, business logic, model integration, caching, safety checks, and logging. The `create_app(settings, provider)` factory allows tests to inject a deterministic fake provider instead of calling an external LLM.

## Getting Started

### Prerequisites

- Python 3.10 or later
- A Groq API key for live LLM assessments
- Internet access for installing dependencies and making live API requests

### 1. Clone the repository

```bash
git clone https://github.com/sravyamangipudi11/healthtrack-ai.git
cd healthtrack-ai
```


### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` locally and configure the provider:

```dotenv
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b

AUTH_ENABLED=true
API_KEYS=replace_with_clinician_key:clinician,replace_with_admin_key:admin

CACHE_TTL_SECONDS=3600
LOG_PATH=logs/interactions.jsonl
```

Replace all example credentials with your own values. Use strong, randomly generated API keys and never commit `.env` or real credentials to version control.

The application also supports alternative providers where implemented in the code. Check `app/llm.py` and `app/config.py` for the supported provider names and configuration options.

### 5. Start the application

```bash
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

Enter the configured clinician API key in the UI to submit assessments.

### 6. Run the tests

```bash
pytest -q
```

Tests use a deterministic fake provider and need no API key.

## API Overview

| Endpoint | Purpose | Access |
|---|---|---|
| `GET /` | Serve the web interface | Public |
| `GET /health` | Basic health check | Public |
| `POST /api/analyze` | Generate a preliminary symptom assessment | Clinician or admin |
| `GET /api/logs` | Retrieve recent interaction logs | Admin only |

When authentication is enabled, requests to protected endpoints must include the `X-API-Key` header. Missing or invalid keys are rejected, and authenticated users without the required role receive a forbidden response.

## Requirements Mapping

| Requirement | Implementation |
|---|---|
| Symptom input UI | `app/templates/index.html` |
| LLM integration | `app/llm.py` |
| Input validation | `app/schemas.py` |
| Safety escalation | `app/safety.py` |
| Logging | `app/logging_utils.py` |
| Caching | `app/cache.py` |
| Role-based access control | `app/auth.py` |
| HTTP routes and error handling | `app/main.py` |
| Business logic | `app/service.py` |
| Automated tests | `tests/test_app.py` |

## Key Design Decisions and Trade-offs

### Provider abstraction and deterministic tests

The model integration is separated behind a provider interface. Tests can inject a fake provider, making automated checks deterministic and avoiding external API calls. The trade-off is an additional abstraction layer.

### Structured model output

LLM responses are checked against the expected schema. Malformed output is retried and ultimately mapped to a controlled error rather than being treated as a valid assessment. This improves output reliability, but schema validation does not establish medical correctness.

### Deterministic safety escalation

A rule-based safety layer can raise urgency when configured red-flag symptoms are detected. It does not rely solely on the model to identify potential emergencies.

The current keyword-based approach is intentionally simple. It can miss synonyms and context, and it can produce false positives. It is not a clinically validated triage system.

### Input validation and prompt-injection hygiene

Pydantic validates incoming request fields, and symptom input is constrained before it reaches the model. The application treats user-provided symptoms as data rather than instructions. Input validation reduces risk but cannot eliminate every prompt-injection or model-output risk.

### In-memory TTL caching

Eligible requests can reuse a cached result to reduce repeated model calls and latency. Requests containing free-text notes bypass the cache.

The cache is process-local, is lost when the application restarts, and is not shared between multiple application instances. A shared cache such as Redis could support a multi-instance deployment.

### Privacy-aware logging

Free-text notes are excluded from interaction logs because they may contain sensitive information. The logger records a `has_notes` indicator instead.

Logs can still contain sensitive operational or assessment information. The application is a synthetic assessment exercise and is not designed for production handling of protected health information.

### API-key role-based access control

Static API keys map to clinician and admin roles. Clinicians can perform assessments, while admins can also retrieve logs.

This is a lightweight demonstration of authorization, not a complete identity-management system. Production use would require a stronger authentication and secret-management strategy.

### Synchronous request handling

Synchronous endpoints keep the implementation straightforward for a small demonstration. Higher traffic would require further work on concurrency, rate limiting, background processing, monitoring, and deployment.

## Security and Limitations

- Do not enter real patient information. Use synthetic data only.
- Do not commit `.env`, API keys, logs, or local backup files.
- Keep authentication enabled when evaluating protected endpoints.
- The in-memory cache is not persistent or shared across workers.
- The red-flag rules and generated medical insights have not been clinically validated.
- There is no rate limiting or production-grade identity management.
- A successful model response does not guarantee that the assessment is correct or complete.
- The app must not be used as a substitute for clinical judgment or emergency services.

## AI Usage

- **Claude (Anthropic):** generated the initial scaffold, application code, tests and first README draft.
- **ChatGPT (OpenAI):** helped switch the provider from Gemini to Groq, debug the failing LLM call, and refine the UI and README.

**What I verified or changed:**
- Ran the test suite (`pytest`; 18 passed on the final commit).
- Ran the app against the live Groq API and checked: normal assessment, chest-pain emergency escalation, mild symptoms not escalated, missing vs "Not measured yet" temperature, and rejected missing/invalid API keys.
- Changed: switched the provider to Groq (`llm.py`, `config.py`), added the body-temperature field with validation, and redesigned the UI.
- Checked that `.env` and logs are git-ignored and that no keys are committed.

AI output is not clinically validated; see Security and Limitations.