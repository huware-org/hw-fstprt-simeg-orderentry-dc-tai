"""Flat table transformer for Mago4 ERP integration."""

import uuid
from datetime import datetime
from typing import Optional
from BE.models import ExtractedOrder, ExtractedItem, FlatTableRow


def transform_to_flat_table(
    extracted_order: ExtractedOrder,
    customer_code: Optional[str],
    transcodified_items: list[tuple[ExtractedItem, str]]
) -> list[FlatTableRow]:
    """
    Transform order data into Mago4 flat table format.
    
    Each line item becomes one row with repeated header fields.
    
    Args:
        extracted_order: Extracted order data from Gemini
        customer_code: Customer code from validation (or None if not found)
        transcodified_items: List of (ExtractedItem, mago4_code) tuples
        
    Returns:
        List of FlatTableRow objects in Mago4 bridge table format
    """
    flat_table = []
    
    # Generate timestamp once for all rows
    created_date = datetime.utcnow().isoformat()
    
    # Header fields (repeated on each row)
    h_external_ord_no = extracted_order.customer_name  # Using customer name as order reference
    h_order_date = extracted_order.order_date
    h_confirmed_delivery_date = None  # Not extracted in this prototype
    h_notes = extracted_order.notes
    h_currency = "EUR"
    
    # Create one row per line item
    for extracted_item, mago4_code in transcodified_items:
        # Generate unique ID for this row
        row_id = str(uuid.uuid4())
        
        # Calculate taxable amount
        unit_value = extracted_item.unit_price or 0.0
        taxable_amount = extracted_item.quantity * unit_value
        
        # Build line-level notes from item attributes
        notes_parts = []
        if extracted_item.customer_item_code:
            notes_parts.append(f"Customer code: {extracted_item.customer_item_code}")
        if extracted_item.discount_percentage:
            notes_parts.append(f"Discount: {extracted_item.discount_percentage}%")
        line_notes = " | ".join(notes_parts) if notes_parts else None
        
        # Create flat table row
        row = FlatTableRow(
            # Service fields
            Id=row_id,
            CreatedDate=created_date,
            Processed=0,
            
            # Header fields (repeated)
            H_ExternalOrdNo=h_external_ord_no,
            H_OrderDate=h_order_date,
            H_ConfirmedDeliveryDate=h_confirmed_delivery_date,
            H_Notes=h_notes,
            H_Currency=h_currency,
            
            # Line item fields
            Item=mago4_code,
            Description=extracted_item.description,
            Qty=extracted_item.quantity,
            UoM="PZ",  # Default unit of measure
            UnitValue=unit_value,
            TaxableAmount=taxable_amount,
            Notes=line_notes
        )
        
        flat_table.append(row)
    
    return flat_table
