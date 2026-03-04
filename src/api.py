from fastapi import FastAPI, HTTPException
from typing import Dict
from .llm_service import extract_entities_from_text, answer_clinical_question
from .schemas import ClinicalNoteInput, ExtractedEntity, QueryInput, QueryResponse

# Initialize FastAPI app
app = FastAPI(
    title="Clinical Note Processing API",
    description="API for extracting structured data and answering questions from clinical notes",
    version="1.0.0"
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Clinical Note Processing API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "extract": "/api/v1/extract",
            "query": "/api/v1/query"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Clinical Note Processing API"}

# Endpoint 1: Structured Extraction
@app.post("/api/v1/extract", response_model=ExtractedEntity)
async def extract_entities(input: ClinicalNoteInput):
    """
    Extract structured medical data from a clinical note.
    
    Returns:
    - diagnoses: List of medical conditions
    - medications: List of medications with name, dosage, and frequency
    - phi_detected: Boolean indicating if PHI is present
    """
    try:
        extracted_data = extract_entities_from_text(input.clinical_note)
        return extracted_data
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting entities: {str(e)}")

# Endpoint 2: Clinical Q&A
@app.post("/api/v1/query", response_model=QueryResponse)
async def query_clinical_note(input: QueryInput):
    """
    Answer a question based on the provided clinical note.
    
    Returns an answer based strictly on the clinical note content.
    If the answer is not in the note, returns a standard message.
    """
    try:
        answer = answer_clinical_question(input.clinical_note, input.question)
        return QueryResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")