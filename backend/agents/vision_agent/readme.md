# Vision Agent - LangGraph Supervisor Architecture

A LangGraph-based vision agent that validates and processes medical images (skin and oral) using Google Cloud services.

## Architecture

The agent follows this workflow:

1. **Validate URL**: Checks if image URL is valid (GCS or local path)
2. **Validate Content**: Uses Gemini Vision to validate if the image matches the expected chat_type (skin/oral)
3. **Get Prediction**: If valid, sends image to appropriate CV model API for disease prediction

The agent accepts:
- **GCS URLs**: `gs://bucket-name/path/to/image.jpg`
- **Local file paths**: `/path/to/local/image.png`

## Features

- ✅ LangGraph state machine architecture
- ✅ Gemini Vision-based image validation
- ✅ Automatic routing to skin/oral CV models
- ✅ RESTful API with FastAPI
- ✅ Docker containerized for Cloud Run
- ✅ Comprehensive error handling

## Prerequisites

- Google Cloud Project with billing enabled
- APIs enabled:
  - Cloud Run API
  - Cloud Build API
  - Container Registry API
  - Vertex AI API
  - Cloud Storage API
- Docker installed locally
- gcloud CLI installed and authenticated

## Project Structure

```
.
├── vision_agent.py       # Core LangGraph agent logic
├── app.py               # FastAPI application
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker container definition
├── .dockerignore       # Docker ignore rules
├── cloudbuild.yaml     # Cloud Build configuration
├── deploy.sh           # Deployment script
└── README.md           # This file
```

## Local Development

### 1. Set up environment

```bash
# Set your GCP project ID
export GCP_PROJECT_ID="adsp-34002-ip07"
export GCP_LOCATION="us-central1"

# Authenticate with Google Cloud
gcloud auth application-default login
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run locally

```bash
python app.py
```

The API will be available at `http://localhost:8080`

### 4. Test locally

```bash
curl -X POST http://localhost:8080/process \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "9vEu1qRQ1lgphdnpN5mO", "chat_type": "skin"}'
```

## Deployment to Cloud Run

### Option 1: Using deployment script (Recommended)

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### Option 2: Manual deployment

```bash
# Set project
gcloud config set project adsp-34002-ip07

# Build and push image
docker build -t gcr.io/adsp-34002-ip07/vision-agent:latest .
docker push gcr.io/adsp-34002-ip07/vision-agent:latest

# Deploy to Cloud Run
gcloud run deploy vision-agent \
  --image=gcr.io/adsp-34002-ip07/vision-agent:latest \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --max-instances=10 \
  --set-env-vars="GCP_PROJECT_ID=adsp-34002-ip07,GCP_LOCATION=us-central1"
```

### Option 3: Using Cloud Build

```bash
gcloud builds submit --config cloudbuild.yaml
```

## API Endpoints

### POST /process

Process a complete vision request (validate + predict)

**Request:**
```json
{
  "chat_id": "9vEu1qRQ1lgphdnpN5mO",
  "chat_type": "skin"
}
```

**Response:**
```json
{
  "chat_id": "9vEu1qRQ1lgphdnpN5mO",
  "chat_type": "skin",
  "is_valid": true,
  "validation_reason": "Image shows human skin with visible dermatological features",
  "prediction_result": {
    "predicted_disease": "Acne",
    "confidence": 0.92,
    "top_predictions": [...]
  },
  "error": null
}
```

### POST /validate-only

Validate image only without prediction (for testing)

**Request:**
```json
{
  "chat_id": "9vEu1qRQ1lgphdnpN5mO",
  "chat_type": "oral"
}
```

**Response:**
```json
{
  "chat_id": "9vEu1qRQ1lgphdnpN5mO",
  "chat_type": "oral",
  "is_valid": false,
  "validation_reason": "Image shows skin condition, not oral cavity",
  "prediction_result": null,
  "error": null
}
```

### GET /health

Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "gcp_project": "adsp-34002-ip07",
  "location": "us-central1"
}
```

## Configuration

Environment variables can be set during deployment:

- `GCP_PROJECT_ID`: Your Google Cloud project ID (default: adsp-34002-ip07)
- `GCP_LOCATION`: GCP region (default: us-central1)
- `ORAL_CV_ENDPOINT`: Oral CV model endpoint URL
- `PORT`: Server port (default: 8080)

## Integration with Supervisor Agent

The vision agent returns a standardized response that can be easily integrated with a LangGraph supervisor:

```python
from vision_agent import process_vision_request

# In your supervisor agent
result = process_vision_request(
    chat_id=state['chat_id'],
    chat_type=state['chat_type']
)

if result['is_valid']:
    # Process prediction result
    state['prediction'] = result['prediction_result']
else:
    # Handle invalid image
    state['error'] = result['validation_reason']
```

## CV Model Endpoints

The agent expects CV model endpoints to accept multipart form data with a file field:

**Skin Disease Model:**
- URL: `https://skin-disease-cv-model-139431081773.us-central1.run.app/predict`

**Oral Disease Model:**
- URL: Set via `ORAL_CV_ENDPOINT` environment variable

## Error Handling

The agent handles various error scenarios:

- ❌ Image not found in GCS
- ❌ Invalid image type (doesn't match chat_type)
- ❌ CV model API failures
- ❌ Gemini Vision API errors
- ❌ Network/timeout issues

All errors are returned in the response with descriptive messages.

## Monitoring

View logs in Cloud Console:

```bash
gcloud run services logs read vision-agent --region=us-central1
```

## Cost Considerations

- Cloud Run: Pay per request + compute time
- Vertex AI (Gemini): Pay per API call
- Cloud Storage: Egress charges for image downloads
- Estimated cost: ~$0.001-0.005 per request

## Security

- Service uses Google Cloud default credentials
- Images are accessed via service account permissions
- API can be configured for authenticated-only access if needed

## Troubleshooting

### Images not found
- Verify chat_id exists in GCS bucket
- Check bucket permissions
- Confirm bucket name in configuration

### Validation failures
- Check Gemini API quotas
- Verify image format (JPEG, PNG, WebP)
- Review validation logs

### Prediction failures
- Verify CV model endpoints are running
- Check network connectivity
- Review CV model logs

## Support

For issues or questions, check:
- Cloud Run logs: `gcloud run services logs read vision-agent`
- Service health: `GET https://your-service-url/health`
- API documentation: `GET https://your-service-url/docs`