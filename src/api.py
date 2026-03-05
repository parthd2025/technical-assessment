"""
FastAPI application for Clinical Note Processing.

This module provides RESTful API endpoints for:
1. Health checking
2. Structured entity extraction from clinical notes
3. Question answering based on clinical notes

All endpoints include proper error handling, logging, and validation.
The API follows healthcare data standards and HIPAA compliance guidelines.

API Documentation:
    Interactive docs: http://localhost:8000/docs
    ReDoc: http://localhost:8000/redoc
"""

from fastapi import FastAPI, HTTPException
from typing import Dict
import time
from .llm_service import extract_entities_from_text, answer_clinical_question
from .schemas import ClinicalNoteInput, ExtractedEntity, QueryInput, QueryResponse
from .logger import setup_logger, log_api_request, log_api_response

# Initialize logger
logger = setup_logger(__name__)

# Initialize FastAPI app
logger.info("Initializing FastAPI application...")
app = FastAPI(
    title="Clinical Note Processing API",
    description="API for extracting structured data and answering questions from clinical notes using LLMs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

logger.info("FastAPI application initialized successfully")


@app.get("/")
async def root() -> Dict:
    """
    Root endpoint providing API information and available endpoints.
    
    Returns:
        Dict with API metadata and endpoint URLs
    
    Example:
        >>> GET /
        {
            "message": "Clinical Note Processing API",
            "version": "1.0.0",
            "endpoints": {...}
        }
    """
    logger.debug("Root endpoint called")
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


@app.get("/health")
async def health_check() -> Dict:
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        Dict with service status
    
    Example:
        >>> GET /health
        {"status": "healthy", "service": "Clinical Note Processing API"}
    """
    logger.debug("Health check endpoint called")
    return {"status": "healthy", "service": "Clinical Note Processing API"}

@app.post("/api/v1/extract", response_model=ExtractedEntity)
async def extract_entities(input: ClinicalNoteInput) -> ExtractedEntity:
    """
    Extract structured medical data from a clinical note.
    
    This endpoint uses an LLM to extract:
    - Diagnoses/medical conditions
    - Medications with dosage and frequency
    - PHI (Protected Health Information) detection flag
    
    Args:
        input: ClinicalNoteInput containing the clinical note text
    
    Returns:
        ExtractedEntity: Structured extraction results
    
    Raises:
        HTTPException 422: If validation fails or LLM returns invalid data
        HTTPException 500: If extraction process fails
    
    Example:
        >>> POST /api/v1/extract
        >>> {"clinical_note": "Patient has diabetes, on Metformin 500mg BID"}
        >>> Response: {"diagnoses": ["diabetes"], "medications": [...]}
    """
    start_time = time.time()
    log_api_request(logger, "/api/v1/extract", note_length=len(input.clinical_note))
    
    try:
        extracted_data = extract_entities_from_text(input.clinical_note)
        
        duration_ms = (time.time() - start_time) * 1000
        log_api_response(
            logger,
            "/api/v1/extract",
            status="success",
            duration_ms=duration_ms,
            diagnoses_count=len(extracted_data.diagnoses),
            medications_count=len(extracted_data.medications),
            phi_detected=extracted_data.phi_detected
        )
        
        return extracted_data
        
    except ValueError as e:
        logger.warning(f"Validation error during extraction: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during extraction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error extracting entities: {str(e)}")

@app.post("/api/v1/query", response_model=QueryResponse)
async def query_clinical_note(input: QueryInput) -> QueryResponse:
    """
    Answer a question based on the provided clinical note.
    
    This endpoint uses an LLM to answer questions strictly based on
    the content of the clinical note. If the answer is not in the note,
    it returns a standard refusal message.
    
    Args:
        input: QueryInput containing clinical note and question
    
    Returns:
        QueryResponse: Answer to the question
    
    Raises:
        HTTPException 500: If query processing fails
    
    Example:
        >>> POST /api/v1/query
        >>> {"clinical_note": "...", "question": "What is the dosage?"}
        >>> Response: {"answer": "The dosage is 10mg daily"}
    """
    start_time = time.time()
    log_api_request(
        logger,
        "/api/v1/query",
        note_length=len(input.clinical_note),
        question=input.question[:100]
    )
    
    try:
        answer = answer_clinical_question(input.clinical_note, input.question)
        
        duration_ms = (time.time() - start_time) * 1000
        log_api_response(
            logger,
            "/api/v1/query",
            status="success",
            duration_ms=duration_ms,
            answer_length=len(answer)
        )
        
        return QueryResponse(answer=answer)
        
    except Exception as e:
        logger.error(f"Error during query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")