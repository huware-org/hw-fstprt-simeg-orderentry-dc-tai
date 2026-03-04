#!/bin/bash
# Start the Gradio frontend

echo "🎨 Starting Simeg Order Entry Frontend..."
echo ""
echo "Make sure the backend is running at http://127.0.0.1:8000"
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start Gradio app
python FE/app.py
