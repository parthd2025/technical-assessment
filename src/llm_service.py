import json
from groq import Groq
from pydantic import ValidationError
from .schemas import ExtractedEntity, Medication
from .config import Config

# Initialize Groq client
client = Groq(api_key=Config.GROQ_API_KEY)

def extract_entities_from_text(clinical_note: str) -> ExtractedEntity:
    """
    Extract structured entities from clinical note using Groq.
    
    This function uses a carefully crafted prompt to ensure:
    1. Valid JSON output
    2. Accurate entity extraction
    3. PHI detection
    4. No hallucinations
    """
    
    system_prompt = """You are a medical information extraction assistant. Your task is to extract specific entities from clinical notes and return them in a strict JSON format.

CRITICAL RULES:
1. Output ONLY valid JSON - no additional text, explanations, or markdown
2. Extract only information explicitly stated in the text
3. Do not infer, guess, or hallucinate any medical information
4. PHI (Protected Health Information) includes: names, dates of birth, phone numbers, addresses, medical record numbers, social security numbers

JSON Schema:
{
  "diagnoses": ["list of medical conditions mentioned"],
  "medications": [
    {
      "name": "medication name",
      "dosage": "dosage amount",
      "frequency": "how often"
    }
  ],
  "phi_detected": true or false
}"""

    user_prompt = f"""Extract entities from this clinical note:

{clinical_note}

Return ONLY the JSON object with diagnoses, medications, and phi_detected."""

    try:
        # Call Groq API with JSON mode for structured output
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=Config.GROQ_MODEL,
            temperature=Config.LLM_TEMPERATURE,
            max_tokens=Config.LLM_MAX_TOKENS_EXTRACT,
            response_format={"type": "json_object"}  # Force JSON output
        )
        
        result = chat_completion.choices[0].message.content.strip()
        
        # Parse and validate JSON
        data = json.loads(result)
        
        # Convert medications to proper format
        medications = []
        for med in data.get("medications", []):
            if isinstance(med, dict):
                medications.append(Medication(**med))
            else:
                # Handle edge case where medication might be a string
                medications.append(Medication(name=str(med), dosage="", frequency=""))
        
        # Create validated response
        return ExtractedEntity(
            diagnoses=data.get("diagnoses", []),
            medications=medications,
            phi_detected=data.get("phi_detected", False)
        )
        
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}")
    except ValidationError as e:
        raise ValueError(f"LLM output does not match expected schema: {e}")
    except Exception as e:
        raise RuntimeError(f"Error calling Groq API: {e}")


def answer_clinical_question(clinical_note: str, question: str) -> str:
    """
    Answer a clinical question based on the provided note using Groq.
    
    This function is designed to:
    1. Answer only based on information in the note
    2. Explicitly refuse to answer if information is not present
    3. Avoid hallucinations and speculation
    """
    
    system_prompt = """You are a medical assistant that answers questions based strictly on the provided clinical notes.

CRITICAL RULES:
1. Answer ONLY based on information explicitly stated in the clinical note
2. If the answer is not in the note, respond EXACTLY with: "I cannot answer this based on the provided clinical note."
3. Do not infer, speculate, or add medical knowledge not present in the text
4. Be concise and factual
5. Quote relevant parts of the note when appropriate"""

    user_prompt = f"""Clinical Note:
{clinical_note}

Question: {question}

Answer:"""

    try:
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
        return answer
        
    except Exception as e:
        raise RuntimeError(f"Error calling Groq API: {e}")