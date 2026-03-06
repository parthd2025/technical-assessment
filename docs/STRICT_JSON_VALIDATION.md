# Strict JSON Validation for LLM Responses

## Overview

This document describes the comprehensive JSON validation system implemented to ensure LLM responses are strictly valid JSON and prevent hallucinations or malformed outputs.

## Problem Statement

Large Language Models (LLMs) may occasionally:
1. **Hallucinate data** - Add extra fields or information not in the source
2. **Format JSON incorrectly** - Include markdown code blocks, extra text, or malformed syntax
3. **Violate schema** - Return data that doesn't match the expected structure
4. **Omit required fields** - Miss critical fields in the response
5. **Use incorrect data types** - Return strings instead of booleans, etc.

## Solution Architecture

The implementation uses a **multi-layered validation approach** with automatic retry logic:

```
┌─────────────────────────────────────────────────────────┐
│                    LLM Response                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Output Sanitization                           │
│  - Remove markdown code blocks (```json ... ```)        │
│  - Strip extra text before/after JSON                   │
│  - Clean whitespace and formatting                      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 2: JSON Parsing                                  │
│  - Parse with json.loads()                              │
│  - Catch syntax errors (trailing commas, etc.)          │
│  - Validate JSON structure integrity                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Schema Validation                             │
│  - Verify all required fields present                   │
│  - Check data types (list, dict, bool, str)             │
│  - Validate nested structures                           │
│  - Detect and remove hallucinated extra fields          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 4: Pydantic Validation                           │
│  - Strict type checking with Pydantic models            │
│  - Field-level validation                               │
│  - Ensure business logic constraints                    │
└─────────────────────────────────────────────────────────┘
                          ↓
                 ✓ Valid Entity Object
```

## Key Features

### 1. JSON Sanitization

**Function:** `sanitize_json_string(raw_output: str) -> str`

Handles common LLM output issues:

```python
# Example: LLM returns markdown code block
Input:  "```json\n{\"diagnoses\": [\"diabetes\"]}\n```"
Output: "{\"diagnoses\": [\"diabetes\"]}"

# Example: LLM adds explanatory text
Input:  "Here is the result:\n{\"diagnoses\": []}"
Output: "{\"diagnoses\": []}"
```

**Patterns handled:**
- Markdown code blocks with/without `json` label
- Explanatory text before JSON
- Additional commentary after JSON
- Mixed text and JSON content

### 2. Schema Validation

**Function:** `validate_json_schema(data: Dict[str, Any]) -> None`

Performs strict structure validation:

```python
# Required fields check
required_fields = ['diagnoses', 'medications', 'phi_detected']

# Type validation
- diagnoses: List[str]
- medications: List[Dict[str, str]]
- phi_detected: bool

# Nested validation
Each medication must have:
- name: str
- dosage: str
- frequency: str
```

**Hallucination detection:**
```python
# Extra fields are detected and removed
Input:  {
    "diagnoses": ["diabetes"],
    "medications": [],
    "phi_detected": false,
    "confidence": 0.95,          # ← Hallucinated field
    "source": "clinical_note"    # ← Hallucinated field
}

Output: {
    "diagnoses": ["diabetes"],
    "medications": [],
    "phi_detected": false
}
# Extra fields removed with warning logged
```

### 3. Retry Logic with Backoff

**Function:** `extract_entities_from_text()` with retry loop

```python
MAX_RETRY_ATTEMPTS = 3

for attempt in range(1, 4):
    try:
        # Call LLM with enhanced prompts on retry
        if attempt > 1:
            # Lower temperature to 0.0 for deterministic output
            # Add warning to system prompt
        
        # Validate response
        # ...
        
        return result  # Success!
        
    except ValueError as e:
        if attempt == 3:
            raise  # Give up after 3 attempts
        
        # Exponential backoff: 0.5s, 1.0s, 1.5s
        time.sleep(0.5 * attempt)
```

**Retry strategy:**
- **Attempt 1:** Normal temperature (e.g., 0.3), standard prompt
- **Attempt 2:** Temperature = 0.0, enhanced prompt with warning
- **Attempt 3:** Temperature = 0.0, final attempt before failure

**Enhanced prompt on retry:**
```python
"⚠️ CRITICAL: Previous response had formatting errors. 
Ensure output is STRICTLY valid JSON with no extra text."
```

### 4. Comprehensive Error Messages

All validation errors include specific details:

```python
# Missing field
"Missing required fields: ['medications', 'phi_detected']"

# Type error
"'diagnoses' must be a list, got str"

# Nested error
"medication[2].dosage must be a string, got int"

# JSON syntax error
"Invalid JSON structure: Expecting ',' delimiter at position 45"
```

## Usage Examples

### Valid Response - First Attempt Success

```python
clinical_note = "Patient has Type 2 Diabetes. On Metformin 500mg BID."

result = extract_entities_from_text(clinical_note)
# ✓ Success on first attempt
# Logs: "✓ Entity extraction successful - Attempt: 1, Duration: 234.56ms"

print(result.diagnoses)      # ['Type 2 Diabetes']
print(result.medications[0]) # Medication(name='Metformin', dosage='500mg', frequency='BID')
```

### Malformed JSON - Retry Success

```python
# LLM returns markdown on first attempt:
# "```json\n{\"diagnoses\": [\"diabetes\"]}\n```"
# System retries with enhanced prompt
# Second attempt returns clean JSON

result = extract_entities_from_text(clinical_note)
# ✓ Success on attempt 2
# Logs: 
#   "Retry attempt 2 due to previous error: ..."
#   "✓ Entity extraction successful - Attempt: 2, Duration: 456.78ms"
```

### Complete Failure - All Retries Exhausted

```python
# LLM consistently returns invalid output
# After 3 attempts with different temperatures and enhanced prompts:

try:
    result = extract_entities_from_text(clinical_note)
except ValueError as e:
    print(e)
    # "LLM failed to return valid JSON after 3 attempts: ..."
    # Logs: "All 3 attempts failed. Last error: Invalid JSON structure..."
```

### Hallucination Detection

```python
# LLM adds extra fields not in schema
# Example LLM response:
{
    "diagnoses": ["Hypertension"],
    "medications": [...],
    "phi_detected": true,
    "confidence_score": 0.95,        # Extra field
    "processing_time": "1.2s",       # Extra field
    "data_source": "EMR"             # Extra field
}

result = extract_entities_from_text(clinical_note)
# Extra fields automatically removed
# Logs: "Unexpected extra fields detected (potential hallucination): 
#        ['confidence_score', 'processing_time', 'data_source']"

# Result only contains valid fields
assert not hasattr(result, 'confidence_score')
```

## API Error Handling

The FastAPI layer wraps validation errors appropriately:

```python
@app.post("/api/v1/extract")
async def extract_entities(input: ClinicalNoteInput):
    try:
        return extract_entities_from_text(input.clinical_note)
    
    except ValueError as e:
        # Validation or JSON parsing errors → HTTP 422
        raise HTTPException(status_code=422, detail=str(e))
    
    except RuntimeError as e:
        # API or system errors → HTTP 500
        raise HTTPException(status_code=500, detail=str(e))
```

**Error responses:**

```json
// HTTP 422 - Validation Error
{
    "detail": "LLM failed to return valid JSON after 3 attempts: Invalid JSON structure"
}

// HTTP 500 - System Error  
{
    "detail": "Error calling Groq API: Connection timeout"
}
```

## Testing

Comprehensive test suite in `tests/test_json_validation.py`:

### Test Categories

1. **Sanitization Tests** (`TestSanitizeJsonString`)
   - Clean JSON passthrough
   - Markdown block removal
   - Text trimming before/after JSON
   - Error handling for missing JSON

2. **Schema Validation Tests** (`TestValidateJsonSchema`)
   - Required field presence
   - Type checking (list, dict, bool, str)
   - Nested structure validation
   - Hallucination detection and removal

3. **Parsing Tests** (`TestParseAndValidateJson`)
   - Valid JSON parsing
   - Markdown-wrapped JSON
   - Syntax error detection

4. **Retry Logic Tests** (`TestExtractEntitiesWithRetry`)
   - First attempt success
   - Retry on malformed JSON
   - Max retries exhaustion
   - Temperature adjustment on retry

5. **Edge Case Tests** (`TestEdgeCases`)
   - Empty lists handling
   - Multiple medications
   - Invalid medication formats

### Running Tests

```bash
# Run all JSON validation tests
pytest tests/test_json_validation.py -v

# Run with coverage
pytest tests/test_json_validation.py --cov=src.llm_service --cov-report=html

# Run specific test class
pytest tests/test_json_validation.py::TestSanitizeJsonString -v

# Run specific test
pytest tests/test_json_validation.py::TestRetry::test_retry_on_malformed_json -v
```

## Performance Impact

### Latency Analysis

- **Normal case (1st attempt success):** Negligible overhead (~1-2ms for validation)
- **Retry case (2nd attempt):** +500ms delay + additional LLM call (~200-400ms)
- **Max retries (3rd attempt):** +1500ms delay + 2 additional LLM calls

### Token Usage

- **Retry enhancement:** ~20-30 additional tokens per retry for enhanced prompt
- **Multiple attempts:** Linear multiplication of base token usage

### Success Rates (Expected)

With Groq's JSON mode:
- **1st attempt success:** ~98%
- **2nd attempt success:** ~99.5%
- **Complete failure:** <0.5%

## Logging and Observability

### Log Levels

```python
# DEBUG - Detailed validation steps
logger.debug("Sanitized JSON (attempt 1): {...}")
logger.debug("Parsed JSON - Diagnoses: 2, Medications: 3")

# INFO - Successful operations
logger.info("✓ Entity extraction successful - Attempt: 1, Duration: 234.56ms")

# WARNING - Retry attempts and hallucinations
logger.warning("Retry attempt 2 due to previous error: Invalid JSON")
logger.warning("Unexpected extra fields detected: ['confidence', 'source']")

# ERROR - Validation failures and final errors
logger.error("JSON validation failed (attempt 3): Missing required fields")
logger.error("All 3 attempts failed. Last error: ...")
```

### Monitoring Metrics

Track these metrics in production:
- `llm_retry_count` - Number of retry attempts per request
- `llm_validation_failures` - Total validation failures
- `llm_hallucination_detections` - Extra fields detected
- `llm_response_time` - Time including retries

## Best Practices

### 1. Prompt Engineering

Ensure prompts explicitly request JSON-only output:

```python
system_prompt = """
CRITICAL RULES:
1. Output ONLY valid JSON - no additional text, explanations, or markdown
2. Extract only information explicitly stated in the text
3. Do not infer, guess, or hallucinate any medical information
"""
```

### 2. Use Groq's JSON Mode

Always set `response_format`:

```python
chat_completion = client.chat.completions.create(
    messages=[...],
    response_format={"type": "json_object"}  # Forces JSON output
)
```

### 3. Monitor Retry Rates

High retry rates indicate prompt or model issues:
- **<2% retries:** Normal operation
- **2-5% retries:** Consider prompt improvements
- **>5% retries:** Investigate model or prompt issues

### 4. Set Appropriate Timeouts

```python
# For LLM calls
timeout = 30  # seconds

# For retries
MAX_RETRY_ATTEMPTS = 3
retry_delay = 0.5  # seconds per attempt
```

## Security Considerations

### PHI Protection

Validation doesn't log full clinical notes:
```python
logger.info(f"Note length: {len(clinical_note)} chars")  # ✓ Safe
# Don't log: logger.debug(f"Note content: {clinical_note}")  # ✗ PHI leak
```

### Input Validation

Pydantic validates input sizes:
```python
clinical_note: str = Field(..., min_length=10)
```

### Dependency Security

Regular updates for:
- `groq`
- `pydantic`
- `fastapi`

## Troubleshooting

### Issue: High Retry Rates

**Symptoms:** >5% of requests require retries

**Solutions:**
1. Review and refine system prompt
2. Check model version and settings
3. Consider increasing temperature for more creative tasks
4. Analyze failed responses for patterns

### Issue: Hallucinated Fields

**Symptoms:** Frequent extra field warnings in logs

**Solutions:**
1. Strengthen prompt with explicit schema
2. Add examples of valid output to prompt
3. Use lower temperature (0.2-0.3)
4. Consider few-shot prompting with examples

### Issue: Timeout Errors

**Symptoms:** RuntimeError: "Error calling Groq API..."

**Solutions:**
1. Increase timeout value
2. Check API rate limits
3. Implement exponential backoff
4. Add circuit breaker pattern

## Future Enhancements

Potential improvements:
1. **JSON Schema validation** - Use `jsonschema` library for formal schema validation
2. **Streaming validation** - Validate JSON as it streams from LLM
3. **Caching** - Cache validated responses to reduce re-validation
4. **Metrics dashboard** - Real-time monitoring of validation success rates
5. **A/B testing** - Test different validation strategies

## References

- [Groq API Documentation](https://console.groq.com/docs)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [JSON Schema Specification](https://json-schema.org/)
- [FastAPI Error Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)

## Changelog

### Version 1.0.0 (Current)
- ✓ Multi-layer validation (sanitization, parsing, schema, Pydantic)
- ✓ Automatic retry with exponential backoff
- ✓ Hallucination detection
- ✓ Comprehensive error messages
- ✓ Full test coverage
- ✓ Production-ready logging

---

**Last Updated:** March 5, 2026
**Authors:** Technical Assessment Team
**Status:** Production Ready ✓
