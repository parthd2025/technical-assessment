"""
LLM Service for Clinical Note Processing.

This module provides the core LLM integration for:
1. Structured entity extraction from clinical notes
2. Question answering based on clinical notes

Uses Groq API with Llama 3.1 70B model for high-quality medical NLP.
All operations are designed to prevent hallucinations and ensure HIPAA compliance.
"""

import json
import re
import time
from typing import Dict, Any, Optional
from groq import Groq
from pydantic import ValidationError
from .schemas import ExtractedEntity, Medication
from .config import Config
from .logger import setup_logger, log_llm_call

# Initialize logger
logger = setup_logger(__name__)

# Initialize Groq client
logger.info(f"Initializing Groq client with model: {Config.GROQ_MODEL}")
client = Groq(api_key=Config.GROQ_API_KEY)

# Maximum retry attempts for malformed JSON
MAX_RETRY_ATTEMPTS = 3


def parse_and_validate_json(json_string: str, attempt: int) -> Dict[str, Any]:
    """
    Parse and validate JSON string with strict error handling.
    
    This function implements multiple layers of validation:
    1. Strip markdown code blocks and extra text
    2. Parse JSON with error handling
    3. Validate required fields exist
    4. Validate data types match expected schema
    
    Args:
        json_string: Raw string from LLM that should contain JSON
        attempt: Current retry attempt number (for logging)
    
    Returns:
        Dict with validated JSON data
    
    Raises:
        ValueError: If JSON is malformed or doesn't match expected schema
    """
    logger.debug(f"Parsing JSON (attempt {attempt}): {json_string[:100]}...")
    
    # Step 1: Clean up common LLM hallucinations and formatting issues
    cleaned = json_string.strip()
    
    # Remove markdown code blocks if present
    if cleaned.startswith("```"):
        logger.debug("Removing markdown code blocks")
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        cleaned = cleaned.strip()
    
    # Remove any text before first { or after last }
    first_brace = cleaned.find('{')
    last_brace = cleaned.rfind('}')
    
    if first_brace == -1 or last_brace == -1:
        logger.error(f"No valid JSON object found in response: {cleaned[:200]}")
        raise ValueError("Response does not contain a valid JSON object")
    
    if first_brace > 0 or last_brace < len(cleaned) - 1:
        logger.warning(f"Extra text detected around JSON - extracting object only")
        cleaned = cleaned[first_brace:last_brace + 1]
    
    # Step 2: Parse JSON
    try:
        data = json.loads(cleaned)
        logger.debug(f"Successfully parsed JSON: {type(data)}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error at position {e.pos}: {e.msg}")
        logger.error(f"Problematic JSON: {cleaned}")
        raise ValueError(f"Invalid JSON format: {e.msg} at position {e.pos}")
    
    # Step 3: Validate this is a dict (not list or other type)
    if not isinstance(data, dict):
        logger.error(f"Expected dict but got {type(data)}")
        raise ValueError(f"Expected JSON object (dict), got {type(data).__name__}")
    
    # Step 4: Validate required fields
    required_fields = ["diagnoses", "medications", "phi_detected"]
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        logger.error(f"Missing required fields: {missing_fields}")
        raise ValueError(f"Missing required fields in JSON: {', '.join(missing_fields)}")
    
    # Step 5: Validate field types
    if not isinstance(data["diagnoses"], list):
        logger.error(f"diagnoses should be list, got {type(data['diagnoses'])}")
        raise ValueError(f"Field 'diagnoses' must be a list, got {type(data['diagnoses']).__name__}")
    
    if not isinstance(data["medications"], list):
        logger.error(f"medications should be list, got {type(data['medications'])}")
        raise ValueError(f"Field 'medications' must be a list, got {type(data['medications']).__name__}")
    
    if not isinstance(data["phi_detected"], bool):
        logger.error(f"phi_detected should be bool, got {type(data['phi_detected'])}")
        raise ValueError(f"Field 'phi_detected' must be a boolean, got {type(data['phi_detected']).__name__}")
    
    # Step 6: Validate medication structure
    for idx, med in enumerate(data["medications"]):
        if not isinstance(med, dict):
            logger.error(f"Medication at index {idx} is not a dict: {type(med)}")
            raise ValueError(f"Medication at index {idx} must be an object, got {type(med).__name__}")
        
        required_med_fields = ["name", "dosage", "frequency"]
        missing_med_fields = [field for field in required_med_fields if field not in med]
        
        if missing_med_fields:
            logger.error(f"Medication at index {idx} missing fields: {missing_med_fields}")
            raise ValueError(f"Medication at index {idx} missing fields: {', '.join(missing_med_fields)}")
        
        # Validate all medication fields are strings
        for field in required_med_fields:
            if not isinstance(med[field], str):
                logger.error(f"Medication[{idx}].{field} should be string, got {type(med[field])}")
                raise ValueError(f"Medication field '{field}' must be a string, got {type(med[field]).__name__}")
    
    # Step 7: Validate all diagnoses are strings
    for idx, diag in enumerate(data["diagnoses"]):
        if not isinstance(diag, str):
            logger.error(f"Diagnosis at index {idx} is not a string: {type(diag)}")
            raise ValueError(f"Diagnosis at index {idx} must be a string, got {type(diag).__name__}")
    
    logger.info(f"✓ JSON validation passed - {len(data['diagnoses'])} diagnoses, {len(data['medications'])} medications")
    return data


def extract_entities_from_text(clinical_note: str) -> ExtractedEntity:
    """
    Extract structured entities from clinical note using Groq LLM.
    
    This function uses a carefully crafted prompt to ensure:
    - Valid JSON output through response_format specification
    - Accurate entity extraction without hallucination
    - PHI detection per HIPAA guidelines
    - Proper medication parsing with dosage and frequency
    
    Args:
        clinical_note: Raw clinical note text from EMR/EHR
    
    Returns:
        ExtractedEntity: Structured data with diagnoses, medications, and PHI flag
    
    Raises:
        ValueError: If LLM returns invalid JSON or data doesn't match schema, or if input is invalid
        RuntimeError: If Groq API call fails
    
    Example:
        >>> note = "Patient has Type 2 Diabetes. Started on Metformin 500mg BID."
        >>> result = extract_entities_from_text(note)
        >>> print(result.diagnoses)
        ['Type 2 Diabetes']
        >>> print(result.medications[0].name)
        'Metformin'
    """
    # Edge case: Empty or whitespace-only input
    if not clinical_note or not clinical_note.strip():
        logger.warning("Empty clinical note provided")
        raise ValueError("Clinical note cannot be empty")
    
    # Edge case: Very short input (likely not a real clinical note)
    if len(clinical_note.strip()) < 10:
        logger.warning(f"Clinical note too short: {len(clinical_note)} chars")
        raise ValueError("Clinical note must be at least 10 characters")
    
    # Edge case: Very long input (may exceed token limits)
    MAX_NOTE_LENGTH = 50000  # ~12,500 tokens with 4 chars/token ratio
    if len(clinical_note) > MAX_NOTE_LENGTH:
        logger.warning(f"Clinical note too long: {len(clinical_note)} chars, truncating to {MAX_NOTE_LENGTH}")
        clinical_note = clinical_note[:MAX_NOTE_LENGTH]
    
    logger.info(f"Starting entity extraction - Note length: {len(clinical_note)} chars")
    start_time = time.time()
    
    system_prompt = """You are a medical information extraction assistant. Your task is to extract specific entities from clinical notes and return them in a strict JSON format.

CRITICAL RULES:
1. Output ONLY valid JSON - no additional text, explanations, or markdown
2. Extract only information explicitly stated in the text
3. Do not infer, guess, or hallucinate any medical information
4. If no diagnoses found, return empty array []
5. If no medications found, return empty array []
6. PHI (Protected Health Information) includes: patient names, dates of birth, phone numbers, addresses, medical record numbers, social security numbers, email addresses

JSON Schema (REQUIRED FORMAT):
{
  "diagnoses": ["list of medical conditions mentioned"],
  "medications": [
    {
      "name": "medication name",
      "dosage": "dosage amount with units",
      "frequency": "administration schedule"
    }
  ],
  "phi_detected": boolean
}

EXAMPLES:

Example 1 - Full clinical note:
Input: "Patient John Doe (DOB: 11/04/1958) diagnosed with Type 2 Diabetes and Hypertension. Prescribed Metformin 500mg BID and Lisinopril 10mg daily."
Output: {"diagnoses": ["Type 2 Diabetes", "Hypertension"], "medications": [{"name": "Metformin", "dosage": "500mg", "frequency": "BID"}, {"name": "Lisinopril", "dosage": "10mg", "frequency": "daily"}], "phi_detected": true}

Example 2 - No medications:
Input: "Patient diagnosed with seasonal allergies. No medications prescribed at this time."
Output: {"diagnoses": ["seasonal allergies"], "medications": [], "phi_detected": false}

Example 3 - No PHI:
Input: "Patient presents with acute bronchitis. Started on Azithromycin 250mg daily for 5 days."
Output: {"diagnoses": ["acute bronchitis"], "medications": [{"name": "Azithromycin", "dosage": "250mg", "frequency": "daily for 5 days"}], "phi_detected": false}

MEDICATION EXTRACTION RULES:
- Always include units with dosage (mg, mL, tablets, etc.)
- Capture full frequency instructions (BID, TID, QID, PRN, daily, twice daily, etc.)
- For PRN medications, include the condition (e.g., "PRN for pain")
- Extract generic names when mentioned, otherwise brand names

DIAGNOSIS EXTRACTION RULES:
- Extract medical conditions, diseases, and diagnoses
- Include both acute and chronic conditions
- Do not extract symptoms unless explicitly labeled as a diagnosis
- Preserve medical terminology as written"""

    user_prompt = f"""Extract entities from this clinical note:

{clinical_note}

Return ONLY the JSON object with diagnoses, medications, and phi_detected."""

    # Retry loop for handling malformed JSON responses
    last_error = None
    
    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        try:
            logger.debug(
                f"Calling Groq API for extraction (attempt {attempt}/{MAX_RETRY_ATTEMPTS}) - "
                f"Model: {Config.GROQ_MODEL}, Temp: {Config.LLM_TEMPERATURE}"
            )
            
            # Enhance prompt on retry attempts
            retry_system_prompt = system_prompt
            if attempt > 1:
                retry_system_prompt += f"\n\n⚠️ CRITICAL: Previous response had formatting errors. Ensure output is STRICTLY valid JSON with no extra text."
                logger.warning(f"Retry attempt {attempt} due to previous error: {last_error}")
            
            # Call Groq API with JSON mode for structured output
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": retry_system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=Config.GROQ_MODEL,
                temperature=Config.LLM_TEMPERATURE if attempt == 1 else 0.0,  # Lower temp on retry
                max_tokens=Config.LLM_MAX_TOKENS_EXTRACT,
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            result = chat_completion.choices[0].message.content.strip()
            tokens_used = chat_completion.usage.total_tokens if hasattr(chat_completion, 'usage') else None
            
            log_llm_call(
                logger, 
                operation="extract", 
                model=Config.GROQ_MODEL, 
                tokens=tokens_used,
                note_length=len(clinical_note)
            )
            
            logger.debug(f"Raw LLM response (attempt {attempt}): {result[:200]}...")
            
            # Parse and validate JSON with strict checking
            data = parse_and_validate_json(result, attempt)
            logger.debug(f"Parsed JSON - Diagnoses: {len(data.get('diagnoses', []))}, Medications: {len(data.get('medications', []))}")
            
            # Convert medications to proper format with validation
            medications = []
            for idx, med in enumerate(data.get("medications", [])):
                try:
                    # Strict Pydantic validation for each medication
                    medication = Medication(**med)
                    medications.append(medication)
                    logger.debug(
                        f"Extracted medication[{idx}]: {medication.name} "
                        f"{medication.dosage} {medication.frequency}"
                    )
                except ValidationError as ve:
                    logger.error(f"Medication validation error at index {idx}: {ve}")
                    raise ValueError(f"Invalid medication format at index {idx}: {ve}")
            
            # Create validated response with strict Pydantic validation
            try:
                result_entity = ExtractedEntity(
                    diagnoses=data.get("diagnoses", []),
                    medications=medications,
                    phi_detected=data.get("phi_detected", False)
                )
            except ValidationError as ve:
                logger.error(f"Entity validation error: {ve}")
                raise ValueError(f"LLM output validation failed: {ve}")
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"✓ Entity extraction successful - Attempt: {attempt}, Duration: {duration_ms:.2f}ms, "
                f"Diagnoses: {len(result_entity.diagnoses)}, "
                f"Medications: {len(result_entity.medications)}, "
                f"PHI: {result_entity.phi_detected}"
            )
            
            return result_entity
            
        except ValueError as e:
            last_error = str(e)
            logger.warning(f"Attempt {attempt} failed with validation error: {e}")
            
            if attempt == MAX_RETRY_ATTEMPTS:
                logger.error(f"All {MAX_RETRY_ATTEMPTS} attempts failed. Last error: {last_error}")
                raise ValueError(f"LLM failed to return valid JSON after {MAX_RETRY_ATTEMPTS} attempts: {last_error}")
            
            # Small delay before retry
            time.sleep(0.5 * attempt)
            
        except Exception as e:
            logger.error(f"Unexpected error during extraction (attempt {attempt}): {e}", exc_info=True)
            
            if attempt == MAX_RETRY_ATTEMPTS:
                raise RuntimeError(f"Error calling Groq API after {MAX_RETRY_ATTEMPTS} attempts: {e}")
            
            time.sleep(0.5 * attempt)


def answer_clinical_question(clinical_note: str, question: str) -> str:
    """
    Answer a clinical question based on the provided note using Groq LLM.
    
    This function is designed to:
    1. Answer only based on information explicitly in the note
    2. Explicitly refuse to answer if information is not present
    3. Avoid hallucinations and speculation
    4. Provide concise, factual answers with quotes when appropriate
    
    Args:
        clinical_note: The clinical note text to query
        question: Natural language question about the note
    
    Returns:
        str: Answer based on the note, or refusal message if info not present
    
    Raises:
        ValueError: If inputs are invalid
        RuntimeError: If Groq API call fails
    
    Example:
        >>> note = "Patient on Lisinopril 10mg daily for hypertension."
        >>> answer = answer_clinical_question(note, "What is the Lisinopril dosage?")
        >>> print(answer)
        'The Lisinopril dosage is 10mg daily'
    """
    # Edge case: Empty or whitespace-only inputs
    if not clinical_note or not clinical_note.strip():
        logger.warning("Empty clinical note provided to Q&A")
        raise ValueError("Clinical note cannot be empty")
    
    if not question or not question.strip():
        logger.warning("Empty question provided to Q&A")
        raise ValueError("Question cannot be empty")
    
    # Edge case: Very long inputs
    MAX_NOTE_LENGTH = 50000
    MAX_QUESTION_LENGTH = 500
    
    if len(clinical_note) > MAX_NOTE_LENGTH:
        logger.warning(f"Clinical note too long for Q&A: {len(clinical_note)} chars, truncating")
        clinical_note = clinical_note[:MAX_NOTE_LENGTH]
    
    if len(question) > MAX_QUESTION_LENGTH:
        logger.warning(f"Question too long: {len(question)} chars, truncating")
        question = question[:MAX_QUESTION_LENGTH]
    
    logger.info(f"Answering clinical question - Note length: {len(clinical_note)} chars, Question: {question[:100]}")
    start_time = time.time()
    
    system_prompt = """You are a medical assistant that answers questions based strictly on the provided clinical notes.

CRITICAL RULES:
1. Answer ONLY based on information explicitly stated in the clinical note
2. If the answer is not in the note, respond EXACTLY with: "I cannot answer this based on the provided clinical note."
3. Do not infer, speculate, or add medical knowledge not present in the text
4. Do not use your general medical knowledge - only what's in the note
5. Be concise and factual - maximum 3 sentences
6. Quote relevant parts of the note when appropriate using quotation marks
7. For medication questions, include name, dosage, and frequency if available
8. For diagnosis questions, use the exact terminology from the note

EXAMPLES:

Example 1 - Information present:
Note: "Patient prescribed Lisinopril 10mg daily for hypertension."
Question: "What is the Lisinopril dosage?"
Answer: "The Lisinopril dosage is 10mg taken daily."

Example 2 - Information not present:
Note: "Patient has Type 2 Diabetes."
Question: "What is the patient's A1C level?"
Answer: "I cannot answer this based on the provided clinical note."

Example 3 - Partial information:
Note: "Patient started on Metformin for diabetes management."
Question: "What is the Metformin dosage?"
Answer: "I cannot answer this based on the provided clinical note."

Remember: If any part of the answer requires information not in the note, use the refusal response."""

    user_prompt = f"""Clinical Note:
{clinical_note}

Question: {question}

Answer:"""

    try:
        logger.debug(f"Calling Groq API for Q&A - Model: {Config.GROQ_MODEL}")
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=Config.GROQ_MODEL,
            temperature=Config.LLM_TEMPERATURE,
            max_tokens=Config.LLM_MAX_TOKENS_QUERY
        )
        
        answer = chat_completion.choices[0].message.content.strip()
        tokens_used = chat_completion.usage.total_tokens if hasattr(chat_completion, 'usage') else None
        
        log_llm_call(
            logger,
            operation="query",
            model=Config.GROQ_MODEL,
            tokens=tokens_used,
            question_length=len(question)
        )
        
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Q&A completed - Duration: {duration_ms:.2f}ms, Answer length: {len(answer)} chars")
        logger.debug(f"Answer: {answer[:200]}...")
        
        return answer
        
    except Exception as e:
        logger.error(f"Error during Q&A: {e}", exc_info=True)
        raise RuntimeError(f"Error calling Groq API: {e}")