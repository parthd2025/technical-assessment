# Technical Implementation Guide

## Overview
This document provides detailed technical explanations for the Clinical Note Processing API implementation.

## Architecture Overview

### System Design
```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────────────┐
│   FastAPI Server    │
│  (API Layer)        │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  LLM Service Layer  │
│  (Business Logic)   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   Groq API          │
│   (Llama 3.1)       │
└─────────────────────┘
```

### Component Breakdown

#### 1. API Layer (`src/api.py`)
- **FastAPI Application**: Modern async web framework
- **Endpoints**:
  - `GET /health`: Health check for monitoring
  - `POST /api/v1/extract`: Structured data extraction
  - `POST /api/v1/query`: Question answering
- **Responsibilities**:
  - HTTP request/response handling
  - Input validation via Pydantic
  - Error handling with proper status codes
  - Automatic OpenAPI documentation

#### 2. LLM Service Layer (`src/llm_service.py`)
- **Groq Client**: Interface to Groq's API
- **Functions**:
  - `extract_entities_from_text()`: Medical entity extraction
  - `answer_clinical_question()`: Q&A functionality
- **Responsibilities**:
  - Prompt engineering
  - LLM API communication
  - Response parsing and validation
  - Error handling for LLM failures

#### 3. Data Models (`src/schemas.py`)
- **Pydantic Models**: Type-safe data structures
- **Models**:
  - `ClinicalNoteInput`: Request validation
  - `Medication`: Structured medication data
  - `ExtractedEntity`: Extraction response
  - `QueryInput`/`QueryResponse`: Q&A interface
- **Benefits**:
  - Automatic validation
  - JSON serialization
  - OpenAPI schema generation

#### 4. Configuration (`src/config.py`)
- **Environment-based configuration**
- **Settings**:
  - API keys (never hardcoded)
  - Model selection
  - Temperature and token limits
- **Validation**: Fails fast if config is invalid

## LLM Engineering Details

### 1. Structured Extraction (`/api/v1/extract`)

#### Prompt Design
```
System Prompt:
- Define role: "medical information extraction assistant"
- Set constraints: ONLY valid JSON, NO extra text
- Define schema explicitly
- List PHI examples
- Emphasize: No hallucinations

User Prompt:
- Provide clinical note
- Request specific entities
- Remind: JSON only
```

#### JSON Stability Techniques
1. **Groq JSON Mode**: `response_format={"type": "json_object"}`
   - Forces LLM to output valid JSON
   - Rejects invalid responses automatically
2. **Temperature 0**: Deterministic outputs
3. **Explicit Schema**: Define exact structure in prompt
4. **Post-processing**: Parse and validate with Pydantic
5. **Error Handling**: Try-catch for JSON parsing errors

#### PHI Detection Strategy
- **Pattern-based**: LLM identifies names, DOBs, phone numbers
- **Examples in Prompt**: Show what counts as PHI
- **Boolean Output**: Simple true/false for compliance workflows
- **Conservative**: Better to flag potential PHI than miss it

### 2. Clinical Q&A (`/api/v1/query`)

#### Hallucination Prevention
This is CRITICAL for healthcare applications.

**Techniques**:
1. **Explicit Refusal Instruction**:
   - System prompt: "If answer not in text, say: 'I cannot answer...'"
   - LLM learns to refuse gracefully
2. **Grounding**:
   - "Answer ONLY based on information explicitly stated"
   - "Do not use your medical knowledge"
3. **Temperature 0**: No creativity/speculation
4. **Quote-based Reasoning**:
   - Encourage quoting relevant sections
   - Improves accuracy and traceability
5. **Testing**: Verify with unanswerable questions

#### Example Prompt Flow
```
System: You are a medical assistant. Answer ONLY from the note.
        If not in note → "I cannot answer..."

User: Clinical Note: [text]
      Question: [question]
      Answer:

LLM: [Answer based strictly on note]
```

### 3. Model Selection: Llama 3.1 70B

**Why Llama 3.1 70B?**
- **Parameters**: 70 billion → strong reasoning
- **Context Window**: 128K tokens → handles long clinical notes
- **Instruction Following**: Excellent with system prompts
- **Speed**: Groq inference is 10-20x faster than standard
- **Cost**: ~$0.50 per 1M tokens (cheaper than GPT-4)

**Alternative Models**:
- `mixtral-8x7b-32768`: Faster, cheaper, slightly less accurate
- `llama-3.3-70b-versatile`: Newer version with improved reasoning

## Error Handling Strategy

### HTTP Status Codes
- `200 OK`: Successful request
- `422 Unprocessable Entity`: Invalid input (Pydantic validation)
- `500 Internal Server Error`: LLM or server error

### Error Scenarios Handled
1. **Missing API Key**: Fails at startup with clear message
2. **Invalid JSON from LLM**: Caught and re-raised as 422
3. **LLM API Timeout**: Caught and returned as 500
4. **Empty Clinical Note**: Validated by Pydantic
5. **Network Errors**: Caught and logged

### Example Error Response
```json
{
  "detail": "Error extracting entities: LLM returned invalid JSON"
}
```

## Testing Strategy

### Unit Tests (`tests/test_api.py`)
- **Mock LLM Responses**: No real API calls in tests
- **Test Coverage**:
  - Valid inputs → correct outputs
  - Invalid inputs → proper error codes
  - Missing fields → validation errors
  - Edge cases → graceful handling

### Manual Testing (`test_manual.py`)
- **End-to-end**: Real API calls to running server
- **Sample Data**: Uses assignment's sample clinical note
- **Multiple Scenarios**: Answerable and unanswerable questions

### Integration Testing (Future)
- Test with real Groq API
- Measure latency and accuracy
- Test rate limiting and retries

## Performance Considerations

### Current Performance
- **Latency**: ~1-3 seconds per request (mostly LLM API call)
- **Throughput**: Single instance can handle ~5-10 req/sec
- **Bottleneck**: LLM API call is synchronous

### Optimization Opportunities
1. **Async Processing**: Use FastAPI's async features
2. **Connection Pooling**: Reuse HTTP connections
3. **Batch Processing**: Group multiple requests
4. **Caching**: Cache frequent queries (Redis)
5. **Streaming**: Stream LLM responses for faster TTFB

## Security Considerations

### Current Implementation
- ✓ **Environment Variables**: API keys not in code
- ✓ **Input Validation**: Pydantic prevents injection
- ✓ **.gitignore**: Secrets excluded from version control
- ✓ **Error Messages**: Don't leak sensitive info

### Production Additions Needed
- ⚠ **Authentication**: Add JWT or API key auth
- ⚠ **Rate Limiting**: Prevent abuse
- ⚠ **HTTPS Only**: Encrypt in transit
- ⚠ **Audit Logging**: Track all requests
- ⚠ **PHI Encryption**: Encrypt at rest
- ⚠ **HIPAA Compliance**: BAA with Groq

## Monitoring & Observability

### Recommended Metrics
- **Request Rate**: Requests per second
- **Latency**: p50, p95, p99 response times
- **Error Rate**: 4xx and 5xx errors
- **LLM Metrics**:
  - API call duration
  - Token usage
  - Cost per request

### Recommended Tools
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards
- **ELK/Loki**: Log aggregation
- **Sentry**: Error tracking

## Deployment Considerations

### Docker
- **Multi-stage Build**: Could reduce image size
- **Health Checks**: Built into docker-compose
- **Environment Variables**: Injected at runtime
- **Port Mapping**: 8000:8000

### Kubernetes (Production)
- **Deployment**: 10-50 replicas
- **Service**: ClusterIP with Ingress
- **ConfigMap**: Non-sensitive config
- **Secret**: API keys
- **HPA**: Auto-scaling based on CPU/memory
- **Resource Limits**: 1 CPU, 2GB RAM per pod

### Cloud Providers
- **AWS**: ECS/EKS + ALB
- **GCP**: Cloud Run or GKE
- **Azure**: AKS or Container Apps

## Cost Analysis

### Current Costs (at 10,000 req/min)
- **Groq API**: ~$50-$200/day
- **Infrastructure**: ~$50-$100/day
- **Total**: ~$100-$300/day = $3K-$9K/month

### Cost Optimization
- **Caching**: 20-40% savings
- **Smart Routing**: Use cheaper models when possible
- **Request Deduplication**: Avoid duplicate processing

## Future Enhancements

### Short Term
1. Add authentication and authorization
2. Implement request rate limiting
3. Add caching layer (Redis)
4. Improve test coverage to 90%+

### Medium Term
1. Async processing with message queue
2. Database for results storage
3. Batch processing endpoint
4. Multi-model support (fallbacks)

### Long Term
1. Fine-tuned model for clinical notes
2. Self-hosted LLM option
3. Real-time streaming responses
4. Advanced PHI redaction

## Lessons Learned

### What Worked Well
- **Groq JSON Mode**: Eliminated JSON parsing errors
- **Pydantic**: Caught bugs early
- **Temperature 0**: Consistent outputs
- **Explicit Prompts**: Better than vague instructions

### Challenges Faced
- **Hallucination Prevention**: Required careful prompt design
- **JSON Stability**: Initial attempts had formatting issues
- **PHI Detection**: Balancing false positives vs false negatives

### Best Practices
1. **Prompt Engineering**: Spend time on system prompts
2. **Validation**: Never trust LLM output without validation
3. **Error Handling**: Graceful degradation is key
4. **Testing**: Mock external APIs in unit tests
5. **Documentation**: Clear README is critical

## References
- [Groq Documentation](https://console.groq.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [HIPAA Guidelines](https://www.hhs.gov/hipaa/index.html)
