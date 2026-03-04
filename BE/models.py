"""Pydantic data models for the Simeg Order Entry system."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


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
    order_date: Optional[str] = Field(
        None,
        description="Order date in ISO format (YYYY-MM-DD)"
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
    execution_log: list[str] = Field(
        ...,
        description="Step-by-step processing log with explanations"
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
