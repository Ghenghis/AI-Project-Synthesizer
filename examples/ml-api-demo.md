# ML API Synthesis Demo

## Overview
This demo shows how to synthesize a complete Machine Learning API project that combines a FastAPI backend with an ML model from HuggingFace.

## MCP Server Command

```
Synthesize a project from the idea: "Create a REST API for text classification using FastAPI and a pre-trained transformer model from HuggingFace"
```

## Expected Result

The AI Project Synthesizer will:

1. **Search for Relevant Resources**
   - Find FastAPI boilerplate projects
   - Locate HuggingFace text classification models
   - Discover ML serving utilities
   - Find API documentation examples

2. **Create Project Structure**
   ```
   ml-api-project/
   ├── src/
   │   ├── api/
   │   │   ├── __init__.py
   │   │   ├── main.py
   │   │   ├── routes.py
   │   │   └── schemas.py
   │   ├── ml/
   │   │   ├── __init__.py
   │   │   ├── model_loader.py
   │   │   ├── predictor.py
   │   │   └── preprocessor.py
   │   └── utils/
   │       ├── __init__.py
   │       ├── logging.py
   │       └── metrics.py
   ├── tests/
   │   ├── test_api.py
   │   ├── test_ml.py
   │   └── test_integration.py
   ├── models/
   │   └── .gitkeep
   ├── config/
   │   ├── settings.yaml
   │   └── model_config.yaml
   ├── requirements.txt
   ├── Dockerfile
   ├── README.md
   └── .gitignore
   ```

3. **Generate Requirements**
   ```txt
   # Core dependencies
   torch>=2.0.0
   transformers>=4.30.0
   datasets>=2.0.0
   numpy>=1.24.0
   pandas>=2.0.0
   
   # Utilities
   tqdm
   python-dotenv
   pyyaml
   
   # API
   fastapi>=0.104.0
   uvicorn[standard]>=0.24.0
   pydantic>=2.4.0
   
   # ML
   scikit-learn>=1.3.0
   joblib>=1.3.0
   ```

4. **Create API Endpoints**

## Generated API Endpoints

### POST /classify
```json
{
  "text": "This is amazing! I love this product.",
  "model": "distilbert-base-uncased-finetuned-sst-2-english"
}
```

Response:
```json
{
  "label": "POSITIVE",
  "score": 0.9998,
  "model": "distilbert-base-uncased-finetuned-sst-2-english",
  "processed_at": "2024-01-01T12:00:00Z"
}
```

### GET /models
Lists all available models
```json
{
  "models": [
    {
      "name": "distilbert-base-uncased-finetuned-sst-2-english",
      "type": "text-classification",
      "loaded": true
    }
  ]
}
```

### GET /health
Health check endpoint
```json
{
  "status": "healthy",
  "model_loaded": true,
  "uptime": 3600
}
```

## Usage Example

### Start the API
```bash
pip install -r requirements.txt
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Use the API
```python
import requests

# Classify text
response = requests.post(
    "http://localhost:8000/classify",
    json={"text": "This product is terrible!"}
)
result = response.json()
print(f"Label: {result['label']}, Score: {result['score']}")
```

## Features Included

- Automatic model loading from HuggingFace
- Batch text processing
- Model caching for performance
- Input validation with Pydantic
- Comprehensive error handling
- Request/response logging
- Metrics collection
- OpenAPI/Swagger documentation
- Docker deployment support
- Environment-based configuration

## Configuration

The `config/model_config.yaml` allows you to:
- Specify default models
- Set model parameters
- Configure preprocessing steps
- Define output labels

## Extending the Project

The synthesized project includes:
- Modular ML pipeline
- Pluggable model architecture
- Custom preprocessing hooks
- Async API endpoints
- Background model loading
- Graceful shutdown handling

## Production Deployment

The generated Dockerfile includes:
- Multi-stage build for optimization
- Non-root user for security
- Health check endpoint
- Proper signal handling
- Volume mounts for models

## Monitoring

Built-in monitoring features:
- Request latency tracking
- Model prediction metrics
- Error rate monitoring
- Resource usage logging
