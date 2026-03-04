"""Italian column name mapper for Mago4 flat table."""

from typing import Dict, List


# Mapping from English column names to Italian
COLUMN_NAME_MAPPING = {
    # Service fields
    "Id": "Id",
    "CreatedDate": "DataCreazione",
    "Processed": "Elaborato",
    
    # Header fields
    "H_ExternalOrdNo": "H_NumeroOrdineEsterno",
    "H_OrderDate": "H_DataOrdine",
    "H_ConfirmedDeliveryDate": "H_DataConsegnaConfermata",
    "H_Notes": "H_Note",
    "H_Currency": "H_Valuta",
    
    # Line item fields
    "Item": "Articolo",
    "Description": "Descrizione",
    "Qty": "Quantita",
    "UoM": "UnitaMisura",
    "UnitValue": "ValoreUnitario",
    "TaxableAmount": "ImportoImponibile",
    "Notes": "Note"
}


def translate_flat_table_to_italian(flat_table: List[Dict]) -> List[Dict]:
    """
    Translate flat table column names from English to Italian.
    
    Args:
        flat_table: List of dictionaries with English column names
        
    Returns:
        List of dictionaries with Italian column names
    """
    italian_table = []
    
    for row in flat_table:
        italian_row = {}
        for eng_key, value in row.items():
            italian_key = COLUMN_NAME_MAPPING.get(eng_key, eng_key)
            italian_row[italian_key] = value
        italian_table.append(italian_row)
    
    return italian_table


def get_italian_column_names() -> List[str]:
    """
    Get the list of Italian column names in order.
    
    Returns:
        List of Italian column names
    """
    return list(COLUMN_NAME_MAPPING.values())
