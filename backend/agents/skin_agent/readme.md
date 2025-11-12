# Skin Specialist Agent - Deployment Guide

LangGraph-based dermatology consultation agent with supervisor architecture deployed on Google Cloud Run.

## 📁 Project Structure

```
skin-specialist-agent/
├── app.py              # Main Flask application with LangGraph workflow
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker container configuration
├── cloudbuild.yaml    # Cloud Build configuration (optional)
├── deploy.sh          # Deployment script
├── test_skin_agent.py # Testing script
└── README.md          # This file
```

## 🚀 Quick Deployment

### Prerequisites

1. **Google Cloud SDK** installed and configured
   ```bash
   gcloud --version
   ```

2. **Docker** installed (optional, for local testing)
   ```bash
   docker --version
   ```

3. **Google Cloud Project** with billing enabled
   ```bash
   gcloud config set project adsp-34002-ip07-visionary-ai
   ```

### Option 1: Automated Deployment (Recommended)

```bash
# Make the deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

This script will:
- ✅ Enable required APIs
- ✅ Build Docker image
- ✅ Deploy to Cloud Run
- ✅ Output the service URL

### Option 2: Manual Deployment

#### Step 1: Enable Required APIs

```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    aiplatform.googleapis.com
```

#### Step 2: Build and Submit Docker Image

```bash
# Set variables
PROJECT_ID="adsp-34002-ip07-visionary-ai"
SERVICE_NAME="skin-specialist-agent"
REGION="us-central1"

# Build and push image
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME}
```

#### Step 3: Deploy to Cloud Run

```bash
gcloud run deploy ${SERVICE_NAME} \
    --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --set-env-vars GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION}
```

#### Step 4: Get Service URL

```bash
gcloud run services describe ${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --format 'value(status.url)'
```

### Option 3: Using Cloud Build Trigger (CI/CD)

```bash
# Submit build using cloudbuild.yaml
gcloud builds submit --config cloudbuild.yaml
```

## 🧪 Testing the Deployment

### Quick Health Check

```bash
SERVICE_URL="https://your-service-url.run.app"

# Health check
curl ${SERVICE_URL}/health
```

### Using the Test Script

```python
# Update API_URL in test_skin_agent.py
API_URL = "https://your-service-url.run.app"

# Run tests
python test_skin_agent.py
```

### Manual API Testing

#### 1. Start a Consultation

```bash
curl -X POST ${SERVICE_URL}/start \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**
```json
{
  "status": "success",
  "thread_id": "consultation_20250102_123456_789012",
  "response": "Hello! I'm here to help you with your skin concern...",
  "information_complete": false,
  "should_request_image": false,
  "collected_info": {
    "age": "",
    "gender": "",
    "body_region": "",
    "symptoms": {},
    ...
  }
}
```

#### 2. Send Messages

```bash
THREAD_ID="consultation_20250102_123456_789012"

curl -X POST ${SERVICE_URL}/chat \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "'${THREAD_ID}'",
    "message": "I am 45 years old, male"
  }'
```

#### 3. Check Conversation State

```bash
curl ${SERVICE_URL}/state/${THREAD_ID}
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API documentation |
| `/health` | GET | Health check |
| `/start` | POST | Start new consultation |
| `/chat` | POST | Send message in consultation |
| `/state/<thread_id>` | GET | Get conversation state |

## 🏗️ Architecture

### LangGraph Workflow

```
User Message → Extract Info → Assess Completeness
                                    ↓
                     ┌──────────────┴──────────────┐
                     ↓                             ↓
            Generate Question              Request Image
                     ↓                             ↓
                   END                           END
```

### State Management

The agent maintains stateful conversations using LangGraph's `MemorySaver`:

- **Thread-based**: Each consultation has a unique `thread_id`
- **Persistent**: State is maintained across API calls
- **Isolated**: Multiple consultations run independently

### Information Collection

**Required Fields:**
- Age
- Gender
- Body region
- At least one symptom (itch, hurt, grow, change, bleed)

**Optional Fields:**
- Skin cancer history
- Family cancer history
- Duration
- Other information

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | 8080 |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | adsp-34002-ip07-visionary-ai |
| `GOOGLE_CLOUD_LOCATION` | Vertex AI region | us-central1 |

### Resource Configuration

- **Memory**: 2Gi
- **CPU**: 2
- **Timeout**: 300 seconds
- **Max Instances**: 10
- **Min Instances**: 0 (scales to zero)

## 📊 Monitoring

### View Logs

```bash
# Stream logs
gcloud run services logs tail skin-specialist-agent \
    --region=us-central1

# View in Cloud Console
https://console.cloud.google.com/run/detail/us-central1/skin-specialist-agent/logs
```

### Metrics

Access Cloud Run metrics in the Google Cloud Console:
- Request count
- Request latency
- Error rate
- Instance count

## 🔒 Security

### Authentication

Currently deployed with `--allow-unauthenticated` for testing.

**For production**, enable authentication:

```bash
gcloud run deploy skin-specialist-agent \
    --no-allow-unauthenticated \
    ...
```

Then use service account or OAuth tokens:

```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
    ${SERVICE_URL}/health
```

## 🐛 Troubleshooting

### Build Fails

```bash
# Check build logs
gcloud builds list --limit=5

# View specific build
gcloud builds log <BUILD_ID>
```

### Deployment Fails

```bash
# Check service status
gcloud run services describe skin-specialist-agent \
    --region=us-central1

# Check revisions
gcloud run revisions list \
    --service=skin-specialist-agent \
    --region=us-central1
```

### Runtime Errors

```bash
# Check logs
gcloud run services logs read skin-specialist-agent \
    --region=us-central1 \
    --limit=50
```

### Common Issues

1. **Out of Memory**: Increase memory allocation
   ```bash
   gcloud run services update skin-specialist-agent \
       --memory 4Gi \
       --region=us-central1
   ```

2. **Timeout**: Increase timeout
   ```bash
   gcloud run services update skin-specialist-agent \
       --timeout 600 \
       --region=us-central1
   ```

3. **Cold Start**: Set min instances
   ```bash
   gcloud run services update skin-specialist-agent \
       --min-instances 1 \
       --region=us-central1
   ```

## 💰 Cost Optimization

- **Scales to zero**: No instances when not in use
- **CPU throttling**: CPU only allocated during request processing
- **Pay per use**: Billed per 100ms of request processing

**Estimated costs** (with typical usage):
- First 2 million requests/month: Free tier
- Additional requests: ~$0.40 per million requests
- Memory/CPU: ~$0.00002448 per GB-second

## 🔄 Updates and Redeployment

### Quick Update

```bash
# Rebuild and redeploy
./deploy.sh
```

### Rolling Back

```bash
# List revisions
gcloud run revisions list \
    --service=skin-specialist-agent \
    --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic skin-specialist-agent \
    --to-revisions=<REVISION_NAME>=100 \
    --region=us-central1
```

## 📚 Integration with Supervisor Agent

The agent is designed to integrate with a supervisor agent:

```python
# In your supervisor agent
import requests

# Start consultation
response = requests.post(f"{AGENT_URL}/start")
thread_id = response.json()["thread_id"]

# Process user messages
while not ready_for_image:
    response = requests.post(
        f"{AGENT_URL}/chat",
        json={
            "thread_id": thread_id,
            "message": user_message
        }
    )
    
    if response.json()["should_request_image"]:
        # Trigger image upload flow in supervisor
        ready_for_image = True
```

## 📞 Support

For issues or questions:
1. Check logs: `gcloud run services logs tail skin-specialist-agent`
2. Review documentation: [Cloud Run Docs](https://cloud.google.com/run/docs)
3. Check LangGraph docs: [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

## 📄 License

This project is part of the Visionary AI healthcare platform.

---

**Last Updated**: November 2025  
**Version**: 1.0  
**Maintainer**: Healthcare AI Team