"""AI extraction service using Google Gemini."""

import os
from typing import Optional
from fastapi import UploadFile
from google import genai
from google.genai import types
from BE.models import ExtractedOrder


# System prompt for Gemini (Italian)
SYSTEM_PROMPT = """Sei un esperto data entry clerk per un'azienda italiana che produce top in marmo e ceramica per l'arredamento di lusso (es. tavoli, cucine).
Il tuo compito è estrarre le informazioni dai PDF o dalle immagini degli ordini dei clienti (es. Molteni, DV Home, Visionnaire) e strutturarle rigidamente nel formato JSON richiesto.

REGOLE DI ESTRAZIONE RIGHE ORDINE (Items):
1. Cerca righe che descrivono lavorazioni in marmo, pietra o ceramica (es. "TOP MARMO", "TAVOLO MANHATTAN").
2. "customer_item_code": Estrai il codice articolo del cliente se presente (es. "101MATPI2403", "FEMM1655MBR").
3. "description": Inserisci la descrizione generale dell'oggetto (es. "TOP TAVOLO MANHATTAN", "C/LAV. TOP MARMO 3306 SX").
4. "color": Isola SEMPRE il nome del colore/materiale e mettilo in questo campo separato (es. "OROBICO ARABESCATO", "CAPRAIA"). Non lasciarlo nella descrizione generica.
5. "thickness": Estrai lo spessore se presente (es. "20mm", "12mm", "30mm").
6. "quantity": Estrai sempre la quantità numerica (es. 1, 2).
7. "unit_price": Estrai il prezzo unitario senza il simbolo dell'euro. Assicurati di non scambiarlo con lo sconto.
8. "discount_percentage": Estrai lo sconto percentuale se presente.

REGOLE DI ESTRAZIONE TESTATA ORDINE:
1. "customer_name": Estrai il nome completo dell'azienda cliente (es. "MOLTENI&C. S.P.A.", "DV HOME S.R.L.").
2. "customer_address": Estrai l'indirizzo completo se presente.
3. "order_date": Estrai la data dell'ordine in formato ISO (YYYY-MM-DD).
4. "payment_terms_requested": Estrai i termini di pagamento richiesti (es. "30gg DFFM", "60gg DF").
5. "notes": Inserisci note generali o istruzioni per l'intero ordine.
"""


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass


class ExtractionError(Exception):
    """Raised when AI extraction fails."""
    pass


def _get_gemini_client() -> genai.Client:
    """
    Get configured Gemini client.
    
    Returns:
        Configured Gemini client
        
    Raises:
        ConfigurationError: If GEMINI_API_KEY is not set
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ConfigurationError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please set it to your Google Gemini API key."
        )
    
    return genai.Client(api_key=api_key)


def _detect_file_type(filename: str) -> str:
    """
    Detect file type from filename extension.
    
    Args:
        filename: Name of the uploaded file
        
    Returns:
        File type: "pdf", "image", "xml", or "csv"
    """
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


async def extract_order_from_document(
    file: UploadFile,
) -> ExtractedOrder:
    """
    Extract structured order data from uploaded document.
    
    Args:
        file: Uploaded document file
    
    Returns:
        ExtractedOrder: Structured order data
    
    Raises:
        ConfigurationError: If GEMINI_API_KEY is not set
        ExtractionError: If AI extraction fails
    """
    try:
        # Get Gemini client
        client = _get_gemini_client()
        
        # Detect file type
        file_type = _detect_file_type(file.filename or "")
        
        # Read file content
        content = await file.read()
        
        # Prepare content for Gemini
        if file_type in ["pdf", "image"]:
            # For PDF and images, send as binary with proper MIME type
            if file_type == "pdf":
                mime_type = "application/pdf"
            elif file.content_type:
                mime_type = file.content_type
            else:
                # Default MIME types for images
                if file.filename and file.filename.lower().endswith('.png'):
                    mime_type = "image/png"
                elif file.filename and file.filename.lower().endswith(('.jpg', '.jpeg')):
                    mime_type = "image/jpeg"
                else:
                    mime_type = "image/jpeg"  # Default fallback
            
            parts = [
                types.Part.from_bytes(
                    data=content,
                    mime_type=mime_type
                ),
                types.Part.from_text(text=SYSTEM_PROMPT)
            ]
        else:
            # For XML and CSV, extract text and send as text
            text_content = content.decode("utf-8", errors="ignore")
            parts = [
                types.Part.from_text(text=SYSTEM_PROMPT),
                types.Part.from_text(text=f"\n\nDocument content:\n{text_content}")
            ]
        
        # Create generation config with response schema
        generation_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractedOrder,
        )
        
        # Call Gemini API
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=parts,
            config=generation_config,
        )
        
        # Parse response
        if not response.text:
            raise ExtractionError("Gemini returned empty response")
        
        # Parse JSON response into ExtractedOrder
        extracted_order = ExtractedOrder.model_validate_json(response.text)
        
        return extracted_order
        
    except ConfigurationError:
        raise
    except Exception as e:
        raise ExtractionError(f"Failed to extract order data: {str(e)}")
