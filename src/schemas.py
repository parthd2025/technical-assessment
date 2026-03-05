"""
Pydantic schemas for Clinical Note Processing API.

This module defines request and response models using Pydantic for:
- Data validation
- Automatic API documentation
- Type safety
- JSON serialization/deserialization

All models follow healthcare data standards and include comprehensive field descriptions.
"""

from pydantic import BaseModel, Field
from typing import List


class ClinicalNoteInput(BaseModel):
    """
    Input schema for clinical note text.
    
    Attributes:
        clinical_note: Raw clinical note text from EMR/EHR systems
    
    Example:
        >>> note = ClinicalNoteInput(clinical_note="Patient presents with...")
    """
    clinical_note: str = Field(
        ..., 
        description="Raw clinical note text",
        min_length=10,
        examples=["Patient John Doe presents with chest pain..."]
    )


class Medication(BaseModel):
    """
    Medication information extracted from clinical notes.
    
    Attributes:
        name: Generic or brand name of the medication
        dosage: Amount and unit (e.g., "40mg", "2 tablets")
        frequency: How often the medication is taken (e.g., "daily", "BID", "PRN")
    
    Example:
        >>> med = Medication(name="Lisinopril", dosage="10mg", frequency="daily")
    """
    name: str = Field(
        ..., 
        description="Medication name",
        examples=["Lisinopril", "Metformin", "Aspirin"]
    )
    dosage: str = Field(
        ..., 
        description="Medication dosage with units",
        examples=["10mg", "500mg", "2 tablets"]
    )
    frequency: str = Field(
        ..., 
        description="Frequency of medication intake",
        examples=["daily", "BID", "PRN", "q12h"]
    )


class ExtractedEntity(BaseModel):
    """
    Structured data extracted from clinical notes.
    
    This schema represents the complete extraction result including:
    - Medical diagnoses
    - Prescribed medications with details
    - PHI detection flag for compliance
    
    Attributes:
        diagnoses: List of medical conditions/diagnoses mentioned
        medications: List of medications with dosage and frequency
        phi_detected: Whether Protected Health Information (PHI) was detected
    
    Example:
        >>> result = ExtractedEntity(
        ...     diagnoses=["Hypertension", "Diabetes Type 2"],
        ...     medications=[Medication(...)],
        ...     phi_detected=True
        ... )
    """
    diagnoses: List[str] = Field(
        ..., 
        description="List of medical conditions and diagnoses",
        examples=[["Hypertension", "Type 2 Diabetes", "Hyperlipidemia"]]
    )
    medications: List[Medication] = Field(
        ..., 
        description="List of prescribed medications with details",
        examples=[[{"name": "Lisinopril", "dosage": "10mg", "frequency": "daily"}]]
    )
    phi_detected: bool = Field(
        ..., 
        description="Whether Protected Health Information (PHI) is detected per HIPAA guidelines"
    )


class QueryInput(BaseModel):
    """
    Input schema for clinical Q&A queries.
    
    Attributes:
        clinical_note: The clinical note to query
        question: Natural language question about the note
    
    Example:
        >>> query = QueryInput(
        ...     clinical_note="Patient on Lisinopril 10mg daily",
        ...     question="What is the dosage of Lisinopril?"
        ... )
    """
    clinical_note: str = Field(
        ..., 
        description="Clinical note text to query",
        min_length=10
    )
    question: str = Field(
        ..., 
        description="Question to answer based on the clinical note",
        min_length=5,
        examples=["What medications is the patient taking?", "What is the diagnosis?"]
    )


class QueryResponse(BaseModel):
    """
    Response schema for clinical Q&A queries.
    
    Attributes:
        answer: Answer to the question based strictly on the clinical note
    
    Example:
        >>> response = QueryResponse(answer="The patient is taking Lisinopril 10mg daily")
    """
    answer: str = Field(
        ..., 
        description="Answer to the question based on the clinical note content"
    )