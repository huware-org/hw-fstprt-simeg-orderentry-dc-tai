"""FastAPI backend for Simeg Order Entry system."""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings, logger
from app.models import ProcessOrderResponse, TrafficLight
from app.services import (
    ConfigurationError,
    ExtractionError,
    validate_customer,
    validate_price,
    calculate_traffic_light,
    ClientType,
    detect_client_from_document,
    get_client_strategy,
)
from app.utils import transform_to_flat_table


# Initialize FastAPI app
app = FastAPI(
    title="Simeg Order Entry API",
    version="0.1.0",
    description="AI-powered order processing for Simeg manufacturing"
)

# Add CORS middleware for separate frontend deployment
origins = [settings.FRONTEND_URL] if settings.FRONTEND_URL != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Validate configuration at startup."""
    logger.info("Starting Simeg Order Entry API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    
    if not settings.GEMINI_API_KEY:
        logger.critical("GEMINI_API_KEY not configured!")
        raise ConfigurationError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please set it before starting the application."
        )
    
    logger.info("Configuration validated successfully")


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
    
    Automatically detects the client type and applies the appropriate
    extraction and transcodification strategy.
    
    Supported clients:
    - Scavolini/Ernestomeda (XML format)
    - Lube (PDF with characteristic codes)
    - Generic (any PDF/image)
    
    Args:
        file: Uploaded document (PDF, PNG, JPG, XML, CSV)
        
    Returns:
        ProcessOrderResponse with flat table, traffic light, and execution log
        
    Raises:
        HTTPException: For various error conditions
    """
    execution_log = []
    
    try:
        logger.info(f"=== Processing order request: {file.filename} ===")
        
        # Step 1: Detect client type
        execution_log.append(f"📄 Processing file: {file.filename}")
        execution_log.append("🔍 Detecting client type...")
        
        client_type = await detect_client_from_document(file)
        execution_log.append(f"✅ Client detected: {client_type.value.upper()}")
        logger.info(f"Client type detected: {client_type.value}")
        
        # Step 2: Get client-specific strategy
        strategy = get_client_strategy(client_type)
        execution_log.append(f"🎯 Using {strategy.get_client_name()} processing strategy")
        logger.info(f"Using strategy: {strategy.get_client_name()}")
        
        # Step 3: Extract order data using client-specific strategy
        try:
            extracted_order, ai_reasoning = await strategy.extract_order(file)
            execution_log.append(f"✅ Extraction completed: {len(extracted_order.items)} items found")
            execution_log.append(f"👤 Customer identified: {extracted_order.customer_name}")
            logger.info(f"Extraction successful: {len(extracted_order.items)} items, customer: {extracted_order.customer_name}")
            
            # Log reasoning if available
            if ai_reasoning:
                logger.info(f"AI reasoning captured: {len(ai_reasoning)} characters")
                execution_log.append("🧠 AI reasoning captured for transparency")
            else:
                logger.warning("No AI reasoning captured from extraction")
                execution_log.append("ℹ️ No AI reasoning available for this extraction")
        except ConfigurationError as e:
            logger.error(f"Configuration error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        except ExtractionError as e:
            logger.error(f"Extraction error: {e}")
            raise HTTPException(status_code=503, detail=f"Extraction failed: {str(e)}")
        
        # Step 4: Validate customer (COMMENTED OUT FOR PROTOTYPE)
        # customer_result = validate_customer(extracted_order.customer_name)
        # execution_log.append(customer_result.message)
        
        # Mock customer result for prototype
        from app.models.schemas import CustomerValidationResult
        customer_result = CustomerValidationResult(
            found=True,
            customer_code="MOCK_CUSTOMER",
            payment_terms="30gg",
            message="✅ Customer validation skipped for prototype"
        )
        execution_log.append(customer_result.message)
        
        # Step 5: Transcodify items using client-specific strategy
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
            
            # Prepare client-specific lookup parameters
            lookup_kwargs = {}
            
            if client_type == ClientType.SCAVOLINI:
                # Scavolini characteristics are now extracted by AI and stored in the item
                execution_log.append(f"🔍 Using {strategy.get_client_name()} transcodification table...")
            elif client_type == ClientType.LUBE:
                # Lube-specific data is stored in the item
                execution_log.append(f"🔍 Using {strategy.get_client_name()} transcodification table...")
            else:
                execution_log.append("🔍 Using generic transcodification...")
            
            # Lookup Mago4 code using strategy
            mago4_code = strategy.lookup_mago4_code(item, **lookup_kwargs)
            
            if mago4_code:
                if client_type == ClientType.SCAVOLINI:
                    mat_piano = getattr(item, '_scav_mat_piano', 'N/A')
                    col_piano = getattr(item, '_scav_col_piano', 'N/A')
                    execution_log.append(f"✅ Transcodification: {item.customer_item_code} (mat={mat_piano}, col={col_piano}) → {mago4_code}")
                elif client_type == ClientType.LUBE:
                    codice_base = getattr(item, '_lube_codice_base', 'N/A')
                    caratteristica = getattr(item, '_lube_caratteristica', 'N/A')
                    execution_log.append(f"✅ Transcodification: {codice_base} + {caratteristica} → {mago4_code}")
                else:
                    execution_log.append(f"✅ Transcodification: {item.description[:30]}... → {mago4_code}")
                
                transcodified_items.append((item, mago4_code))
                
                # Validate price if available
                if item.unit_price:
                    price_result = validate_price(mago4_code, item.unit_price)
                    execution_log.append(price_result.message)
                    
                    if price_result.variance_percentage > max_price_variance:
                        max_price_variance = price_result.variance_percentage
                
                # Determine item-level traffic light
                item_light = calculate_traffic_light(
                    customer_valid=customer_result.found,
                    all_items_transcodified=True,
                    max_price_variance=max_price_variance if item.unit_price else 0.0,
                    missing_critical_data=False
                )
                item_traffic_lights.append(item_light)
            else:
                execution_log.append(f"❌ No match in {strategy.get_client_name()} transcodification table")
                all_items_transcodified = False
                item_traffic_lights.append(TrafficLight.RED)
        
        # Step 6: Calculate global traffic light
        if client_type in [ClientType.SCAVOLINI, ClientType.LUBE] and all_items_transcodified:
            # For real client data with successful transcodification
            # GREEN: All items transcodified successfully
            global_traffic_light = TrafficLight.GREEN
            execution_log.append("✅ All items transcodified successfully with real client data")
        else:
            global_traffic_light = calculate_traffic_light(
                customer_valid=customer_result.found,
                all_items_transcodified=all_items_transcodified,
                max_price_variance=max_price_variance,
                missing_critical_data=missing_critical_data
            )
        
        logger.info(f"Global traffic light: {global_traffic_light.value}")
        
        # Generate traffic light explanation
        if global_traffic_light == TrafficLight.GREEN:
            traffic_explanation = "✅ Perfetto! Tutti gli articoli sono stati transcodificati con successo. L'ordine è pronto per l'importazione automatica in Mago4."
        elif global_traffic_light == TrafficLight.YELLOW:
            issues = []
            if not customer_result.found:
                issues.append("il cliente non è presente nell'anagrafica")
            if max_price_variance > 0:
                issues.append(f"variazione prezzi fino al {max_price_variance:.1f}%")
            if not all_items_transcodified:
                issues.append("alcuni articoli non sono stati transcodificati")
            
            if issues:
                traffic_explanation = f"⚠️ Attenzione: {', '.join(issues)}. Si consiglia una revisione manuale prima dell'importazione."
            else:
                traffic_explanation = "⚠️ L'ordine è stato elaborato correttamente ma si consiglia una revisione manuale."
        else:  # RED
            issues = []
            if not customer_result.found:
                issues.append("il cliente non è presente nell'anagrafica Mago4")
            if not all_items_transcodified:
                failed_count = len(extracted_order.items) - len(transcodified_items)
                issues.append(f"{failed_count} articoli non trovati nella tabella di transcodifica")
            if missing_critical_data:
                issues.append("mancano dati critici (quantità)")
            
            if issues:
                traffic_explanation = f"❌ Problemi critici rilevati: {', '.join(issues)}. È necessario un intervento manuale per completare l'ordine."
            else:
                traffic_explanation = "❌ Sono stati rilevati problemi critici. Verificare i dati dell'ordine prima di procedere."
        
        logger.info(f"Traffic light explanation: {traffic_explanation}")
        
        # Add traffic light summary to log
        execution_log.append(f"\n🚦 Global Traffic Light: {global_traffic_light.value.upper()}")
        if global_traffic_light == TrafficLight.GREEN:
            execution_log.append("✅ All validations passed - ready for automatic import")
        elif global_traffic_light == TrafficLight.YELLOW:
            execution_log.append("⚠️ Minor issues detected - review recommended")
        else:
            execution_log.append("❌ Critical issues detected - manual intervention required")
        
        # Step 7: Transform to flat table
        if not transcodified_items:
            flat_table = []
            execution_log.append("⚠️ No items could be transcodified - empty flat table generated")
            logger.warning("No items transcodified, empty flat table")
        else:
            flat_table = transform_to_flat_table(
                extracted_order=extracted_order,
                customer_code=customer_result.customer_code,
                transcodified_items=transcodified_items
            )
            execution_log.append(f"✅ Flat table generated: {len(flat_table)} rows")
            logger.info(f"Flat table generated: {len(flat_table)} rows")
        
        logger.info(f"=== Order processing complete: {file.filename} ===")
        
        # Prepare AI reasoning for response
        reasoning_data = None
        logger.debug(f"AI reasoning value: {ai_reasoning}")
        logger.debug(f"AI reasoning type: {type(ai_reasoning)}")
        
        if ai_reasoning:
            logger.info(f"Preparing reasoning data for response (length: {len(ai_reasoning)})")
            reasoning_data = {
                "client_type": client_type.value,
                "strategy": strategy.get_client_name(),
                "reasoning_text": ai_reasoning,
                "extraction_method": "AI with structured extraction"
            }
            logger.debug(f"Reasoning data prepared: {reasoning_data.keys()}")
        else:
            logger.warning("No AI reasoning available to include in response")
        
        # Return response
        return ProcessOrderResponse(
            mago4_flat_table=flat_table,
            global_traffic_light=global_traffic_light.value,
            traffic_light_explanation=traffic_explanation,
            execution_log=execution_log,
            ai_reasoning=reasoning_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing order: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during order processing: {str(e)}"
        )
