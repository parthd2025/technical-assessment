"""
Clinical Note Assistant - Web Interface for Healthcare Practitioners.

This Streamlit application provides a user-friendly web interface for:
1. Inputting clinical notes from EMR/EHR systems
2. Extracting structured data (diagnoses, medications, PHI)
3. Asking verification questions about the note
4. Viewing raw JSON responses for debugging

The application connects to the FastAPI backend and provides real-time
feedback on extraction results with clinical-focused UI/UX.

Usage:
    streamlit run streamlit_app.py

Prerequisites:
    - FastAPI backend running on http://localhost:8000
    - API must be started with: uvicorn src.api:app --reload

Author: Clinical Note Processing System
Version: 1.0.0
"""

import streamlit as st
import requests
from datetime import datetime
import logging
import os

# Configuration - Use environment variable or default to localhost
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Setup basic logging for Streamlit
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Starting Streamlit Clinical Note Assistant")

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
    logger.debug("Checking API health status")
    response = requests.get(f"{API_BASE_URL}/health", timeout=1)
    if response.status_code == 200:
        st.success("✅ API Connected")
        logger.info("API health check successful")
    else:
        st.error("⚠️ API Error")
        logger.warning(f"API health check failed with status {response.status_code}")
except Exception as e:
    st.error("❌ API Offline - Start with: uvicorn src.api:app --reload")
    logger.error(f"API health check failed: {e}")

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
        height=400,
        placeholder="Paste clinical note from EMR...",
        label_visibility="collapsed",
        key="clinical_note"
    )
    
    # Extract button
    if st.button("🔍 Extract Information", type="primary", use_container_width=True):
        if clinical_note.strip():
            logger.info(f"User initiated extraction - Note length: {len(clinical_note)} chars")
            with st.spinner("⏳ Analyzing note..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/api/v1/extract",
                        json={"clinical_note": clinical_note},
                        timeout=30
                    )
                    if response.status_code == 200:
                        st.session_state.extraction_result = response.json()
                        logger.info("Extraction successful")
                        st.rerun()
                    else:
                        logger.error(f"Extraction failed with status {response.status_code}")
                        st.error(f"Error: {response.status_code}")
                except Exception as e:
                    logger.error(f"Extraction request failed: {e}")
                    st.error(f"Connection failed: {e}")
        else:
            logger.warning("User attempted extraction with empty note")
            st.warning("Please enter a clinical note")
    
    # Clear button
    if st.session_state.extraction_result:
        if st.button("🗑️ Clear Results", use_container_width=True):
            logger.info("User cleared extraction results")
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
                logger.info(f"User asked question: {question[:100]}")
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
                                logger.info("Q&A - Cannot answer from note")
                                st.warning(answer)
                            else:
                                logger.info("Q&A answered successfully")
                                st.success(answer)
                    except Exception as e:
                        logger.error(f"Query request failed: {e}")
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
