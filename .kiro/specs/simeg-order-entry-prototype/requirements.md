# Requirements Document

## Introduction

The Simeg Intelligent Order Entry system is a Pre-PoC prototype for an Italian manufacturing company that demonstrates AI-powered order processing. The system accepts unstructured or semi-structured order documents in various formats (PDF, images, XML, CSV), extracts structured order data using Google Gemini AI, applies business logic including N:1 transcodification using mock master data, and outputs a Mago4 ERP-ready "Flat Table" (Tabella Piana) with validation confidence indicators.

## Glossary

- **System**: The Simeg Intelligent Order Entry prototype application
- **Gradio_UI**: The web-based user interface component built with Gradio
- **FastAPI_Backend**: The REST API server component built with FastAPI
- **Gemini_AI**: The Google Gemini AI service used for document processing
- **Mago4**: The target ERP system that will receive the processed order data
- **Flat_Table**: The flattened row-based data structure (Tabella Piana) required by Mago4
- **Traffic_Light**: The validation confidence indicator (Green/Yellow/Red)
- **Mock_Master_Data**: Hardcoded dictionaries simulating ERP master data (customers, transcodification, price lists)
- **Transcodification**: The process of mapping customer item codes and attributes to internal Mago4 item codes (N:1 mapping)
- **Bridge_Table**: The intermediate table structure used to import orders into Mago4

## Requirements

### Requirement 1: Document Upload Interface

**User Story:** As an order entry operator, I want to upload order documents in various formats, so that I can process orders regardless of how customers submit them.

#### Acceptance Criteria

1. THE Gradio_UI SHALL provide a file upload component
2. THE Gradio_UI SHALL accept PDF file formats
3. THE Gradio_UI SHALL accept image file formats (PNG, JPG)
4. THE Gradio_UI SHALL accept XML file formats
5. THE Gradio_UI SHALL accept CSV file formats
6. THE Gradio_UI SHALL provide a submit button to initiate processing

### Requirement 2: Order Document Processing

**User Story:** As an order entry operator, I want the system to automatically extract order data from uploaded documents, so that I don't have to manually transcribe information.

#### Acceptance Criteria

1. WHEN a document is submitted, THE FastAPI_Backend SHALL send the document to Gemini_AI for processing
2. THE FastAPI_Backend SHALL provide a Pydantic schema to Gemini_AI to structure the extraction
3. WHEN the document is a PDF or image, THE Gemini_AI SHALL process it using vision capabilities
4. WHEN the document is XML or CSV, THE FastAPI_Backend SHALL extract text content and send it to Gemini_AI
5. THE Gemini_AI SHALL extract customer name, customer address, order date, payment terms, and notes
6. THE Gemini_AI SHALL extract line items including customer item code, description, color, thickness, quantity, unit price, and discount percentage
7. THE FastAPI_Backend SHALL return structured JSON conforming to the ExtractedOrder Pydantic model

### Requirement 3: Customer Master Data Validation

**User Story:** As an order entry operator, I want the system to validate customer information against master data, so that orders are linked to the correct customer accounts.

#### Acceptance Criteria

1. THE FastAPI_Backend SHALL maintain Mock_Master_Data for customers
2. THE Mock_Master_Data SHALL map customer names to customer codes, payment terms, and addresses
3. WHEN customer data is extracted, THE FastAPI_Backend SHALL lookup the customer in Mock_Master_Data
4. WHEN a customer is found, THE FastAPI_Backend SHALL retrieve the customer code
5. WHEN a customer is not found, THE FastAPI_Backend SHALL flag the order for manual intervention

### Requirement 4: Item Transcodification

**User Story:** As an order entry operator, I want the system to map customer item codes to internal Mago4 codes, so that orders use the correct product identifiers.

#### Acceptance Criteria

1. THE FastAPI_Backend SHALL maintain Mock_Master_Data for transcodification
2. THE Mock_Master_Data SHALL map combinations of base code, color, and thickness to internal Mago4 item codes
3. WHEN an item is extracted, THE FastAPI_Backend SHALL lookup the item attributes in the transcodification table
4. WHEN a match is found, THE FastAPI_Backend SHALL retrieve the internal Mago4 item code
5. WHEN no match is found, THE FastAPI_Backend SHALL flag the item for manual intervention
6. THE FastAPI_Backend SHALL log the transcodification result for each item

### Requirement 5: Price Validation

**User Story:** As an order entry operator, I want the system to validate item prices against the price list, so that I can identify pricing discrepancies.

#### Acceptance Criteria

1. THE FastAPI_Backend SHALL maintain Mock_Master_Data for price lists
2. THE Mock_Master_Data SHALL map internal Mago4 item codes to standard unit prices
3. WHEN an item is transcodified, THE FastAPI_Backend SHALL lookup the standard price
4. THE FastAPI_Backend SHALL compare the extracted price to the standard price
5. THE FastAPI_Backend SHALL calculate the percentage difference between prices
6. THE FastAPI_Backend SHALL log price comparison results for each item

### Requirement 6: Traffic Light Validation Logic

**User Story:** As an order entry operator, I want to see a confidence indicator for each order, so that I know which orders need manual review.

#### Acceptance Criteria

1. THE FastAPI_Backend SHALL assign a Traffic_Light status to each processed order
2. WHEN the customer exists AND all items are transcodified successfully AND all extracted prices match the price list exactly, THE FastAPI_Backend SHALL assign Green status
3. WHEN all items are transcodified successfully AND price discrepancies are less than 5 percent AND no critical data is missing, THE FastAPI_Backend SHALL assign Yellow status
4. WHEN the customer is not found OR any item fails transcodification OR critical data is missing, THE FastAPI_Backend SHALL assign Red status
5. THE FastAPI_Backend SHALL determine the global Traffic_Light status as the worst status among all items
6. THE FastAPI_Backend SHALL include the Traffic_Light status in the API response

### Requirement 7: Flat Table Generation

**User Story:** As an ERP integration specialist, I want the system to output data in Mago4's flat table format, so that orders can be imported into the ERP system.

#### Acceptance Criteria

1. THE FastAPI_Backend SHALL transform extracted order data into Flat_Table format
2. THE Flat_Table SHALL include service fields: Id, CreatedDate, and Processed
3. THE Flat_Table SHALL include header fields with H_ prefix: H_ExternalOrdNo, H_OrderDate, H_ConfirmedDeliveryDate, H_Notes, H_Currency
4. THE Flat_Table SHALL repeat header field values on every row belonging to the same order
5. THE Flat_Table SHALL include line item fields: Item, Description, Qty, UoM, UnitValue, TaxableAmount, Notes
6. THE Flat_Table SHALL create one row per line item
7. THE Flat_Table SHALL use internal Mago4 item codes in the Item field
8. THE Flat_Table SHALL calculate TaxableAmount as Qty multiplied by UnitValue
9. THE Flat_Table SHALL set Processed field to 0 by default
10. THE Flat_Table SHALL set CreatedDate to the current timestamp

### Requirement 8: API Endpoint

**User Story:** As a frontend developer, I want a REST API endpoint to process orders, so that the UI can communicate with the backend.

#### Acceptance Criteria

1. THE FastAPI_Backend SHALL provide a POST endpoint at /api/v1/process-order
2. THE FastAPI_Backend SHALL accept UploadFile as input
3. THE FastAPI_Backend SHALL return JSON containing mago4_flat_table, global_traffic_light, and execution_log
4. THE FastAPI_Backend SHALL include the Flat_Table as a list of dictionaries in mago4_flat_table
5. THE FastAPI_Backend SHALL include the global Traffic_Light status in global_traffic_light
6. THE FastAPI_Backend SHALL include explanations for mappings and validations in execution_log

### Requirement 9: Results Display Interface

**User Story:** As an order entry operator, I want to see the processing results in a clear format, so that I can verify the extracted data and take appropriate action.

#### Acceptance Criteria

1. THE Gradio_UI SHALL display the Traffic_Light status using visual indicators (🔴, 🟡, 🟢)
2. THE Gradio_UI SHALL display the execution log in a readable format
3. THE Gradio_UI SHALL display the Flat_Table using a dataframe component
4. THE Gradio_UI SHALL show all columns defined in the Bridge_Table schema
5. THE Gradio_UI SHALL update the display after each order is processed

### Requirement 10: Environment Configuration

**User Story:** As a system administrator, I want to configure the Gemini API key via environment variables, so that credentials are not hardcoded.

#### Acceptance Criteria

1. THE FastAPI_Backend SHALL load the Gemini API key from the GEMINI_API_KEY environment variable
2. WHEN the GEMINI_API_KEY is not set, THE FastAPI_Backend SHALL raise a configuration error
3. THE System SHALL use the API key to authenticate with Gemini_AI

### Requirement 11: Pydantic Data Models

**User Story:** As a backend developer, I want strongly-typed data models, so that data validation is automatic and consistent.

#### Acceptance Criteria

1. THE FastAPI_Backend SHALL define an ExtractedItem Pydantic model
2. THE ExtractedItem model SHALL include fields: customer_item_code, description, color, thickness, quantity, unit_price, discount_percentage
3. THE FastAPI_Backend SHALL define an ExtractedOrder Pydantic model
4. THE ExtractedOrder model SHALL include fields: customer_name, customer_address, order_date, payment_terms_requested, notes, items
5. THE ExtractedOrder model SHALL use a list of ExtractedItem for the items field
6. THE FastAPI_Backend SHALL pass the ExtractedOrder model to Gemini_AI as the response schema

### Requirement 12: Mock Master Data

**User Story:** As a prototype developer, I want to use mock master data, so that I can demonstrate the system without connecting to a real ERP database.

#### Acceptance Criteria

1. THE FastAPI_Backend SHALL define mock_customers as a Python dictionary
2. THE mock_customers SHALL map customer names to customer codes, payment terms, and addresses
3. THE FastAPI_Backend SHALL define mock_transcodification as a Python dictionary
4. THE mock_transcodification SHALL map combinations of base code, color, and thickness to Mago4 item codes
5. THE FastAPI_Backend SHALL define mock_price_list as a Python dictionary
6. THE mock_price_list SHALL map Mago4 item codes to standard unit prices
