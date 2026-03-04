from pydantic import BaseModel, Field
from typing import List

class ClinicalNoteInput(BaseModel):
    clinical_note: str = Field(..., description="Raw clinical note text")

class Medication(BaseModel):
    name: str = Field(..., description="Medication name")
    dosage: str = Field(..., description="Medication dosage")
    frequency: str = Field(..., description="Frequency of medication intake")

class ExtractedEntity(BaseModel):
    diagnoses: List[str] = Field(..., description="List of medical conditions")
    medications: List[Medication] = Field(..., description="List of prescribed medications")
    phi_detected: bool = Field(..., description="Whether Protected Health Information is detected")

class QueryInput(BaseModel):
    clinical_note: str = Field(..., description="Clinical note text")
    question: str = Field(..., description="Question to answer based on the clinical note")

class QueryResponse(BaseModel):
    answer: str = Field(..., description="Answer to the question")