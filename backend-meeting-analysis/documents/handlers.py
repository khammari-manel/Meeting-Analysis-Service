"""Document processing - Extract text from PDF, DOCX, TXT files"""
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO
import requests


def extract_text_from_pdf(file_content):
    """Extract text from PDF file."""
    try:
        pdf_reader = PdfReader(BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"❌ Error extracting PDF: {e}")
        return None


def extract_text_from_docx(file_content):
    """Extract text from DOCX file."""
    try:
        doc = Document(BytesIO(file_content))
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        print(f"❌ Error extracting DOCX: {e}")
        return None


def extract_text_from_txt(file_content):
    """Extract text from TXT file."""
    try:
        return file_content.decode('utf-8')
    except Exception as e:
        print(f"❌ Error extracting TXT: {e}")
        return None


def extract_text_from_url(url):
    """Extract text from URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"❌ Error fetching URL: {e}")
        return None


def extract_text_from_file(file):
    """Main function to extract text from uploaded file."""
    if not file or file.filename == '':
        raise ValueError("No file selected")
    
    filename = file.filename.lower()
    file_content = file.read()
    
    if filename.endswith('.pdf'):
        return extract_text_from_pdf(file_content)
    elif filename.endswith('.docx'):
        return extract_text_from_docx(file_content)
    elif filename.endswith('.txt'):
        return extract_text_from_txt(file_content)
    else:
        raise ValueError("Unsupported file type. Use PDF, DOCX, or TXT")