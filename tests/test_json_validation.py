"""
Unit tests for strict JSON validation in LLM service.

Tests cover:
1. JSON sanitization (removing markdown, extra text)
2. Schema validation (required fields, types, structure)
3. Retry logic for malformed responses
4. Hallucination detection (extra fields)
5. Error handling and recovery
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from src.llm_service import (
    sanitize_json_string,
    validate_json_schema,
    parse_and_validate_json,
    extract_entities_from_text
)
from src.schemas import ExtractedEntity, Medication


class TestSanitizeJsonString:
    """Test JSON sanitization from LLM output."""
    
    def test_clean_json_passthrough(self):
        """Test that clean JSON passes through unchanged."""
        clean_json = '{"diagnoses": [], "medications": [], "phi_detected": false}'
        result = sanitize_json_string(clean_json)
        assert result == clean_json
    
    def test_remove_markdown_code_block(self):
        """Test removal of markdown code blocks."""
        markdown_json = '```json\n{"diagnoses": ["diabetes"], "medications": [], "phi_detected": false}\n```'
        result = sanitize_json_string(markdown_json)
        expected = '{"diagnoses": ["diabetes"], "medications": [], "phi_detected": false}'
        assert result == expected
    
    def test_remove_markdown_without_json_label(self):
        """Test removal of markdown blocks without 'json' label."""
        markdown_json = '```\n{"diagnoses": [], "medications": [], "phi_detected": true}\n```'
        result = sanitize_json_string(markdown_json)
        expected = '{"diagnoses": [], "medications": [], "phi_detected": true}'
        assert result == expected
    
    def test_trim_text_before_json(self):
        """Test trimming extra text before JSON object."""
        prefixed_json = 'Here is the result:\n{"diagnoses": [], "medications": [], "phi_detected": false}'
        result = sanitize_json_string(prefixed_json)
        assert result.startswith('{')
        assert '"diagnoses"' in result
    
    def test_trim_text_after_json(self):
        """Test trimming extra text after JSON object."""
        suffixed_json = '{"diagnoses": [], "medications": [], "phi_detected": false}\n\nHope this helps!'
        result = sanitize_json_string(suffixed_json)
        assert result.endswith('}')
    
    def test_no_json_object_raises_error(self):
        """Test that missing JSON raises ValueError."""
        invalid_text = "This is just plain text with no JSON"
        with pytest.raises(ValueError, match="No JSON object found"):
            sanitize_json_string(invalid_text)
    
    def test_incomplete_json_object_raises_error(self):
        """Test that incomplete JSON raises ValueError."""
        incomplete_json = '{"diagnoses": ["diabetes"], "medications": ['
        with pytest.raises(ValueError, match="No complete JSON object found"):
            sanitize_json_string(incomplete_json)


class TestValidateJsonSchema:
    """Test JSON schema validation."""
    
    def test_valid_schema_passes(self):
        """Test that valid schema passes validation."""
        valid_data = {
            "diagnoses": ["Hypertension"],
            "medications": [
                {"name": "Lisinopril", "dosage": "10mg", "frequency": "daily"}
            ],
            "phi_detected": True
        }
        # Should not raise any exception
        validate_json_schema(valid_data)
    
    def test_missing_diagnoses_fails(self):
        """Test that missing diagnoses field fails."""
        invalid_data = {
            "medications": [],
            "phi_detected": False
        }
        with pytest.raises(ValueError, match="Missing required fields.*diagnoses"):
            validate_json_schema(invalid_data)
    
    def test_missing_medications_fails(self):
        """Test that missing medications field fails."""
        invalid_data = {
            "diagnoses": [],
            "phi_detected": False
        }
        with pytest.raises(ValueError, match="Missing required fields.*medications"):
            validate_json_schema(invalid_data)
    
    def test_missing_phi_detected_fails(self):
        """Test that missing phi_detected field fails."""
        invalid_data = {
            "diagnoses": [],
            "medications": []
        }
        with pytest.raises(ValueError, match="Missing required fields.*phi_detected"):
            validate_json_schema(invalid_data)
    
    def test_diagnoses_not_list_fails(self):
        """Test that non-list diagnoses fails."""
        invalid_data = {
            "diagnoses": "Diabetes",
            "medications": [],
            "phi_detected": False
        }
        with pytest.raises(ValueError, match="'diagnoses' must be a list"):
            validate_json_schema(invalid_data)
    
    def test_diagnoses_non_string_items_fail(self):
        """Test that non-string items in diagnoses fail."""
        invalid_data = {
            "diagnoses": ["Diabetes", 123, "Hypertension"],
            "medications": [],
            "phi_detected": False
        }
        with pytest.raises(ValueError, match="diagnosis\\[1\\] must be a string"):
            validate_json_schema(invalid_data)
    
    def test_medications_not_list_fails(self):
        """Test that non-list medications fails."""
        invalid_data = {
            "diagnoses": [],
            "medications": "Lisinopril 10mg daily",
            "phi_detected": False
        }
        with pytest.raises(ValueError, match="'medications' must be a list"):
            validate_json_schema(invalid_data)
    
    def test_medication_not_dict_fails(self):
        """Test that non-dict medication fails."""
        invalid_data = {
            "diagnoses": [],
            "medications": ["Lisinopril"],
            "phi_detected": False
        }
        with pytest.raises(ValueError, match="medication\\[0\\] must be an object"):
            validate_json_schema(invalid_data)
    
    def test_medication_missing_name_fails(self):
        """Test that medication without name fails."""
        invalid_data = {
            "diagnoses": [],
            "medications": [
                {"dosage": "10mg", "frequency": "daily"}
            ],
            "phi_detected": False
        }
        with pytest.raises(ValueError, match="medication\\[0\\] missing fields.*name"):
            validate_json_schema(invalid_data)
    
    def test_medication_missing_dosage_fails(self):
        """Test that medication without dosage fails."""
        invalid_data = {
            "diagnoses": [],
            "medications": [
                {"name": "Lisinopril", "frequency": "daily"}
            ],
            "phi_detected": False
        }
        with pytest.raises(ValueError, match="medication\\[0\\] missing fields.*dosage"):
            validate_json_schema(invalid_data)
    
    def test_medication_missing_frequency_fails(self):
        """Test that medication without frequency fails."""
        invalid_data = {
            "diagnoses": [],
            "medications": [
                {"name": "Lisinopril", "dosage": "10mg"}
            ],
            "phi_detected": False
        }
        with pytest.raises(ValueError, match="medication\\[0\\] missing fields.*frequency"):
            validate_json_schema(invalid_data)
    
    def test_medication_non_string_name_fails(self):
        """Test that non-string medication name fails."""
        invalid_data = {
            "diagnoses": [],
            "medications": [
                {"name": 123, "dosage": "10mg", "frequency": "daily"}
            ],
            "phi_detected": False
        }
        with pytest.raises(ValueError, match="medication\\[0\\].name must be a string"):
            validate_json_schema(invalid_data)
    
    def test_phi_detected_not_bool_fails(self):
        """Test that non-boolean phi_detected fails."""
        invalid_data = {
            "diagnoses": [],
            "medications": [],
            "phi_detected": "true"
        }
        with pytest.raises(ValueError, match="'phi_detected' must be a boolean"):
            validate_json_schema(invalid_data)
    
    def test_extra_fields_removed(self):
        """Test that extra fields are removed (hallucination prevention)."""
        data_with_extra = {
            "diagnoses": ["Diabetes"],
            "medications": [],
            "phi_detected": False,
            "hallucinated_field": "extra data",
            "another_extra": 123
        }
        validate_json_schema(data_with_extra)
        # Extra fields should be removed
        assert "hallucinated_field" not in data_with_extra
        assert "another_extra" not in data_with_extra
        # Required fields should remain
        assert "diagnoses" in data_with_extra
        assert "medications" in data_with_extra
        assert "phi_detected" in data_with_extra


class TestParseAndValidateJson:
    """Test combined JSON parsing and validation."""
    
    def test_valid_json_string(self):
        """Test parsing valid JSON string."""
        json_str = '{"diagnoses": ["Diabetes"], "medications": [], "phi_detected": true}'
        result = parse_and_validate_json(json_str, attempt=1)
        assert result["diagnoses"] == ["Diabetes"]
        assert result["medications"] == []
        assert result["phi_detected"] is True
    
    def test_json_with_markdown_parsed(self):
        """Test parsing JSON wrapped in markdown."""
        json_str = '```json\n{"diagnoses": [], "medications": [], "phi_detected": false}\n```'
        result = parse_and_validate_json(json_str, attempt=1)
        assert "diagnoses" in result
    
    def test_invalid_json_syntax_fails(self):
        """Test that invalid JSON syntax raises error."""
        invalid_json = '{"diagnoses": ["Diabetes",], "medications": []}'  # Trailing comma
        with pytest.raises(ValueError, match="Invalid JSON structure"):
            parse_and_validate_json(invalid_json, attempt=1)
    
    def test_malformed_json_fails(self):
        """Test that malformed JSON raises error."""
        malformed = '{diagnoses: ["Diabetes"]}'  # Missing quotes on key
        with pytest.raises(ValueError):
            parse_and_validate_json(malformed, attempt=1)


class TestExtractEntitiesWithRetry:
    """Test entity extraction with retry logic."""
    
    @patch('src.llm_service.client')
    def test_successful_extraction_first_attempt(self, mock_client):
        """Test successful extraction on first attempt."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "diagnoses": ["Type 2 Diabetes"],
            "medications": [
                {"name": "Metformin", "dosage": "500mg", "frequency": "BID"}
            ],
            "phi_detected": False
        })
        mock_response.usage.total_tokens = 150
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_entities_from_text("Patient has diabetes on Metformin 500mg BID")
        
        assert len(result.diagnoses) == 1
        assert result.diagnoses[0] == "Type 2 Diabetes"
        assert len(result.medications) == 1
        assert result.medications[0].name == "Metformin"
        assert mock_client.chat.completions.create.call_count == 1
    
    @patch('src.llm_service.client')
    @patch('src.llm_service.time.sleep')  # Mock sleep to speed up tests
    def test_retry_on_malformed_json(self, mock_sleep, mock_client):
        """Test retry logic when LLM returns malformed JSON."""
        # First attempt: malformed JSON
        mock_response_1 = MagicMock()
        mock_response_1.choices[0].message.content = '{"diagnoses": ["Diabetes"'  # Incomplete
        mock_response_1.usage.total_tokens = 100
        
        # Second attempt: valid JSON
        mock_response_2 = MagicMock()
        mock_response_2.choices[0].message.content = json.dumps({
            "diagnoses": ["Diabetes"],
            "medications": [],
            "phi_detected": False
        })
        mock_response_2.usage.total_tokens = 120
        
        mock_client.chat.completions.create.side_effect = [mock_response_1, mock_response_2]
        
        result = extract_entities_from_text("Patient has diabetes")
        
        assert result.diagnoses == ["Diabetes"]
        assert mock_client.chat.completions.create.call_count == 2
        assert mock_sleep.called
    
    @patch('src.llm_service.client')
    @patch('src.llm_service.time.sleep')
    def test_max_retries_then_fail(self, mock_sleep, mock_client):
        """Test that extraction fails after max retries."""
        # All attempts return malformed JSON
        mock_response = MagicMock()
        mock_response.choices[0].message.content = 'Invalid JSON response'
        mock_response.usage.total_tokens = 100
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(ValueError, match="LLM failed to return valid JSON after 3 attempts"):
            extract_entities_from_text("Test note")
        
        assert mock_client.chat.completions.create.call_count == 3
    
    @patch('src.llm_service.client')
    @patch('src.llm_service.time.sleep')
    def test_retry_with_lower_temperature(self, mock_sleep, mock_client):
        """Test that retry attempts use lower temperature."""
        # First attempt fails
        mock_response_1 = MagicMock()
        mock_response_1.choices[0].message.content = '{}'  # Missing required fields
        mock_response_1.usage.total_tokens = 50
        
        # Second attempt succeeds
        mock_response_2 = MagicMock()
        mock_response_2.choices[0].message.content = json.dumps({
            "diagnoses": [],
            "medications": [],
            "phi_detected": False
        })
        mock_response_2.usage.total_tokens = 80
        
        mock_client.chat.completions.create.side_effect = [mock_response_1, mock_response_2]
        
        result = extract_entities_from_text("Test note")
        
        # Check that second call used temperature=0.0
        second_call_kwargs = mock_client.chat.completions.create.call_args_list[1][1]
        assert second_call_kwargs['temperature'] == 0.0
    
    @patch('src.llm_service.client')
    def test_hallucinated_fields_removed(self, mock_client):
        """Test that hallucinated extra fields are removed."""
        # Mock response with extra fields
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "diagnoses": ["Diabetes"],
            "medications": [],
            "phi_detected": False,
            "confidence": 0.95,  # Extra field
            "source": "clinical note"  # Extra field
        })
        mock_response.usage.total_tokens = 150
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_entities_from_text("Patient has diabetes")
        
        # Should successfully extract without extra fields
        assert hasattr(result, 'diagnoses')
        assert hasattr(result, 'medications')
        assert hasattr(result, 'phi_detected')
        assert not hasattr(result, 'confidence')
        assert not hasattr(result, 'source')


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    @patch('src.llm_service.client')
    def test_empty_lists_valid(self, mock_client):
        """Test that empty lists for diagnoses and medications are valid."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "diagnoses": [],
            "medications": [],
            "phi_detected": False
        })
        mock_response.usage.total_tokens = 80
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_entities_from_text("Normal checkup, no issues")
        
        assert result.diagnoses == []
        assert result.medications == []
        assert result.phi_detected is False
    
    @patch('src.llm_service.client')
    def test_multiple_medications_parsed(self, mock_client):
        """Test parsing multiple medications correctly."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "diagnoses": ["Hypertension", "Diabetes"],
            "medications": [
                {"name": "Lisinopril", "dosage": "10mg", "frequency": "daily"},
                {"name": "Metformin", "dosage": "500mg", "frequency": "BID"},
                {"name": "Aspirin", "dosage": "81mg", "frequency": "daily"}
            ],
            "phi_detected": True
        })
        mock_response.usage.total_tokens = 200
        mock_client.chat.completions.create.return_value = mock_response
        
        result = extract_entities_from_text("Complex patient with multiple medications")
        
        assert len(result.diagnoses) == 2
        assert len(result.medications) == 3
        assert result.medications[1].name == "Metformin"
        assert result.phi_detected is True
    
    @patch('src.llm_service.client')
    def test_invalid_medication_format_fails(self, mock_client):
        """Test that invalid medication format causes retry."""
        # Response with invalid medication (missing dosage)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "diagnoses": ["Diabetes"],
            "medications": [
                {"name": "Metformin", "frequency": "BID"}  # Missing dosage
            ],
            "phi_detected": False
        })
        mock_response.usage.total_tokens = 120
        mock_client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(ValueError, match="Invalid medication format"):
            extract_entities_from_text("Patient on Metformin")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
