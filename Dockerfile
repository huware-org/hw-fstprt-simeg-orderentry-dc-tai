# Use official Python slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock* ./

# Install dependencies using uv (frozen lockfile for reproducibility)
RUN uv sync --frozen --no-dev || uv sync --no-dev

# Copy application code
COPY . .

# Expose port (Cloud Run will inject $PORT at runtime)
EXPOSE 8080

# Start uvicorn with dynamic port from environment variable
# Cloud Run requires listening on $PORT
CMD sh -c "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"
