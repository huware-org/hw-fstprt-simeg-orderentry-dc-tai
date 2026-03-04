# Implementation Plan: Simeg Intelligent Order Entry Prototype

## Overview

This implementation plan creates a working prototype with a FastAPI backend and Gradio frontend for AI-powered order processing. The system extracts structured data from unstructured documents using Google Gemini, applies business validation logic with mock master data, and outputs Mago4 ERP-ready flat tables with traffic light confidence indicators.

## Tasks

- [x] 1. Set up project structure and environment
  - Create BE/ and FE/ directories
  - Create pyproject.toml with uv configuration
  - Add dependencies: fastapi, uvicorn, pydantic, google-genai, python-multipart, gradio, pandas, requests, pytest, hypothesis
  - Create .env.example file with GEMINI_API_KEY placeholder
  - Create .gitignore for Python projects
  - _Requirements: 10.1, 10.2_

- [x] 2. Implement Pydantic data models
  - [x] 2.1 Create BE/models.py with all data models
    - Define ExtractedItem model with customer_item_code, description, color, thickness, quantity, unit_price, discount_percentage
    - Define ExtractedOrder model with customer_name, customer_address, order_date, payment_terms_requested, notes, items
    - Define FlatTableRow model with service fields (Id, CreatedDate, Processed), header fields (H_ prefix), and line item fields
    - Define ProcessOrderResponse model with mago4_flat_table, global_traffic_light, execution_log
    - Define TrafficLight enum (GREEN, YELLOW, RED)
    - Define validation result models: CustomerValidationResult, TranscodificationResult, PriceValidationResult
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

- [x] 3. Create mock master data
  - [x] 3.1 Create BE/mock_data.py with hardcoded dictionaries
    - Define mock_customers mapping customer names to codes, payment terms, addresses
    - Define mock_transcodification mapping (base_code, color, thickness) tuples to Mago4 item codes
    - Define mock_price_list mapping Mago4 item codes to standard unit prices
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [x] 4. Implement validation service
  - [x] 4.1 Create BE/validation_service.py with validation functions
    - Implement validate_customer() to lookup customer in mock_customers
    - Implement transcodify_item() to lookup item attributes in mock_transcodification
    - Implement validate_price() to compare extracted price vs standard price and calculate variance
    - Implement calculate_traffic_light() with Green/Yellow/Red logic based on validation results
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 4.2 Write property test for customer validation
    - **Property 4: Customer lookup execution**
    - **Validates: Requirements 3.3, 3.4**

  - [ ]* 4.3 Write property test for item transcodification
    - **Property 5: Item transcodification execution**
    - **Validates: Requirements 4.3, 4.4**

  - [ ]* 4.4 Write property test for price validation
    - **Property 7: Price validation execution**
    - **Validates: Requirements 5.3, 5.4, 5.5**

  - [ ]* 4.5 Write property tests for traffic light assignment
    - **Property 8: Green traffic light assignment**
    - **Property 9: Yellow traffic light assignment**
    - **Property 10: Red traffic light assignment**
    - **Property 11: Traffic light worst-case aggregation**
    - **Validates: Requirements 6.2, 6.3, 6.4, 6.5**

  - [ ]* 4.6 Write unit tests for validation service
    - Test successful customer lookup with known customer
    - Test customer not found scenario
    - Test successful transcodification with known item
    - Test transcodification failure with unknown item
    - Test Green assignment with perfect match
    - Test Yellow assignment with minor price variance
    - Test Red assignment with missing customer
    - Test worst-case aggregation with mixed statuses
    - _Requirements: 3.3, 3.4, 4.3, 4.4, 6.2, 6.3, 6.4, 6.5_

- [x] 5. Implement flat table transformer
  - [x] 5.1 Create BE/flat_table_transformer.py
    - Implement transform_to_flat_table() function
    - Generate unique Id (UUID) for each row
    - Set CreatedDate to current timestamp in ISO format
    - Set Processed to 0
    - Repeat header fields (H_ExternalOrdNo, H_OrderDate, H_ConfirmedDeliveryDate, H_Notes, H_Currency) on all rows
    - Create one row per line item with Item (Mago4 code), Description, Qty, UoM, UnitValue, TaxableAmount, Notes
    - Calculate TaxableAmount as Qty * UnitValue
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10_

  - [ ]* 5.2 Write property test for flat table schema compliance
    - **Property 13: Flat table schema compliance**
    - **Validates: Requirements 7.2, 7.3, 7.5**

  - [ ]* 5.3 Write property test for header field repetition
    - **Property 14: Header field repetition**
    - **Validates: Requirements 7.4**

  - [ ]* 5.4 Write property test for line item cardinality
    - **Property 15: Line item cardinality preservation**
    - **Validates: Requirements 7.6**

  - [ ]* 5.5 Write property test for TaxableAmount calculation
    - **Property 17: TaxableAmount calculation correctness**
    - **Validates: Requirements 7.8**

  - [ ]* 5.6 Write unit tests for flat table transformer
    - Test single line item order transformation
    - Test multi-line item order transformation
    - Test header field repetition across rows
    - Test TaxableAmount calculation
    - Test default field values (Processed=0, CreatedDate)
    - _Requirements: 7.4, 7.6, 7.8, 7.9, 7.10_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement AI extraction service
  - [x] 7.1 Create BE/extraction_service.py with Gemini integration
    - Implement extract_order_from_document() async function
    - Load GEMINI_API_KEY from environment variable
    - Detect file type (PDF, image, XML, CSV)
    - For PDF/image: send file directly to Gemini with vision capabilities
    - For XML/CSV: extract text content and send to Gemini
    - Provide Italian system prompt for marble/ceramic order extraction
    - Pass ExtractedOrder Pydantic schema to Gemini for structured output
    - Handle Gemini API errors with appropriate error messages
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 10.1, 10.2, 10.3_

  - [ ]* 7.2 Write property test for extraction schema conformance
    - **Property 3: Extraction response schema conformance**
    - **Validates: Requirements 2.7**

  - [ ]* 7.3 Write unit tests for extraction service
    - Test missing GEMINI_API_KEY raises ConfigurationError
    - Test file type detection for PDF, image, XML, CSV
    - Test error handling for Gemini API failures
    - _Requirements: 10.2, 2.1, 2.3, 2.4_

- [x] 8. Implement FastAPI backend
  - [x] 8.1 Create BE/main.py with FastAPI application
    - Initialize FastAPI app with title and version
    - Validate GEMINI_API_KEY at startup
    - Implement POST /api/v1/process-order endpoint
    - Accept UploadFile parameter
    - Orchestrate workflow: extract → validate customer → transcodify items → validate prices → calculate traffic light → transform to flat table
    - Build execution_log with step-by-step explanations
    - Return ProcessOrderResponse with mago4_flat_table, global_traffic_light, execution_log
    - Handle errors with appropriate HTTP status codes (400, 422, 500, 503)
    - Add CORS middleware for Gradio frontend communication
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 6.6_

  - [ ]* 8.2 Write property test for API response structure
    - **Property 19: API response structure completeness**
    - **Validates: Requirements 8.3, 8.4, 8.5, 8.6**

  - [ ]* 8.3 Write unit tests for API endpoint
    - Test successful order processing returns 200
    - Test response contains all required fields
    - Test response validates against ProcessOrderResponse schema
    - Test invalid file type returns 400 error
    - Test Pydantic validation failure returns 422 error
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 9. Implement Gradio frontend
  - [x] 9.1 Create FE/app.py with Gradio UI
    - Create file upload component accepting PDF, PNG, JPG, XML, CSV
    - Create submit button to trigger processing
    - Implement process_order() function to call backend API at http://127.0.0.1:8000/api/v1/process-order
    - Parse API response and extract mago4_flat_table, global_traffic_light, execution_log
    - Display traffic light status with visual indicators (🔴 Red, 🟡 Yellow, 🟢 Green)
    - Display execution log in text component
    - Display flat table using gr.Dataframe component
    - Handle API errors and display error messages
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 9.2 Write integration test for frontend-backend communication
    - Test file upload and API call
    - Test response parsing and display
    - _Requirements: 1.6, 9.5_

- [x] 10. Create project documentation
  - [x] 10.1 Create README.md with setup and usage instructions
    - Document prerequisites (Python 3.11+, uv, Gemini API key)
    - Document installation steps using uv
    - Document how to set GEMINI_API_KEY environment variable
    - Document how to run backend (uvicorn BE.main:app)
    - Document how to run frontend (python FE/app.py)
    - Document project structure
    - Document API endpoint details
    - _Requirements: 10.1, 10.2_

- [x] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The backend must be running before starting the frontend
- Gemini API key is required for document processing functionality
