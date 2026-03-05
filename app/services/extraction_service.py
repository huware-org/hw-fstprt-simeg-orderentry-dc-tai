"""AI extraction service using Google Gemini."""

from typing import Optional
from fastapi import UploadFile
from google import genai
from google.genai import types
from app.models.schemas import ExtractedOrder, LubeExtractedOrder
from app.config.settings import settings, logger


# System prompt for Gemini (Italian) with reasoning
SYSTEM_PROMPT_WITH_REASONING = """Sei un esperto data entry clerk per un'azienda italiana che produce top in marmo e ceramica per l'arredamento di lusso (es. tavoli, cucine).
Il tuo compito è estrarre le informazioni dai PDF o dalle immagini degli ordini dei clienti (es. Molteni, DV Home, Visionnaire) e strutturarle rigidamente nel formato JSON richiesto.

IMPORTANTE: Prima di estrarre i dati, SPIEGA il tuo ragionamento:
- Quali elementi del documento hai identificato
- Come hai interpretato le informazioni
- Eventuali ambiguità o decisioni prese

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


# Lube-specific system prompt (Italian) with reasoning
LUBE_SYSTEM_PROMPT_WITH_REASONING = """Sei un estrattore dati per ordini Lube.

Per ogni riga dell'ordine, devi estrarre:

1. "codice_base": Il codice base del prodotto Lube (es. "000TKSP005")
2. "caratteristica": Cerca ESATTAMENTE uno dei codici caratteristica forniti nello schema JSON (es. KS06, LT59, D005, G01)
   - Questi codici appaiono nella descrizione come codici alfanumerici brevi
   - Estrai SOLO il codice se corrisponde ESATTAMENTE a uno dei valori permessi
3. "quantita": La quantità ordinata (numero)
4. "reasoning": Spiega brevemente come hai identificato questo articolo (es. "Trovato codice base 000TKSP005 e caratteristica KS06 nella descrizione articolo")

IMPORTANTE:
- Il campo "caratteristica" accetta SOLO i codici esatti definiti nello schema
- Nei PDF troverai SOLO il codice (es. "KS06"), NON il formato completo "TKS=KS06"

REGOLE TESTATA (OBBLIGATORIO):
1. "customer_name": Nome completo del cliente (OBBLIGATORIO)
2. "order_number": Numero ordine se presente
3. "order_date": Data ordine in formato ISO (YYYY-MM-DD)
4. "delivery_date": Data consegna in formato ISO (YYYY-MM-DD) - cerca "Data consegna", "Consegna", "Delivery"
5. "notes": Note generali o istruzioni speciali
6. "extraction_reasoning": Breve spiegazione di come hai interpretato il documento (es. "Documento Lube con 6 articoli, identificato cliente e date consegna")

IMPORTANTE: Estrai TUTTE le date che trovi. Includi sempre il campo "reasoning" per ogni articolo e "extraction_reasoning" per il documento.
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
    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not configured")
        raise ConfigurationError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please set it to your Google Gemini API key."
        )
    
    logger.debug("Creating Gemini client")
    return genai.Client(api_key=settings.GEMINI_API_KEY)


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
) -> tuple[ExtractedOrder, Optional[str]]:
    """
    Extract structured order data from uploaded document.
    
    Args:
        file: Uploaded document file
    
    Returns:
        Tuple of (ExtractedOrder, reasoning_text)
    
    Raises:
        ConfigurationError: If GEMINI_API_KEY is not set
        ExtractionError: If AI extraction fails
    """
    try:
        logger.info(f"Starting generic order extraction for: {file.filename}")
        
        # Get Gemini client
        client = _get_gemini_client()
        
        # Detect file type
        file_type = _detect_file_type(file.filename or "")
        logger.debug(f"File type detected: {file_type}")
        
        # Read file content
        content = await file.read()
        logger.debug(f"Read {len(content)} bytes from file")
        
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
            
            logger.debug(f"Using MIME type: {mime_type}")
            parts = [
                types.Part.from_bytes(
                    data=content,
                    mime_type=mime_type
                ),
                types.Part.from_text(text=SYSTEM_PROMPT_WITH_REASONING)
            ]
        else:
            # For XML and CSV, extract text and send as text
            text_content = content.decode("utf-8", errors="ignore")
            logger.debug(f"Decoded text content: {len(text_content)} characters")
            parts = [
                types.Part.from_text(text=SYSTEM_PROMPT_WITH_REASONING),
                types.Part.from_text(text=f"\n\nDocument content:\n{text_content}")
            ]
        
        # Create generation config with response schema
        generation_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractedOrder,
            thinking_config=types.ThinkingConfig(
                thinkingBudget=8192,  # Allow model to think
                includeThoughts=True  # Include reasoning in response
            )
        )
        
        # Call Gemini API
        logger.info("Calling Gemini API for extraction with reasoning")
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=parts,
            config=generation_config,
        )
        
        # Parse response
        if not response.text:
            logger.error("Gemini returned empty response")
            raise ExtractionError("Gemini returned empty response")
        
        logger.debug(f"Gemini response length: {len(response.text)} characters")
        
        # Extract reasoning if available
        reasoning = None
        logger.debug(f"Response object type: {type(response)}")
        logger.debug(f"Response has candidates: {hasattr(response, 'candidates')}")
        
        if hasattr(response, 'candidates') and response.candidates:
            logger.debug(f"Number of candidates: {len(response.candidates)}")
            candidate = response.candidates[0]
            logger.debug(f"Candidate type: {type(candidate)}")
            logger.debug(f"Candidate has thoughts: {hasattr(candidate, 'thoughts')}")
            
            if hasattr(candidate, 'thoughts') and candidate.thoughts:
                reasoning = candidate.thoughts
                logger.info(f"Captured AI reasoning: {len(reasoning)} characters")
            else:
                logger.warning("No thoughts found in candidate")
                # Try to inspect what's available
                logger.debug(f"Candidate attributes: {dir(candidate)}")
        else:
            logger.warning("No candidates in response")
        
        # Parse JSON response into ExtractedOrder
        extracted_order = ExtractedOrder.model_validate_json(response.text)
        logger.info(f"Successfully extracted order with {len(extracted_order.items)} items")
        
        return extracted_order, reasoning
        
    except ConfigurationError:
        raise
    except Exception as e:
        logger.error(f"Order extraction failed: {e}", exc_info=True)
        raise ExtractionError(f"Failed to extract order data: {str(e)}")


async def extract_lube_order_from_document(
    file: UploadFile,
) -> tuple[LubeExtractedOrder, Optional[str]]:
    """
    Extract structured Lube order data from uploaded document.
    
    Uses strict enum validation to ensure only valid characteristic codes are extracted.
    
    Args:
        file: Uploaded document file (PDF or image)
    
    Returns:
        Tuple of (LubeExtractedOrder, reasoning_text)
    
    Raises:
        ConfigurationError: If GEMINI_API_KEY is not set
        ExtractionError: If AI extraction fails
    """
    try:
        logger.info(f"Starting Lube order extraction for: {file.filename}")
        
        # Get Gemini client
        client = _get_gemini_client()
        
        # Detect file type
        file_type = _detect_file_type(file.filename or "")
        logger.debug(f"File type detected: {file_type}")
        
        # Read file content
        content = await file.read()
        logger.debug(f"Read {len(content)} bytes from file")
        
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
            
            logger.debug(f"Using MIME type: {mime_type}")
            parts = [
                types.Part.from_bytes(
                    data=content,
                    mime_type=mime_type
                ),
                types.Part.from_text(text=LUBE_SYSTEM_PROMPT_WITH_REASONING)
            ]
        else:
            # For CSV and other text-based formats, decode and pass as text
            try:
                text_content = content.decode("utf-8")
            except UnicodeDecodeError:
                text_content = content.decode("iso-8859-1", errors="ignore")
            
            logger.debug(f"Decoded text content: {len(text_content)} characters")
            
            # Add CSV-specific context to the prompt
            csv_context = """
NOTA: Questo è un file CSV con dati strutturati. Ogni riga rappresenta un articolo.
Il formato è: OrderNumber;ItemCode;CodiceBase;Description;Price;Thickness;Width;Caratteristica;...

Esempio di riga CSV:
2025353738;506000;000TKSS12;SCHIENALE GRES KOROS MM 12;3182;350;12;TKS=KS05;...

Estrai i dati seguendo le regole del prompt principale.
"""
            
            parts = [
                types.Part.from_text(text=LUBE_SYSTEM_PROMPT_WITH_REASONING),
                types.Part.from_text(text=csv_context),
                types.Part.from_text(text=f"\n\nContenuto del documento CSV:\n{text_content}")
            ]
        
        # Create generation config with Lube response schema
        generation_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=LubeExtractedOrder,
        )
        
        # Call Gemini API
        logger.info("Calling Gemini API for Lube extraction with enum validation")
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=parts,
            config=generation_config,
        )
        
        # Parse response
        if not response.text:
            logger.error("Gemini returned empty response")
            raise ExtractionError("Gemini returned empty response")
        
        logger.debug(f"Gemini response length: {len(response.text)} characters")
        
        # Parse JSON response into LubeExtractedOrder
        extracted_order = LubeExtractedOrder.model_validate_json(response.text)
        logger.info(f"Successfully extracted Lube order with {len(extracted_order.items)} items")
        
        # Get reasoning from the JSON response
        reasoning = extracted_order.extraction_reasoning
        if reasoning:
            logger.info(f"Captured AI reasoning from JSON: {len(reasoning)} characters")
        else:
            logger.warning("No extraction_reasoning in response")
        
        return extracted_order, reasoning
        
    except ConfigurationError:
        raise
    except Exception as e:
        logger.error(f"Lube order extraction failed: {e}", exc_info=True)
        raise ExtractionError(f"Failed to extract Lube order data: {str(e)}")
