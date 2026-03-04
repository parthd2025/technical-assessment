"""
Unit tests for the Clinical Note Processing API
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.api import app
from src.schemas import ExtractedEntity, Medication

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for the health check endpoint"""
    
    def test_health_check(self):
        """Test that health endpoint returns correct status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data


class TestExtractEndpoint:
    """Tests for the /api/v1/extract endpoint"""
    
    @patch('src.llm_service.client')
    def test_extract_valid_note(self, mock_client):
        """Test extraction with a valid clinical note"""
        # Mock Groq API response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '''
        {
            "diagnoses": ["COPD", "Type 2 Diabetes Mellitus"],
            "medications": [
                {"name": "Metformin", "dosage": "500mg", "frequency": "BID"},
                {"name": "Albuterol HFA inhaler", "dosage": "2 puffs", "frequency": "q4h PRN"}
            ],
            "phi_detected": true
        }
        '''
        mock_client.chat.completions.create.return_value = mock_response
        
        response = client.post(
            "/api/v1/extract",
            json={
                "clinical_note": "Patient John Doe (DOB: 11/04/1958) was admitted on Oct 12th for acute exacerbation of COPD and Type 2 Diabetes. Prescribed Metformin 500mg BID and Albuterol HFA inhaler 2 puffs q4h PRN."
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "diagnoses" in data
        assert "medications" in data
        assert "phi_detected" in data
        assert isinstance(data["diagnoses"], list)
        assert isinstance(data["medications"], list)
        assert len(data["medications"]) == 2
    
    def test_extract_missing_clinical_note(self):
        """Test extraction with missing clinical_note field"""
        response = client.post(
            "/api/v1/extract",
            json={}
        )
        assert response.status_code == 422  # Validation error
    
    def test_extract_empty_clinical_note(self):
        """Test extraction with empty clinical_note"""
        response = client.post(
            "/api/v1/extract",
            json={"clinical_note": ""}
        )
        # Should still process but may return empty results
        assert response.status_code in [200, 422, 500]


class TestQueryEndpoint:
    """Tests for the /api/v1/query endpoint"""
    
    @patch('src.llm_service.client')
    def test_query_valid_question(self, mock_client):
        """Test Q&A with a valid question"""
        # Mock Groq API response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "The patient should take their Albuterol HFA inhaler 2 puffs every 4 hours as needed (q4h PRN) for wheezing."
        mock_client.chat.completions.create.return_value = mock_response
        
        response = client.post(
            "/api/v1/query",
            json={
                "clinical_note": "Patient prescribed Albuterol HFA inhaler 2 puffs q4h PRN for wheezing.",
                "question": "How often should the patient take their inhaler?"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0
    
    @patch('src.llm_service.client')
    def test_query_unanswerable_question(self, mock_client):
        """Test Q&A with a question that can't be answered from the note"""
        # Mock Groq API response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "I cannot answer this based on the provided clinical note."
        mock_client.chat.completions.create.return_value = mock_response
        
        response = client.post(
            "/api/v1/query",
            json={
                "clinical_note": "Patient prescribed Metformin 500mg BID.",
                "question": "What is the patient's blood pressure?"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "cannot answer" in data["answer"].lower()
    
    def test_query_missing_fields(self):
        """Test Q&A with missing required fields"""
        response = client.post(
            "/api/v1/query",
            json={"clinical_note": "Some note"}
        )
        assert response.status_code == 422  # Validation error
        
        response = client.post(
            "/api/v1/query",
            json={"question": "What is the diagnosis?"}
        )
        assert response.status_code == 422  # Validation error


class TestSchemas:
    """Tests for Pydantic schemas"""
    
    def test_medication_schema(self):
        """Test Medication model validation"""
        med = Medication(name="Aspirin", dosage="100mg", frequency="daily")
        assert med.name == "Aspirin"
        assert med.dosage == "100mg"
        assert med.frequency == "daily"
    
    def test_extracted_entity_schema(self):
        """Test ExtractedEntity model validation"""
        entity = ExtractedEntity(
            diagnoses=["COPD"],
            medications=[Medication(name="Aspirin", dosage="100mg", frequency="daily")],
            phi_detected=True
        )
        assert len(entity.diagnoses) == 1
        assert len(entity.medications) == 1
        assert entity.phi_detected is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])