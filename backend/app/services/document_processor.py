"""
Document Processor Service

Purpose:
    Handles extraction of raw text from uploaded files (PDF, Text).
    Used primarily for ingesting Course Materials for the RAG system.

Limitations:
    - Currently uses basic `pypdf` extraction (text-only, no OCR).
    - Chunking is simple character-based sliding window.
"""
import io
from pypdf import PdfReader
from fastapi import UploadFile

class DocumentProcessor:
    @staticmethod
    async def extract_text_from_file(file: UploadFile) -> str:
        """
        Reads an UploadFile and returns its text content.
        Supports PDF and plain text files.
        """
        content = await file.read()
        
        if file.content_type == "application/pdf":
            return DocumentProcessor._extract_from_pdf(content)
        elif file.content_type.startswith("text/"):
            return content.decode("utf-8")
        else:
            raise ValueError(f"Unsupported file type: {file.content_type}")

    @staticmethod
    def _extract_from_pdf(content: bytes) -> str:
        """Helper to extract text from PDF bytes using pypdf."""
        reader = PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
        """
        Splits text into overlapping chunks for vector embedding.
        
        Inputs:
            text: The full document text.
            chunk_size: Target characters per chunk (default 1000).
            overlap: Overlap to preserve context between chunks (default 200).
            
        Note:
            - This is a naive implementation. 
            - TODO: Upgrade to LangChain's RecursiveCharacterTextSplitter for semantic awareness.
        """
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += (chunk_size - overlap)
        return chunks
