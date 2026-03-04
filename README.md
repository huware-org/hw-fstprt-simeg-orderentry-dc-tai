# Simeg Intelligent Order Entry - Pre-PoC Prototype

AI-powered order processing system for Italian manufacturing company Simeg. This prototype demonstrates how Google Gemini AI can extract structured data from unstructured order documents and transform them into ERP-ready format.

## 🎯 Features

- **Multi-format Document Processing**: Accepts PDF, images (PNG/JPG), XML, and CSV files
- **AI-Powered Extraction**: Uses Google Gemini to extract order data with vision capabilities for PDFs and images
- **Scavolini XML Support**: Direct XML parsing for Scavolini orders with real transcodification table lookup
- **Business Logic Validation**: Customer validation, N:1 item transcodification, and price verification
- **Real Transcodification Data**: Uses actual Scavolini Excel table (24 columns, thousands of rows) for XML orders
- **Mock Data Fallback**: Uses mock transcodification for PDF/image orders
- **Traffic Light System**: Visual confidence indicators (🟢 Green, 🟡 Yellow, 🔴 Red)
- **Mago4 ERP Integration**: Outputs data in Mago4 bridge table format (Tabella Piana)
- **User-Friendly Interface**: Gradio web UI for easy document upload and results visualization

## 📋 Prerequisites

- **Python**: 3.11 or higher
- **uv**: Fast Python package installer ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Google Gemini API Key**: Get yours at [Google AI Studio](https://aistudio.google.com/app/apikey)

## 🚀 Installation

### 1. Clone or download this repository

```bash
cd simeg-order-entry-prototype
```

### 2. Install dependencies using uv

```bash
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install project dependencies
uv pip install -e .
```

### 3. Set up environment variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your_actual_api_key_here
```

Or export directly:

```bash
export GEMINI_API_KEY="your_actual_api_key_here"
```

## 🏃 Running the Application

The application consists of two components that must run simultaneously:

### Terminal 1: Start the Backend (FastAPI)

```bash
# Activate virtual environment if not already active
source .venv/bin/activate

# Start FastAPI server
uvicorn BE.main:app --reload --host 127.0.0.1 --port 8000
```

The backend API will be available at `http://127.0.0.1:8000`

### Terminal 2: Start the Frontend (Gradio)

```bash
# Activate virtual environment if not already active
source .venv/bin/activate

# Start Gradio UI
python FE/app.py
```

The Gradio interface will open automatically in your browser at `http://127.0.0.1:7860`

## 📁 Project Structure

```
simeg-order-entry-prototype/
├── BE/                          # Backend (FastAPI)
│   ├── __init__.py
│   ├── main.py                  # FastAPI application and endpoints
│   ├── models.py                # Pydantic data models
│   ├── mock_data.py             # Mock master data (customers, transcodification, prices)
│   ├── extraction_service.py   # Gemini AI integration
│   ├── validation_service.py   # Business logic validation
│   └── flat_table_transformer.py # Mago4 format transformation
├── FE/                          # Frontend (Gradio)
│   ├── __init__.py
│   └── app.py                   # Gradio web interface
├── docs/                        # Documentation
│   └── Tabella transcodifica Scavolini 13.02.26.xlsx
├── .kiro/                       # Spec files
│   └── specs/
│       └── simeg-order-entry-prototype/
│           ├── requirements.md
│           ├── design.md
│           └── tasks.md
├── pyproject.toml               # Project dependencies
├── .env.example                 # Environment variable template
├── .gitignore
└── README.md                    # This file
```

## 🔌 API Endpoints

### POST `/api/v1/process-order`

Process an order document and return Mago4 flat table.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: `file` (UploadFile)

**Response:**
```json
{
  "mago4_flat_table": [
    {
      "Id": "uuid",
      "CreatedDate": "2024-01-15T10:30:00",
      "Processed": 0,
      "H_ExternalOrdNo": "MOLTENI&C. S.P.A.",
      "H_OrderDate": "2024-01-15",
      "H_ConfirmedDeliveryDate": null,
      "H_Notes": "Customer notes",
      "H_Currency": "EUR",
      "Item": "48NLPIOSM12ALZ",
      "Description": "TOP MARMO BRECCIA CAPRAIA",
      "Qty": 1.0,
      "UoM": "PZ",
      "UnitValue": 1500.00,
      "TaxableAmount": 1500.00,
      "Notes": "Customer code: 101MATPI2403"
    }
  ],
  "global_traffic_light": "green",
  "execution_log": [
    "📄 Processing file: order.pdf",
    "✅ AI extraction completed: 1 items found",
    "Customer 'MOLTENI&C. S.P.A.' mapped to code 'C-MOL'",
    "Item transcodified: BRECCIA/CAPRAIA/20mm → 48NLPIOSM12ALZ",
    "Price validation: extracted 1500.00 vs standard 1500.00 (perfect match)",
    "🚦 Global Traffic Light: GREEN"
  ]
}
```

## 🚦 Traffic Light System

The system assigns a confidence indicator to each processed order:

- **🟢 GREEN (Automazione Totale)**
  - Customer found in master data
  - All items successfully transcodified
  - Prices match standard price list exactly
  - Ready for automatic ERP import

- **🟡 YELLOW (Revisione Assistita)**
  - All items transcodified
  - Minor price discrepancies (< 5%)
  - Review recommended before import

- **🔴 RED (Intervento Manuale)**
  - Customer not found
  - Item transcodification failed
  - Critical data missing (e.g., quantity)
  - Manual intervention required

## 🗄️ Mock Master Data

The prototype uses hardcoded dictionaries to simulate ERP master data:

### Customers
- MOLTENI&C. S.P.A. → C-MOL
- DV HOME S.R.L. → C-DV
- VISIONNAIRE S.R.L. → C-VIS

### Transcodification Examples
- (BRECCIA, CAPRAIA, 20mm) → 48NLPIOSM12ALZ
- (MARMO, OROBICO ARABESCATO, 20mm) → 31CACDLU02SST014
- (CERAMICA, NERO MARQUINA, 12mm) → 40SEGBLUM300440A0

### Price List
- 48NLPIOSM12ALZ → €1,500.00
- 31CACDLU02SST014 → €2,200.00
- 40SEGBLUM300440A0 → €850.00

## 🧪 Testing

Run tests using pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=BE --cov-report=html
```

## 🔧 Troubleshooting

### Backend won't start
- Ensure `GEMINI_API_KEY` is set in environment
- Check that port 8000 is not already in use
- Verify all dependencies are installed: `uv pip list`

### Frontend can't connect to backend
- Ensure backend is running at `http://127.0.0.1:8000`
- Check backend logs for errors
- Try accessing `http://127.0.0.1:8000` in browser to verify it's running

### Gemini API errors
- Verify your API key is valid
- Check your API quota at [Google AI Studio](https://aistudio.google.com/)
- Ensure you have internet connectivity

## 📝 Notes

- This is a **prototype** for demonstration purposes only
- Uses mock data instead of real database connections
- No actual ERP integration or data persistence
- Local execution only (no Docker or cloud deployment)
- Gemini API key required for document processing

## 📄 License

This is a prototype project for Simeg. All rights reserved.

## 🤝 Support

For questions or issues, please refer to the project documentation in the `.kiro/specs/` directory.
