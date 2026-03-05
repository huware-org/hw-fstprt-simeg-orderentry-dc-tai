"""Business logic services."""

from app.services.extraction_service import (
    extract_order_from_document,
    extract_lube_order_from_document,
    ConfigurationError,
    ExtractionError,
)
from app.services.validation_service import (
    validate_customer,
    transcodify_item,
    validate_price,
    calculate_traffic_light,
)
from app.services.xml_processor import (
    parse_scavolini_xml,
    lookup_scavolini_mago4_code,
    lookup_lube_mago4_code,
)
from app.services.client_detector import (
    ClientType,
    detect_client_from_document,
    ClientDetectionError,
)
from app.services.client_strategy import (
    ClientStrategy,
    get_client_strategy,
)

__all__ = [
    "extract_order_from_document",
    "extract_lube_order_from_document",
    "ConfigurationError",
    "ExtractionError",
    "validate_customer",
    "transcodify_item",
    "validate_price",
    "calculate_traffic_light",
    "parse_scavolini_xml",
    "lookup_scavolini_mago4_code",
    "lookup_lube_mago4_code",
    "ClientType",
    "detect_client_from_document",
    "ClientDetectionError",
    "ClientStrategy",
    "get_client_strategy",
]
