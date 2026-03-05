"""
PDF Processor Module
Handles PDF text extraction and processing for comparison demo
"""

import io
import re
from typing import List, Dict, Optional
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class PDFProcessor:
    """Process PDF files and extract text content"""
    
    def __init__(self):
        """Initialize PDF processor"""
        self.max_file_size_mb = 10
        self.supported = PYPDF2_AVAILABLE or PDFPLUMBER_AVAILABLE
        
        if not self.supported:
            raise ImportError(
                "PDF processing requires PyPDF2 or pdfplumber. "
                "Install with: pip install PyPDF2 pdfplumber"
            )
    
    def extract_text_from_pdf(self, pdf_file) -> Dict[str, any]:
        """
        Extract text from a single PDF file
        
        Args:
            pdf_file: Streamlit UploadedFile object or file-like object
            
        Returns:
            dict with:
                - text: Extracted text
                - pages: Number of pages
                - filename: Original filename
                - success: Boolean
                - error: Error message if any
        """
        result = {
            "text": "",
            "pages": 0,
            "filename": getattr(pdf_file, 'name', 'unknown.pdf'),
            "success": False,
            "error": None
        }
        
        try:
            # Check file size
            file_size_mb = len(pdf_file.getvalue()) / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                result["error"] = f"File too large ({file_size_mb:.1f}MB). Max: {self.max_file_size_mb}MB"
                return result
            
            # Try pdfplumber first (better quality)
            if PDFPLUMBER_AVAILABLE:
                text = self._extract_with_pdfplumber(pdf_file)
            elif PYPDF2_AVAILABLE:
                text = self._extract_with_pypdf2(pdf_file)
            else:
                result["error"] = "No PDF extraction library available"
                return result
            
            # Clean and validate text
            if text and text.strip():
                result["text"] = self._clean_text(text)
                result["pages"] = text.count('\f') + 1  # Page breaks
                result["success"] = True
            else:
                result["error"] = "No text extracted from PDF (may be image-based)"
            
        except Exception as e:
            result["error"] = f"PDF extraction error: {str(e)}"
        
        return result
    
    def _extract_with_pdfplumber(self, pdf_file) -> str:
        """Extract text using pdfplumber"""
        pdf_file.seek(0)  # Reset file pointer
        text_parts = []
        
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        return '\n\n'.join(text_parts)
    
    def _extract_with_pypdf2(self, pdf_file) -> str:
        """Extract text using PyPDF2"""
        pdf_file.seek(0)  # Reset file pointer
        text_parts = []
        
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        return '\n\n'.join(text_parts)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted PDF text
        - Remove excessive whitespace
        - Preserve medical formatting
        - Remove artifacts
        """
        # Remove form feed characters but preserve structure
        text = text.replace('\f', '\n\n')
        
        # Remove excessive whitespace but keep paragraph breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Remove extra spaces
        text = re.sub(r' +', ' ', text)
        
        # Remove zero-width characters and other artifacts
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()
    
    def extract_text_from_multiple_pdfs(self, pdf_files: List) -> List[Dict[str, any]]:
        """
        Extract text from multiple PDF files
        
        Args:
            pdf_files: List of Streamlit UploadedFile objects
            
        Returns:
            List of result dictionaries (same format as extract_text_from_pdf)
        """
        results = []
        
        for pdf_file in pdf_files:
            result = self.extract_text_from_pdf(pdf_file)
            results.append(result)
        
        return results
    
    def validate_pdf(self, pdf_file) -> tuple[bool, str]:
        """
        Validate if file is a valid PDF
        
        Returns:
            (is_valid, error_message)
        """
        try:
            pdf_file.seek(0)
            header = pdf_file.read(4)
            pdf_file.seek(0)
            
            if header != b'%PDF':
                return False, "Not a valid PDF file"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_pdf_metadata(self, pdf_file) -> Dict[str, any]:
        """
        Get PDF metadata (pages, size, etc.)
        
        Returns:
            dict with metadata
        """
        metadata = {
            "filename": getattr(pdf_file, 'name', 'unknown.pdf'),
            "size_kb": len(pdf_file.getvalue()) / 1024,
            "pages": 0,
            "valid": False
        }
        
        try:
            is_valid, error = self.validate_pdf(pdf_file)
            metadata["valid"] = is_valid
            
            if is_valid:
                if PYPDF2_AVAILABLE:
                    pdf_file.seek(0)
                    reader = PyPDF2.PdfReader(pdf_file)
                    metadata["pages"] = len(reader.pages)
                elif PDFPLUMBER_AVAILABLE:
                    pdf_file.seek(0)
                    with pdfplumber.open(pdf_file) as pdf:
                        metadata["pages"] = len(pdf.pages)
            
            pdf_file.seek(0)  # Reset for later use
            
        except Exception as e:
            metadata["error"] = str(e)
        
        return metadata


# Convenience functions
def extract_text_from_pdf(pdf_file) -> Dict[str, any]:
    """
    Convenience function to extract text from a single PDF
    
    Args:
        pdf_file: Streamlit UploadedFile object
        
    Returns:
        dict with extraction results
    """
    processor = PDFProcessor()
    return processor.extract_text_from_pdf(pdf_file)


def extract_text_from_multiple_pdfs(pdf_files: List) -> List[Dict[str, any]]:
    """
    Convenience function to extract text from multiple PDFs
    
    Args:
        pdf_files: List of Streamlit UploadedFile objects
        
    Returns:
        List of extraction results
    """
    processor = PDFProcessor()
    return processor.extract_text_from_multiple_pdfs(pdf_files)


def is_pdf_support_available() -> bool:
    """Check if PDF processing libraries are available"""
    return PYPDF2_AVAILABLE or PDFPLUMBER_AVAILABLE
