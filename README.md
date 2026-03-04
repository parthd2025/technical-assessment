# Clinical Note Processing API

## Overview
This project provides a production-ready REST API for processing unstructured clinical notes using Groq's LLM API (Llama 3.1). It includes two endpoints:
1. **Structured Extraction**: Extracts structured medical data from clinical notes.
2. **Clinical Q&A**: Answers questions based on the content of clinical notes.

## Features
- **Endpoint 1**: `/api/v1/extract`
  - Input: JSON payload with a clinical note.
  - Output: Structured JSON containing diagnoses, medications (with name, dosage, frequency), and PHI detection.
- **Endpoint 2**: `/api/v1/query`
  - Input: JSON payload with a clinical note and a question.
  - Output: Answer to the question based strictly on the clinical note.
- **Health Check**: `/health` - Check API status.

## Requirements
- Python 3.10+
- Groq API key (sign up at https://console.groq.com)
- Docker (optional for containerized deployment)

## Setup Instructions

### Local Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd "Technical Assessment"
   ```

2. **Create and activate virtual environment**:
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   
   # Linux/Mac
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   - Copy the `.env` file and add your Groq API key:
   ```bash
   GROQ_API_KEY=your-groq-api-key-here
   ```
   - Get your API key from: https://console.groq.com/keys

5. **Run the application**:
   ```bash
   uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Access the API**:
   - API: http://localhost:8000
   - Interactive Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Docker Setup

1. **Build the Docker image**:
   ```bash
   docker build -t clinical-note-api .
   ```

2. **Run the Docker container**:
   ```bash
   docker run -p 8000:8000 -e GROQ_API_KEY="your-groq-api-key-here" clinical-note-api
   ```

3. **Access the API at** `http://localhost:8000`

## API Endpoints

### 1. Health Check - `GET /health`
Check if the API is running.

**Response**:
```json
{
  "status": "healthy",
  "service": "Clinical Note Processing API"
}
```

### 2. Structured Extraction - `POST /api/v1/extract`

Extract structured medical data from clinical notes.

**Request**:
```json
{
  "clinical_note": "Patient John Doe (DOB: 11/04/1958) was admitted on Oct 12th for acute exacerbation of chronic obstructive pulmonary disease (COPD) and poorly controlled Type 2 Diabetes Mellitus. Patient was stabilized in the ICU. Upon discharge, patient is prescribed Metformin 500mg PO BID and an Albuterol HFA inhaler 2 puffs q4h PRN for wheezing."
}
```

**Response**:
```json
{
  "diagnoses": [
    "chronic obstructive pulmonary disease (COPD)",
    "Type 2 Diabetes Mellitus"
  ],
  "medications": [
    {
      "name": "Metformin",
      "dosage": "500mg",
      "frequency": "BID"
    },
    {
      "name": "Albuterol HFA inhaler",
      "dosage": "2 puffs",
      "frequency": "q4h PRN"
    }
  ],
  "phi_detected": true
}
```

### 3. Clinical Q&A - `POST /api/v1/query`

Answer questions based strictly on the provided clinical note.

**Request**:
```json
{
  "clinical_note": "Patient John Doe (DOB: 11/04/1958) was admitted on Oct 12th for acute exacerbation of chronic obstructive pulmonary disease (COPD) and poorly controlled Type 2 Diabetes Mellitus. Patient was stabilized in the ICU. Upon discharge, patient is prescribed Metformin 500mg PO BID and an Albuterol HFA inhaler 2 puffs q4h PRN for wheezing.",
  "question": "How often should the patient take their inhaler?"
}
```

**Response**:
```json
{
  "answer": "The patient should take their Albuterol HFA inhaler 2 puffs every 4 hours as needed (q4h PRN) for wheezing."
}
```

**Important Note**: If the answer is not in the clinical note, the API returns:
```json
{
  "answer": "I cannot answer this based on the provided clinical note."
}
```

## Testing

### Manual Testing with cURL

Test the extraction endpoint:
```bash
curl -X POST http://localhost:8000/api/v1/extract \
  -H "Content-Type: application/json" \
  -d '{
    "clinical_note": "Patient John Doe (DOB: 11/04/1958) was admitted on Oct 12th for acute exacerbation of COPD and Type 2 Diabetes. Prescribed Metformin 500mg BID."
  }'
```

Test the Q&A endpoint:
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "clinical_note": "Patient prescribed Metformin 500mg BID.",
    "question": "What medication was prescribed?"
  }'
```

### Automated Testing

Run unit tests:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

## Architecture & Design Decisions

### 1. **LLM Choice: Groq with Llama 3.1**
- **Why Groq**: Groq provides extremely fast inference speeds (up to 300+ tokens/second) with high-quality open-source models.
- **Model**: Using `llama-3.1-70b-versatile` for superior reasoning and instruction-following capabilities.
- **Benefits**:
  - Cost-effective compared to GPT-4
  - Fast response times critical for production
  - Good balance between accuracy and speed

### 2. **JSON Output Stability**
To ensure the LLM always returns valid JSON:
- **Groq's JSON Mode**: Using `response_format={"type": "json_object"}` to force structured output
- **System Prompts**: Carefully crafted prompts that explicitly define the expected JSON schema
- **Temperature 0**: Deterministic outputs to avoid randomness
- **Pydantic Validation**: Double-layer validation to catch any malformed responses
- **Error Handling**: Graceful degradation with clear error messages

### 3. **Hallucination Prevention**
Critical for healthcare applications:
- **Explicit Instructions**: System prompts emphasize "extract ONLY what is explicitly stated"
- **Refusal Mechanism**: Q&A endpoint explicitly returns "I cannot answer..." when information is missing
- **No Medical Knowledge Injection**: LLM is instructed NOT to use its training data for medical facts
- **Temperature 0**: Eliminates creative/speculative responses
- **Validation**: Strict schema enforcement prevents unexpected outputs

### 4. **PHI Detection**
Protected Health Information detection via:
- **Pattern Recognition**: LLM identifies names, dates of birth, phone numbers, addresses, MRNs
- **Boolean Flag**: Simple true/false output for downstream HIPAA compliance workflows
- **Examples**: System prompt includes examples of PHI to improve detection accuracy

### 5. **Framework & Code Quality**
- **FastAPI**: Chosen for:
  - Automatic OpenAPI documentation (`/docs` endpoint)
  - Built-in request validation with Pydantic
  - Async support for future scalability
  - Type hints and modern Python features
- **Modular Architecture**:
  - `api.py`: HTTP layer and routing
  - `llm_service.py`: LLM business logic
  - `schemas.py`: Data models and validation
  - Clean separation of concerns for testability
- **Type Safety**: Full type hints with Pydantic models
- **Error Handling**: Proper HTTP status codes (422 for validation, 500 for server errors)

### 6. **Environment Configuration**
- `.env` file for local development
- Environment variable injection for Docker and production
- API keys never hardcoded in source code

## Scaling to 10,000 Clinical Notes Per Minute

### Current Bottlenecks
At 10,000 requests/minute (167 req/sec), the main constraints are:
1. **LLM API Rate Limits**: Groq has rate limits per API key
2. **Single-Instance Processing**: One container can't handle 167 concurrent requests efficiently
3. **Network Latency**: External API calls add 200-500ms per request

### Scaling Strategy

#### 1. **Horizontal Scaling with Load Balancing**
- Deploy 20-50 API instances behind a load balancer (AWS ALB, NGINX, or Kubernetes Ingress)
- Each instance handles 3-10 req/sec comfortably
- Auto-scaling based on CPU/memory metrics
- **Technology**: Kubernetes (EKS, GKE, AKS) with HPA (Horizontal Pod Autoscaler)

#### 2. **Asynchronous Processing Architecture**
Current synchronous flow is a bottleneck. Solution:
- **Message Queue**: Implement RabbitMQ, AWS SQS, or Apache Kafka
- **Flow**:
  1. API accepts request → validates → queues job → returns job ID immediately
  2. Worker pool processes jobs asynchronously
  3. Client polls `/api/v1/status/{job_id}` or uses webhooks for results
- **Benefits**:
  - API responds in <50ms instead of 2-3 seconds
  - Decouples ingestion from processing
  - Natural backpressure handling

#### 3. **Caching Layer**
Many clinical notes and questions may be similar:
- **Redis/Memcached**: Cache frequent queries and extractions
- **Cache Key**: Hash of clinical note + question
- **TTL**: 1-24 hours depending on use case
- **Hit Rate**: Even 20% cache hits reduce LLM costs by 20%

#### 4. **Database for Results**
- **PostgreSQL or MongoDB**: Store processed results
- Enables analytics, audit trails, and historical queries
- Indexed by patient ID, note hash, timestamp

#### 5. **LLM API Optimization**
- **Multiple API Keys**: Rotate between 5-10 Groq API keys to increase rate limits
- **Batch Processing**: If Groq supports batching, send multiple notes per request
- **Fallback Models**: Use `mixtral-8x7b-32768` as a faster fallback for simpler queries
- **Self-Hosted Option**: For ultra-high scale, deploy Llama 3.1 on GPU clusters (Kubernetes + NVIDIA Triton)

#### 6. **Monitoring & Observability**
- **Metrics**: Prometheus + Grafana
  - Request rate, latency percentiles (p50, p95, p99)
  - Error rates (4xx, 5xx)
  - LLM API latency and costs
- **Logging**: Structured JSON logs (ELK stack or CloudWatch)
- **Tracing**: Distributed tracing (Jaeger, Datadog) for debugging

#### 7. **Cost Optimization**
At 10,000 requests/min → ~14.4M requests/day:
- **Groq Cost**: ~$0.50-$1.00 per 1M tokens → ~$50-$200/day
- **Caching**: Reduces costs by 20-40%
- **Smart Routing**: Use smaller/faster models for simple queries

### Estimated Infrastructure
- **50 API pods** (1 vCPU, 2GB RAM each)
- **10 worker pods** for async processing
- **Redis cluster** (3 nodes)
- **PostgreSQL** (2-core, 16GB RAM)
- **Message queue** (managed service)
- **Total Cost**: ~$1,500-$3,000/month on AWS/GCP

This architecture can comfortably handle 10,000 notes/minute with room for 2-3x growth.

## Project Structure
```
Technical Assessment/
├── src/
│   ├── api.py              # FastAPI routes and HTTP logic
│   ├── llm_service.py      # LLM integration and prompt engineering
│   ├── schemas.py          # Pydantic models for validation
├── tests/
│   ├── test_api.py         # API endpoint tests
├── .env                    # Environment variables (not in git)
├── .gitignore              # Files to exclude from git
├── Dockerfile              # Container definition
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Security Considerations
- **API Key Protection**: Never commit `.env` to version control
- **PHI Handling**: Consider encryption at rest and in transit for production
- **Rate Limiting**: Implement rate limiting to prevent abuse (not included in this demo)
- **HIPAA Compliance**: For production, ensure Groq has a BAA (Business Associate Agreement)

## Future Enhancements
- [ ] Add authentication (JWT tokens or API keys)
- [ ] Implement rate limiting per user
- [ ] Add batch processing endpoint
- [ ] Store processed results in database
- [ ] Add audit logging for compliance
- [ ] Implement caching for frequent queries
- [ ] Add support for multiple LLM providers (OpenAI, Anthropic fallbacks)
- [ ] Add more sophisticated PHI redaction
- [ ] Implement async job processing with webhooks

## License
MIT License

## Contact
For questions or issues, please open a GitHub issue or contact the development team.