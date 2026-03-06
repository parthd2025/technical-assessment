"""
LLM vs Hybrid Approach Comparison Demo

This module demonstrates the difference between:
1. Full LLM Approach - Every query goes to Groq LLM
2. Hybrid Approach - Rule-based matching first, LLM for complex queries only

Shows token savings, time savings, and accuracy comparison.
Perfect for client demonstrations.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

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
    from src.pdf_processor import PDFProcessor, is_pdf_support_available
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
        Simple Hybrid: Try basic regex patterns first, fall back to LLM.
        
        Args:
            query: User query
            context: Clinical note
            
        Returns:
            dict with answer, tokens, time, used_llm flag
        """
        logger.info(f"Hybrid approach - Query: {query[:50]}...")
        start_time = time.time()
        query_lower = query.lower()
        
        # Skip complex queries - send directly to LLM
        if any(word in query_lower for word in ['why', 'how', 'explain', 'summarize', 'compare']):
            result = self.full_llm_approach(query, context)
            result["used_llm"] = True
            return result
        
        # Try simple regex patterns
        
        # PATTERN 1: Patient Name
        if 'name' in query_lower:
            match = re.search(r'[Pp]atient\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', context)
            if match:
                execution_time = time.time() - start_time
                return {
                    "answer": f"Patient name: {match.group(1)}",
                    "tokens": 0, "input_tokens": 0, "output_tokens": 0,
                    "time": execution_time, "used_llm": False
                }
        
        # PATTERN 2: Medications (simple - one pattern only)
        if any(word in query_lower for word in ['medication', 'drug', 'prescribed', 'taking']):
            pattern = r'([A-Z][a-z]+(?:formin|pril|terol)?)\s+(\d+)\s*(mg|mcg|units?)\s*(?:(PO|IV))?\s*(?:(BID|TID|daily|q\d+h))?'
            matches = re.findall(pattern, context, re.IGNORECASE)
            if matches:
                meds = [f"{m[0]} {m[1]}{m[2]}" + (f" {m[4]}" if m[4] else "") for m in matches]
                execution_time = time.time() - start_time
                return {
                    "answer": f"Medications: {', '.join(meds)}",
                    "tokens": 0, "input_tokens": 0, "output_tokens": 0,
                    "time": execution_time, "used_llm": False
                }
        
        # PATTERN 3: Diagnosis
        if 'diagnosis' in query_lower or 'condition' in query_lower:
            match = re.search(r'[Dd]iagnosis:\s*([A-Za-z\s\d]+?)(?:\.|,|\n)', context)
            if match:
                execution_time = time.time() - start_time
                return {
                    "answer": f"Diagnosis: {match.group(1).strip()}",
                    "tokens": 0, "input_tokens": 0, "output_tokens": 0,
                    "time": execution_time, "used_llm": False
                }
        
        # PATTERN 4: Date of Birth
        if any(word in query_lower for word in ['dob', 'birth', 'born']):
            match = re.search(r'DOB[:\s]*\(?(\d{1,2}[/-]\d{1,2}[/-]\d{4})\)?', context, re.IGNORECASE)
            if match:
                execution_time = time.time() - start_time
                return {
                    "answer": f"Date of birth: {match.group(1)}",
                    "tokens": 0, "input_tokens": 0, "output_tokens": 0,
                    "time": execution_time, "used_llm": False
                }
        
        # PATTERN 5: Simple "what is X" extraction
        what_match = re.search(r'what\s+is\s+(?:the\s+)?(?:patient\s+)?(\w+)', query_lower)
        if what_match:
            keyword = what_match.group(1)
            # Try finding "keyword: value" pattern in context
            value_match = re.search(rf'{keyword}[:\s]+([^,.\n]+)', context, re.IGNORECASE)
            if value_match:
                execution_time = time.time() - start_time
                return {
                    "answer": f"{keyword.title()}: {value_match.group(1).strip()}",
                    "tokens": 0, "input_tokens": 0, "output_tokens": 0,
                    "time": execution_time, "used_llm": False
                }
        
        # No pattern matched - use LLM
        logger.info("Hybrid - No regex matched, using LLM")
        result = self.full_llm_approach(query, context)
        result["used_llm"] = True
        return result


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
        if st.button("📋 Load Sample Data", width='stretch'):
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
                if st.button("📄 Extract PDF Text", width='stretch'):
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
        if st.button("🗑️ Clear Context", width='stretch'):
            st.session_state.pdf_text = None
            st.session_state.pdf_metadata = None
            # Use temporary variables to clear - they'll transfer before widget creation
            st.session_state.sample_query = ''
            st.session_state.sample_context = ''
            st.rerun()
        
        compare_button = st.button("🚀 Compare Approaches", type="primary", width='stretch')
    
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
            
            st.plotly_chart(fig_tokens, width='stretch')
        
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
            
            st.plotly_chart(fig_time, width='stretch')
    
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
