import io

from mcp.server.fastmcp import FastMCP
from PyPDF2 import PdfReader

mcp = FastMCP("PDF Extraction Tool Example")


@mcp.tool()
def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from a PDF file (bytes)"""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return text[:2000] + ("..." if len(text) > 2000 else "")
