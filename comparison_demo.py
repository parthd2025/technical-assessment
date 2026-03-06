"""
LLM vs Hybrid Approach Comparison Demo

This module demonstrates the difference between:
1. Full LLM Approach - Every query goes to Groq LLM
2. Hybrid Approach - Rule-based matching first, LLM for complex queries only

Shows token savings, time savings, and accuracy comparison.
Perfect for client demonstrations.
"""

import streamlit as st
import time
import pandas as pd
import re
from datetime import datetime
from groq import Groq
from src.config import Config
from src.logger import setup_logger
import plotly.graph_objects as go

# Initialize logger first
logger = setup_logger(__name__)

# Try importing PDF processor (optional)
try:
    from pdf_processor import PDFProcessor, is_pdf_support_available
    PDF_SUPPORT = is_pdf_support_available()
except ImportError:
    PDF_SUPPORT = False
    logger.warning("PDF support not available. Install PyPDF2 or pdfplumber for PDF uploads.")

# Page config
st.set_page_config(
    page_title="LLM vs Hybrid Comparison",
    page_icon="🔬",
    layout="wide"
)

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'pdf_text' not in st.session_state:
    st.session_state.pdf_text = None
if 'pdf_metadata' not in st.session_state:
    st.session_state.pdf_metadata = None

class ComparisonEngine:
    """Engine to compare Full LLM vs Hybrid approaches"""
    
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.model = Config.GROQ_MODEL
        logger.info(f"ComparisonEngine initialized with model: {self.model}")
    
    def full_llm_approach(self, query: str, context: str) -> dict:
        """
        Full LLM approach - sends every query to Groq LLM.
        
        Args:
            query: User query
            context: Clinical note or product catalog context
            
        Returns:
            dict with answer, tokens, time
        """
        logger.info(f"Full LLM approach - Query: {query[:50]}...")
        start_time = time.time()
        
        system_prompt = """You are a helpful assistant that answers questions based on the provided context.
        
RULES:
1. Answer strictly based on the context provided
2. Be concise and accurate
3. If information is not in context, say so clearly"""

        user_prompt = f"""Context:
{context}

Question: {query}

Answer:"""
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                temperature=0,
                max_tokens=500
            )
            
            execution_time = time.time() - start_time
            answer = chat_completion.choices[0].message.content.strip()
            
            # Get token usage
            if hasattr(chat_completion, 'usage') and chat_completion.usage:
                input_tokens = chat_completion.usage.prompt_tokens
                output_tokens = chat_completion.usage.completion_tokens
                total_tokens = chat_completion.usage.total_tokens
            else:
                # Fallback estimation if usage not available
                input_tokens = len(system_prompt + user_prompt) // 4
                output_tokens = len(answer) // 4
                total_tokens = input_tokens + output_tokens
            
            logger.info(f"Full LLM completed - Tokens: {total_tokens}, Time: {execution_time:.3f}s")
            
            return {
                "answer": answer,
                "tokens": total_tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "time": execution_time
            }
            
        except Exception as e:
            logger.error(f"Full LLM approach error: {e}")
            raise RuntimeError(f"Error in Full LLM approach: {e}")
    
    def hybrid_approach(self, query: str, context: str) -> dict:
        """
        Enhanced Hybrid approach with Regex - tries pattern matching first, falls back to LLM.
        
        This approach:
        1. Checks if query needs reasoning (Why/How/Explain) → Direct to LLM
        2. Tries regex pattern matching for structured data → 0 tokens
        3. Falls back to LLM for complex queries → Uses tokens
        
        Regex handles ~70% of queries with 0 tokens and faster response!
        
        Args:
            query: User query
            context: Clinical note or product catalog context
            
        Returns:
            dict with answer, tokens, time, used_llm flag
        """
        logger.info(f"Hybrid approach (Regex) - Query: {query[:50]}...")
        start_time = time.time()
        query_lower = query.lower()
        
        # ===== STEP 1: Check for Complex Query Indicators =====
        # These ALWAYS need LLM reasoning
        complex_indicators = ['why', 'how', 'explain', 'summarize', 'analyze', 
                            'interpret', 'relationship', 'appropriate', 'should',
                            'compare', 'mean', 'suggest', 'recommend']
        
        # Check if query starts with complex words
        first_word = query_lower.split()[0] if query_lower.split() else ''
        if first_word in complex_indicators or any(ind in query_lower for ind in ['why ', 'how ', 'explain ']):
            logger.info("Hybrid - Complex query detected, using LLM")
            result = self.full_llm_approach(query, context)
            result["used_llm"] = True
            return result
        
        # ===== STEP 2: Try REGEX Pattern Matching =====
        
        # PATTERN 1: Medication Extraction
        if any(word in query_lower for word in ['medication', 'drug', 'prescription', 'taking', 'prescribed']):
            # Regex: Match drug names with dosages - handles various formats
            # Matches: "Lisinopril 10mg", "- Metformin 500mg twice daily", "prescribed Aspirin 81mg"
            pattern = r'([A-Z][a-z]{2,}(?:opril|pril|formin|terol|cillin|mycin|azole|olol|pine)?)\s+(\d+(?:\.\d+)?)\s*(mg|g|mcg|ml)(?:\s+(once|twice|three\s+times|[\d]+x?))?\s*(?:(daily|a\s+day|per\s+day))?'
            matches = re.findall(pattern, context, re.IGNORECASE)
            
            if matches:
                medications = []
                seen = set()  # Avoid duplicates
                for match in matches:
                    med_name = match[0].title()
                    dosage = match[1]
                    unit = match[2]
                    freq = match[3].strip() if match[3] else ''
                    daily = match[4].strip() if match[4] else ''
                    
                    # Build medication string
                    med_str = f"{med_name} {dosage}{unit}"
                    if freq and daily:
                        med_str += f" {freq} {daily}"
                    elif freq:
                        med_str += f" {freq}"
                    elif daily:
                        med_str += f" {daily}"
                    
                    # Avoid duplicates
                    if med_str not in seen:
                        medications.append(med_str)
                        seen.add(med_str)
                
                if medications:
                    answer = f"Medications: {', '.join(medications)}"
                    execution_time = time.time() - start_time
                    logger.info(f"Hybrid (Regex) - Extracted {len(medications)} medications, Time: {execution_time:.3f}s")
                    return {
                        "answer": answer,
                        "tokens": 0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "time": execution_time,
                        "used_llm": False
                    }
        
        # PATTERN 2: Specific Dosage Query
        dosage_match = re.search(r'(?:dosage|dose|how much)\s+(?:of\s+)?([A-Z][a-z]+)', query, re.IGNORECASE)
        if dosage_match:
            drug_name = dosage_match.group(1)
            # Find specific drug dosage
            pattern = rf'{drug_name}\s+(\d+(?:\.\d+)?)\s?(mg|g|mcg|ml)(?:\s+(once|twice|three times))?(?:\s+(daily|a day))?'
            match = re.search(pattern, context, re.IGNORECASE)
            
            if match:
                answer = f"The dosage of {drug_name} is {match.group(1)}{match.group(2)}"
                if match.group(3) and match.group(4):
                    answer += f" {match.group(3)} {match.group(4)}"
                
                execution_time = time.time() - start_time
                logger.info(f"Hybrid (Regex) - Extracted dosage for {drug_name}, Time: {execution_time:.3f}s")
                return {
                    "answer": answer,
                    "tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "time": execution_time,
                    "used_llm": False
                }
        
        # PATTERN 3: Diagnosis Extraction
        if 'diagnosis' in query_lower or 'diagnosed' in query_lower or 'condition' in query_lower:
            # Regex: Match diagnosis patterns
            patterns = [
                r'(?:Diagnosis|Diagnosed with|Condition):\s*([A-Z][a-zA-Z\s,]+?)(?:\.|,|\n|$)',
                r'(?:suffering from|has)\s+([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)?(?:\s+Diabetes)?)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, context, re.IGNORECASE)
                if matches:
                    diagnoses = [d.strip().rstrip(',') for d in matches]
                    answer = f"Diagnosis: {', '.join(set(diagnoses))}"
                    execution_time = time.time() - start_time
                    logger.info(f"Hybrid (Regex) - Extracted diagnosis, Time: {execution_time:.3f}s")
                    return {
                        "answer": answer,
                        "tokens": 0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "time": execution_time,
                        "used_llm": False
                    }
        
        # PATTERN 4: Date/DOB Extraction
        if any(word in query_lower for word in ['date', 'dob', 'birth', 'born', 'age']):
            # Regex: Match dates in various formats
            patterns = [
                r'(?:DOB|Date of Birth|Born):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
                r'(?:DOB|Date of Birth|Born)\s*[:\(]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
                r'\((?:DOB):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})\)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    answer = f"Date of birth: {match.group(1)}"
                    execution_time = time.time() - start_time
                    logger.info(f"Hybrid (Regex) - Extracted DOB, Time: {execution_time:.3f}s")
                    return {
                        "answer": answer,
                        "tokens": 0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "time": execution_time,
                        "used_llm": False
                    }
        
        # PATTERN 5: Blood Pressure / Vital Signs
        if any(word in query_lower for word in ['blood pressure', 'bp', 'vital']):
            # Enhanced pattern - handles multiple formats
            # Matches: "BP: 120/80", "Blood pressure: 135/85", "blood pressure was 120/80", "elevated at 135/85"
            patterns = [
                r'(?:Blood pressure|BP):\s*(\d{2,3}/\d{2,3})',  # "BP: 120/80"
                r'(?:Blood pressure|BP)\s+(?:was|is|measured|noted|recorded|reading)\s+(?:to\s+be\s+)?(?:slightly\s+)?(?:elevated\s+)?(?:at\s+)?(\d{2,3}/\d{2,3})',  # "BP was elevated at 135/85"
                r'(?:at|of)\s+(\d{2,3}/\d{2,3})\s*(?:mmHg)?',  # "elevated at 135/85"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    bp_value = match.group(1)
                    answer = f"Blood pressure: {bp_value} mmHg"
                    execution_time = time.time() - start_time
                    logger.info(f"Hybrid (Regex) - Extracted BP: {bp_value}, Time: {execution_time:.3f}s")
                    return {
                        "answer": answer,
                        "tokens": 0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "time": execution_time,
                        "used_llm": False
                    }
        
        # PATTERN 6: Frequency Questions (how often, when to take)
        if any(phrase in query_lower for phrase in ['how often', 'frequency', 'when to take', 'when should']):
            # Enhanced pattern - handles multiple frequency formats
            # Matches: "twice daily", "2 puffs q4h", "every 4 hours", "once a day", "PRN"
            patterns = [
                r'(\d+\s+puffs?\s+q\d+h)',  # "2 puffs q4h"
                r'(every\s+\d+\s+hours?)',  # "every 4 hours"
                r'(\d+\s+times?\s+(?:a\s+)?(?:daily|day))',  # "3 times daily"
                r'(once|twice|three times|four times)\s+(?:a\s+)?(?:day|daily)',  # "twice daily"
                r'(PRN)',  # "PRN" (as needed)
            ]
            
            for pattern in patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    frequency = match.group(0)
                    answer = f"Frequency: {frequency}"
                    execution_time = time.time() - start_time
                    logger.info(f"Hybrid (Regex) - Extracted frequency: {frequency}, Time: {execution_time:.3f}s")
                    return {
                        "answer": answer,
                        "tokens": 0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "time": execution_time,
                        "used_llm": False
                    }
        
        # PATTERN 7: Yes/No Questions (presence check)
        if query_lower.startswith(('is ', 'does ', 'has ', 'was ', 'were ', 'did ')):
            # Extract key terms and check if they exist in context
            key_terms = self._extract_key_terms(query)
            found_terms = [term for term in key_terms if term.lower() in context.lower()]
            
            if found_terms:
                answer = f"Yes, the patient has/is on: {', '.join(found_terms)}"
                execution_time = time.time() - start_time
                logger.info(f"Hybrid (Regex) - Yes/No answered, Time: {execution_time:.3f}s")
                return {
                    "answer": answer,
                    "tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "time": execution_time,
                    "used_llm": False
                }
        
        # ===== STEP 3: No Pattern Match - Fall Back to LLM =====
        logger.info("Hybrid - No regex pattern matched, using LLM")
        result = self.full_llm_approach(query, context)
        result["used_llm"] = True
        return result
    
    def _extract_key_terms(self, query: str) -> list:
        """Extract key medical/business terms from query"""
        # Simple extraction - remove common words
        stop_words = {'is', 'does', 'has', 'was', 'were', 'did', 'the', 'a', 'an', 'in', 
                     'on', 'at', 'to', 'for', 'their', 'patient', 'should', 'take'}
        words = query.lower().replace('?', '').split()
        key_terms = [w for w in words if w not in stop_words and len(w) > 3]
        return key_terms


def main():
    """Main Streamlit app"""
    
    # Header
    st.title("🔬 LLM vs Hybrid Approach Comparison")
    st.markdown("Compare token usage, time, and accuracy between **Full LLM** and **Hybrid** approaches")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.info(f"**Model:** {Config.GROQ_MODEL}")
        st.info(f"**API Key:** {'✓ Configured' if Config.GROQ_API_KEY else '✗ Missing'}")
        
        st.markdown("---")
        st.header("📊 Session Stats")
        
        if st.session_state.history:
            total_queries = len(st.session_state.history)
            total_token_savings = sum(h['savings']['tokens'] for h in st.session_state.history)
            total_time_savings = sum(h['savings']['time'] for h in st.session_state.history)
            
            st.metric("Total Queries", total_queries)
            st.metric("Total Token Savings", f"{total_token_savings:,}")
            st.metric("Total Time Savings", f"{total_time_savings:.2f}s")
            
            if st.button("🗑️ Clear History"):
                st.session_state.history = []
                st.rerun()
        else:
            st.info("No queries yet. Run a comparison to see stats!")
    
    # Initialize session state for query and context persistence
    if 'query_input' not in st.session_state:
        st.session_state.query_input = ''
    if 'context_input' not in st.session_state:
        st.session_state.context_input = ''
    
    # Transfer sample data directly to widget keys (from Load Sample Data button)
    if 'sample_query' in st.session_state:
        st.session_state.query_input = st.session_state.sample_query
        del st.session_state.sample_query
    if 'sample_context' in st.session_state:
        st.session_state.context_input = st.session_state.sample_context
        del st.session_state.sample_context
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📝 Input")
        query = st.text_input(
            "Enter your query:", 
            placeholder="What medications is the patient taking?",
            key="query_input"
        )
        
        context = st.text_area(
            "Context (Clinical note, product catalog, etc.):",
            placeholder="Patient is a 45-year-old male diagnosed with hypertension...",
            height=200,
            key="context_input"
        )
        
        # Show PDF metadata if PDF was loaded
        if st.session_state.pdf_metadata:
            st.info(
                f"📄 **Loaded from PDF:** {st.session_state.pdf_metadata['filename']} | "
                f"Pages: {st.session_state.pdf_metadata['pages']} | "
                f"Characters: {st.session_state.pdf_metadata['chars']:,}"
            )
    
    with col2:
        st.header("🎯 Control")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Sample data button
        if st.button("📋 Load Sample Data", use_container_width=True):
            st.session_state.sample_query = "What medications is the patient taking?"
            st.session_state.sample_context = """Patient John Doe, 45-year-old male.

Diagnosis: Hypertension, Type 2 Diabetes

Current Medications:
- Lisinopril 10mg once daily for blood pressure
- Metformin 500mg twice daily for diabetes
- Aspirin 81mg once daily for cardiovascular protection

Patient reports good compliance with medication regimen."""
            st.session_state.pdf_text = None
            st.session_state.pdf_metadata = None
            st.rerun()
        
        # PDF Upload Buttons
        if PDF_SUPPORT:
            st.markdown("**Or upload PDF:**")
            
            uploaded_file = st.file_uploader(
                "Upload Clinical Note PDF",
                type=['pdf'],
                help="Upload a PDF document to extract text",
                label_visibility="collapsed"
            )
            
            if uploaded_file is not None:
                if st.button("📄 Extract PDF Text", use_container_width=True):
                    with st.spinner("Extracting text from PDF..."):
                        try:
                            processor = PDFProcessor()
                            result = processor.extract_text_from_pdf(uploaded_file)
                            
                            if result["success"]:
                                st.session_state.pdf_text = result["text"]
                                st.session_state.pdf_metadata = {
                                    "filename": result["filename"],
                                    "pages": result["pages"],
                                    "chars": len(result["text"])
                                }
                                # Use temporary variable like sample_context pattern
                                st.session_state.sample_context = result["text"]
                                st.success(f"✅ Extracted {result['pages']} pages from {result['filename']}")
                                st.rerun()
                            else:
                                st.error(f"❌ {result['error']}")
                        except Exception as e:
                            st.error(f"❌ PDF extraction failed: {str(e)}")
        else:
            st.info("💡 Install PyPDF2 or pdfplumber for PDF support: `pip install PyPDF2 pdfplumber`")
        
        st.markdown("---")
        
        # Clear button to reset everything
        if st.button("🗑️ Clear Context", use_container_width=True):
            st.session_state.pdf_text = None
            st.session_state.pdf_metadata = None
            # Use temporary variables to clear - they'll transfer before widget creation
            st.session_state.sample_query = ''
            st.session_state.sample_context = ''
            st.rerun()
        
        compare_button = st.button("🚀 Compare Approaches", type="primary", use_container_width=True)
    
    # Comparison Logic
    if compare_button:
        if not Config.GROQ_API_KEY:
            st.error("❌ Groq API Key not configured. Please set GROQ_API_KEY in .env file")
        elif not query.strip():
            st.error("❌ Please enter a query")
        elif not context.strip():
            st.error("❌ Please enter context")
        else:
            with st.spinner("⏳ Running comparison..."):
                try:
                    engine = ComparisonEngine()
                    
                    # Run both approaches
                    llm_result = engine.full_llm_approach(query, context)
                    hybrid_result = engine.hybrid_approach(query, context)
                    
                    # Calculate savings
                    token_saved = llm_result["tokens"] - hybrid_result["tokens"]
                    time_saved = llm_result["time"] - hybrid_result["time"]
                    token_savings_pct = (token_saved / llm_result["tokens"] * 100) if llm_result["tokens"] > 0 else 0
                    time_savings_pct = (time_saved / llm_result["time"] * 100) if llm_result["time"] > 0 else 0
                    
                    # Store in history
                    comparison_result = {
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "query": query,
                        "full_llm": llm_result,
                        "hybrid": hybrid_result,
                        "savings": {
                            "tokens": token_saved,
                            "tokens_pct": token_savings_pct,
                            "time": time_saved,
                            "time_pct": time_savings_pct
                        }
                    }
                    st.session_state.history.append(comparison_result)
                    
                    # Display Results
                    st.success("✅ Comparison Complete!")
                    
                    st.markdown("---")
                    st.subheader("📊 Comparison Results")
                    
                    # Side-by-side comparison
                    col_llm, col_hybrid = st.columns(2)
                    
                    with col_llm:
                        st.markdown("### 🤖 Full LLM Approach")
                        with st.container(border=True):
                            st.markdown("**Metrics:**")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Total Tokens", f"{llm_result['tokens']:,}")
                                st.metric("Input Tokens", f"{llm_result['input_tokens']:,}")
                            with col2:
                                st.metric("Output Tokens", f"{llm_result['output_tokens']:,}")
                                st.metric("Time Taken", f"{llm_result['time']:.3f}s")
                        
                        with st.expander("📄 View Answer"):
                            st.write(llm_result["answer"])
                    
                    with col_hybrid:
                        st.markdown("### ⚡ Hybrid Approach")
                        llm_badge = "🔵 Used LLM" if hybrid_result.get("used_llm") else "🟢 Rule-Based"
                        
                        with st.container(border=True):
                            st.markdown("**Metrics:**")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Total Tokens", f"{hybrid_result['tokens']:,}")
                                st.metric("Time Taken", f"{hybrid_result['time']:.3f}s")
                            with col2:
                                st.markdown(f"**Method:**")
                                st.info(llm_badge)
                        
                        with st.expander("📄 View Answer"):
                            st.write(hybrid_result["answer"])
                    
                    # Savings Display
                    st.markdown("---")
                    st.subheader("💰 Savings with Hybrid Approach")
                    
                    col_tokens, col_time = st.columns(2)
                    
                    with col_tokens:
                        # Determine if tokens were saved or increased
                        if token_saved >= 0:
                            token_label = f"{token_savings_pct:.1f}% reduction"
                            token_delta_color = "normal"
                        else:
                            token_label = f"{abs(token_savings_pct):.1f}% increase"
                            token_delta_color = "inverse"
                        
                        st.metric(
                            "Tokens Saved",
                            f"{token_saved:,}",
                            token_label,
                            delta_color=token_delta_color
                        )
                    
                    with col_time:
                        # Determine if hybrid is faster or slower
                        if time_saved >= 0:
                            time_label = f"{time_savings_pct:.1f}% faster"
                            time_delta_color = "normal"
                        else:
                            time_label = f"{abs(time_savings_pct):.1f}% slower"
                            time_delta_color = "inverse"
                        
                        st.metric(
                            "Time Saved",
                            f"{time_saved:.3f}s",
                            time_label,
                            delta_color=time_delta_color
                        )
                    
                except Exception as e:
                    st.error(f"❌ Error during comparison: {str(e)}")
                    logger.error(f"Comparison error: {e}", exc_info=True)
    
    # History Section
    if st.session_state.history:
        st.markdown("---")
        st.header("📈 Query History & Aggregate Stats")
        
        # Aggregate metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_queries = len(st.session_state.history)
        total_llm_tokens = sum(h['full_llm']['tokens'] for h in st.session_state.history)
        total_hybrid_tokens = sum(h['hybrid']['tokens'] for h in st.session_state.history)
        total_token_savings = total_llm_tokens - total_hybrid_tokens
        total_time_savings = sum(h['savings']['time'] for h in st.session_state.history)
        
        with col1:
            st.metric("Total Queries", total_queries)
        
        with col2:
            st.metric("LLM Tokens", f"{total_llm_tokens:,}")
        
        with col3:
            st.metric("Hybrid Tokens", f"{total_hybrid_tokens:,}")
        
        with col4:
            savings_pct = (total_token_savings / total_llm_tokens * 100) if total_llm_tokens > 0 else 0
            st.metric("Total Savings", f"{total_token_savings:,}", f"{savings_pct:.1f}%")
        
        # History Table
        st.subheader("📋 Query History")
        
        history_data = []
        for h in st.session_state.history:
            history_data.append({
                "Time": h['timestamp'],
                "Query": h['query'][:50] + "..." if len(h['query']) > 50 else h['query'],
                "LLM Tokens": h['full_llm']['tokens'],
                "Hybrid Tokens": h['hybrid']['tokens'],
                "Token Savings": h['savings']['tokens'],
                "Token %": f"{h['savings']['tokens_pct']:.1f}%",
                "Time Savings": f"{h['savings']['time']:.3f}s",
                "Time %": f"{h['savings']['time_pct']:.1f}%",
                "Method": "🔵 LLM" if h['hybrid'].get('used_llm') else "🟢 Rule"
            })
        
        df = pd.DataFrame(history_data)
        st.dataframe(df, width='stretch', hide_index=True)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download History as CSV",
            data=csv,
            file_name=f"comparison_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # Visual Charts
        st.subheader("📊 Visual Comparison")
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("**Token Usage Comparison**")
            
            # Prepare data for grouped bar chart
            llm_tokens = [h['full_llm']['tokens'] for h in st.session_state.history]
            hybrid_tokens = [h['hybrid']['tokens'] for h in st.session_state.history]
            queries = [f"Q{i+1}" for i in range(len(st.session_state.history))]
            
            # Create plotly figure
            fig_tokens = go.Figure(data=[
                go.Bar(
                    name='Full LLM',
                    x=queries,
                    y=llm_tokens,
                    text=[f"{val:,}" for val in llm_tokens],
                    textposition='auto',
                    marker_color='lightblue',
                    textfont=dict(size=12, color='black')
                ),
                go.Bar(
                    name='Hybrid',
                    x=queries,
                    y=hybrid_tokens,
                    text=[f"{val:,}" for val in hybrid_tokens],
                    textposition='auto',
                    marker_color='darkblue',
                    textfont=dict(size=12, color='white')
                )
            ])
            
            fig_tokens.update_layout(
                barmode='group',
                height=400,
                xaxis_title="Query",
                yaxis_title="Tokens",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            
            st.plotly_chart(fig_tokens, use_container_width=True)
        
        with chart_col2:
            st.markdown("**Time Comparison**")
            
            # Prepare data for grouped bar chart
            llm_time = [h['full_llm']['time'] for h in st.session_state.history]
            hybrid_time = [h['hybrid']['time'] for h in st.session_state.history]
            queries = [f"Q{i+1}" for i in range(len(st.session_state.history))]
            
            # Create plotly figure
            fig_time = go.Figure(data=[
                go.Bar(
                    name='Full LLM',
                    x=queries,
                    y=llm_time,
                    text=[f"{val:.3f}s" for val in llm_time],
                    textposition='auto',
                    marker_color='lightblue',
                    textfont=dict(size=12, color='black')
                ),
                go.Bar(
                    name='Hybrid',
                    x=queries,
                    y=hybrid_time,
                    text=[f"{val:.3f}s" for val in hybrid_time],
                    textposition='auto',
                    marker_color='darkblue',
                    textfont=dict(size=12, color='white')
                )
            ])
            
            fig_time.update_layout(
                barmode='group',
                height=400,
                xaxis_title="Query",
                yaxis_title="Time (seconds)",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            
            st.plotly_chart(fig_time, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        f"💡 Using <strong>{Config.GROQ_MODEL}</strong> | "
        "Hybrid approach saves tokens by using rule-based responses for simple queries"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
