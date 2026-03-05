# Clinical Note Processing System - Technical Documentation

**Version:** 1.0.0  
**Date:** March 4, 2026  
**Status:** Production Ready

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Solution Architecture](#3-solution-architecture)
4. [Technical Implementation](#4-technical-implementation)
5. [Logging & Debugging](#5-logging--debugging)
6. [Use Cases](#6-use-cases)
7. [Best Practices](#7-best-practices)
8. [Operational Flow](#8-operational-flow)
9. [Verification & Testing](#9-verification--testing)
10. [Future Enhancements](#10-future-enhancements)

---

## 1. Project Overview

### What is This Project?

The **Clinical Note Processing System** is an AI-powered application that extracts structured medical information from unstructured clinical notes and provides intelligent question-answering capabilities. It consists of:

- **Backend API** (FastAPI): RESTful service for entity extraction and Q&A
- **Frontend UI** (Streamlit): Web interface for healthcare practitioners
- **LLM Integration** (Groq/Llama 3.1): Advanced natural language processing
- **Logging System**: Comprehensive debugging and monitoring

### Core Capabilities

1. **Structured Entity Extraction**
   - Diagnoses/Medical Conditions
   - Medications (name, dosage, frequency)
   - PHI (Protected Health Information) Detection

2. **Clinical Question Answering**
   - Context-aware responses based strictly on note content
   - Refusal to answer when information is not present
   - No hallucinations or external knowledge injection

3. **HIPAA Compliance Support**
   - PHI detection and flagging
   - Secure data handling
   - Audit logging

---

## 2. Problem Statement

### Healthcare Challenges Addressed

#### A. Unstructured Data Problem
**Issue:** Clinical notes in EMR/EHR systems are unstructured text, making it difficult to:
- Extract specific information quickly
- Perform data analysis at scale
- Identify medication errors
- Track diagnoses programmatically

**Impact:**
- Increased time burden on healthcare providers
- Higher risk of medication errors
- Difficult to aggregate data for research
- Manual review required for compliance

#### B. Information Retrieval Inefficiency
**Issue:** Healthcare providers need to:
- Quickly verify specific details in lengthy notes
- Cross-reference medication dosages
- Confirm diagnosis information
- Review multiple notes for patient history

**Impact:**
- Time-consuming manual search through notes
- Potential for overlooking critical information
- Delayed decision-making
- Reduced time for patient care

#### C. HIPAA Compliance Complexity
**Issue:** Organizations must:
- Identify and protect PHI in clinical documents
- Ensure proper handling of sensitive information
- Maintain audit trails
- Train staff on compliance

**Impact:**
- Risk of HIPAA violations ($100 - $50,000 per violation)
- Complex compliance workflows
- Manual PHI identification is error-prone

---

## 3. Solution Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend                       │
│  (Clinical Note Assistant - Web Interface)                   │
│  - Note Input                                                │
│  - Extraction Display                                        │
│  - Q&A Interface                                             │
│  - JSON Viewer                                               │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  Endpoints:                                                  │
│  - POST /api/v1/extract  (Entity Extraction)                │
│  - POST /api/v1/query    (Q&A)                              │
│  - GET  /health          (Health Check)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  LLM Service Layer                           │
│  - extract_entities_from_text()                             │
│  - answer_clinical_question()                               │
└────────────────────┬────────────────────────────────────────┘
                     │ API Call
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Groq API (Llama 3.1 70B)                       │
│  - JSON Mode for Structured Output                          │
│  - Temperature = 0 (Deterministic)                          │
│  - Prompt Engineering for Medical NLP                       │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Streamlit | Interactive web UI |
| Backend | FastAPI | RESTful API server |
| Validation | Pydantic | Data validation & schemas |
| LLM Provider | Groq | Fast inference API |
| LLM Model | Llama 3.1 70B | Large language model |
| Logging | Python logging | Debugging & monitoring |
| Config | python-dotenv | Environment management |

---

## 4. Technical Implementation

### 4.1 Entity Extraction Pipeline

**Flow:**
```
Clinical Note (Text)
    ↓
API Request Validation (Pydantic)
    ↓
System Prompt + User Prompt
    ↓
Groq API Call (JSON Mode)
    ↓
JSON Response Parsing
    ↓
Pydantic Validation
    ↓
Structured Response (ExtractedEntity)
```

**Key Implementation Details:**

#### Prompt Engineering
```python
# System prompt ensures:
1. JSON-only output (no markdown, no explanations)
2. Extraction of only explicitly stated information
3. No hallucinations or inferences
4. PHI detection per HIPAA guidelines
```

#### JSON Mode
```python
response_format={"type": "json_object"}
```
- Forces LLM to return valid JSON
- Reduces parsing errors
- Ensures consistent structure

#### Temperature = 0
```python
temperature=0
```
- Deterministic outputs
- No creative variations
- Consistent results for same input

### 4.2 Question Answering Pipeline

**Flow:**
```
Clinical Note + Question
    ↓
API Request Validation
    ↓
Context-Aware Prompt
    ↓
Groq API Call
    ↓
Answer Validation
    ↓
Response (Answer or Refusal)
```

**Key Implementation Details:**

#### Strict Context Adherence
- LLM instructed to answer ONLY from provided note
- Explicit refusal message if answer not present
- No external medical knowledge used

#### Refusal Handling
```python
"I cannot answer this based on the provided clinical note."
```
- Prevents hallucinations
- Maintains accuracy
- Clear indication of limitations

### 4.3 Data Models (Pydantic Schemas)

#### ExtractedEntity
```python
class ExtractedEntity(BaseModel):
    diagnoses: List[str]
    medications: List[Medication]
    phi_detected: bool
```

#### Medication
```python
class Medication(BaseModel):
    name: str
    dosage: str
    frequency: str
```

**Benefits:**
- Automatic validation
- Type safety
- API documentation generation
- Serialization/deserialization

---

## 5. Logging & Debugging

### 5.1 Logging Architecture

**Purpose:**
- Debug issues in production
- Track API performance
- Monitor LLM usage and costs
- Audit trail for compliance

### 5.2 Logging Levels

| Level | Use Case | Example |
|-------|----------|---------|
| DEBUG | Development details | "Raw LLM response: {...}" |
| INFO | Normal operations | "Extraction completed - Duration: 1234ms" |
| WARNING | Potential issues | "Medication not in dict format" |
| ERROR | Failures | "LLM API call failed: timeout" |

### 5.3 Log Locations

- **Console Output**: Real-time monitoring during development
- **File Output**: `logs/clinical_api_YYYYMMDD.log`

### 5.4 Structured Logging

**API Requests:**
```
INFO: API Request: /api/v1/extract | note_length=450
```

**API Responses:**
```
INFO: API Response: /api/v1/extract | status=success | duration=1234ms | 
      diagnoses_count=2 | medications_count=3 | phi_detected=True
```

**LLM Calls:**
```
DEBUG: LLM Call: extract | model=llama-3.1-70b-versatile | 
       tokens=456 | note_length=450
```

### 5.5 Debugging Workflow

When issues occur:

1. **Check API Logs** (`logs/clinical_api_*.log`)
   - Find the timestamp of the issue
   - Look for ERROR or WARNING messages
   - Check request/response details

2. **Examine LLM Responses**
   - DEBUG logs show raw LLM output
   - Verify JSON structure
   - Check for unexpected content

3. **Verify Input Data**
   - Check note length
   - Look for special characters
   - Validate encoding

4. **Track Performance**
   - Review duration_ms values
   - Identify slow operations
   - Monitor token usage

---

## 6. Use Cases

### 6.1 Primary Use Cases

#### UC1: Emergency Department Triage
**Scenario:** ER doctor needs quick medication review

**Flow:**
1. Paste transfer note from previous hospital
2. Click "Extract Information"
3. Review medications instantly (dosage, frequency)
4. Verify specific details with Q&A

**Benefit:** Reduces medication errors, saves 5-10 minutes per patient

#### UC2: Medication Reconciliation
**Scenario:** Pharmacist reviewing discharge medications

**Flow:**
1. Input discharge summary
2. Extract medications automatically
3. Compare with current prescriptions
4. Ask questions about discrepancies

**Benefit:** Ensures accurate medication lists, prevents adverse events

#### UC3: Clinical Documentation Review
**Scenario:** Quality assurance review for compliance

**Flow:**
1. Input clinical note
2. Check PHI detection flag
3. Review structured data for completeness
4. Generate audit report

**Benefit:** Automated PHI detection, faster audits

#### UC4: Research Data Extraction
**Scenario:** Extracting data from historical clinical notes

**Flow:**
1. Process batch of notes
2. Extract diagnoses and medications
3. Export structured JSON data
4. Load into research database

**Benefit:** Scalable data extraction, enables retrospective studies

### 6.2 Secondary Use Cases

- **Medical Training**: Students practice extracting key information
- **Handoff Communication**: Standardize information transfer between shifts
- **Insurance Claims**: Extract required information for claims processing
- **Clinical Decision Support**: Integrate with CDS systems

---

## 7. Best Practices

### 7.1 Development Best Practices

#### Code Organization
✅ **DO:**
- Separate concerns (API, LLM, data models)
- Use Pydantic for validation
- Implement comprehensive error handling
- Add docstrings to all functions

❌ **DON'T:**
- Mix business logic with API routes
- Skip input validation
- Ignore error cases
- Leave functions undocumented

#### Prompt Engineering
✅ **DO:**
- Be explicit about output format
- Include negative examples (what NOT to do)
- Test with edge cases
- Version your prompts

❌ **DON'T:**
- Assume LLM will infer requirements
- Use vague instructions
- Skip testing with real data
- Modify prompts without version control

#### Error Handling
✅ **DO:**
- Catch specific exceptions
- Log errors with context
- Provide meaningful error messages
- Implement retry logic for API calls

❌ **DON'T:**
- Use bare `except:` clauses
- Swallow errors silently
- Return generic error messages
- Ignore transient failures

### 7.2 Production Best Practices

#### Security
- ✅ Store API keys in environment variables
- ✅ Use HTTPS in production
- ✅ Implement rate limiting
- ✅ Sanitize inputs
- ✅ Enable CORS selectively

#### Performance
- ✅ Set appropriate timeouts
- ✅ Monitor API latency
- ✅ Cache common requests (if stateless)
- ✅ Use connection pooling
- ✅ Implement circuit breakers

#### Monitoring
- ✅ Log all API requests/responses
- ✅ Track error rates
- ✅ Monitor LLM token usage
- ✅ Set up alerts for failures
- ✅ Regular log rotation

### 7.3 Healthcare-Specific Best Practices

#### HIPAA Compliance
- ✅ Log access to PHI
- ✅ Encrypt data in transit (HTTPS)
- ✅ Encrypt data at rest (if stored)
- ✅ Implement access controls
- ✅ Regular security audits

#### Clinical Safety
- ✅ Never use system for clinical diagnosis
- ✅ Clearly indicate system limitations
- ✅ Require human review of all outputs
- ✅ Include disclaimers in UI
- ✅ Validate with clinical staff

---

## 8. Operational Flow

### 8.1 Complete User Flow

```
┌──────────────────────────┐
│ User Opens Streamlit UI  │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Health Check: API Status │
│ ✅ Connected / ❌ Offline │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Paste Clinical Note (L)  │
│ [Text Area - 400px]      │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Click "Extract Info"     │
│ Loading Spinner...       │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Display Results (R)      │
│ - PHI Warning            │
│ - Diagnoses List         │
│ - Medication Cards       │
│ - JSON Viewer            │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Optional: Ask Question   │
│ [Input Box + Ask Button] │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Display Answer           │
│ ✅ Success / ⚠️ Warning   │
└──────────────────────────┘
```

### 8.2 Backend Processing Flow

```
[Request Received]
       │
       ▼
[Validate Input] ────────► [422 Error]
       │
       ▼
[Log Request Details]
       │
       ▼
[Call LLM Service]
       │
       ├──► [Timeout] ────► [500 Error]
       │
       ├──► [Invalid JSON] ► [422 Error]
       │
       └──► [Success]
              │
              ▼
       [Validate Schema]
              │
              ▼
       [Log Response]
              │
              ▼
       [Return 200 OK]
```

### 8.3 Error Recovery Flow

```
[Error Detected]
       │
       ▼
[Log Error + Context]
       │
       ├──► [Transient?] ──Yes──► [Retry (3x)]
       │                              │
       │                              ├──► [Success]
       │                              └──► [Fail] ──┐
       │                                            │
       └────────────No────────────────────────────►│
                                                    ▼
                                            [Return Error]
                                                    │
                                                    ▼
                                         [User-Friendly Message]
                                                    │
                                                    ▼
                                            [Suggest Action]
```

---

## 9. Verification & Testing

### 9.1 Testing Strategy

#### Unit Tests
```python
# tests/test_api.py - Already exists
- test_health_check()
- test_extract_entities()
- test_query_endpoint()
- test_invalid_inputs()
```

**Coverage:**
- ✅ API endpoints
- ✅ Error handling
- ✅ Schema validation
- ⚠️ LLM service mocking (add this)

#### Integration Tests
```python
# tests/test_integration.py - Create this
- test_end_to_end_extraction()
- test_end_to_end_query()
- test_phi_detection()
- test_timeout_handling()
```

#### Manual Testing Checklist

**Entity Extraction:**
- [ ] Simple note with 1 diagnosis, 1 medication
- [ ] Complex note with multiple diagnoses and medications
- [ ] Note with no medications
- [ ] Note with no diagnoses
- [ ] Note with PHI (name, DOB, phone)
- [ ] Note without PHI
- [ ] Very long note (>2000 words)
- [ ] Note with special characters
- [ ] Empty note (error case)

**Question Answering:**
- [ ] Question answered from note
- [ ] Question not answerable from note
- [ ] Ambiguous question
- [ ] Very specific question
- [ ] Question about medication dosage
- [ ] Question about diagnosis
- [ ] Empty question (error case)

### 9.2 Verification Criteria

#### Functional Requirements
- ✅ Extracts diagnoses accurately (>90%)
- ✅ Extracts medications with dosage and frequency (>90%)
- ✅ Detects PHI correctly (>95%)
- ✅ Answers questions from note content
- ✅ Refuses to answer when info not present
- ✅ Returns valid JSON always

#### Non-Functional Requirements
- ✅ API response time <5 seconds (95th percentile)
- ✅ System uptime >99%
- ✅ Handles concurrent requests (10+ users)
- ✅ Logs all operations
- ✅ Graceful error handling

#### Security Requirements
- ✅ API key not exposed in logs
- ✅ PHI not logged in plain text
- ✅ HTTPS in production
- ✅ Input sanitization
- ✅ Rate limiting implemented

### 9.3 Performance Benchmarks

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Latency (Extract) | <3s | duration_ms in logs |
| API Latency (Query) | <2s | duration_ms in logs |
| LLM Token Usage (Extract) | <1000 tokens | tokens in logs |
| LLM Token Usage (Query) | <300 tokens | tokens in logs |
| Concurrent Users | 10+ | Load testing |
| Error Rate | <1% | Error logs / Total requests |

---

## 10. Future Enhancements

### 10.1 Immediate Improvements (v1.1)

1. **Batch Processing**
   - Process multiple notes at once
   - Export results to CSV/Excel
   - Integration with EMR systems

2. **Advanced PHI Detection**
   - Specific PHI types (dates, MRN, SSN)
   - De-identification capabilities
   - PHI masking/redaction

3. **User Authentication**
   - Login system
   - Role-based access control
   - Audit logs per user

### 10.2 Medium-Term Enhancements (v2.0)

1. **Multi-Language Support**
   - Spanish, French, etc.
   - Unicode handling improvements

2. **Model Fine-Tuning**
   - Custom model trained on medical notes
   - Improved accuracy for specialty areas
   - Reduced latency

3. **Advanced Analytics**
   - Trending diagnoses
   - Medication statistics
   - PHI compliance dashboard

### 10.3 Long-Term Vision (v3.0)

1. **Real-Time Integration**
   - Live EMR/EHR integration
   - Automatic note processing
   - Alerts for critical findings

2. **Clinical Decision Support**
   - Drug interaction checking
   - Diagnosis suggestions
   - Treatment recommendations

3. **Research Platform**
   - De-identified data repository
   - Query interface for researchers
   - Cohort identification

---

## Appendix A: Configuration Reference

### Environment Variables

```bash
# .env file
GROQ_API_KEY=gsk_...                    # Required: Groq API key
GROQ_MODEL=llama-3.1-70b-versatile      # Optional: Model name
LLM_TEMPERATURE=0                        # Optional: Determinism (0-1)
LLM_MAX_TOKENS_EXTRACT=1000             # Optional: Max tokens for extraction
LLM_MAX_TOKENS_QUERY=300                # Optional: Max tokens for Q&A
APP_HOST=0.0.0.0                        # Optional: API host
APP_PORT=8000                            # Optional: API port
```

### Dependencies

```
fastapi==0.104.1       # Web framework
uvicorn==0.24.0        # ASGI server
pydantic==2.5.0        # Data validation
groq==0.4.2            # LLM API client
python-dotenv==1.0.0   # Config management
streamlit>=1.28.0      # Web UI
requests>=2.31.0       # HTTP client
pytest>=7.4.0          # Testing
```

---

## Appendix B: Troubleshooting Guide

### Common Issues

#### Issue 1: "GROQ_API_KEY not found"
**Solution:** Create `.env` file with `GROQ_API_KEY=your_key_here`

#### Issue 2: "API Offline"
**Solution:** Start FastAPI server: `uvicorn src.api:app --reload`

#### Issue 3: "LLM returned invalid JSON"
**Solution:** Check logs for raw response, may need prompt adjustment

#### Issue 4: "Python 3.13 compatibility error"
**Solution:** Use Python 3.12 (pydantic-core not compatible with 3.13 yet)

#### Issue 5: "Timeout errors"
**Solution:** Increase timeout in requests (currently 30s) or check network

---

## Appendix C: API Reference

### POST /api/v1/extract

**Request:**
```json
{
  "clinical_note": "Patient has Type 2 Diabetes. Started on Metformin 500mg BID."
}
```

**Response:**
```json
{
  "diagnoses": ["Type 2 Diabetes"],
  "medications": [
    {
      "name": "Metformin",
      "dosage": "500mg",
      "frequency": "BID"
    }
  ],
  "phi_detected": false
}
```

### POST /api/v1/query

**Request:**
```json
{
  "clinical_note": "Patient on Lisinopril 10mg daily for hypertension.",
  "question": "What is the dosage of Lisinopril?"
}
```

**Response:**
```json
{
  "answer": "The Lisinopril dosage is 10mg daily."
}
```

---

## Document Control

**Author:** Clinical Note Processing Team  
**Reviewers:** Technical Lead, Clinical SME  
**Last Updated:** March 4, 2026  
**Next Review:** June 4, 2026  
**Version History:**
- v1.0.0 (March 4, 2026): Initial comprehensive documentation
