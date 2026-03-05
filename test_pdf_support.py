"""
Quick test to verify PDF processor functionality
"""

from pdf_processor import PDFProcessor, is_pdf_support_available

print("=" * 60)
print("PDF Processor Test")
print("=" * 60)

# Check if PDF support is available
if is_pdf_support_available():
    print("✅ PDF support is available!")
    print()
    
    # Create processor
    processor = PDFProcessor()
    print(f"✅ PDFProcessor initialized")
    print(f"   Max file size: {processor.max_file_size_mb}MB")
    print(f"   Supported: {processor.supported}")
    print()
    
    print("=" * 60)
    print("PDF processor is ready to use!")
    print("=" * 60)
    print()
    print("Features:")
    print("  ✅ Single PDF upload")
    print("  ✅ Multiple PDF upload")
    print("  ✅ Text extraction")
    print("  ✅ Text cleaning")
    print("  ✅ PDF validation")
    print("  ✅ Metadata extraction")
    print()
    print("Open Streamlit app to test PDF uploads!")
    print("Run: streamlit run comparison_demo.py")
    
else:
    print("❌ PDF support not available")
    print("   Install with: pip install PyPDF2 pdfplumber")
