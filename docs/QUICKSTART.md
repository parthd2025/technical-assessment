# Quick Start Guide

## 🚀 Getting Started (5 Minutes)

### Prerequisites
- Python 3.10 or higher
- Groq API key ([Get one here](https://console.groq.com/keys))

### Option 1: Local Setup (Recommended for Development)

```bash
# 1. Run setup script
# Windows:
setup.bat

# Linux/Mac:
chmod +x setup.sh
./setup.sh

# 2. Edit .env file
# Add your GROQ_API_KEY=your-actual-key-here

# 3. Activate virtual environment
# Windows:
.venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate

# 4. Start the server
uvicorn src.api:app --reload

# 5. Open your browser
# http://localhost:8000/docs
```

### Option 2: Docker (Recommended for Production)

```bash
# 1. Edit .env file
# Add your GROQ_API_KEY=your-actual-key-here

# 2. Build and run with Docker Compose
docker-compose up --build

# 3. Open your browser
# http://localhost:8000/docs
```

## 📝 Testing the API

### Interactive Documentation
Visit http://localhost:8000/docs for Swagger UI

### Manual Test Script
```bash
# Make sure server is running, then:
python test_manual.py
```

### cURL Examples

**Extract Entities:**
```bash
curl -X POST http://localhost:8000/api/v1/extract \
  -H "Content-Type: application/json" \
  -d '{
    "clinical_note": "Patient John Doe (DOB: 11/04/1958) was admitted for COPD. Prescribed Metformin 500mg BID."
  }'
```

**Ask a Question:**
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "clinical_note": "Patient prescribed Metformin 500mg BID.",
    "question": "What medication was prescribed?"
  }'
```

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

## 🐛 Troubleshooting

### "GROQ_API_KEY not found"
- Make sure you've edited the `.env` file
- Check that it's in the project root directory
- Format: `GROQ_API_KEY=your-key-here` (no quotes)

### "Connection refused"
- Make sure the server is running
- Check if port 8000 is available
- Try: `netstat -an | findstr 8000` (Windows) or `lsof -i :8000` (Linux/Mac)

### Tests failing
- Make sure virtual environment is activated
- Run: `pip install -r requirements.txt`
- Check that all dependencies are installed

## 📦 Project Structure

```
Technical Assessment/
├── src/                    # Source code
│   ├── api.py             # FastAPI endpoints
│   ├── llm_service.py     # LLM integration
│   ├── schemas.py         # Pydantic models
│   └── config.py          # Configuration
├── tests/                 # Unit tests
│   └── test_api.py
├── .env                   # Environment variables
├── Dockerfile             # Container definition
├── docker-compose.yml     # Docker orchestration
├── requirements.txt       # Python dependencies
├── README.md              # Main documentation
└── TECHNICAL_GUIDE.md     # Technical details
```

## 🔑 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Your Groq API key | *Required* |
| `GROQ_MODEL` | LLM model to use | `llama-3.1-70b-versatile` |
| `LLM_TEMPERATURE` | Randomness (0-1) | `0` |
| `APP_PORT` | Server port | `8000` |

## 🎯 Common Commands

```bash
# Start server with auto-reload (development)
uvicorn src.api:app --reload

# Start server (production)
uvicorn src.api:app --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run manual test
python test_manual.py

# Build Docker image
docker build -t clinical-note-api .

# Run Docker container
docker run -p 8000:8000 -e GROQ_API_KEY="your-key" clinical-note-api

# Docker Compose
docker-compose up         # Start
docker-compose down       # Stop
docker-compose logs -f    # View logs
```

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Groq Console**: https://console.groq.com
- **Technical Guide**: See TECHNICAL_GUIDE.md
- **Full README**: See README.md

## 💡 Tips

1. **Use the /docs endpoint** - FastAPI provides interactive API documentation
2. **Check /health first** - Verify the server is running
3. **Start with test_manual.py** - Easiest way to test the API
4. **Use temperature 0** - For consistent results in healthcare applications
5. **Monitor token usage** - Track your Groq API costs

## ⚠️ Important Notes

- **Never commit .env** - It contains your API key
- **PHI Handling** - This is a demo; add encryption for production
- **Rate Limits** - Groq has rate limits; add retry logic for production
- **HIPAA Compliance** - Ensure proper BAA with Groq for production use

---

**Need help?** Check the TECHNICAL_GUIDE.md for detailed explanations.
