# ML Service (AI Microservice)

This directory contains the standalone **FastAPI** microservice dedicated to AI and Machine Learning tasks. It is decoupled from the main Django backend to allow for independent scaling and distinct dependencies.

## Features

- **Description Enhancement**: Uses LLMs to rewrite menu item descriptions using behavioral economics principles.
- **Sales Suggestions**: Generates actionable advice (pricing, marketing) based on item performance.
- **Menu Analysis**: Analyzes menu structure and layout.
- **Owner Reports**: Generates comprehensive business reports from raw data.

## Technology Stack

- **FastAPI**: High-performance async web framework.
- **OpenRouter**: Unified interface for accessing LLMs.
- **Supported Models**:
  - DeepSeek Chat (Recommended)
  - Mistral 7B Instruct
  - Meta Llama 3 8B

## Configuration

The service requires the `OPENROUTER_API_KEY` environment variable to be set in the root `.env` file.

## Running Locally

```bash
# Navigate to root
python -m uvicorn ml_service.main:app --reload --port 8001
```

*Note: The service runs on port **8001** by default to avoid conflict with the Django backend (8000).*
