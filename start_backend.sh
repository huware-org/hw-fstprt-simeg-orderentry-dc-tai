#!/bin/bash
# Start the FastAPI backend server

echo "🚀 Starting Simeg Order Entry Backend..."
echo ""
echo "Make sure you have set GEMINI_API_KEY environment variable:"
echo "  export GEMINI_API_KEY='your_api_key_here'"
echo ""

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  WARNING: GEMINI_API_KEY is not set!"
    echo "The backend will fail to start without it."
    echo ""
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start FastAPI server
uvicorn BE.main:app --reload --host 127.0.0.1 --port 8000
