"""XML order processor for Scavolini and Ernestomeda orders."""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from app.utils.scavolini_loader import get_scavolini_loader
from app.utils.lube_loader import get_lube_loader
from app.models.schemas import ExtractedOrder, ExtractedItem
from app.config.settings import settings
from google import genai
from google.genai import types


def extract_customer_from_xml_with_ai(xml_content: str) -> str:
    """
    Use AI to extract the customer name from XML.
    
    This is more flexible than hardcoding and can handle variations.
    
    Args:
        xml_content: XML content as string
        
    Returns:
        Customer name extracted by AI
    """
    try:
        if not settings.GEMINI_API_KEY:
            # Fallback to parsing if no API key
            return extract_customer_from_xml_direct(xml_content)
        
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        prompt = """Analyze this XML order document and extract the customer/company name.
        
Look for fields like:
- DESTINATARIO_MERCI/ID (goods recipient)
- COMMITTENTE/ID (ordering party)
- Any company name fields

Return ONLY the company name, nothing else.

XML:
""" + xml_content[:2000]  # Send first 2000 chars to keep it manageable
        
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt
        )
        
        if response.text:
            customer_name = response.text.strip()
            # Clean up common AI response patterns
            customer_name = customer_name.replace('"', '').replace("'", "")
            return customer_name
        
    except Exception as e:
        print(f"AI extraction failed, falling back to direct parsing: {e}")
    
    # Fallback to direct parsing
    return extract_customer_from_xml_direct(xml_content)


def extract_customer_from_xml_direct(xml_content: str) -> str:
    """
    Direct XML parsing to extract customer name.
    
    Args:
        xml_content: XML content as string
        
    Returns:
        Customer name from XML structure
    """
    try:
        root = ET.fromstring(xml_content)
        testata = root.find('TESTATA')
        
        if testata is not None:
            # Try DESTINATARIO_MERCI first (goods recipient)
            destinatario = testata.find('DESTINATARIO_MERCI')
            if destinatario is not None:
                id_elem = destinatario.find('ID')
                if id_elem is not None and id_elem.text:
                    return id_elem.text.strip()
            
            # Try COMMITTENTE (ordering party)
            committente = testata.find('COMMITTENTE')
            if committente is not None:
                id_elem = committente.find('ID')
                if id_elem is not None and id_elem.text:
                    return id_elem.text.strip()
        
        # Default fallback
        return "Unknown Customer"
        
    except Exception:
        return "Unknown Customer"


def parse_scavolini_xml(xml_content: str, use_ai_extraction: bool = True) -> ExtractedOrder:
    """
    Parse Scavolini XML order format.
    
    Args:
        xml_content: XML content as string
        use_ai_extraction: Whether to use AI for customer extraction (default: True)
        
    Returns:
        ExtractedOrder with parsed data
    """
    root = ET.fromstring(xml_content)
    
    # Extract customer name using AI or direct parsing
    if use_ai_extraction:
        customer_name = extract_customer_from_xml_with_ai(xml_content)
    else:
        customer_name = extract_customer_from_xml_direct(xml_content)
    
    # Parse header (TESTATA)
    testata = root.find('TESTATA')
    
    order_date = None
    notes = None
    
    if testata is not None:
        # Extract order date
        data_ordine = testata.find('DATA_ORDINE')
        if data_ordine is not None and data_ordine.text:
            # Convert from DD/MM/YYYY to YYYY-MM-DD
            parts = data_ordine.text.split('/')
            if len(parts) == 3:
                order_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
        
        # Extract notes from various fields
        note_parts = []
        numero_ordine = testata.find('NUMERO_ORDINE')
        if numero_ordine is not None and numero_ordine.text:
            note_parts.append(f"Order: {numero_ordine.text}")
        
        tipo_ordine = testata.find('TIPO_ORDINE')
        if tipo_ordine is not None and tipo_ordine.text:
            note_parts.append(f"Type: {tipo_ordine.text}")
        
        notes = " | ".join(note_parts) if note_parts else None
    
    # Parse line items (DETTAGLIO)
    items = []
    for dettaglio in root.findall('DETTAGLIO'):
        item = parse_scavolini_dettaglio(dettaglio)
        if item:
            items.append(item)
    
    return ExtractedOrder(
        customer_name=customer_name,
        customer_address=None,
        order_date=order_date,
        payment_terms_requested=None,
        notes=notes,
        items=items
    )


def parse_scavolini_dettaglio(dettaglio: ET.Element) -> Optional[ExtractedItem]:
    """
    Parse a single DETTAGLIO (line item) from Scavolini XML.
    
    Args:
        dettaglio: XML element for line item
        
    Returns:
        ExtractedItem or None if parsing fails
    """
    # Extract basic item info
    cod_art_cliente = dettaglio.find('COD_ART_CLIENTE')
    desc_art_cliente = dettaglio.find('DESC_ART_CLIENTE')
    quantita = dettaglio.find('QUANTITA_ORDINATA')
    valore_netto = dettaglio.find('VALORE_NETTO_RIGA')
    
    if cod_art_cliente is None or desc_art_cliente is None:
        return None
    
    # Parse characteristics (CARATTERISTICHE)
    caratteristiche = {}
    caratteristiche_elem = dettaglio.find('CARATTERISTICHE')
    if caratteristiche_elem is not None:
        for car in caratteristiche_elem.findall('CARATTERISTICA'):
            cod_nome = car.find('COD_NOME')
            cod_valore = car.find('COD_VALORE')
            if cod_nome is not None and cod_valore is not None:
                if cod_nome.text and cod_valore.text:
                    caratteristiche[cod_nome.text] = cod_valore.text
    
    # Extract key attributes for transcodification
    mat_piano = caratteristiche.get('C_MATPIANO')
    col_piano = caratteristiche.get('C_COLPIANO')
    fin_piano = caratteristiche.get('C_FINPIANO')
    prof_piano = caratteristiche.get('C_PROFPIANO')
    
    # Parse quantity
    qty = 1.0
    if quantita is not None and quantita.text:
        try:
            qty = float(quantita.text.replace(',', '.'))
        except ValueError:
            qty = 1.0
    
    # Parse unit price (calculate from total and quantity)
    unit_price = None
    if valore_netto is not None and valore_netto.text and qty > 0:
        try:
            total = float(valore_netto.text.replace(',', '.'))
            unit_price = total / qty
        except ValueError:
            pass
    
    # Build description with material info
    description_parts = [desc_art_cliente.text]
    if mat_piano:
        valore_mat = caratteristiche.get('C_MATPIANO')
        if valore_mat:
            description_parts.append(f"Material: {valore_mat}")
    
    description = " | ".join(description_parts)
    
    return ExtractedItem(
        customer_item_code=cod_art_cliente.text,
        description=description,
        color=col_piano,
        thickness=caratteristiche.get('C_SPESSORE'),
        quantity=qty,
        unit_price=unit_price,
        discount_percentage=None
    )


def get_scavolini_attributes_from_item(item: ExtractedItem) -> Dict[str, Optional[str]]:
    """
    Extract Scavolini transcodification attributes from an ExtractedItem.
    
    This is used to lookup the Mago4 code from the Scavolini table.
    
    Args:
        item: ExtractedItem with Scavolini data
        
    Returns:
        Dictionary with transcodification attributes
    """
    # For Scavolini items, the attributes are stored in the item fields
    # We need to extract them from the original XML parsing
    # This is a placeholder - in practice, we'd store these during XML parsing
    return {
        'cod_art_cliente': item.customer_item_code,
        'mat_piano': None,  # Would be extracted during XML parsing
        'col_piano': item.color,
        'fin_piano': None,  # Would be extracted during XML parsing
        'prof_piano': None,  # Would be extracted during XML parsing
    }


def lookup_scavolini_mago4_code(
    cod_art_cliente: Optional[str],
    mat_piano: Optional[str],
    col_piano: Optional[str],
    fin_piano: Optional[str],
    prof_piano: Optional[str]
) -> Optional[str]:
    """
    Lookup Mago4 code from Scavolini transcodification table.
    
    Args:
        cod_art_cliente: Customer article code
        mat_piano: Material code
        col_piano: Color code
        fin_piano: Finish code
        prof_piano: Profile code
        
    Returns:
        Mago4 code if found, None otherwise
    """
    loader = get_scavolini_loader()
    
    # Convert cod_art_cliente to int if it's a string
    cod_art_int = None
    if cod_art_cliente:
        try:
            cod_art_int = int(cod_art_cliente)
        except ValueError:
            pass
    
    return loader.lookup_mago4_code(
        mat_piano=mat_piano,
        col_piano=col_piano,
        fin_piano=fin_piano,
        prof_piano=prof_piano,
        cod_art_cliente=cod_art_int
    )


def lookup_lube_mago4_code(
    codice_base: str,
    caratteristica: str
) -> Optional[str]:
    """
    Lookup Mago4 code from Lube transcodification table.
    
    The Lube table has a 'Caratteristica' column with format "PREFIX=CODE" (e.g., "TKS=KS06").
    The loader automatically splits this and matches against just the CODE part.
    
    Args:
        codice_base: Base product code from Lube
        caratteristica: Characteristic code (just the CODE part, e.g., "KS06")
        
    Returns:
        Mago4 code if found, None otherwise
    """
    loader = get_lube_loader()
    
    return loader.lookup_mago4_code(
        codice_base=codice_base,
        caratteristica=caratteristica
    )
