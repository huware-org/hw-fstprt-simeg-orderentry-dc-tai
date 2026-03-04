"""FastAPI backend for Simeg Order Entry system."""

import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from BE.models import ProcessOrderResponse, TrafficLight
from BE.extraction_service import extract_order_from_document, ConfigurationError, ExtractionError
from BE.validation_service import validate_customer, transcodify_item, validate_price, calculate_traffic_light
from BE.flat_table_transformer import transform_to_flat_table
from BE.xml_processor import parse_scavolini_xml, lookup_scavolini_mago4_code
import xml.etree.ElementTree as ET


# Initialize FastAPI app
app = FastAPI(
    title="Simeg Order Entry API",
    version="0.1.0",
    description="AI-powered order processing for Simeg manufacturing"
)

# Add CORS middleware for Gradio frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Validate configuration at startup."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ConfigurationError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please set it before starting the application."
        )


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Simeg Order Entry API",
        "version": "0.1.0"
    }


@app.post("/api/v1/process-order", response_model=ProcessOrderResponse)
async def process_order(file: UploadFile = File(...)):
    """
    Process an order document and return Mago4 flat table.
    
    Args:
        file: Uploaded document (PDF, PNG, JPG, XML, CSV)
        
    Returns:
        ProcessOrderResponse with flat table, traffic light, and execution log
        
    Raises:
        HTTPException: For various error conditions
    """
    execution_log = []
    
    try:
        # Step 1: Detect file type
        execution_log.append(f"📄 Processing file: {file.filename}")
        
        is_xml = file.filename and file.filename.lower().endswith('.xml')
        
        # Step 2: Extract order data
        if is_xml:
            # Process Scavolini XML directly
            execution_log.append("🔧 Detected Scavolini/Ernestomeda XML format")
            content = await file.read()
            
            # Try to detect encoding from XML declaration or use common encodings
            try:
                # First try UTF-8
                xml_content = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    # Try ISO-8859-1 (Latin-1) - common for Italian XML files
                    xml_content = content.decode('iso-8859-1')
                    execution_log.append("📝 Using ISO-8859-1 encoding")
                except UnicodeDecodeError:
                    try:
                        # Try Windows-1252 as fallback
                        xml_content = content.decode('windows-1252')
                        execution_log.append("📝 Using Windows-1252 encoding")
                    except UnicodeDecodeError:
                        raise HTTPException(status_code=400, detail="Unable to decode XML file. Unsupported encoding.")
            
            try:
                # Use AI extraction for customer name (more flexible)
                use_ai_extraction = True  # Can be made configurable
                if use_ai_extraction:
                    execution_log.append("🤖 Using AI to extract customer name from XML")
                else:
                    execution_log.append("📋 Using direct XML parsing for customer name")
                
                extracted_order = parse_scavolini_xml(xml_content, use_ai_extraction=use_ai_extraction)
                execution_log.append(f"✅ XML parsing completed: {len(extracted_order.items)} items found")
                execution_log.append(f"👤 Customer identified: {extracted_order.customer_name}")
                
                # Parse XML again to extract characteristics for transcodification
                root = ET.fromstring(xml_content)
                item_characteristics = []
                for dettaglio in root.findall('.//DETTAGLIO'):
                    chars = {}
                    cod_art = dettaglio.find('COD_ART_CLIENTE')
                    if cod_art is not None and cod_art.text:
                        chars['cod_art_cliente'] = cod_art.text
                    
                    for car in dettaglio.findall('.//CARATTERISTICA'):
                        cod_nome = car.find('COD_NOME')
                        cod_valore = car.find('COD_VALORE')
                        if cod_nome is not None and cod_valore is not None:
                            if cod_nome.text and cod_valore.text:
                                chars[cod_nome.text] = cod_valore.text
                    
                    item_characteristics.append(chars)
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"XML parsing failed: {str(e)}")
        else:
            # Use AI extraction for PDF/images
            try:
                extracted_order = await extract_order_from_document(file)
                execution_log.append(f"✅ AI extraction completed: {len(extracted_order.items)} items found")
                item_characteristics = None
            except ConfigurationError as e:
                raise HTTPException(status_code=500, detail=str(e))
            except ExtractionError as e:
                raise HTTPException(status_code=503, detail=f"AI extraction failed: {str(e)}")
        
        # Step 2: Validate customer
        customer_result = validate_customer(extracted_order.customer_name)
        execution_log.append(customer_result.message)
        
        # Step 3: Transcodify items and validate prices
        transcodified_items = []
        item_traffic_lights = []
        max_price_variance = 0.0
        all_items_transcodified = True
        missing_critical_data = False
        
        for idx, item in enumerate(extracted_order.items, 1):
            execution_log.append(f"\n--- Item {idx}: {item.description} ---")
            
            # Check for missing quantity (critical data)
            if item.quantity <= 0:
                missing_critical_data = True
                execution_log.append("❌ Critical: Missing or invalid quantity")
            
            # Try Scavolini transcodification first if XML
            mago4_code = None
            if is_xml and item_characteristics and idx <= len(item_characteristics):
                chars = item_characteristics[idx - 1]
                execution_log.append("🔍 Using Scavolini transcodification table...")
                
                mago4_code = lookup_scavolini_mago4_code(
                    cod_art_cliente=chars.get('cod_art_cliente'),
                    mat_piano=chars.get('C_MATPIANO'),
                    col_piano=chars.get('C_COLPIANO'),
                    fin_piano=chars.get('C_FINPIANO'),
                    prof_piano=chars.get('C_PROFPIANO')
                )
                
                if mago4_code:
                    execution_log.append(f"✅ Scavolini transcodification: {chars.get('cod_art_cliente')} → {mago4_code}")
                    transcodified_items.append((item, mago4_code))
                else:
                    execution_log.append(f"❌ No match in Scavolini table for: {chars.get('cod_art_cliente')}")
                    all_items_transcodified = False
            
            # Fallback to mock transcodification for non-XML or failed lookups
            if not mago4_code:
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
                
                # Transcodify item using mock data
                transcode_result = transcodify_item(base_code, item.color, item.thickness)
                execution_log.append(transcode_result.message)
                
                if transcode_result.success:
                    mago4_code = transcode_result.mago4_code
                    transcodified_items.append((item, mago4_code))
                else:
                    all_items_transcodified = False
                    item_traffic_lights.append(TrafficLight.RED)
                    continue
            
            # Validate price
            if mago4_code:
                price_result = validate_price(mago4_code, item.unit_price)
                execution_log.append(price_result.message)
                
                # Track max price variance
                if price_result.variance_percentage > max_price_variance:
                    max_price_variance = price_result.variance_percentage
                
                # Determine item-level traffic light
                item_light = calculate_traffic_light(
                    customer_valid=customer_result.found,
                    all_items_transcodified=True,
                    max_price_variance=price_result.variance_percentage,
                    missing_critical_data=False
                )
                item_traffic_lights.append(item_light)
        
        # Step 4: Calculate global traffic light
        # For Scavolini XML with successful transcodification, be more lenient about missing prices
        if is_xml and all_items_transcodified:
            execution_log.append("\n💡 Note: Using real Scavolini transcodification data (price validation skipped)")
            # If all items transcodified successfully, assign YELLOW instead of RED for missing prices
            if customer_result.found:
                global_traffic_light = TrafficLight.YELLOW
            else:
                global_traffic_light = TrafficLight.RED
        else:
            global_traffic_light = calculate_traffic_light(
                customer_valid=customer_result.found,
                all_items_transcodified=all_items_transcodified,
                max_price_variance=max_price_variance,
                missing_critical_data=missing_critical_data
            )
        
        # Add traffic light summary to log
        execution_log.append(f"\n🚦 Global Traffic Light: {global_traffic_light.value.upper()}")
        if global_traffic_light == TrafficLight.GREEN:
            execution_log.append("✅ All validations passed - ready for automatic import")
        elif global_traffic_light == TrafficLight.YELLOW:
            execution_log.append("⚠️ Minor issues detected - review recommended")
        else:
            execution_log.append("❌ Critical issues detected - manual intervention required")
        
        # Step 5: Transform to flat table
        if not transcodified_items:
            # If no items were transcodified, create empty flat table
            flat_table = []
            execution_log.append("⚠️ No items could be transcodified - empty flat table generated")
        else:
            flat_table = transform_to_flat_table(
                extracted_order=extracted_order,
                customer_code=customer_result.customer_code,
                transcodified_items=transcodified_items
            )
            execution_log.append(f"✅ Flat table generated: {len(flat_table)} rows")
        
        # Return response
        return ProcessOrderResponse(
            mago4_flat_table=flat_table,
            global_traffic_light=global_traffic_light.value,
            execution_log=execution_log
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during order processing: {str(e)}"
        )
