"""File text extraction utilities for PDF, DOCX, and TXT files."""

import io
from pypdf import PdfReader
from docx import Document


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text content from a PDF file."""
    pdf_file = io.BytesIO(file_content)
    reader = PdfReader(pdf_file)
    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
    return "\n".join(text_parts)


def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text content from a DOCX file."""
    docx_file = io.BytesIO(file_content)
    doc = Document(docx_file)
    text_parts = []
    for paragraph in doc.paragraphs:
        if paragraph.text:
            text_parts.append(paragraph.text)
    return "\n".join(text_parts)


def extract_text_from_txt(file_content: bytes) -> str:
    """Extract text content from a TXT file."""
    return file_content.decode("utf-8")


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def extract_text(filename: str, file_content: bytes) -> str:
    """Extract text from file based on extension."""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    
    if ext == ".pdf":
        return extract_text_from_pdf(file_content)
    elif ext == ".docx":
        return extract_text_from_docx(file_content)
    elif ext == ".txt":
        return extract_text_from_txt(file_content)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
