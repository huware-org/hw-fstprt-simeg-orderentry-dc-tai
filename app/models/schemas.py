"""Pydantic data models for the Simeg Order Entry system."""

from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel, Field


# Lube characteristic codes extracted from transcodification table
LubeCodeEnum = Literal[
    "D001","D005","D006","D008","D009","D010","D011","D020","D021","D022","D023","D025",
    "G01","G20","G21","G22","G23","G40","G43","G70","G71","G72","G73","G80","G81","G90","G91","G92","G93","G94","G95","G96",
    "KS01","KS02","KS03","KS04","KS05","KS06","KS07","KS08","KS09","KS11","KS12","KS13","KS53","KS54","KS59","KS61","KS64","KS65",
    "LT14","LT26","LT27","LT28","LT29","LT30","LT56","LT57","LT58","LT59","LT60","LT61"
]


class TrafficLight(str, Enum):
    """Validation confidence indicator."""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class ExtractedItem(BaseModel):
    """Line item extracted from order document."""
    customer_item_code: Optional[str] = Field(
        None,
        description="Customer's item code if present"
    )
    description: str = Field(
        ...,
        description="General description of the item"
    )
    color: Optional[str] = Field(
        None,
        description="Material color (e.g., 'CAPRAIA', 'OROBICO ARABESCATO')"
    )
    thickness: Optional[str] = Field(
        None,
        description="Material thickness (e.g., '20mm', '12mm')"
    )
    quantity: float = Field(
        ...,
        description="Quantity ordered (must be greater than 0)"
    )
    unit_price: Optional[float] = Field(
        None,
        description="Unit price without currency symbol (must be non-negative)"
    )
    discount_percentage: Optional[float] = Field(
        None,
        description="Discount percentage if applicable (0-100)"
    )


class ScavoliniExtractedItem(BaseModel):
    """Line item extracted from Scavolini/Ernestomeda XML order."""
    customer_item_code: str = Field(
        ...,
        description="Customer's item code (COD_ART_CLIENTE)"
    )
    description: str = Field(
        ...,
        description="Item description (DESC_ART_CLIENTE)"
    )
    color: Optional[str] = Field(
        None,
        description="Material color code or name from C_COLPIANO"
    )
    thickness: Optional[str] = Field(
        None,
        description="Material thickness from C_SPESSORE (e.g., '20,0')"
    )
    quantity: float = Field(
        ...,
        description="Quantity ordered (QUANTITA_ORDINATA)"
    )
    unit_price: Optional[float] = Field(
        None,
        description="Unit price calculated from VALORE_NETTO_RIGA / quantity"
    )
    # Scavolini-specific characteristic codes for transcodification
    mat_piano: Optional[str] = Field(
        None,
        description="Material code from C_MATPIANO characteristic (e.g., 'MP0047')"
    )
    col_piano: Optional[str] = Field(
        None,
        description="Color code from C_COLPIANO characteristic (e.g., 'CP1291')"
    )
    fin_piano: Optional[str] = Field(
        None,
        description="Finish code from C_FINPIANO characteristic (e.g., 'FP0207')"
    )
    prof_piano: Optional[str] = Field(
        None,
        description="Profile code from C_PROFPIANO characteristic (e.g., 'PP1083')"
    )
    reasoning: Optional[str] = Field(
        None,
        description="AI reasoning for how this item was identified and extracted"
    )


class LubeExtractedItem(BaseModel):
    """Line item extracted from Lube order document."""
    codice_base: str = Field(
        ...,
        description="Base product code from Lube (e.g., 'BASE123')"
    )
    caratteristica: LubeCodeEnum = Field(
        ...,
        description="Characteristic code - MUST be exactly one of the valid codes from the enum"
    )
    quantita: float = Field(
        ...,
        description="Quantity ordered (must be greater than 0)"
    )
    reasoning: Optional[str] = Field(
        None,
        description="AI reasoning for how this item was identified and extracted"
    )


class ExtractedOrder(BaseModel):
    """Complete order extracted from document."""
    customer_name: str = Field(
        ...,
        description="Customer company name"
    )
    customer_address: Optional[str] = Field(
        None,
        description="Customer address"
    )
    order_number: Optional[str] = Field(
        None,
        description="Order number from the document"
    )
    order_date: Optional[str] = Field(
        None,
        description="Order date in ISO format (YYYY-MM-DD)"
    )
    delivery_date: Optional[str] = Field(
        None,
        description="Requested delivery date in ISO format (YYYY-MM-DD)"
    )
    payment_terms_requested: Optional[str] = Field(
        None,
        description="Payment terms requested by customer"
    )
    notes: Optional[str] = Field(
        None,
        description="General order notes"
    )
    items: list[ExtractedItem] = Field(
        ...,
        description="List of line items (at least one required)"
    )


class LubeExtractedOrder(BaseModel):
    """Complete Lube order extracted from document."""
    customer_name: str = Field(
        ...,
        description="Customer company name"
    )
    order_number: Optional[str] = Field(
        None,
        description="Order number from the document"
    )
    order_date: Optional[str] = Field(
        None,
        description="Order date in ISO format (YYYY-MM-DD)"
    )
    delivery_date: Optional[str] = Field(
        None,
        description="Requested delivery date in ISO format (YYYY-MM-DD)"
    )
    notes: Optional[str] = Field(
        None,
        description="General order notes or special instructions"
    )
    extraction_reasoning: Optional[str] = Field(
        None,
        description="Overall reasoning about how the document was interpreted"
    )
    items: list[LubeExtractedItem] = Field(
        ...,
        description="List of Lube line items (at least one required)"
    )


class ScavoliniExtractedOrder(BaseModel):
    """Complete Scavolini/Ernestomeda order extracted from XML document."""
    customer_name: str = Field(
        ...,
        description="Customer company name from DESTINATARIO_MERCI or COMMITTENTE"
    )
    customer_address: Optional[str] = Field(
        None,
        description="Customer address from DESTINATARIO_MERCI"
    )
    order_number: Optional[str] = Field(
        None,
        description="Order number from NUMERO_ORDINE"
    )
    order_date: Optional[str] = Field(
        None,
        description="Order date in ISO format (YYYY-MM-DD) from DATA_ORDINE"
    )
    delivery_date: Optional[str] = Field(
        None,
        description="Delivery date in ISO format (YYYY-MM-DD) from DATA_CONSEGNA"
    )
    notes: Optional[str] = Field(
        None,
        description="General order notes including TIPO_ORDINE, DIVISIONE, etc."
    )
    extraction_reasoning: Optional[str] = Field(
        None,
        description="Overall reasoning about how the XML document was interpreted"
    )
    items: list[ScavoliniExtractedItem] = Field(
        ...,
        description="List of Scavolini line items (at least one required)"
    )


class FlatTableRow(BaseModel):
    """Single row in Mago4 bridge table format."""
    # Service fields
    Id: str = Field(..., description="Unique row identifier (UUID)")
    CreatedDate: str = Field(..., description="Timestamp of creation (ISO format)")
    Processed: int = Field(0, description="Processing status (0=pending, 1=processed)")
    
    # Header fields (repeated on each row)
    H_ExternalOrdNo: Optional[str] = Field(None, description="External order number")
    H_OrderDate: Optional[str] = Field(None, description="Order date")
    H_ConfirmedDeliveryDate: Optional[str] = Field(None, description="Delivery date")
    H_Notes: Optional[str] = Field(None, description="Order-level notes")
    H_Currency: str = Field("EUR", description="Currency code")
    
    # Line item fields
    Item: str = Field(..., description="Mago4 internal item code")
    Description: str = Field(..., description="Item description")
    Qty: float = Field(..., description="Quantity")
    UoM: str = Field("PZ", description="Unit of measure")
    UnitValue: float = Field(..., description="Unit price")
    TaxableAmount: float = Field(..., description="Line total (Qty * UnitValue)")
    Notes: Optional[str] = Field(None, description="Line-level notes")


class ProcessOrderResponse(BaseModel):
    """API response for order processing."""
    mago4_flat_table: list[FlatTableRow] = Field(
        ...,
        description="Flattened order data in Mago4 format"
    )
    global_traffic_light: str = Field(
        ...,
        description="Overall confidence indicator (green/yellow/red)"
    )
    traffic_light_explanation: str = Field(
        ...,
        description="AI-generated explanation of what's missing or needs attention"
    )
    execution_log: list[str] = Field(
        ...,
        description="Step-by-step processing log with explanations"
    )
    ai_reasoning: Optional[dict] = Field(
        None,
        description="AI model's reasoning and thought process during extraction"
    )


class CustomerValidationResult(BaseModel):
    """Result of customer validation."""
    found: bool
    customer_code: Optional[str] = None
    payment_terms: Optional[str] = None
    message: str


class TranscodificationResult(BaseModel):
    """Result of item transcodification."""
    success: bool
    mago4_code: Optional[str] = None
    message: str


class PriceValidationResult(BaseModel):
    """Result of price validation."""
    standard_price: Optional[float] = None
    extracted_price: float
    variance_percentage: float
    message: str
