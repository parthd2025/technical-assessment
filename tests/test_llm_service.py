"""
Unit tests for the LLM Service module

This module tests:
- JSON parsing and validation logic
- Entity extraction from clinical notes
- Clinical question answering
- Error handling and retry logic
- PHI detection
"""

import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError
from src.llm_service import (
    parse_and_validate_json,
    extract_entities_from_text,
    answer_clinical_question,
    MAX_RETRY_ATTEMPTS
)
from src.schemas import ExtractedEntity, Medication


class TestParseAndValidateJson:
    """Tests for JSON parsing and validation function"""
    
    def test_parse_valid_json(self):
        """Test parsing a valid JSON response"""
        json_string = '''
        {
            "diagnoses": ["Hypertension", "Type 2 Diabetes"],
            "medications": [
                {"name": "Lisinopril", "dosage": "10mg", "frequency": "daily"}
            ],
            "phi_detected": true
        }
        '''
        result = parse_and_validate_json(json_string, 1)
        
        assert result["diagnoses"] == ["Hypertension", "Type 2 Diabetes"]
        assert len(result["medications"]) == 1
        assert result["medications"][0]["name"] == "Lisinopril"
        assert result["phi_detected"] is True
    
    def test_parse_json_with_markdown_blocks(self):
        """Test parsing JSON wrapped in markdown code blocks"""
        json_string = '''```json
        {
            "diagnoses": ["COPD"],
            "medications": [],
            "phi_detected": false
        }
        ```'''
        result = parse_and_validate_json(json_string, 1)
        
        assert result["diagnoses"] == ["COPD"]
        assert result["medications"] == []
        assert result["phi_detected"] is False
    
    def test_parse_json_with_extra_text(self):
        """Test parsing JSON with extra text before and after"""
        json_string = '''Here is the extracted data:
        {
            "diagnoses": ["Migraine"],
            "medications": [
                {"name": "Sumatriptan", "dosage": "50mg", "frequency": "PRN"}
            ],
            "phi_detected": false
        }
        Hope this helps!'''
        result = parse_and_validate_json(json_string, 1)
        
        assert result["diagnoses"] == ["Migraine"]
        assert len(result["medications"]) == 1
        assert result["phi_detected"] is False
    
    def test_parse_json_missing_required_field(self):
        """Test parsing JSON with missing required field raises ValueError"""
        json_string = '''
        {
            "diagnoses": ["Asthma"],
            "medications": []
        }
        '''
        with pytest.raises(ValueError, match="Missing required fields"):
            parse_and_validate_json(json_string, 1)
    
    def test_parse_json_invalid_diagnoses_type(self):
        """Test parsing JSON with wrong type for diagnoses field"""
        json_string = '''
        {
            "diagnoses": "Asthma",
            "medications": [],
            "phi_detected": false
        }
        '''
        with pytest.raises(ValueError, match="diagnoses.*must be a list"):
            parse_and_validate_json(json_string, 1)
    
    def test_parse_json_invalid_medications_type(self):
        """Test parsing JSON with wrong type for medications field"""
        json_string = '''
        {
            "diagnoses": ["Asthma"],
            "medications": "Albuterol",
            "phi_detected": false
        }
        '''
        with pytest.raises(ValueError, match="medications.*must be a list"):
            parse_and_validate_json(json_string, 1)
    
    def test_parse_json_invalid_phi_detected_type(self):
        """Test parsing JSON with wrong type for phi_detected field"""
        json_string = '''
        {
            "diagnoses": ["Asthma"],
            "medications": [],
            "phi_detected": "yes"
        }
        '''
        with pytest.raises(ValueError, match="phi_detected.*must be a boolean"):
            parse_and_validate_json(json_string, 1)
    
    def test_parse_json_medication_missing_field(self):
        """Test parsing JSON with medication missing required fields"""
        json_string = '''
        {
            "diagnoses": ["Asthma"],
            "medications": [
                {"name": "Albuterol", "dosage": "2 puffs"}
            ],
            "phi_detected": false
        }
        '''
        with pytest.raises(ValueError, match="Medication.*missing fields"):
            parse_and_validate_json(json_string, 1)
    
    def test_parse_json_medication_invalid_field_type(self):
        """Test parsing JSON with medication field as non-string"""
        json_string = '''
        {
            "diagnoses": ["Asthma"],
            "medications": [
                {"name": "Albuterol", "dosage": 100, "frequency": "daily"}
            ],
            "phi_detected": false
        }
        '''
        with pytest.raises(ValueError, match="dosage.*must be a string"):
            parse_and_validate_json(json_string, 1)
    
    def test_parse_json_diagnosis_not_string(self):
        """Test parsing JSON with diagnosis as non-string"""
        json_string = '''
        {
            "diagnoses": ["Asthma", 123, "COPD"],
            "medications": [],
            "phi_detected": false
        }
        '''
        with pytest.raises(ValueError, match="Diagnosis.*must be a string"):
            parse_and_validate_json(json_string, 1)
    
    def test_parse_json_no_braces(self):
        """Test parsing text with no JSON braces"""
        json_string = "This is not JSON at all"
        with pytest.raises(ValueError, match="does not contain a valid JSON object"):
            parse_and_validate_json(json_string, 1)
    
    def test_parse_json_malformed(self):
        """Test parsing malformed JSON"""
        json_string = '''
        {
            "diagnoses": ["Asthma"],
            "medications": [],
            "phi_detected": false
        '''  # Missing closing brace
        with pytest.raises(ValueError, match="does not contain a valid JSON object"):
            parse_and_validate_json(json_string, 1)
    
    def test_parse_json_empty_lists(self):
        """Test parsing valid JSON with empty lists"""
        json_string = '''
        {
            "diagnoses": [],
            "medications": [],
            "phi_detected": false
        }
        '''
        result = parse_and_validate_json(json_string, 1)
        
        assert result["diagnoses"] == []
        assert result["medications"] == []
        assert result["phi_detected"] is False


class TestExtractEntitiesFromText:
    """Tests for entity extraction function"""
    
    @patch('src.llm_service.client')
    def test_extract_entities_success(self, mock_client):
        """Test successful entity extraction"""
        # Mock Groq API response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '''
        {
            "diagnoses": ["Hypertension", "Type 2 Diabetes"],
            "medications": [
                {"name": "Lisinopril", "dosage": "10mg", "frequency": "daily"},
                {"name": "Metformin", "dosage": "500mg", "frequency": "BID"}
            ],
            "phi_detected": true
        }
        '''
        mock_response.usage.total_tokens = 150
        mock_client.chat.completions.create.return_value = mock_response
        
        clinical_note = "Patient John Doe has hypertension and diabetes. On Lisinopril 10mg daily and Metformin 500mg BID."
        result = extract_entities_from_text(clinical_note)
        
        assert isinstance(result, ExtractedEntity)
        assert len(result.diagnoses) == 2
        assert "Hypertension" in result.diagnoses
        assert "Type 2 Diabetes" in result.diagnoses
        assert len(result.medications) == 2
        assert result.medications[0].name == "Lisinopril"
        assert result.medications[0].dosage == "10mg"
        assert result.medications[0].frequency == "daily"
        assert result.phi_detected is True
        
        # Verify API was called correctly
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]["response_format"] == {"type": "json_object"}
    
    @patch('src.llm_service.client')
    def test_extract_entities_no_medications(self, mock_client):
        """Test extraction with no medications found"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '''
        {
            "diagnoses": ["Migraine"],
            "medications": [],
            "phi_detected": false
        }
        '''
        mock_response.usage.total_tokens = 100
        mock_client.chat.completions.create.return_value = mock_response
        
        clinical_note = "Patient presents with migraine headache."
        result = extract_entities_from_text(clinical_note)
        
        assert len(result.diagnoses) == 1
        assert result.diagnoses[0] == "Migraine"
        assert len(result.medications) == 0
        assert result.phi_detected is False
    
    @patch('src.llm_service.client')
    def test_extract_entities_no_diagnoses(self, mock_client):
        """Test extraction with no diagnoses found"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '''
        {
            "diagnoses": [],
            "medications": [
                {"name": "Aspirin", "dosage": "81mg", "frequency": "daily"}
            ],
            "phi_detected": false
        }
        '''
        mock_response.usage.total_tokens = 100
        mock_client.chat.completions.create.return_value = mock_response
        
        clinical_note = "Patient taking Aspirin 81mg daily for prevention."
        result = extract_entities_from_text(clinical_note)
        
        assert len(result.diagnoses) == 0
        assert len(result.medications) == 1
        assert result.medications[0].name == "Aspirin"
    
    @patch('src.llm_service.client')
    def test_extract_entities_retry_on_malformed_json(self, mock_client):
        """Test retry logic when LLM returns malformed JSON"""
        # First attempt returns malformed JSON
        mock_response_1 = MagicMock()
        mock_response_1.choices[0].message.content = "This is not valid JSON"
        mock_response_1.usage.total_tokens = 50
        
        # Second attempt returns valid JSON
        mock_response_2 = MagicMock()
        mock_response_2.choices[0].message.content = '''
        {
            "diagnoses": ["COPD"],
            "medications": [],
            "phi_detected": false
        }
        '''
        mock_response_2.usage.total_tokens = 80
        
        mock_client.chat.completions.create.side_effect = [mock_response_1, mock_response_2]
        
        clinical_note = "Patient has COPD."
        result = extract_entities_from_text(clinical_note)
        
        assert len(result.diagnoses) == 1
        assert result.diagnoses[0] == "COPD"
        
        # Verify API was called twice (1 initial + 1 retry)
        assert mock_client.chat.completions.create.call_count == 2
    
    @patch('src.llm_service.client')
    def test_extract_entities_max_retries_exceeded(self, mock_client):
        """Test that extraction fails after max retries"""
        # All attempts return malformed JSON
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_response.usage.total_tokens = 50
        mock_client.chat.completions.create.return_value = mock_response
        
        clinical_note = "Patient has asthma."
        
        with pytest.raises(ValueError, match=f"failed to return valid JSON after {MAX_RETRY_ATTEMPTS} attempts"):
            extract_entities_from_text(clinical_note)
        
        # Verify API was called MAX_RETRY_ATTEMPTS times
        assert mock_client.chat.completions.create.call_count == MAX_RETRY_ATTEMPTS
    
    @patch('src.llm_service.client')
    def test_extract_entities_api_error(self, mock_client):
        """Test handling of API errors"""
        mock_client.chat.completions.create.side_effect = Exception("API connection failed")
        
        clinical_note = "Patient has diabetes."
        
        with pytest.raises(RuntimeError, match=f"Error calling Groq API after {MAX_RETRY_ATTEMPTS} attempts"):
            extract_entities_from_text(clinical_note)
    
    @patch('src.llm_service.client')
    def test_extract_entities_phi_detection_true(self, mock_client):
        """Test that PHI is correctly detected"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '''
        {
            "diagnoses": ["Hypertension"],
            "medications": [],
            "phi_detected": true
        }
        '''
        mock_response.usage.total_tokens = 100
        mock_client.chat.completions.create.return_value = mock_response
        
        clinical_note = "John Doe (DOB: 01/15/1975) has hypertension."
        result = extract_entities_from_text(clinical_note)
        
        assert result.phi_detected is True
    
    @patch('src.llm_service.client')
    def test_extract_entities_invalid_medication_validation(self, mock_client):
        """Test that invalid medication data fails validation"""
        # Return medication with wrong field name (should cause validation error)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '''
        {
            "diagnoses": ["Asthma"],
            "medications": [
                {"medication_name": "Albuterol", "dosage": "100mg", "frequency": "daily"}
            ],
            "phi_detected": false
        }
        '''
        mock_response.usage.total_tokens = 100
        mock_client.chat.completions.create.return_value = mock_response
        
        clinical_note = "Patient has asthma."
        
        with pytest.raises(ValueError, match="Medication.*missing fields"):
            extract_entities_from_text(clinical_note)


class TestAnswerClinicalQuestion:
    """Tests for clinical question answering function"""
    
    @patch('src.llm_service.client')
    def test_answer_question_success(self, mock_client):
        """Test successful question answering"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "The patient is taking Lisinopril 10mg daily."
        mock_response.usage.total_tokens = 80
        mock_client.chat.completions.create.return_value = mock_response
        
        clinical_note = "Patient on Lisinopril 10mg daily for hypertension."
        question = "What medication is the patient taking?"
        
        answer = answer_clinical_question(clinical_note, question)
        
        assert isinstance(answer, str)
        assert "Lisinopril" in answer
        assert "10mg daily" in answer
        
        # Verify API was called
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('src.llm_service.client')
    def test_answer_question_information_not_present(self, mock_client):
        """Test question answering when information is not in note"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "I cannot answer this based on the provided clinical note."
        mock_response.usage.total_tokens = 60
        mock_client.chat.completions.create.return_value = mock_response
        
        clinical_note = "Patient has hypertension."
        question = "What is the patient's blood pressure reading?"
        
        answer = answer_clinical_question(clinical_note, question)
        
        assert "cannot answer" in answer.lower()
    
    @patch('src.llm_service.client')
    def test_answer_question_with_quote(self, mock_client):
        """Test question answering that includes a quote from the note"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = 'The patient was diagnosed with "Type 2 Diabetes Mellitus".'
        mock_response.usage.total_tokens = 90
        mock_client.chat.completions.create.return_value = mock_response
        
        clinical_note = "Patient diagnosed with Type 2 Diabetes Mellitus on 12/15/2024."
        question = "What was the patient diagnosed with?"
        
        answer = answer_clinical_question(clinical_note, question)
        
        assert "Type 2 Diabetes Mellitus" in answer
    
    @patch('src.llm_service.client')
    def test_answer_question_api_error(self, mock_client):
        """Test handling of API errors during Q&A"""
        mock_client.chat.completions.create.side_effect = Exception("API timeout")
        
        clinical_note = "Patient has diabetes."
        question = "What condition does the patient have?"
        
        with pytest.raises(RuntimeError, match="Error calling Groq API"):
            answer_clinical_question(clinical_note, question)
    
    @patch('src.llm_service.client')
    def test_answer_question_empty_response(self, mock_client):
        """Test handling of empty response from API"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = ""
        mock_response.usage.total_tokens = 20
        mock_client.chat.completions.create.return_value = mock_response
        
        clinical_note = "Patient has COPD."
        question = "What is the diagnosis?"
        
        answer = answer_clinical_question(clinical_note, question)
        
        assert answer == ""
    
    @patch('src.llm_service.client')
    def test_answer_question_long_note(self, mock_client):
        """Test question answering with a long clinical note"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "The patient has multiple chronic conditions including diabetes, hypertension, and COPD."
        mock_response.usage.total_tokens = 500
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create a long clinical note
        clinical_note = """
        Patient is a 65-year-old male with multiple chronic conditions.
        Past medical history includes Type 2 Diabetes Mellitus diagnosed 10 years ago,
        essential hypertension for 15 years, and COPD for 5 years.
        Current medications include Metformin 1000mg BID, Lisinopril 20mg daily,
        and Albuterol inhaler PRN for shortness of breath.
        """ * 5
        
        question = "What chronic conditions does the patient have?"
        
        answer = answer_clinical_question(clinical_note, question)
        
        assert len(answer) > 0
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('src.llm_service.client')
    def test_answer_question_medication_dosage(self, mock_client):
        """Test question answering about specific medication dosage"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "The Metformin dosage is 500mg twice daily (BID)."
        mock_response.usage.total_tokens = 70
        mock_client.chat.completions.create.return_value = mock_response
        
        clinical_note = "Patient prescribed Metformin 500mg BID for diabetes management."
        question = "What is the Metformin dosage?"
        
        answer = answer_clinical_question(clinical_note, question)
        
        assert "500mg" in answer
        assert "BID" in answer or "twice daily" in answer


class TestIntegration:
    """Integration tests combining multiple functions"""
    
    @patch('src.llm_service.client')
    def test_full_workflow_with_phi(self, mock_client):
        """Test complete workflow from extraction to Q&A with PHI present"""
        # Mock extraction response
        extract_response = MagicMock()
        extract_response.choices[0].message.content = '''
        {
            "diagnoses": ["Hypertension", "Type 2 Diabetes"],
            "medications": [
                {"name": "Lisinopril", "dosage": "10mg", "frequency": "daily"}
            ],
            "phi_detected": true
        }
        '''
        extract_response.usage.total_tokens = 150
        
        # Mock Q&A response
        qa_response = MagicMock()
        qa_response.choices[0].message.content = "The patient is taking Lisinopril 10mg daily."
        qa_response.usage.total_tokens = 80
        
        mock_client.chat.completions.create.side_effect = [extract_response, qa_response]
        
        clinical_note = "John Doe (SSN: 123-45-6789) has hypertension and diabetes. On Lisinopril 10mg daily."
        
        # First, extract entities
        entities = extract_entities_from_text(clinical_note)
        assert entities.phi_detected is True
        assert len(entities.diagnoses) == 2
        assert len(entities.medications) == 1
        
        # Then, answer a question
        question = "What medication is prescribed?"
        answer = answer_clinical_question(clinical_note, question)
        assert "Lisinopril" in answer
        
        # Verify both API calls were made
        assert mock_client.chat.completions.create.call_count == 2
