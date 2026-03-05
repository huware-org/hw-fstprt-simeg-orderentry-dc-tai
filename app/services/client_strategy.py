"""Client-specific strategy pattern for order processing."""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, List
from fastapi import UploadFile
from app.models.schemas import ExtractedOrder, ExtractedItem
from app.services.client_detector import ClientType
from app.config.settings import logger


class ClientStrategy(ABC):
    """Abstract base class for client-specific processing strategies."""
    
    @abstractmethod
    async def extract_order(self, file: UploadFile) -> tuple[ExtractedOrder, Optional[str]]:
        """
        Extract order data from document using client-specific logic.
        
        Args:
            file: Uploaded document file
            
        Returns:
            Tuple of (ExtractedOrder, reasoning_text)
        """
        pass
    
    @abstractmethod
    def lookup_mago4_code(self, item: ExtractedItem, **kwargs) -> Optional[str]:
        """
        Lookup Mago4 code using client-specific transcodification table.
        
        Args:
            item: Extracted item
            **kwargs: Additional client-specific parameters
            
        Returns:
            Mago4 code if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_client_name(self) -> str:
        """Get the client name for logging."""
        pass


class ScavoliniStrategy(ClientStrategy):
    """Strategy for Scavolini/Ernestomeda orders."""
    
    async def extract_order(self, file: UploadFile) -> tuple[ExtractedOrder, Optional[str]]:
        """Extract Scavolini order using AI extraction from XML."""
        from app.services.extraction_service import extract_scavolini_order_from_document
        
        logger.info("Extracting Scavolini order using AI from XML")
        
        # Extract using Scavolini-specific AI model
        scavolini_order, reasoning = await extract_scavolini_order_from_document(file)
        logger.info(f"Scavolini extraction complete: {len(scavolini_order.items)} items")
        logger.debug(f"Reasoning from extraction: {reasoning is not None}")
        
        # Convert to generic ExtractedOrder for compatibility
        items = []
        for idx, scav_item in enumerate(scavolini_order.items, 1):
            logger.debug(f"Processing Scavolini item {idx}: {scav_item.customer_item_code}")
            
            # Build description with reasoning if available
            description = scav_item.description
            if scav_item.reasoning:
                description += f" | AI: {scav_item.reasoning}"
            
            item = ExtractedItem(
                customer_item_code=scav_item.customer_item_code,
                description=description,
                color=scav_item.color,
                thickness=scav_item.thickness,
                quantity=scav_item.quantity,
                unit_price=scav_item.unit_price,
                discount_percentage=None
            )
            # Store Scavolini-specific characteristic codes for transcodification
            item._scav_mat_piano = scav_item.mat_piano
            item._scav_col_piano = scav_item.col_piano
            item._scav_fin_piano = scav_item.fin_piano
            item._scav_prof_piano = scav_item.prof_piano
            items.append(item)
        
        order = ExtractedOrder(
            customer_name=scavolini_order.customer_name,
            customer_address=scavolini_order.customer_address,
            order_number=scavolini_order.order_number,
            order_date=scavolini_order.order_date,
            delivery_date=scavolini_order.delivery_date,
            payment_terms_requested=None,
            notes=scavolini_order.notes,
            items=items
        )
        
        logger.debug(f"Returning order with reasoning: {reasoning is not None}")
        return order, reasoning
    
    def lookup_mago4_code(self, item: ExtractedItem, **kwargs) -> Optional[str]:
        """Lookup using Scavolini transcodification table."""
        from app.services.xml_processor import lookup_scavolini_mago4_code
        
        # Extract Scavolini-specific characteristic codes
        mat_piano = getattr(item, '_scav_mat_piano', None) or kwargs.get('mat_piano')
        col_piano = getattr(item, '_scav_col_piano', None) or kwargs.get('col_piano')
        fin_piano = getattr(item, '_scav_fin_piano', None) or kwargs.get('fin_piano')
        prof_piano = getattr(item, '_scav_prof_piano', None) or kwargs.get('prof_piano')
        cod_art_cliente = kwargs.get('cod_art_cliente') or item.customer_item_code
        
        logger.debug(f"Looking up Scavolini code for item: {item.customer_item_code}")
        logger.debug(f"Characteristics: mat={mat_piano}, col={col_piano}, fin={fin_piano}, prof={prof_piano}")
        
        result = lookup_scavolini_mago4_code(
            cod_art_cliente=cod_art_cliente,
            mat_piano=mat_piano,
            col_piano=col_piano,
            fin_piano=fin_piano,
            prof_piano=prof_piano
        )
        
        if result:
            logger.debug(f"Found Scavolini Mago4 code: {result}")
        else:
            logger.warning(f"No Scavolini match for item: {item.customer_item_code}")
        
        return result
    
    def get_client_name(self) -> str:
        return "Scavolini/Ernestomeda"


class LubeStrategy(ClientStrategy):
    """Strategy for Lube orders."""
    
    async def extract_order(self, file: UploadFile) -> tuple[ExtractedOrder, Optional[str]]:
        """Extract Lube order using AI with strict enum validation."""
        from app.services.extraction_service import extract_lube_order_from_document
        from app.models.schemas import ExtractedItem
        
        logger.info("Extracting Lube order with enum validation")
        
        # Extract using Lube-specific model
        lube_order, reasoning = await extract_lube_order_from_document(file)
        logger.info(f"Lube extraction complete: {len(lube_order.items)} items")
        logger.debug(f"Reasoning from extraction: {reasoning is not None}, type: {type(reasoning) if reasoning else 'None'}")
        
        # Convert to generic ExtractedOrder for compatibility
        items = []
        for idx, lube_item in enumerate(lube_order.items, 1):
            logger.debug(f"Processing Lube item {idx}: {lube_item.codice_base} + {lube_item.caratteristica}")
            
            # Build description with reasoning
            description = f"Lube {lube_item.codice_base} with {lube_item.caratteristica}"
            if lube_item.reasoning:
                description += f" | AI: {lube_item.reasoning}"
            
            item = ExtractedItem(
                customer_item_code=f"{lube_item.codice_base}_{lube_item.caratteristica}",
                description=description,
                color=None,
                thickness=None,
                quantity=lube_item.quantita,
                unit_price=None,
                discount_percentage=None
            )
            # Store Lube-specific data in a way we can retrieve it
            item._lube_codice_base = lube_item.codice_base
            item._lube_caratteristica = lube_item.caratteristica
            items.append(item)
        
        order = ExtractedOrder(
            customer_name=lube_order.customer_name,
            customer_address=None,
            order_number=lube_order.order_number,
            order_date=lube_order.order_date,
            delivery_date=lube_order.delivery_date,
            payment_terms_requested=None,
            notes=lube_order.notes,
            items=items
        )
        
        logger.debug(f"Returning order with reasoning: {reasoning is not None}")
        return order, reasoning
    
    def lookup_mago4_code(self, item: ExtractedItem, **kwargs) -> Optional[str]:
        """Lookup using Lube transcodification table."""
        from app.services.xml_processor import lookup_lube_mago4_code
        
        # Extract Lube-specific data
        codice_base = getattr(item, '_lube_codice_base', None) or kwargs.get('codice_base')
        caratteristica = getattr(item, '_lube_caratteristica', None) or kwargs.get('caratteristica')
        
        if not codice_base or not caratteristica:
            logger.warning(f"Missing Lube data for item: {item.customer_item_code}")
            return None
        
        logger.debug(f"Looking up Lube code: {codice_base} + {caratteristica}")
        
        result = lookup_lube_mago4_code(
            codice_base=codice_base,
            caratteristica=caratteristica
        )
        
        if result:
            logger.debug(f"Found Lube Mago4 code: {result}")
        else:
            logger.warning(f"No Lube match for: {codice_base} + {caratteristica}")
        
        return result
    
    def get_client_name(self) -> str:
        return "Lube"


class GenericStrategy(ClientStrategy):
    """Strategy for generic/unknown clients."""
    
    async def extract_order(self, file: UploadFile) -> tuple[ExtractedOrder, Optional[str]]:
        """Extract order using generic AI extraction."""
        from app.services.extraction_service import extract_order_from_document
        
        logger.info("Extracting order using generic strategy")
        order, reasoning = await extract_order_from_document(file)
        logger.info(f"Generic extraction complete: {len(order.items)} items")
        return order, reasoning
    
    def lookup_mago4_code(self, item: ExtractedItem, **kwargs) -> Optional[str]:
        """Lookup using mock/generic transcodification."""
        from app.services.validation_service import transcodify_item
        
        logger.debug(f"Using generic transcodification for: {item.description[:50]}")
        
        # Extract base code from description (simple heuristic)
        base_code = None
        description_upper = item.description.upper()
        if "MARMO" in description_upper:
            base_code = "MARMO"
        elif "CERAMICA" in description_upper:
            base_code = "CERAMICA"
        elif "GRANITO" in description_upper:
            base_code = "GRANITO"
        elif "BRECCIA" in description_upper:
            base_code = "BRECCIA"
        
        result = transcodify_item(base_code, item.color, item.thickness)
        
        if result.success:
            logger.debug(f"Generic transcodification successful: {result.mago4_code}")
        else:
            logger.warning(f"Generic transcodification failed for: {item.description[:50]}")
        
        return result.mago4_code if result.success else None
    
    def get_client_name(self) -> str:
        return "Generic"


def get_client_strategy(client_type: ClientType) -> ClientStrategy:
    """
    Factory function to get the appropriate client strategy.
    
    Args:
        client_type: Type of client detected
        
    Returns:
        ClientStrategy instance for the client
    """
    strategies = {
        ClientType.SCAVOLINI: ScavoliniStrategy(),
        ClientType.LUBE: LubeStrategy(),
        ClientType.GENERIC: GenericStrategy(),
    }
    
    return strategies.get(client_type, GenericStrategy())
