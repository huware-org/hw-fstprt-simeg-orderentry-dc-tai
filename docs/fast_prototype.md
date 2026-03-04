# Project Specification: Simeg Intelligent Order Entry (Pre-PoC Prototype)

## 1. Project Overview & Objective
This project is a rapid prototype (Pre-PoC) for an Italian manufacturing company (Simeg). The goal is to demonstrate that AI (Google Gemini) can process complex order workflows. 

**Demo Strategy (Two Tracks):**
1.  **Unstructured Track (PDF/Images):** Process messy luxury furniture orders (e.g., Molteni, DV Home). Extract semantic data and map it to internal codes.
2.  **Structured Track (N:1 Transcodification):** Process rigid configurator inputs (e.g., Scavolini). Take 4-5 specific attributes (Material, Color, Finish, Edge) and map them to a single internal code.

**Scope Constraints:**
* **Local Execution Only:** Do not generate deployment configurations (No Docker, no cloud deployment). 
* **Mock Data:** Use hardcoded Python dictionaries instead of an actual database.
* **Output:** The final payload must be a "Flat Table" (Tabella Piana) format ready for Mago4 ERP.

## 2. Technology Stack & Environment
* **Environment Management:** `uv` (Use `uv` instead of standard `pip` or `venv` for speed).
* **Frontend (FE):** Gradio (Python)
* **Backend (BE):** FastAPI (Python)
* **AI Integration:** `google-genai` SDK (Google Gemini 1.5 Flash or 2.0 Flash)
* **Data Validation:** Pydantic

## 3. Project Structure
Create two strictly separate folders to simulate a decoupled architecture:

simeg_poc/
├── BE/
│   ├── requirements.txt (FastAPI, pydantic, google-genai, python-multipart, uvicorn)
│   └── main.py
└── FE/
    ├── requirements.txt (gradio, requests, pandas)
    └── app.py


## 4. Backend Specifications (`BE/main.py`)

### 4.1 Mock Master Data (Anagrafiche)
Create small, hardcoded dictionaries:
* `mock_customers`: E.g., `{"MOLTENI&C. S.P.A.": "C-MOL", "DV HOME S.R.L.": "C-DV"}`.
* `mock_pdf_transcodification`: Maps unstructured PDF descriptions to Mago4 codes (e.g., `{"BRECCIA CAPRAIA_TOP MARMO": "48NLPIOSM12ALZ"}`).
* `mock_scavolini_transcodification`: Maps a composite key `(Material, Color, Finish, Edge)` to a Mago4 code (e.g., `{"MP0001-CP0922-FP0008-PP0001": "40SEGBLUM300440A0"}`).
* `mock_price_list`: Maps Mago4 codes to a standard unit price for validation.

### 4.2 Traffic Light Logic (Semaforo)
Evaluate the processed data:
* **Green:** Customer mapped, all items mapped to Mago4 codes, prices match standard lists (or are within 5%).
* **Yellow:** Items mapped, but price discrepancies exist, or non-critical fields missing.
* **Red:** Customer not found, failure to resolve the N:1 Mago4 code, or critical data (Qty) missing.

### 4.3 Endpoints
Implement two distinct API routes:
1.  `POST /api/v1/process-document`: 
    * **Input:** `UploadFile` (Accepts .pdf, .png, .jpg, .xml, .csv).
    * **Logic:** Calls Gemini using `google-genai` with a strict Pydantic `response_schema` to extract order data. Matches results against `mock_pdf_transcodification`. Applies Traffic Light logic. Flattens data into the Mago4 "Tabella Piana" format.
2.  `POST /api/v1/transcode-attributes`:
    * **Input:** JSON payload with `material`, `color`, `finish`, `edge` (simulating Scavolini input).
    * **Logic:** Performs dictionary lookup against `mock_scavolini_transcodification`. Returns the resolved Mago4 Code and a Green/Red traffic light.

## 5. AI Integration Specifications (Gemini)
* Read API key from `GEMINI_API_KEY` environment variable.
* Pass the Pydantic schema to Gemini to force structured JSON output.
* Provide a strong system prompt instructing the model to act as an expert marble/ceramics data entry clerk, extracting material types, dimensions, and special instructions separately.

## 6. Frontend Specifications (`FE/app.py`)
Use `gr.Blocks()` to build an interface with **Two Tabs**:

### Tab 1: Unstructured Orders (PDF/Documenti)
* **Left Column:** `gr.File` for uploading documents. Submit button.
* **Right Column:** * `gr.HTML`/`gr.Markdown` for the Traffic Light status (🔴, 🟡, 🟢) and execution reasoning.
    * `gr.Dataframe` to display the final `mago4_flat_table` as a clean, tabular grid.

### Tab 2: Structured Transcodification (Configuratore Scavolini)
* **Left Column:** 4 `gr.Textbox` or `gr.Dropdown` inputs representing the Scavolini attributes (Materiale, Colore, Finitura, Bordo). Submit button.
* **Right Column:** * Display the Traffic Light status.
    * Large text display showing the final resolved **Codice Mago4**.

## 7. Execution Steps for Kira
1.  Initialize the project structure (`FE` and `BE` folders).
2.  Generate the `BE/main.py` code including FastAPI setup, Pydantic models, Mock Dictionaries, routing, flattening logic, and Gemini SDK integration.
3.  Generate the `FE/app.py` code using Gradio, ensuring it makes HTTP requests to `http://127.0.0.1:8000` (the BE).
4.  Provide terminal commands using `uv` to setup the local virtual environment, install dependencies for both folders, and run the FastAPI server and Gradio app concurrently.