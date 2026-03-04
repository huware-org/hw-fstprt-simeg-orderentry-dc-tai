# Project Structure

This document describes the organization of the Simeg Order Entry Backend codebase.

## Directory Layout

```
simeg-order-entry-backend/
├── app/                          # Main application package
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI application entry point
│   │
│   ├── config/                  # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py          # Environment variables & settings
│   │
│   ├── models/                  # Data models and schemas
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic models for API & data
│   │
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── extraction_service.py    # AI-powered document extraction
│   │   ├── validation_service.py    # Customer & price validation
│   │   └── xml_processor.py         # Scavolini XML parsing
│   │
│   └── utils/                   # Utility functions and helpers
│       ├── __init__.py
│       ├── flat_table_transformer.py  # Mago4 table generation
│       ├── mock_data.py              # Mock data for testing
│       └── scavolini_loader.py       # Scavolini transcodification
│
├── docs/                        # Documentation
│   ├── architecture/            # Architecture documentation
│   │   ├── mago4_bridge_table_schema.md
│   │   └── REFACTORING_SUMMARY.md
│   ├── deployment/              # Deployment guides
│   │   ├── CLOUD_RUN_DEPLOYMENT.md
│   │   └── DEPLOYMENT_COMMANDS.md
│   ├── fast_prototype.md        # Prototype documentation
│   ├── README_SCAVOLINI.md      # Scavolini integration docs
│   └── PROJECT_STRUCTURE.md     # This file
│
├── scripts/                     # Utility scripts
│   ├── start_backend.sh         # Local development server
│   └── inspect_scavolini_table.py  # Debug Scavolini data
│
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── Dockerfile                   # Container definition
├── .dockerignore               # Docker build exclusions
├── pyproject.toml              # Python dependencies (uv)
├── uv.lock                     # Locked dependencies
└── README.md                   # Main project README
```

## Architecture Layers

### 1. Entry Point (`app/main.py`)
- FastAPI application initialization
- Route definitions
- Middleware configuration (CORS)
- Request/response handling

### 2. Configuration (`app/config/`)
- Environment variable management
- Application settings
- Type-safe configuration using Pydantic

### 3. Models (`app/models/`)
- Pydantic schemas for request/response validation
- Data transfer objects (DTOs)
- Type definitions

### 4. Services (`app/services/`)
Business logic layer containing:
- **extraction_service.py**: AI-powered document extraction using Google Gemini
- **validation_service.py**: Customer lookup, item transcodification, price validation
- **xml_processor.py**: Scavolini/Ernestomeda XML parsing

### 5. Utils (`app/utils/`)
Helper functions and utilities:
- **flat_table_transformer.py**: Converts extracted orders to Mago4 flat table format
- **scavolini_loader.py**: Loads and queries Scavolini transcodification table
- **mock_data.py**: Mock data for development and testing

## Design Patterns

### Separation of Concerns
- **Routes** (main.py): Handle HTTP requests/responses
- **Services**: Implement business logic
- **Models**: Define data structures
- **Utils**: Provide reusable helpers

### Dependency Injection
- Configuration injected via `settings` object
- Services imported and used by routes
- Easy to mock for testing

### Single Responsibility
- Each module has a clear, focused purpose
- Services handle one domain area
- Utils provide specific functionality

## Import Conventions

### Absolute Imports
Always use absolute imports from the `app` package:

```python
from app.config import settings
from app.models import ExtractedOrder
from app.services import extract_order_from_document
from app.utils import transform_to_flat_table
```

### Package Exports
Each package's `__init__.py` exports commonly used items:

```python
# Instead of:
from app.models.schemas import ExtractedOrder

# You can use:
from app.models import ExtractedOrder
```

## Running the Application

### Local Development
```bash
# From project root
bash scripts/start_backend.sh
```

### Docker
```bash
docker build -t simeg-backend .
docker run -p 8080:8080 -e GEMINI_API_KEY="your_key" simeg-backend
```

### Cloud Run
```bash
gcloud run deploy simeg-order-entry-backend --source .
```

## Adding New Features

### New API Endpoint
1. Add route handler in `app/main.py`
2. Create/update service in `app/services/`
3. Define request/response models in `app/models/schemas.py`

### New Service
1. Create file in `app/services/`
2. Export in `app/services/__init__.py`
3. Import in `app/main.py` or other services

### New Utility
1. Create file in `app/utils/`
2. Export in `app/utils/__init__.py`
3. Import where needed

## Testing Strategy

### Unit Tests
- Test services independently
- Mock external dependencies (Gemini API, file I/O)
- Test utils with various inputs

### Integration Tests
- Test API endpoints end-to-end
- Use test fixtures for file uploads
- Validate response schemas

### Test Location
```
tests/
├── unit/
│   ├── test_extraction_service.py
│   ├── test_validation_service.py
│   └── test_xml_processor.py
├── integration/
│   └── test_api.py
└── fixtures/
    ├── sample_order.pdf
    └── sample_scavolini.xml
```

## Best Practices

1. **Type Hints**: Use type hints for all function parameters and returns
2. **Docstrings**: Document all public functions and classes
3. **Error Handling**: Use custom exceptions and proper HTTP status codes
4. **Logging**: Use structured logging for debugging
5. **Configuration**: Never hardcode secrets or environment-specific values
6. **Validation**: Validate all inputs using Pydantic models

## Related Documentation

- [Cloud Run Deployment Guide](deployment/CLOUD_RUN_DEPLOYMENT.md)
- [Deployment Commands](deployment/DEPLOYMENT_COMMANDS.md)
- [Architecture Summary](architecture/REFACTORING_SUMMARY.md)
- [Mago4 Schema](architecture/mago4_bridge_table_schema.md)
- [Scavolini Integration](README_SCAVOLINI.md)
