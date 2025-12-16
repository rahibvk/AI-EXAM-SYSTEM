import io
from pypdf import PdfReader
from fastapi import UploadFile

class DocumentProcessor:
    @staticmethod
    async def extract_text_from_file(file: UploadFile) -> str:
        content = await file.read()
        
        if file.content_type == "application/pdf":
            return DocumentProcessor._extract_from_pdf(content)
        elif file.content_type.startswith("text/"):
            return content.decode("utf-8")
        else:
            raise ValueError(f"Unsupported file type: {file.content_type}")

    @staticmethod
    def _extract_from_pdf(content: bytes) -> str:
        reader = PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
        # Simple character based chunking for now
        # In production, use LangChain's RecursiveCharacterTextSplitter
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += (chunk_size - overlap)
        return chunks
