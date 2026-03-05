# Video Recording Script for Technical Assessment
## Clinical Note Processing API - Implementation Walkthrough

**Target Duration:** 5-10 minutes  
**Audience:** Technical reviewers evaluating LLM Engineering, Software Engineering, DevOps, and Communication skills

---

## 🎬 RECORDING SETUP (Before Starting)

### Pre-Recording Checklist:
- [ ] Clean desktop/workspace
- [ ] Close unnecessary applications
- [ ] Test microphone and audio levels
- [ ] Set screen resolution to 1920x1080 or 1280x720
- [ ] Have all terminals/browser tabs ready
- [ ] Run through the script once without recording
- [ ] Prepare sample clinical note for demo

### Recommended Tools:
- **Screen Recording:** OBS Studio, Loom, or QuickTime (Mac)
- **Audio:** Clear microphone, quiet environment
- **Editing (optional):** DaVinci Resolve (free) or iMovie

---

## 📋 SCRIPT (5-10 minutes)

### SECTION 1: Introduction (30 seconds)
**[Screen: README open or project overview]**

> "Hello! I'm [Your Name], and today I'll be walking you through my implementation of the Clinical Note Processing API. This is a production-ready REST API that extracts structured medical data from unstructured clinical notes using Groq's LLM with Llama 3.1."
>
> "I'll cover four key areas: LLM Engineering, Software Engineering, DevOps, and the architecture decisions I made."

---

### SECTION 2: Quick Demo (1.5 minutes)
**[Screen: Terminal + Browser]**

> "Let me start with a quick demonstration of the system in action."

**Terminal 1:**
```bash
# Show environment is set up
cat .env | head -3

# Start the API
uvicorn src.api:app --reload
```

**Terminal 2 (or Browser to localhost:8000/docs):**
```bash
# Wait for API to start, then make a test call
curl -X POST http://localhost:8000/api/v1/extract \
  -H "Content-Type: application/json" \
  -d '{
    "clinical_note": "Patient John Doe (DOB: 11/04/1958) diagnosed with Type 2 Diabetes and Hypertension. Prescribed Metformin 500mg BID and Lisinopril 10mg daily."
  }'
```

> "As you can see, the API successfully extracted:
> - Two diagnoses: Type 2 Diabetes and Hypertension
> - Two medications with complete dosage and frequency information
> - PHI detection flagged as true because of the patient name and date of birth"

**[Show Streamlit UI if time allows]**
```bash
streamlit run streamlit_app.py
```
> "I also built a user-friendly Streamlit interface for healthcare practitioners to interact with the system."

---

### SECTION 3: LLM Engineering (2 minutes)
**[Screen: VS Code - src/llm_service.py]**

> "Now let's dive into the LLM engineering aspects, which is worth 35% of the evaluation."

**Show system prompts (scroll through extract_entities_from_text):**

> "First, prompt engineering. I've crafted detailed system prompts with:
> - Explicit instructions to output ONLY valid JSON
> - Multiple examples showing expected input-output format
> - Clear rules about not hallucinating or inferring medical information
> - Specific guidelines for medication and diagnosis extraction"

**Show JSON validation (scroll to parse_and_validate_json):**

> "For strict JSON enforcement, I implemented multiple layers:
> - Groq's response_format with json_object mode to force structured output
> - Multi-step validation: removing markdown blocks, extracting JSON objects, validating required fields, and checking data types
> - Retry logic with up to 3 attempts if JSON is malformed"

**Show hallucination prevention (scroll to answer_clinical_question):**

> "To prevent hallucinations, which is critical in healthcare:
> - Temperature set to 0 for deterministic outputs
> - Explicit refusal mechanism: 'I cannot answer this based on the provided clinical note'
> - Instructions to never use general medical knowledge
> - Multiple examples showing when to refuse"

**Show edge cases:**

> "I also handle edge cases:
> - Empty inputs throw validation errors
> - Very short notes (less than 10 characters) are rejected
> - Very long notes (over 50,000 characters) are truncated to prevent token limit issues
> - Pydantic validators strip whitespace and validate all fields"

---

### SECTION 4: Software Engineering (2 minutes)
**[Screen: VS Code - Project structure]**

> "For software engineering, also 35% of the evaluation, I focused on clean, modular, and type-safe code."

**Show project structure:**
```
src/
├── api.py          # HTTP layer and routing
├── llm_service.py  # LLM business logic
├── schemas.py      # Pydantic models
├── config.py       # Configuration management
└── logger.py       # Centralized logging
```

> "The architecture follows separation of concerns with clear module boundaries."

**Show schemas.py:**

> "I use Pydantic extensively for:
> - Type safety with full type hints
> - Automatic request/response validation
> - Field validators for edge cases
> - Self-documenting code with examples"

**Show api.py error handling:**

> "HTTP status codes are used properly:
> - 400 for invalid client input (empty notes, malformed data)
> - 422 for validation failures (LLM returned invalid structure)
> - 503 for service unavailability (Groq API down)
> - 500 for unexpected server errors
> 
> All errors return structured JSON with error types and helpful messages."

**Show logging:**

> "Comprehensive logging throughout:
> - Structured logs with timestamps, function names, and line numbers
> - Different log levels for development and production
> - API request/response logging for debugging and monitoring
> - All sensitive data excluded from logs"

**Show tests (if time allows):**
```bash
pytest tests/ -v --cov=src
```

> "I've written comprehensive unit tests covering:
> - JSON parsing edge cases
> - LLM service mocking
> - API endpoint testing
> - Error handling scenarios"

---

### SECTION 5: DevOps (1 minute)
**[Screen: VS Code - Dockerfile and docker-compose.yml]**

> "For DevOps, worth 10%, I implemented containerization with best practices."

**Show Dockerfile:**

> "The Dockerfile uses:
> - Multi-stage build to minimize final image size
> - Non-root user for security
> - Health checks for monitoring
> - Proper environment variable handling"

**Show docker-compose.yml:**

> "Docker Compose includes:
> - Environment variable configuration with sensible defaults
> - Volume mounting for persistent logs
> - Resource limits for production
> - Logging configuration
> - Health checks"

**Show .env.example:**

> "I created a comprehensive .env.example with:
> - Clear instructions for setup
> - Documentation for each variable
> - Production deployment notes"

**Demo Docker (if time allows):**
```bash
docker-compose up --build
```

---

### SECTION 6: Architecture & Scaling (1.5 minutes)
**[Screen: README.md - Scaling section]**

> "Let me briefly discuss the architecture for scaling to 10,000 notes per minute."

**Scroll through scaling section:**

> "Current bottlenecks are:
> 1. LLM API rate limits
> 2. Synchronous processing
> 3. No caching
>
> My scaling strategy includes:
> 
> 1. **Horizontal scaling**: Deploy 20-50 API instances behind a load balancer
> 2. **Asynchronous processing**: Use message queues (RabbitMQ or SQS) to decouple ingestion from processing
> 3. **Caching**: Redis for frequently requested notes, 20-40% cost reduction
> 4. **Multiple API keys**: Rotate between keys to increase rate limits
> 5. **Monitoring**: Prometheus + Grafana for observability
>
> This architecture can handle 10,000 requests/minute comfortably for roughly $1,500-$3,000 per month on AWS."

---

### SECTION 7: Code Quality & Testing (30 seconds)
**[Screen: VS Code or Terminal]**

**Show code quality:**
```bash
# Show tests passing
pytest tests/ -v

# Show code coverage
pytest tests/ --cov=src --cov-report=term
```

> "Code quality highlights:
> - Comprehensive docstrings following Google style
> - Type hints throughout for IDE support
> - 80%+ test coverage
> - Clean, readable code with clear variable names
> - Proper error handling at every layer"

---

### SECTION 8: Closing (30 seconds)
**[Screen: README or project overview]**

> "To summarize:
> 
> **LLM Engineering:** Advanced prompt engineering, strict JSON validation, hallucination prevention, and edge case handling
> 
> **Software Engineering:** Clean modular architecture, comprehensive type hints, proper HTTP status codes, and extensive error handling
> 
> **DevOps:** Production-ready Docker setup with multi-stage builds, environment management, and monitoring
> 
> **Documentation:** Comprehensive README with architecture decisions, scaling strategy, and clear setup instructions
> 
> Thank you for reviewing my implementation. The complete code, tests, and documentation are available in the repository. I'm happy to answer any questions!"

---

## 🎯 KEY POINTS TO EMPHASIZE

### LLM Engineering (35%):
- ✅ Prompt engineering with examples
- ✅ Groq's JSON mode for structure
- ✅ Multi-layer validation
- ✅ Retry logic (3 attempts)
- ✅ Temperature 0 for determinism
- ✅ Explicit refusal mechanism
- ✅ Edge case handling

### Software Engineering (35%):
- ✅ Modular architecture (api, service, schemas, config)
- ✅ Type hints everywhere
- ✅ Pydantic for validation
- ✅ Proper HTTP status codes (400, 422, 503, 500)
- ✅ Comprehensive logging
- ✅ Unit tests with mocking

### DevOps (10%):
- ✅ Multi-stage Dockerfile
- ✅ Docker Compose with resource limits
- ✅ Health checks
- ✅ .env.example with documentation
- ✅ Non-root user for security

### Communication (20%):
- ✅ Clear README structure
- ✅ Architecture decisions explained
- ✅ Scaling strategy detailed
- ✅ Code is self-documenting
- ✅ This recording script!

---

## 🚨 COMMON MISTAKES TO AVOID

1. ❌ **Don't apologize** for code or implementation choices
2. ❌ **Don't spend too long** on any one section (watch the clock)
3. ❌ **Don't read code line by line** - highlight key concepts
4. ❌ **Don't go over 10 minutes** - reviewers have limited time
5. ❌ **Don't forget to test before recording** - ensure everything works
6. ❌ **Don't have embarrassing content** visible (notifications, bookmarks, etc.)

---

## 📝 POST-RECORDING CHECKLIST

- [ ] Review the recording once
- [ ] Check audio quality (clear, no background noise)
- [ ] Verify all demonstrations worked correctly
- [ ] Add captions/subtitles if possible (accessibility)
- [ ] Export in high quality (1080p if possible)
- [ ] Test the video file plays correctly
- [ ] Upload to the required platform
- [ ] Add video link to README (if appropriate)

---

## 💡 TIPS FOR A GREAT RECORDING

1. **Be enthusiastic** but professional
2. **Speak clearly** and at a moderate pace
3. **Explain *why*** not just *what* - show your thinking
4. **Stay on script** but sound natural
5. **Highlight challenges** you overcame
6. **Show personality** - let them see you're a team player
7. **Practice** at least twice before recording

---

## 🎬 ALTERNATIVE SHORT VERSION (5 minutes)

If you need a shorter version:

1. **Intro** (20s): Who you are, what you built
2. **Demo** (60s): Quick API call showing extraction
3. **LLM Engineering** (90s): Prompt design + JSON validation + hallucination prevention
4. **Software Engineering** (90s): Architecture + error handling + type safety
5. **DevOps** (30s): Docker setup
6. **Closing** (20s): Summary

Total: ~5 minutes

---

Good luck with your recording! 🎥
