"""Gradio frontend for Simeg Order Entry system."""

import gradio as gr
import requests
import pandas as pd
from typing import Optional, Tuple


# Backend API URL
BACKEND_URL = "http://127.0.0.1:8000"


def process_order(file) -> Tuple[str, str, Optional[pd.DataFrame], Optional[str]]:
    """
    Process order document by calling backend API.
    
    Args:
        file: Uploaded file object from Gradio
        
    Returns:
        Tuple of (traffic_light_html, execution_log_text, dataframe, csv_file_path)
    """
    if file is None:
        return (
            "⚠️ Please upload a file",
            "No file uploaded",
            None,
            None
        )
    
    try:
        # Prepare file for upload
        with open(file.name, "rb") as f:
            files = {"file": (file.name.split("/")[-1], f, "application/octet-stream")}
            
            # Call backend API
            response = requests.post(
                f"{BACKEND_URL}/api/v1/process-order",
                files=files,
                timeout=60
            )
        
        # Check response status
        if response.status_code != 200:
            error_detail = response.json().get("detail", "Unknown error")
            return (
                "❌ Error",
                f"API Error ({response.status_code}): {error_detail}",
                None,
                None
            )
        
        # Parse response
        result = response.json()
        
        # Extract data
        traffic_light = result.get("global_traffic_light", "unknown")
        execution_log = result.get("execution_log", [])
        flat_table = result.get("mago4_flat_table", [])
        
        # Format traffic light with visual indicator
        traffic_light_icons = {
            "green": "🟢",
            "yellow": "🟡",
            "red": "🔴"
        }
        icon = traffic_light_icons.get(traffic_light.lower(), "⚪")
        traffic_light_html = f"<h2>{icon} {traffic_light.upper()}</h2>"
        
        # Format execution log
        execution_log_text = "\n".join(execution_log)
        
        # Convert flat table to DataFrame and CSV
        csv_file_path = None
        if flat_table:
            df = pd.DataFrame(flat_table)
            
            # Save to CSV for download
            csv_file_path = "/tmp/mago4_flat_table.csv"
            df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')
        else:
            df = None
        
        return (traffic_light_html, execution_log_text, df, csv_file_path)
        
    except requests.exceptions.ConnectionError:
        return (
            "❌ Connection Error",
            "Cannot connect to backend API. Please ensure the FastAPI server is running at http://127.0.0.1:8000",
            None,
            None
        )
    except requests.exceptions.Timeout:
        return (
            "⏱️ Timeout",
            "Request timed out. The document may be too large or complex.",
            None,
            None
        )
    except Exception as e:
        return (
            "❌ Error",
            f"Unexpected error: {str(e)}",
            None,
            None
        )


# Create Gradio interface
with gr.Blocks(title="Simeg Order Entry - AI Prototype") as demo:
    gr.Markdown("""
    # 🏛️ Simeg Intelligent Order Entry
    ### AI-Powered Order Processing Prototype
    
    Upload an order document (PDF, Image, XML, CSV) to extract structured data and generate a Mago4 ERP-ready flat table.
    """)
    
    # Upload section at the top - full width
    gr.Markdown("### 📤 Upload Document")
    file_input = gr.File(
        label="Order Document",
        file_types=[".pdf", ".png", ".jpg", ".jpeg", ".xml", ".csv"],
        type="filepath"
    )
    submit_btn = gr.Button("🚀 Process Order", variant="primary", size="lg")
    
    # Separator
    gr.Markdown("---")
    
    # Results section below - full width
    gr.Markdown("### 📊 Processing Results")
    
    # Traffic light status
    traffic_light_output = gr.HTML(label="Status")
    
    # Execution log
    with gr.Accordion("📝 Execution Log", open=True):
        execution_log_output = gr.Textbox(
            label="Processing Steps",
            lines=10,
            max_lines=20,
            show_label=False
        )
    
    # Flat table - full width
    with gr.Accordion("📋 Mago4 Flat Table", open=True):
        flat_table_output = gr.Dataframe(
            label="ERP-Ready Data",
            wrap=True,
            show_label=False
        )
        download_btn = gr.File(
            label="📥 Download CSV",
            visible=True
        )
    
    # Connect button to processing function
    submit_btn.click(
        fn=process_order,
        inputs=[file_input],
        outputs=[traffic_light_output, execution_log_output, flat_table_output, download_btn]
    )
    
    gr.Markdown("""
    ---
    ### 🚦 Traffic Light Legend
    - 🟢 **GREEN**: All validations passed - ready for automatic ERP import
    - 🟡 **YELLOW**: Minor issues detected - review recommended before import
    - 🔴 **RED**: Critical issues detected - manual intervention required
    
    ### 📌 Notes
    - Ensure the FastAPI backend is running at `http://127.0.0.1:8000`
    - Set `GEMINI_API_KEY` environment variable before starting the backend
    - Supported formats: PDF, PNG, JPG, XML, CSV
    """)


if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False
    )
