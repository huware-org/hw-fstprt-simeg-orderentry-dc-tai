"""Client detection service to identify which client an order belongs to."""

from enum import Enum
from typing import Optional
from fastapi import UploadFile
from google import genai
from google.genai import types
from app.config.settings import settings, logger


class ClientType(str, Enum):
    """Supported client types."""
    SCAVOLINI = "scavolini"
    LUBE = "lube"
    GENERIC = "generic"


class ClientDetectionError(Exception):
    """Raised when client detection fails."""
    pass


async def detect_client_from_document(file: UploadFile) -> ClientType:
    """
    Detect which client an order document belongs to.
    
    Uses AI to analyze the document and identify the client type.
    
    Args:
        file: Uploaded document file
        
    Returns:
        ClientType enum indicating the detected client
        
    Raises:
        ClientDetectionError: If detection fails
    """
    try:
        logger.info(f"Starting client detection for file: {file.filename}")
        
        # Check if it's XML (likely Scavolini/Ernestomeda)
        if file.filename and file.filename.lower().endswith('.xml'):
            logger.debug("File is XML format, checking for Scavolini markers")
            # Read a sample to check structure
            content = await file.read()
            await file.seek(0)  # Reset for later reading
            
            try:
                xml_content = content.decode('utf-8')
            except UnicodeDecodeError:
                xml_content = content.decode('iso-8859-1')
            
            # Simple heuristic: check for Scavolini-specific tags
            if 'CARATTERISTICA' in xml_content or 'C_MATPIANO' in xml_content:
                logger.info("Detected Scavolini client from XML structure")
                return ClientType.SCAVOLINI
        
        # For PDFs and images, use AI detection
        if not settings.GEMINI_API_KEY:
            logger.warning("No GEMINI_API_KEY configured, defaulting to GENERIC client")
            return ClientType.GENERIC
        
        logger.debug("Using AI for client detection")
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        # Read file content
        content = await file.read()
        await file.seek(0)  # Reset for later reading
        
        # Detect file type
        file_type = _detect_file_type(file.filename or "")
        logger.debug(f"Detected file type: {file_type}")
        
        # Prepare content for Gemini
        if file_type in ["pdf", "image"]:
            if file_type == "pdf":
                mime_type = "application/pdf"
            elif file.content_type:
                mime_type = file.content_type
            else:
                mime_type = "image/jpeg"
            
            parts = [
                types.Part.from_bytes(data=content, mime_type=mime_type),
                types.Part.from_text(text=CLIENT_DETECTION_PROMPT)
            ]
        else:
            text_content = content.decode("utf-8", errors="ignore")
            parts = [
                types.Part.from_text(text=CLIENT_DETECTION_PROMPT),
                types.Part.from_text(text=f"\n\nDocument content:\n{text_content[:2000]}")
            ]
        
        # Call Gemini API
        logger.debug("Calling Gemini API for client detection")
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=parts
        )
        
        if not response.text:
            logger.warning("Gemini returned empty response, defaulting to GENERIC")
            return ClientType.GENERIC
        
        # Parse response
        client_name = response.text.strip().lower()
        logger.debug(f"Gemini response: {client_name}")
        
        if "scavolini" in client_name or "ernestomeda" in client_name:
            logger.info("Detected Scavolini client from AI analysis")
            return ClientType.SCAVOLINI
        elif "lube" in client_name:
            logger.info("Detected Lube client from AI analysis")
            return ClientType.LUBE
        else:
            logger.info(f"Unknown client '{client_name}', using GENERIC")
            return ClientType.GENERIC
        
    except Exception as e:
        logger.error(f"Client detection failed: {e}", exc_info=True)
        logger.info("Defaulting to GENERIC client type")
        return ClientType.GENERIC


def _detect_file_type(filename: str) -> str:
    """Detect file type from filename extension."""
    ext = filename.lower().split(".")[-1]
    
    if ext == "pdf":
        return "pdf"
    elif ext in ["png", "jpg", "jpeg"]:
        return "image"
    elif ext == "xml":
        return "xml"
    elif ext == "csv":
        return "csv"
    else:
        return "unknown"


CLIENT_DETECTION_PROMPT = """Analyze this order document and identify which client/manufacturer it belongs to.

Look for:
- Company logos or names in headers
- Specific product codes or formats
- Document structure and layout

Known clients:
- SCAVOLINI / ERNESTOMEDA: Italian kitchen manufacturer, uses specific XML format with codes like C_MATPIANO, C_COLPIANO
- LUBE: Italian kitchen manufacturer, uses codes like KS06, LT59, D005, G01 in product descriptions

Return ONLY the client name (one word): "scavolini", "lube", or "generic" if unknown.
"""
