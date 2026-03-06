"""
Sample test script to manually test the Clinical Note API endpoints
Run this after starting the server to verify it's working correctly
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# Sample clinical note from the assignment
SAMPLE_NOTE = """Patient John Doe (DOB: 11/04/1958) was admitted on Oct 12th for acute 
exacerbation of chronic obstructive pulmonary disease (COPD) and poorly 
controlled Type 2 Diabetes Mellitus. Patient was stabilized in the ICU. Upon 
discharge, patient is prescribed Metformin 500mg PO BID and an Albuterol HFA 
inhaler 2 puffs q4h PRN for wheezing. Patient is advised to follow up with Dr. Smith 
in 2 weeks. Blood pressure was noted to be slightly elevated at 135/85."""

def test_health():
    """Test the health check endpoint"""
    print("\n" + "="*60)
    print("Testing Health Check Endpoint")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, "Health check failed"
    print("✓ Health check passed")


def test_extract():
    """Test the extraction endpoint"""
    print("\n" + "="*60)
    print("Testing Extraction Endpoint (/api/v1/extract)")
    print("="*60)
    
    payload = {
        "clinical_note": SAMPLE_NOTE
    }
    
    print("\nSending request...")
    response = requests.post(
        f"{BASE_URL}/api/v1/extract",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"\nExtracted Data:")
    print(json.dumps(response.json(), indent=2))
    
    assert response.status_code == 200, "Extraction failed"
    data = response.json()
    assert "diagnoses" in data, "Missing diagnoses"
    assert "medications" in data, "Missing medications"
    assert "phi_detected" in data, "Missing phi_detected"
    print("\n✓ Extraction test passed")


def test_query():
    """Test the Q&A endpoint"""
    print("\n" + "="*60)
    print("Testing Query Endpoint (/api/v1/query)")
    print("="*60)
    
    questions = [
        "How often should the patient take their inhaler?",
        "What medications was the patient prescribed?",
        "What is the patient's blood pressure?",
        "What is the patient's favorite color?"  # Should return cannot answer
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n--- Question {i} ---")
        print(f"Q: {question}")
        
        payload = {
            "clinical_note": SAMPLE_NOTE,
            "question": question
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"A: {response.json()['answer']}")
        
        assert response.status_code == 200, f"Query {i} failed"
    
    print("\n✓ Query test passed")


def main():
    """Run all tests"""
    try:
        print("\n" + "="*60)
        print("CLINICAL NOTE PROCESSING API - MANUAL TEST SUITE")
        print("="*60)
        print(f"Testing API at: {BASE_URL}")
        print("Make sure the server is running before running this script!")
        print("="*60)
        
        test_health()
        test_extract()
        test_query()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED! ✓")
        print("="*60 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to the API.")
        print("Make sure the server is running at http://localhost:8000")
        print("Run: uvicorn src.api:app --host 0.0.0.0 --port 8000")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")


if __name__ == "__main__":
    main()
