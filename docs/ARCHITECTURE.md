# System Architecture Documentation
## Clinical Note Processing API

**Last Updated:** March 6, 2026  
**Version:** 1.0.0

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [System Components](#system-components)
3. [Data Flow](#data-flow)
4. [Technology Stack](#technology-stack)
5. [Design Patterns](#design-patterns)
6. [Scaling Architecture](#scaling-architecture)
7. [Security Architecture](#security-architecture)
8. [Deployment Architecture](#deployment-architecture)
9. [Monitoring & Observability](#monitoring--observability)
10. [Future Enhancements](#future-enhancements)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │  Streamlit UI    │  │   REST API       │  │  PDF Upload   │ │
│  │  (Web Interface) │  │   Clients        │  │  Interface    │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway / Load Balancer                 │
│                         (FastAPI + Uvicorn)                      │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API Routes (api.py)                                      │   │
│  │  • /extract - Entity extraction                           │   │
│  │  • /question-answer - Clinical Q&A                        │   │
│  │  • /health - Health check                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────┼────────────────────────────────┐  │
│  │                          ▼                                 │  │
│  │  ┌──────────────────┐  ┌─────────────────┐  ┌──────────┐ │  │
│  │  │  Request         │  │  Business       │  │  PDF     │ │  │
│  │  │  Validation      │  │  Logic Layer    │  │  Processor│ │  │
│  │  │  (schemas.py)    │  │  (llm_service)  │  │          │ │  │
│  │  └──────────────────┘  └─────────────────┘  └──────────┘ │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      External Services Layer                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Groq API (LLM Provider)                                  │   │
│  │  • Model: Llama 3.1 70B                                   │   │
│  │  • JSON Mode: Structured output                           │   │
│  │  • Temperature: 0 (deterministic)                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Infrastructure Layer                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐  │
│  │   Logging  │  │   Metrics  │  │   Config   │  │  Docker  │  │
│  │  (logger)  │  │ (Prometheus)│ │ (env vars) │  │Container │  │
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## System Components

### 1. API Layer (`src/api.py`)

**Responsibility:** HTTP request/response handling, routing, and orchestration

**Key Features:**
- RESTful endpoint definitions
- Request validation via Pydantic
- HTTP status code management (400, 422, 500, 503)
- CORS middleware configuration
- Error handling and exception mapping
- Health check endpoint for monitoring

**Endpoints:**
- `POST /api/v1/extract` - Extract structured entities from clinical notes
- `POST /api/v1/question-answer` - Answer questions based on clinical context
- `GET /health` - Service health check

**Design Decisions:**
- FastAPI for async support and automatic OpenAPI documentation
- Dependency injection for configuration and services
- Structured error responses for client debugging

---

### 2. Business Logic Layer (`src/llm_service.py`)

**Responsibility:** Core LLM integration and medical entity extraction logic

**Key Features:**
- Prompt engineering with medical context
- JSON validation with retry logic (3 attempts)
- Hallucination prevention mechanisms
- Edge case handling (empty inputs, token limits)
- PHI (Protected Health Information) detection

**Functions:**
- `extract_entities_from_text()` - Main entity extraction with structured output
- `answer_clinical_question()` - Context-aware Q&A with refusal mechanism
- `parse_and_validate_json()` - Multi-layer JSON validation
- Retry logic for malformed LLM responses

**Design Decisions:**
- Temperature set to 0 for deterministic medical outputs
- Groq's `response_format={"type": "json_object"}` for structured data
- Explicit refusal mechanism: "I cannot answer based on the provided note"
- Maximum context length: 50,000 characters (prevents token overflow)

---

### 3. Data Models Layer (`src/schemas.py`)

**Responsibility:** Type-safe data contracts and validation

**Key Models:**
```python
- ClinicalNoteRequest: API request validation
- ExtractedEntity: Response schema with medications, diagnoses, PHI flag
- Medication: Structured medication data (name, dosage, frequency, route)
- QuestionAnswerRequest: Q&A request validation
- QuestionAnswerResponse: Q&A response schema
```

**Design Decisions:**
- Pydantic V2 for automatic validation and serialization
- Field validators for whitespace stripping and data integrity
- JSON schema examples for auto-generated documentation
- Type hints throughout for IDE support and runtime validation

---

### 4. Configuration Layer (`src/config.py`)

**Responsibility:** Centralized configuration management

**Key Features:**
- Environment variable loading via python-dotenv
- Default value fallbacks for development
- Configuration validation on startup
- Secrets management (API keys)

**Configuration Parameters:**
- `GROQ_API_KEY` - API authentication
- `GROQ_MODEL` - Model selection (default: llama-3.1-70b-versatile)
- `LOG_LEVEL` - Logging verbosity (DEBUG/INFO/WARNING/ERROR)

---

### 5. Logging Layer (`src/logger.py`)

**Responsibility:** Centralized logging and observability

**Key Features:**
- Structured logging with timestamps
- Function name and line number tracking
- Different log levels per environment
- No PHI/sensitive data in logs (HIPAA compliance)

**Log Levels:**
- DEBUG: Development diagnostics
- INFO: Normal operations
- WARNING: Recoverable issues
- ERROR: Critical failures requiring attention

---

### 6. PDF Processing Layer (`src/pdf_processor.py`)

**Responsibility:** Extract text from PDF clinical documents

**Key Features:**
- Multi-library support (PyPDF2, pdfplumber)
- Automatic fallback if one library fails
- Metadata extraction (page count, creation date)
- Text cleaning and normalization

**Design Decisions:**
- Optional dependency (graceful degradation)
- Prefer pdfplumber for better text extraction quality
- Return metadata for audit trails

---

## Data Flow

### Entity Extraction Flow

```
1. Client Request
   │
   ├─→ [API Layer] POST /api/v1/extract
   │   └─→ Validate request via Pydantic (ClinicalNoteRequest)
   │
2. Business Logic
   │
   ├─→ [LLM Service] extract_entities_from_text()
   │   ├─→ Construct system prompt with medical guidelines
   │   ├─→ Add few-shot examples
   │   ├─→ Call Groq API with json_object mode
   │   │
   │   └─→ [JSON Validation] parse_and_validate_json()
   │       ├─→ Remove markdown code blocks
   │       ├─→ Extract JSON object
   │       ├─→ Validate required fields
   │       ├─→ Check data types
   │       │
   │       └─→ Retry up to 3 times if malformed
   │
3. Response Construction
   │
   ├─→ [API Layer] Build ExtractedEntity response
   │   ├─→ HTTP 200: Success
   │   ├─→ HTTP 422: Validation failure
   │   └─→ HTTP 503: Groq API unavailable
   │
4. Client Response
   └─→ JSON with diagnoses, medications, PHI flag
```

### Question-Answer Flow

```
1. Client Request
   │
   ├─→ [API Layer] POST /api/v1/question-answer
   │   └─→ Validate QuestionAnswerRequest
   │
2. Business Logic
   │
   ├─→ [LLM Service] answer_clinical_question()
   │   ├─→ Construct context-aware prompt
   │   ├─→ Add refusal mechanism instructions
   │   ├─→ Temperature = 0 (deterministic)
   │   │
   │   └─→ Call Groq API
   │       ├─→ If answer in note → Return answer
   │       └─→ If not in note → Refuse with message
   │
3. Response Construction
   │
   └─→ [API Layer] QuestionAnswerResponse
       └─→ Answer or refusal message
```

---

## Technology Stack

### Core Framework
- **FastAPI** (v0.104.1) - High-performance async web framework
  - Automatic OpenAPI/Swagger documentation
  - Built-in request validation
  - Native async/await support

### LLM Provider
- **Groq** (v0.4.2) - LLM inference API
  - Model: Llama 3.1 70B Versatile
  - JSON mode for structured outputs
  - High throughput (fast inference)

### Data Validation
- **Pydantic** (v2.5.0) - Data validation using Python type hints
  - Automatic request/response validation
  - JSON schema generation
  - Custom validators

### Web Server
- **Uvicorn** (v0.24.0) - ASGI server
  - Production-ready performance
  - Hot reload for development
  - Worker process management

### UI Framework
- **Streamlit** (v1.28.0+) - Interactive web interface
  - Rapid prototyping
  - Built-in components for medical UI
  - PDF upload support

### PDF Processing
- **PyPDF2** (v3.0.0+) - PDF text extraction
- **pdfplumber** (v0.10.0+) - Enhanced PDF parsing

### Testing
- **pytest** (v7.4.0) - Unit and integration testing
- **httpx** (v0.24.1) - Async HTTP client for API testing

### Utilities
- **python-dotenv** (v1.0.0) - Environment variable management
- **pandas** (v2.0.0+) - Data analysis (comparison demo)
- **plotly** (v5.18.0+) - Interactive visualizations

---

## Design Patterns

### 1. Separation of Concerns
- **API Layer:** HTTP concerns only
- **Service Layer:** Business logic isolated from HTTP
- **Data Layer:** Type-safe contracts via Pydantic

### 2. Dependency Injection
- Configuration injected via `Config` class
- Groq client instantiated once, reused across requests
- Testable via mocking

### 3. Error Handling Strategy
```python
try:
    # Business logic
except ValidationError:
    # HTTP 422 - Client validation failure
except GroqAPIError:
    # HTTP 503 - External service unavailable
except Exception:
    # HTTP 500 - Unexpected server error
```

### 4. Retry Pattern
- LLM responses retry up to 3 times
- Exponential backoff for rate limiting (future)
- Circuit breaker pattern (future scaling)

### 5. Factory Pattern
- Logger factory creates configured loggers
- PDF processor factory selects best available library

---

## Scaling Architecture

### Current Bottlenecks
1. **Synchronous Processing:** Single-threaded request handling
2. **LLM API Rate Limits:** Groq free tier limitations
3. **No Caching:** Repeated notes re-processed fully
4. **Single Instance:** No horizontal scaling

### Production Scaling Strategy

#### Phase 1: Horizontal Scaling (1,000 req/min)
```
┌─────────────────┐
│  Load Balancer  │ (AWS ALB / Nginx)
│   (Round Robin) │
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┐
    ▼         ▼        ▼        ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│API #1 │ │API #2 │ │API #3 │ │API #N │
└───────┘ └───────┘ └───────┘ └───────┘
    │         │        │        │
    └─────────┴────────┴────────┘
              ▼
         ┌─────────┐
         │ Groq API│
         └─────────┘
```

**Implementation:**
- Deploy 10-20 API instances
- AWS ECS Fargate or Kubernetes
- Health check-based routing
- Auto-scaling based on CPU/memory

**Expected Throughput:** 500-1,000 requests/minute

---

#### Phase 2: Asynchronous Processing (5,000 req/min)
```
┌─────────┐      ┌──────────────┐      ┌─────────────┐
│ API     │─────▶│ Message Queue│─────▶│  Workers    │
│ Ingress │      │ (RabbitMQ/   │      │  (Async     │
│         │      │  AWS SQS)    │      │  Processing)│
└─────────┘      └──────────────┘      └──────┬──────┘
                                              │
                                              ▼
                                        ┌──────────┐
                                        │ Groq API │
                                        └──────────┘
```

**Implementation:**
- API receives request → Returns job ID immediately
- Request queued in RabbitMQ/SQS
- Worker pool processes queue asynchronously
- WebSocket or polling for status updates

**Expected Throughput:** 3,000-5,000 requests/minute

---

#### Phase 3: Caching + Multi-Model (10,000+ req/min)
```
┌──────────┐      ┌───────────┐      ┌────────────┐
│  Client  │─────▶│  Redis    │─────▶│   API      │
│          │      │  Cache    │      │  Cluster   │
└──────────┘      └───────────┘      └─────┬──────┘
                   Cache Hit: 0 tokens           │
                   Cache Miss: Continue ▼        │
                                    ┌────────────┴─────┐
                                    │  LLM Router      │
                                    │  (Load Balance)  │
                                    └┬─────┬─────┬────┘
                                     │     │     │
                                  ┌──▼─┐ ┌─▼──┐ ┌▼───┐
                                  │Key1│ │Key2│ │Key3│
                                  │Groq│ │Groq│ │Groq│
                                  └────┘ └────┘ └────┘
```

**Implementation:**
- Redis caches results by clinical note hash
- 20-40% cache hit rate for repeated notes
- Multiple API keys rotate for rate limit increase
- TTL: 24 hours for cached results

**Expected Throughput:** 10,000+ requests/minute

**Cost Estimate:** $1,500-$3,000/month on AWS

---

## Security Architecture

### Authentication & Authorization
- **API Key Authentication** (future)
  - `X-API-Key` header validation
  - Rate limiting per API key
- **OAuth 2.0** (future enterprise)
  - Hospital system integration
  - Role-based access control

### Data Security
- **PHI Protection**
  - No PHI stored in logs
  - No PHI cached (unless encrypted)
  - HIPAA compliance guidelines followed
- **Data Encryption**
  - TLS 1.3 in transit
  - Encrypted environment variables
  - Secrets Manager for production (AWS Secrets Manager)

### Network Security
- **CORS Configuration**
  - Whitelist allowed origins
  - Secure headers (HSTS, CSP)
- **Rate Limiting** (future)
  - Per-IP limiting: 60 requests/minute
  - Per-API-Key: 1,000 requests/minute

### Input Validation
- **Request Validation**
  - Pydantic schemas reject malformed data
  - Max input length: 50,000 characters
  - SQL injection prevention (no DB currently)
- **Output Sanitization**
  - JSON-only responses
  - No script injection in error messages

---

## Deployment Architecture

### Development Environment
```yaml
docker-compose.yml:
  services:
    - clinical-note-api:
        build: ./Dockerfile
        ports: [8000:8000]
        environment:
          - GROQ_API_KEY=${GROQ_API_KEY}
          - LOG_LEVEL=DEBUG
        volumes:
          - ./logs:/app/logs
```

### Production Environment (AWS Example)
```
┌─────────────────────────────────────────────┐
│              AWS Cloud                      │
│  ┌─────────────────────────────────────┐   │
│  │  VPC (10.0.0.0/16)                  │   │
│  │  ┌──────────────┐  ┌──────────────┐ │   │
│  │  │  Public      │  │  Private     │ │   │
│  │  │  Subnet      │  │  Subnet      │ │   │
│  │  │              │  │              │ │   │
│  │  │ ┌──────────┐ │  │ ┌──────────┐ │ │   │
│  │  │ │   ALB    │ │  │ │  ECS     │ │ │   │
│  │  │ │          │ │  │ │ Fargate  │ │ │   │
│  │  │ └──────────┘ │  │ │ Cluster  │ │ │   │
│  │  └──────┬───────┘  │ └────┬─────┘ │ │   │
│  └─────────┼──────────┴──────┼───────┘ │   │
│            │                 │         │   │
│  ┌─────────▼──────┐ ┌────────▼──────┐  │   │
│  │  CloudWatch    │ │  Secrets      │  │   │
│  │  Logs/Metrics  │ │  Manager      │  │   │
│  └────────────────┘ └───────────────┘  │   │
└─────────────────────────────────────────────┘
```

**Components:**
- **ALB (Application Load Balancer):** HTTPS termination, routing
- **ECS Fargate:** Serverless container orchestration
- **CloudWatch:** Centralized logging and metrics
- **Secrets Manager:** API key and credential storage

---

## Monitoring & Observability

### Logging Strategy
- **Structured Logs:** JSON format for parsing
- **Log Levels:**
  - DEBUG: Function entry/exit, variable values
  - INFO: API requests, LLM calls, extraction results
  - WARNING: Retry attempts, rate limiting
  - ERROR: Exceptions, validation failures, API errors

### Metrics to Track
```
Application Metrics:
- Request rate (req/sec)
- Response time (p50, p95, p99)
- Error rate by status code
- LLM token usage
- Cache hit rate

Business Metrics:
- Medications extracted per request
- Diagnoses extracted per request
- PHI detection rate
- Question-answer refusal rate
```

### Health Checks
```python
GET /health
Response:
{
  "status": "healthy",
  "groq_api": "connected",
  "version": "1.0.0",
  "uptime": 34523
}
```

### Alerting (Future)
- **Critical Alerts:**
  - API error rate > 5%
  - Groq API unavailable
  - Response time > 5 seconds (p95)
- **Warning Alerts:**
  - Error rate > 1%
  - Cache miss rate > 80%
  - Memory usage > 80%

---

## Future Enhancements

### Short-Term (1-3 months)
1. **Batch Processing API**
   - Process multiple notes in one request
   - Async processing with job IDs
2. **Result Caching**
   - Redis integration
   - Cache invalidation strategy
3. **API Key Authentication**
   - Multi-tenant support
   - Usage tracking per client

### Medium-Term (3-6 months)
1. **Database Integration**
   - PostgreSQL for audit logs
   - Query history and analytics
2. **Advanced PHI Redaction**
   - Automatic PHI masking in responses
   - Configurable redaction levels
3. **Multi-Model Support**
   - Fallback to OpenAI/Anthropic
   - Model selection per request
   - Cost optimization routing

### Long-Term (6-12 months)
1. **Fine-Tuned Models**
   - Domain-specific medical model
   - Improved accuracy for edge cases
2. **Real-Time Streaming**
   - WebSocket support
   - Progressive entity extraction
3. **Integration with EHR Systems**
   - HL7 FHIR support
   - Epic/Cerner connectors

---

## Appendix

### Environment Variables Reference
```bash
# Required
GROQ_API_KEY=gsk_...              # Groq API authentication

# Optional
GROQ_MODEL=llama-3.1-70b-versatile  # LLM model selection
LOG_LEVEL=INFO                     # Logging verbosity
PORT=8000                          # API server port
```

### API Response Examples

**Successful Extraction:**
```json
{
  "diagnoses": [
    "Type 2 Diabetes Mellitus",
    "Hypertension"
  ],
  "medications": [
    {
      "name": "Metformin",
      "dosage": "500mg",
      "frequency": "BID",
      "route": "PO"
    }
  ],
  "phi_detected": true
}
```

**Error Response:**
```json
{
  "detail": {
    "error": "validation_error",
    "message": "Clinical note cannot be empty",
    "status_code": 400
  }
}
```

---

**Document Owner:** Clinical Note Processing API Team  
**Contact:** See README.md for project maintainer information  
**License:** See LICENSE file in repository root
