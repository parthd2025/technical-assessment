"""
Clinical Note Assistant - Designed for Healthcare Practitioners

Run: streamlit run streamlit_app.py
Ensure API is running: uvicorn src.api:app --reload
"""

import streamlit as st
import requests
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"

# Initialize session state
if 'clinical_note' not in st.session_state:
    st.session_state.clinical_note = ""
if 'extraction_result' not in st.session_state:
    st.session_state.extraction_result = None

# Page config
st.set_page_config(
    page_title="Clinical Note Assistant",
    page_icon="🏥",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .medication-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 10px 14px;
        border-radius: 6px;
        margin: 6px 0;
        color: white;
    }
    .med-name { font-size: 16px; font-weight: bold; margin-bottom: 4px; }
    .med-details { font-size: 14px; opacity: 0.95; }
    .diagnosis-item { 
        font-size: 15px; 
        padding: 8px 12px; 
        background: #ffffff; 
        color: #1f1f1f;
        margin: 5px 0; 
        border-radius: 5px;
        border-left: 4px solid #667eea;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .phi-warning {
        background: #ff4444;
        color: white;
        padding: 8px 12px;
        border-radius: 5px;
        font-size: 14px;
        font-weight: bold;
        text-align: center;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🏥 Clinical Note Assistant")

# API status
try:
    response = requests.get(f"{API_BASE_URL}/health", timeout=1)
    if response.status_code == 200:
        st.success("✅ API Connected")
    else:
        st.error("⚠️ API Error")
except:
    st.error("❌ API Offline - Start with: uvicorn src.api:app --reload")

st.markdown("---")

# ============================================================================
# TWO COLUMN LAYOUT: Input (Left) | Results (Right)
# ============================================================================
left_col, right_col = st.columns([1, 1])

# ============================================================================
# LEFT SIDE: Clinical Note Input
# ============================================================================
with left_col:
    st.subheader("📋 Clinical Note Input")
    
    clinical_note = st.text_area(
        "Paste clinical note here",
        value=st.session_state.clinical_note,
        height=400,
        placeholder="Paste clinical note from EMR...",
        label_visibility="collapsed"
    )
    
    st.session_state.clinical_note = clinical_note
    
    # Extract button
    if st.button("🔍 Extract Information", type="primary", use_container_width=True):
        if clinical_note.strip():
            with st.spinner("⏳ Analyzing note..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/api/v1/extract",
                        json={"clinical_note": clinical_note},
                        timeout=30
                    )
                    if response.status_code == 200:
                        st.session_state.extraction_result = response.json()
                        st.rerun()
                    else:
                        st.error(f"Error: {response.status_code}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")
        else:
            st.warning("Please enter a clinical note")
    
    # Clear button
    if st.session_state.extraction_result:
        if st.button("🗑️ Clear Results", use_container_width=True):
            st.session_state.extraction_result = None
            st.rerun()

# ============================================================================
# RIGHT SIDE: Extracted Information
# ============================================================================
with right_col:
    st.subheader("📊 Extracted Information")
    
    if st.session_state.extraction_result:
        data = st.session_state.extraction_result
        
        # PHI Warning
        if data.get("phi_detected"):
            st.markdown("""
            <div class="phi-warning">
                ⚠️ PHI DETECTED - Handle per HIPAA guidelines
            </div>
            """, unsafe_allow_html=True)
        
        # Diagnoses
        st.markdown("**🩺 Diagnoses**")
        if data.get("diagnoses"):
            for dx in data["diagnoses"]:
                st.markdown(f"<div class='diagnosis-item'>{dx}</div>", unsafe_allow_html=True)
        else:
            st.info("No diagnoses found")
        
        # Medications
        st.markdown("**💊 Medications**")
        if data.get("medications"):
            for med in data["medications"]:
                st.markdown(f"""
                <div class="medication-card">
                    <div class="med-name">{med['name']}</div>
                    <div class="med-details">{med['dosage']} • {med['frequency']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No medications found")
        
        # Raw JSON Response
        with st.expander("📋 View Raw JSON Response"):
            st.json(data)
        
        # Quick Q&A
        st.markdown("**❓ Quick Verification**")
        question = st.text_input(
            "Ask a question",
            placeholder="e.g., What is the Metformin dosage?",
            label_visibility="collapsed"
        )
        
        if st.button("Ask", type="secondary", use_container_width=True):
            if question:
                with st.spinner("🔍 Checking..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/api/v1/query",
                            json={
                                "clinical_note": st.session_state.clinical_note,
                                "question": question
                            },
                            timeout=30
                        )
                        if response.status_code == 200:
                            answer = response.json().get("answer", "")
                            if "cannot answer" in answer.lower():
                                st.warning(answer)
                            else:
                                st.success(answer)
                    except Exception as e:
                        st.error(f"Error: {e}")
    
    else:
        st.info("""
        **👈 Paste a clinical note on the left and click Extract**
        
        The system will automatically identify:
        - 🩺 Diagnoses
        - 💊 Medications (with dosage & frequency)
        - 🔒 Protected Health Information (PHI)
        
        Then you can ask questions to verify specific details.
        """)
