# Technical Presentation Script
## Clinical Note Processing API - Complete Walkthrough

**Duration: 12-15 minutes**  
**Recording Instructions:** Use screenshare to show code, terminal, and live demos

---

## 🎬 INTRODUCTION (1-2 minutes)

### Opening
"Hello! Today I'll be walking you through my Clinical Note Processing API - a production-ready system that extracts structured medical data from unstructured clinical notes using AI.

This assessment required building two REST API endpoints:
1. **Structured extraction** - pulling diagnoses, medications, and PHI from clinical notes
2. **Question answering** - verifying specific information from the notes

Let me show you what I've built and the key technical decisions behind it."

---

## 📁 REPOSITORY OVERVIEW (2 minutes)

### Code Structure Walkthrough
**[SCREEN: Show project folder structure]**

"First, let's look at the repository structure. This is organized as a production-ready application:

- **src/ folder** contains our core application:
  - `api.py` - FastAPI routes and HTTP layer
  - `llm_service.py` - All LLM integration and prompt engineering
  - `schemas.py` - Pydantic models for strict data validation
  - `config.py` - Centralized configuration management
  - `logger.py` - Structured logging setup

- **tests/ folder** - comprehensive unit tests for all components

- **Dockerfile** - multi-stage Docker build optimized for production

- **requirements.txt** - clean dependency management

- **README.md** - this is critical - contains full setup instructions, architecture decisions, and scaling strategy

I also built a **Streamlit web interface** as a bonus to demonstrate the API in action."

---

## 🔧 TECHNICAL DECISIONS (3-4 minutes)

### LLM Choice
**[SCREEN: Show llm_service.py]**

"Let me explain my key technical decisions:

**First, choosing Groq with Llama 3.1:**
- I chose Groq because it provides incredibly fast inference speeds - up to 300 tokens per second
- Using the `llama-3.1-70b-versatile` model for superior reasoning capabilities
- This balances cost, speed, and accuracy - critical for production healthcare applications

**JSON Output Stability - this was crucial:**

[SCREEN: Highlight the JSON mode configuration]

I implemented a multi-layered approach:
1. **Groq's JSON mode** - forcing structured output with `response_format={'type': 'json_object'}`
2. **Temperature 0** - completely deterministic responses, no randomness
3. **Explicit schema in prompts** - the LLM knows exactly what JSON structure to return
4. **Pydantic validation** - double-checking every response against our data models
5. **Automatic retry logic** - if JSON parsing fails, we retry with stricter instructions

This ensures we NEVER get malformed responses."

### Hallucination Prevention
**[SCREEN: Show system prompts in llm_service.py]**

"**Hallucination prevention** is critical in healthcare:

Look at my system prompts - I explicitly tell the LLM:
- 'Extract ONLY what is explicitly stated in the note'
- 'Do NOT use your medical knowledge to add information'
- 'If you cannot answer from the note, say: I cannot answer this'

For the Q&A endpoint, if the information isn't in the note, it refuses to answer rather than making something up. This is essential for patient safety.

Temperature 0 also helps - no creative interpretations, only extraction of facts."

### Modular Architecture
**[SCREEN: Show api.py briefly]**

"The architecture is clean and modular:
- FastAPI handles all HTTP concerns - routing, validation, error handling
- LLM service is completely decoupled - could swap providers easily
- Pydantic schemas ensure type safety throughout
- This separation makes testing and maintenance much easier"

---

## 🖥️ LIVE DEMONSTRATION (4-5 minutes)

### Starting the Application

**[SCREEN: Terminal]**

"Let me show you how easy it is to run this application.

**First, locally:**

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable
# (Show .env file with GROQ_API_KEY)

# Start the API
uvicorn src.api:app --reload
```

[START THE SERVER]

The API starts on port 8000 with auto-reload for development."

### API Testing

**[SCREEN: Browser - http://localhost:8000/docs]**

"FastAPI automatically generates interactive documentation at /docs.

Let me test the **extraction endpoint** with a real clinical note:

[SCREEN: Paste sample note into the /extract endpoint]

```json
{
  "clinical_note": "Patient John Doe (DOB: 11/04/1958) was admitted on Oct 12th for acute exacerbation of chronic obstructive pulmonary disease (COPD) and poorly controlled Type 2 Diabetes Mellitus. Prescribed Metformin 500mg PO BID and Albuterol HFA inhaler 2 puffs q4h PRN."
}
```

[EXECUTE]

Look at the response - perfectly structured JSON:
- Diagnoses extracted: COPD and Type 2 Diabetes
- Medications with dosage and frequency parsed correctly
- PHI detected: true (because we have a name and DOB)

**Now let's test the Q&A endpoint:**

[SCREEN: Use /query endpoint]

```json
{
  "clinical_note": "Same note...",
  "question": "What is the dosage of Metformin?"
}
```

[EXECUTE]

Response: '500mg BID' - extracted directly from the note.

**What if we ask something NOT in the note?**

```json
{
  "question": "What is the patient's blood pressure?"
}
```

[EXECUTE]

Response: 'I cannot answer this based on the provided clinical note.'

This prevents hallucinations!"

### Streamlit Demo

**[SCREEN: Terminal - start Streamlit]**

"I also built a web interface to showcase the API:

```bash
streamlit run streamlit_app.py
```

[SHOW STREAMLIT UI]

This provides a user-friendly interface for:
- Pasting clinical notes
- Real-time extraction with visual cards
- PHI warnings
- Quick Q&A verification

[DEMO: Paste note, click Extract, show results, ask a question]

This demonstrates how the API could be integrated into a real EMR system."

### Docker Demonstration

**[SCREEN: Terminal]**

"Now let me show you the Docker setup:

```bash
# Build the image
docker build -t clinical-note-api .
```

[Show Dockerfile briefly]

I'm using a **multi-stage build**:
- Stage 1: Install dependencies
- Stage 2: Copy only what's needed for a minimal final image
- Non-root user for security
- Health checks built in

```bash
# Run the container
docker run -p 8000:8000 -e GROQ_API_KEY="gsk_xxx" clinical-note-api
```

[START CONTAINER, show health check working]

The application is now fully containerized and ready for deployment to any cloud platform."

---

## 📊 SCALING STRATEGY (2-3 minutes)

**[SCREEN: README.md - scaling section]**

"Let me address the scaling question: **How do we handle 10,000 clinical notes per minute?**

That's approximately 167 requests per second. Here's my approach:

**1. Horizontal Scaling**
- Deploy 20-50 container instances behind a load balancer
- Use Kubernetes with auto-scaling based on CPU and request metrics
- Each instance handles 3-10 requests per second comfortably

**2. Asynchronous Architecture**
- Current design is synchronous - this becomes a bottleneck
- Solution: Message queue (RabbitMQ or AWS SQS)
- Flow: API accepts request → queues job → returns job ID immediately
- Worker pool processes jobs asynchronously
- Client polls for results or receives webhooks
- This reduces API response time from 2-3 seconds to under 50ms

**3. Caching Layer**
- Redis cache for frequently asked questions
- Cache key: hash of clinical note + question
- Even 20% cache hit rate saves 20% of LLM costs and latency

**4. LLM Optimization**
- Rotate between multiple Groq API keys to increase rate limits
- Use faster models (mixtral-8x7b) for simpler queries
- For ultra-scale: self-host Llama 3.1 on GPU clusters

**5. Observability**
- Prometheus + Grafana for metrics
- Track latency percentiles, error rates, LLM costs
- Distributed tracing for debugging bottlenecks

**Cost Estimate:**
At 10,000 requests/minute (14.4M per day):
- LLM costs: ~$50-200/day
- Infrastructure: ~$1,500-3,000/month on AWS/GCP
- Total: Very feasible for production healthcare applications

This architecture can handle 10,000 notes per minute with room for 2-3x growth."

---

## ✅ PRODUCTION READINESS (1-2 minutes)

**[SCREEN: Show test files]**

"Let me highlight production-readiness features:

**Testing:**
```bash
pytest tests/ -v
```

[RUN TESTS - show them passing]

- Unit tests for API endpoints
- LLM service tests with mocking
- JSON validation tests
- 90%+ code coverage

**Security:**
- Environment variables for API keys - never hardcoded
- Multi-stage Docker with non-root user
- PHI detection for HIPAA compliance workflows
- Input validation with Pydantic

**Error Handling:**
- Proper HTTP status codes (422 for validation, 500 for errors)
- Graceful degradation when LLM fails
- Structured logging for debugging
- Health check endpoint for monitoring

**Documentation:**
- Comprehensive README with setup instructions
- Architecture decision explanations
- Scaling strategy
- API documentation auto-generated by FastAPI
- Additional technical guides for deep dives"

---

## 🎯 VALUE PROPOSITION (1 minute)

"**Why is this valuable?**

This system transforms hours of manual data entry into seconds of automated extraction:
- **Clinical staff** spend less time on documentation
- **Accuracy** improves with consistent extraction
- **PHI detection** supports HIPAA compliance
- **Scalable** to enterprise healthcare systems
- **Fast** response times suitable for real-time use

The modular design means:
- Easy to add new extraction fields (allergies, vitals, procedures)
- Can swap LLM providers (OpenAI, Anthropic)
- Ready to integrate with existing EMR systems via REST API"

---

## 🏁 CLOSING (30 seconds)

"In summary, I've delivered:
1. ✅ Clean, modular source code in src/
2. ✅ Complete requirements.txt
3. ✅ Production-ready Dockerfile with multi-stage builds
4. ✅ Comprehensive README with architecture decisions and scaling strategy
5. ✅ Working application with tests and documentation

The system is ready for deployment today, with a clear path to handle production scale.

Thank you for watching! Please find all code in the GitHub repository, and feel free to reach out with any questions."

---

## 📝 RECORDING TIPS

### Before Recording:
- [ ] Clean up desktop/taskbar
- [ ] Close unnecessary applications
- [ ] Set terminal font size to 14-16pt for visibility
- [ ] Test audio levels
- [ ] Prepare sample clinical notes in clipboard
- [ ] Have .env file ready (with dummy API key visible)
- [ ] Start with all terminals closed

### During Recording:
- [ ] Speak slowly and clearly
- [ ] Pause between sections (easier to edit)
- [ ] Show each file/terminal full screen
- [ ] Zoom in on code when showing specific lines
- [ ] If you make a mistake, pause, then restart that sentence
- [ ] Smile! (viewers can hear it in your voice)

### Recording Software Options:
- **OBS Studio** (free, professional)
- **Loom** (easy, cloud-hosted)
- **Windows Game Bar** (Win+G, built-in)
- **Zoom** (record yourself as the only participant)

### Suggested Video Structure:
1. **Part 1: Overview** (2 min) - Repository structure
2. **Part 2: Technical Deep Dive** (4 min) - Code walkthrough
3. **Part 3: Live Demo** (5 min) - Running the application
4. **Part 4: Scaling & Production** (3 min) - Architecture discussion

Or record as one 12-15 minute video following this script.

---

**Good luck with your recording! 🎬**
