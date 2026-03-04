"""
Streamlit Frontend for Clinical Note Processing API

Run this app with: streamlit run streamlit_app.py
Make sure the FastAPI server is running on http://localhost:8000
"""

import streamlit as st
import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000"

# Sample clinical note for testing
SAMPLE_NOTE = """Patient John Doe (DOB: 11/04/1958) was admitted on Oct 12th for acute exacerbation of chronic obstructive pulmonary disease (COPD) and poorly controlled Type 2 Diabetes Mellitus. Patient was stabilized in the ICU. Upon discharge, patient is prescribed Metformin 500mg PO BID and an Albuterol HFA inhaler 2 puffs q4h PRN for wheezing."""

# Page config
st.set_page_config(
    page_title="Clinical Note Processor",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Clinical Note Processing System")
st.markdown("AI-powered structured extraction and Q&A from clinical notes")

# Check API health
try:
    health_response = requests.get(f"{API_BASE_URL}/health", timeout=2)
    if health_response.status_code == 200:
        st.success("✅ API is running")
    else:
        st.error("⚠️ API is not responding correctly")
except requests.exceptions.RequestException:
    st.error("❌ API is not running. Start it with: `uvicorn src.api:app --reload`")

st.markdown("---")

# Two columns for the two main features
col1, col2 = st.columns(2)

# ============================================================================
# LEFT COLUMN: Structured Extraction
# ============================================================================
with col1:
    st.header("📋 Structured Extraction")
    st.markdown("Extract diagnoses, medications, and detect PHI from clinical notes")
    
    clinical_note_extract = st.text_area(
        "Clinical Note",
        value=SAMPLE_NOTE,
        height=200,
        key="extract_note",
        help="Paste or type a clinical note here"
    )
    
    if st.button("🔍 Extract Entities", type="primary", use_container_width=True):
        if not clinical_note_extract.strip():
            st.warning("Please enter a clinical note")
        else:
            with st.spinner("Extracting entities..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/api/v1/extract",
                        json={"clinical_note": clinical_note_extract},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        st.success("✅ Extraction Complete")
                        
                        # Display diagnoses
                        st.subheader("🩺 Diagnoses")
                        if data.get("diagnoses"):
                            for dx in data["diagnoses"]:
                                st.markdown(f"- {dx}")
                        else:
                            st.info("No diagnoses found")
                        
                        # Display medications
                        st.subheader("💊 Medications")
                        if data.get("medications"):
                            for med in data["medications"]:
                                st.markdown(f"**{med['name']}**")
                                st.markdown(f"  - Dosage: {med['dosage']}")
                                st.markdown(f"  - Frequency: {med['frequency']}")
                                st.markdown("")
                        else:
                            st.info("No medications found")
                        
                        # PHI detection
                        st.subheader("🔒 PHI Detection")
                        if data.get("phi_detected"):
                            st.warning("⚠️ Protected Health Information (PHI) detected")
                        else:
                            st.success("✅ No PHI detected")
                        
                        # Show raw JSON
                        with st.expander("📄 View Raw JSON Response"):
                            st.json(data)
                    else:
                        st.error(f"Error: {response.status_code}")
                        st.code(response.text)
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to connect to API: {str(e)}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ============================================================================
# RIGHT COLUMN: Clinical Q&A
# ============================================================================
with col2:
    st.header("❓ Clinical Q&A")
    st.markdown("Ask questions about the clinical note content")
    
    clinical_note_query = st.text_area(
        "Clinical Note",
        value=SAMPLE_NOTE,
        height=150,
        key="query_note",
        help="Paste or type a clinical note here"
    )
    
    question = st.text_input(
        "Your Question",
        value="How often should the patient take their inhaler?",
        help="Ask a question about the clinical note"
    )
    
    if st.button("💬 Ask Question", type="primary", use_container_width=True):
        if not clinical_note_query.strip():
            st.warning("Please enter a clinical note")
        elif not question.strip():
            st.warning("Please enter a question")
        else:
            with st.spinner("Getting answer..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/api/v1/query",
                        json={
                            "clinical_note": clinical_note_query,
                            "question": question
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        answer = data.get("answer", "")
                        
                        st.success("✅ Answer Generated")
                        
                        # Display answer with appropriate styling
                        if "cannot answer" in answer.lower():
                            st.warning(answer)
                        else:
                            st.info(answer)
                        
                        # Show raw JSON
                        with st.expander("📄 View Raw JSON Response"):
                            st.json(data)
                    else:
                        st.error(f"Error: {response.status_code}")
                        st.code(response.text)
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to connect to API: {str(e)}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ============================================================================
# BOTTOM: Sample Questions
# ============================================================================
st.markdown("---")
st.subheader("💡 Sample Questions to Try")

sample_questions = [
    "What medications was the patient prescribed?",
    "How often should the patient take their inhaler?",
    "What is the patient's diagnosis?",
    "When was the patient admitted?",
    "What is the patient's blood pressure?",  # Unanswerable
]

cols = st.columns(len(sample_questions))
for idx, q in enumerate(sample_questions):
    with cols[idx]:
        if st.button(q, key=f"sample_{idx}", use_container_width=True):
            st.info(f"Copy this to the question field: **{q}**")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
### 📖 Instructions
1. **Start the API**: `uvicorn src.api:app --reload`
2. **Run this app**: `streamlit run streamlit_app.py`
3. **Test extraction**: Paste a clinical note in the left panel and click Extract
4. **Test Q&A**: Enter a question in the right panel and click Ask

**Note**: This is a demonstration interface for testing the Clinical Note Processing API.
""")
