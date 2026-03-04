"""Validation service for customer, item, and price validation."""

from typing import Optional
from BE.models import (
    CustomerValidationResult,
    TranscodificationResult,
    PriceValidationResult,
    TrafficLight
)
from BE.mock_data import mock_customers, mock_transcodification, mock_price_list


def validate_customer(customer_name: str) -> CustomerValidationResult:
    """
    Lookup customer in mock master data.
    
    Args:
        customer_name: Customer company name
        
    Returns:
        CustomerValidationResult with found status and customer details
    """
    customer_data = mock_customers.get(customer_name)
    
    if customer_data:
        return CustomerValidationResult(
            found=True,
            customer_code=customer_data["code"],
            payment_terms=customer_data["payment_terms"],
            message=f"Customer '{customer_name}' mapped to code '{customer_data['code']}'"
        )
    else:
        return CustomerValidationResult(
            found=False,
            message=f"Customer '{customer_name}' not found in master data"
        )


def transcodify_item(
    base_code: Optional[str],
    color: Optional[str],
    thickness: Optional[str]
) -> TranscodificationResult:
    """
    Map customer item attributes to Mago4 item code.
    
    Args:
        base_code: Base material code (e.g., "MARMO", "CERAMICA")
        color: Material color
        thickness: Material thickness
        
    Returns:
        TranscodificationResult with success status and Mago4 code
    """
    # Handle missing attributes
    if not base_code or not color or not thickness:
        missing = []
        if not base_code:
            missing.append("base_code")
        if not color:
            missing.append("color")
        if not thickness:
            missing.append("thickness")
        return TranscodificationResult(
            success=False,
            message=f"Missing attributes for transcodification: {', '.join(missing)}"
        )
    
    # Lookup in transcodification table
    key = (base_code, color, thickness)
    mago4_code = mock_transcodification.get(key)
    
    if mago4_code:
        return TranscodificationResult(
            success=True,
            mago4_code=mago4_code,
            message=f"Item transcodified: {base_code}/{color}/{thickness} → {mago4_code}"
        )
    else:
        return TranscodificationResult(
            success=False,
            message=f"No transcodification found for: {base_code}/{color}/{thickness}"
        )


def validate_price(
    mago4_code: str,
    extracted_price: Optional[float]
) -> PriceValidationResult:
    """
    Compare extracted price to standard price list.
    
    Args:
        mago4_code: Internal Mago4 item code
        extracted_price: Price extracted from document
        
    Returns:
        PriceValidationResult with variance calculation
    """
    standard_price = mock_price_list.get(mago4_code)
    
    if not extracted_price:
        return PriceValidationResult(
            standard_price=standard_price,
            extracted_price=0.0,
            variance_percentage=0.0,
            message="No price extracted from document"
        )
    
    if not standard_price:
        return PriceValidationResult(
            standard_price=None,
            extracted_price=extracted_price,
            variance_percentage=0.0,
            message=f"No standard price found for item {mago4_code}"
        )
    
    # Calculate variance percentage
    variance = abs(extracted_price - standard_price) / standard_price * 100
    
    if variance == 0:
        message = f"Price validation: extracted {extracted_price:.2f} vs standard {standard_price:.2f} (perfect match)"
    else:
        message = f"Price validation: extracted {extracted_price:.2f} vs standard {standard_price:.2f} ({variance:.1f}% variance)"
    
    return PriceValidationResult(
        standard_price=standard_price,
        extracted_price=extracted_price,
        variance_percentage=variance,
        message=message
    )


def calculate_traffic_light(
    customer_valid: bool,
    all_items_transcodified: bool,
    max_price_variance: float,
    missing_critical_data: bool
) -> TrafficLight:
    """
    Determine overall confidence indicator based on validation results.
    
    Args:
        customer_valid: Whether customer was found in master data
        all_items_transcodified: Whether all items were successfully transcodified
        max_price_variance: Maximum price variance percentage across all items
        missing_critical_data: Whether any critical data (quantity) is missing
        
    Returns:
        TrafficLight status (GREEN, YELLOW, or RED)
    """
    # RED: Critical failures
    if not customer_valid or not all_items_transcodified or missing_critical_data:
        return TrafficLight.RED
    
    # GREEN: Perfect match
    if max_price_variance == 0:
        return TrafficLight.GREEN
    
    # YELLOW: Minor issues
    if max_price_variance < 5.0:
        return TrafficLight.YELLOW
    
    # RED: Significant price discrepancies
    return TrafficLight.RED
