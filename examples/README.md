# Examples

This folder contains demonstration scripts and examples for the Clinical Note Processing API.

## Available Examples

### comparison_demo.py
Interactive Streamlit demo comparing two approaches:
- **Full LLM Approach**: Every query goes to the Groq LLM
- **Hybrid Approach**: Rule-based matching first, LLM for complex queries only

**Features:**
- Token usage comparison
- Cost analysis
- Performance metrics
- Interactive UI for testing both approaches

**Usage:**
```bash
streamlit run examples/comparison_demo.py
```

**Note:** PDF support is optional. Install with:
```bash
pip install pypdf2 pdfplumber
```
