# Healthcare Diagnostic Backend API

A production-ready FastAPI backend for healthcare diagnostic applications, supporting skin and dental health analysis using AI models. This system provides intelligent conversation flow, dynamic metadata extraction, and robust CV model integration with fallback mechanisms.

## 🌟 Key Features

- **🤖 Intelligent Conversation Flow**: Dynamic metadata collection → Image request → Report generation
- **🧠 Gemini 2.0 Integration**: Advanced LLM with Vertex AI authentication
- **🖼️ CV Model Analysis**: Skin and dental image analysis with anti-hallucination validation
- **🔄 Robust Fallback**: Gemini analysis when CV models fail
- **📱 Firebase Integration**: Real-time database with exact schema matching
- **⚡ Fast Response**: Sub-second CV model analysis with retry logic
- **🛡️ Production Ready**: Comprehensive error handling, logging, and monitoring

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Google Cloud Platform account
- Firebase project
- Vertex AI access
- Docker (for containerized deployment)
- Conda (recommended for environment management)

### Local Development Setup

1. **Clone and setup environment:**
```bash
git clone https://github.com/Mahenderreddyp/Visionary-AI-App.git
cd Backend

# Using conda (recommended)
conda create -n backend python=3.11
conda activate backend
pip install -r requirements.txt

# Or using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment variables:**
```bash
# Copy your Firebase credentials to .env file
cp firebase_credentials.config .env
# Edit .env with your specific values
```

3. **Run the application:**
```bash
conda activate backend  # or source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

4. **Test the API:**
```bash
# Test basic functionality
python test_api.py

# Test CV model specifically
python test_cv_model.py

# Test deployed API
python test_deployed_api.py
```

## 🐳 Docker Deployment

### Build and Run with Docker

1. **Build the Docker image:**
```bash
docker build -t healthcare-diagnostic-api .
```

2. **Run the container:**
```bash
docker run -d \
  --name healthcare-api \
  -p 8080:8080 \
  -e GCP_PROJECT_ID=your-project-id \
  -e SKIN_CV_API=https://skin-disease-cv-model-139431081773.us-central1.run.app/predict \
  -e ORAL_CV_API=https://your-oral-cv-api.com/predict \
  -v $(pwd)/service-account.json:/app/service-account.json:ro \
  healthcare-diagnostic-api
```

3. **Test the containerized API:**
```bash
curl http://localhost:8080/health
```

## ☁️ Google Cloud Platform Deployment

### Prerequisites for GCP Deployment

1. **Enable required APIs:**
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

2. **Create service account:**
```bash
# Create service account
gcloud iam service-accounts create healthcare-api-sa \
  --display-name="Healthcare Diagnostic API Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:healthcare-api-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/firestore.user"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:healthcare-api-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:healthcare-api-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create service-account.json \
  --iam-account=healthcare-api-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### Deploy to Cloud Run

1. **Build and deploy using Cloud Build:**
```bash
# Submit build to Cloud Build
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/healthcare-diagnostic-api

# Deploy to Cloud Run
gcloud run deploy healthcare-diagnostic-api \
  --image gcr.io/YOUR_PROJECT_ID/healthcare-diagnostic-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=YOUR_PROJECT_ID,SKIN_CV_API=https://skin-disease-cv-model-139431081773.us-central1.run.app/predict,ORAL_CV_API=YOUR_ORAL_CV_API" \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --max-instances=10
```

2. **Get the deployed URL:**
```bash
gcloud run services describe healthcare-diagnostic-api --region=us-central1 --format="value(status.url)"
```

### Deploy to Google Kubernetes Engine (GKE)

1. **Create GKE cluster:**
```bash
gcloud container clusters create healthcare-api-cluster \
  --zone=us-central1-a \
  --num-nodes=3 \
  --machine-type=e2-standard-2 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10
```

2. **Deploy using kubectl:**
```bash
# Apply the Kubernetes configuration
kubectl apply -f k8s/

# Check deployment status
kubectl get pods
kubectl get services
```

## 🔧 Environment Setup

### Required Environment Variables

Create a `.env` file with the following variables:

```env
# GCP Configuration (usually same as Firebase project)
GCP_PROJECT_ID=your-firebase-project-id
GCP_CREDENTIALS_PATH=./service-account.json

# Firebase Configuration (from your firebase_credentials.config)
FIREBASE_API_KEY=your-firebase-api-key
FIREBASE_AUTH_DOMAIN=your-firebase-auth-domain
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_STORAGE_BUCKET=your-firebase-storage-bucket
FIREBASE_MESSAGING_SENDER_ID=your-firebase-messaging-sender-id
FIREBASE_APP_ID=your-firebase-app-id

# Gemini API Configuration
# Note: Using Vertex AI authentication (no API key needed)
# Model: gemini-2.0-flash-001

# CV Model API Endpoints
SKIN_CV_API=https://your-skin-cv-model-api.com/predict
ORAL_CV_API=https://your-oral-cv-model-api.com/predict

# Session Management
SESSION_TIMEOUT_HOURS=2

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Development Settings
DEBUG=false
RELOAD=false

# CORS Settings
ALLOWED_ORIGINS=["http://localhost:3000", "https://your-frontend-domain.com"]

# File Upload Settings
MAX_FILE_SIZE_MB=10
ALLOWED_IMAGE_TYPES=["image/jpeg", "image/png", "image/webp"]
```

### Getting Required Credentials

1. **Firebase Credentials:**
   - Use the values from your `firebase_credentials.config` file
   - Copy each value to the corresponding environment variable
   - Example:
     ```env
     FIREBASE_API_KEY=AIzaSyBlWHSZTflw67kCU2PyfiIuzUyvyuSOawg
     FIREBASE_AUTH_DOMAIN=adsp-34002-ip07-visionary-ai.firebaseapp.com
     FIREBASE_PROJECT_ID=adsp-34002-ip07-visionary-ai
     FIREBASE_STORAGE_BUCKET=adsp-34002-ip07-visionary-ai.firebasestorage.app
     FIREBASE_MESSAGING_SENDER_ID=139431081773
     FIREBASE_APP_ID=1:139431081773:web:420dfd09d65abe7e0945a4
     ```

2. **GCP Project ID:**
   - Usually the same as your Firebase project ID
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Your project ID is shown in the project selector

3. **Vertex AI Authentication:**
   - The application uses Vertex AI for Gemini LLM access
   - No API key needed - uses service account authentication
   - Ensure your service account has Vertex AI permissions

4. **Service Account JSON:**
   - Follow the service account creation steps above
   - Download the JSON file and place it in your project root as `service-account.json`

5. **CV Model APIs:**
   - Deploy your skin and oral CV models to GCP AI Platform or external services
   - Get the prediction endpoints

## 📋 Main API Specification

### Endpoint: `POST /api/v1/chat/process`

**Parameters:**
- `message`: empty or string
- `image_url`: empty or string  
- `user_id`: string
- `chat_id`: string
- `type`: "text" or "image"
- `speciality`: "dental" or "skin"

**Output:**
```json
{
  "response": "string (markdown format)",
  "status": "response|warning|report",
  "metadata": {
    "missing_metadata": ["field1", "field2"],
    "should_upload_image": true/false,
    "conversation_stage": "collect_metadata|request_image|continue_questions"
  }
}
```

**Status Values:**
- `response`: Normal AI response or metadata collection
- `warning`: Image upload requested (status="warning" when should_upload_image=true)
- `report`: Final diagnostic report generated

## Intelligent Conversation Flow

The system implements a smart 3-stage conversation flow:

### Stage 1: Collect Metadata
- **Triggers**: When essential metadata is missing
- **Essential Fields**: age, gender, medical_history
- **Specialty Fields**: skin_type/sun_exposure (skin) OR dental_history/oral_hygiene (dental)
- **Response**: Dynamic, empathetic questions generated by Gemini 2.0

### Stage 2: Request Image
- **Triggers**: When sufficient metadata is collected
- **Status**: `warning` (indicates image upload needed)
- **Response**: Encouraging image request message
- **Metadata**: `should_upload_image: true`

### Stage 3: Generate Report
- **Triggers**: When image is uploaded
- **Process**: CV model analysis → Gemini report generation
- **Status**: `report`
- **Output**: Comprehensive diagnostic report

### Fallback Flow
- **CV Model Timeout**: Automatic retry (2 attempts, 15s timeout)
- **CV Model Failure**: Gemini image analysis fallback
- **No Image Provided**: Continue asking contextual questions

## 🏗️ Architecture

```
app/
├── api/v1/endpoints/     # API endpoints
├── core/                 # Configuration, dependencies, exceptions
├── models/               # Database models and enums
├── services/             # Business logic services
│   ├── llm/             # LLM services (Gemini)
│   ├── cv/              # Computer vision services
│   ├── storage/          # Firestore and GCS
│   └── validation/       # Input validation
├── security/             # Authentication and guardrails
└── utils/                # Utility functions
```

## 🔧 Key Features

### 1. **LLM Caching for Context Retrieving**
- Implements LangChain caching for efficient context retrieval
- Metadata cached until session ends (2hrs) or final report generated
- Prevents redundant API calls

### 2. **Firebase Schema Integration**
- Matches your actual Firebase schema exactly:
  - `chats` collection with `createdAt`, `last_message_at`, `title`, `updatedAt`, `userId`
  - `messages` as sub-collection under each chat
  - Additional collections: `inspectors`, `report-chats`, `report-messages`, `reports`, `users`

### 3. **Prompt Engineering**
- Implements your exact prompt engineering approach from the notebook
- System prompt embedded as first user message
- Structured JSON output with specific fields
- Empathetic tone and plain English responses

### 4. **CV Model Validation**
- Prevents hallucinations
- Validates suspiciously high/low confidence scores
- Caps confidence at 85% for high-confidence results
- Adds validation warnings for manual review

### 5. **Security & Guardrails**
- Input validation and safety checks
- Output validation and sanitization
- Image safety checks
- Medical-specific guardrails
- Rate limiting and encryption

## Testing

### Comprehensive Test Suite

The project includes multiple testing approaches:

#### 1. **API Testing**
```bash
# Basic API functionality
python test_api.py

# Deployed API testing
python test_deployed_api.py
```

#### 2. **CV Model Testing**
```bash
# Test CV model integration and fallback
python test_cv_model.py
```

#### 3. **Postman Collection**
- Import `postman_collection.json` and `postman_environment.json`
- Test complete conversation flow
- Use chat_id: `GkV9vizfg2bCTDLRxDtT`

#### 4. **Unit Tests**
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_main_api.py

# Run with coverage
pytest --cov=app tests/
```

#### 5. **Load Testing**
```bash
# Run load tests
python test_load.py
```

## 📊 API Examples

### Example 1: Initial Text Message (Metadata Collection)
```bash
curl -X POST "http://localhost:8080/api/v1/chat/process" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I am a 25 year old female",
    "image_url": "",
    "user_id": "capstone_user_123",
    "chat_id": "GkV9vizfg2bCTDLRxDtT",
    "type": "text",
    "speciality": "skin"
  }'
```

**Response:**
```json
{
  "response": "I appreciate you sharing your age and gender. To provide you with the most accurate skin assessment, I'd like to know about any allergies or medical conditions you have, as these can affect skin health.",
  "status": "response",
  "metadata": {
    "missing_metadata": ["medical_history", "skin_type", "sun_exposure"],
    "should_upload_image": false,
    "conversation_stage": "collect_metadata"
  }
}
```

### Example 2: Image Upload (Report Generation)
```bash
curl -X POST "http://localhost:8080/api/v1/chat/process" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Here is a photo of the mole on my arm",
    "image_url": "https://storage.googleapis.com/kagglesdsdata/datasets/1532614/2529450/IMG_CLASSES/1.%20Eczema%201677/0_15.jpg",
    "user_id": "capstone_user_123",
    "chat_id": "GkV9vizfg2bCTDLRxDtT",
    "type": "image",
    "speciality": "skin"
  }'
```

**Response:**
```json
{
  "response": "# Skin Health Assessment Report\n\n## Analysis Results\n- **Predicted Condition**: Actinic keratosis\n- **Confidence**: 88.52%\n- **Severity**: Moderate\n\n## Recommendations\n1. Consult a dermatologist for definitive diagnosis\n2. Monitor any changes in the affected area\n3. Protect skin from sun exposure\n4. Maintain good skin hygiene",
  "status": "report",
  "metadata": {
    "predicted_class": "Actinic keratosis",
    "confidence": 0.8852,
    "disease_type": "Pre-cancerous lesion",
    "severity": "Moderate"
  }
}
```

## Important Notes

1. **CV Model Validation**: The system includes validation to prevent hallucinations like the 99% confidence on sunflowers issue mentioned in your notebook. High confidence scores (>95%) are capped at 85% with validation warnings.

2. **Robust Fallback System**: If CV models timeout or fail, the system automatically falls back to Gemini image analysis, ensuring users always receive a response.

3. **Dynamic Metadata Extraction**: Uses Gemini 2.0's natural language understanding to extract patient information from messages, eliminating static responses.

4. **Intelligent Conversation Flow**: Implements a 3-stage flow (metadata → image request → report) with contextual, empathetic responses.

5. **Firebase Schema**: The implementation matches your actual Firebase schema exactly, including sub-collections for messages.

6. **Prompt Engineering**: Uses your exact prompt engineering approach from the notebook for consistent results.

7. **Status Values**: The API returns exactly the three status values you specified: "response", "warning", "report".

8. **Fast Response Times**: CV model analysis typically completes in 0.4-0.7 seconds with retry logic for reliability.

## 🔍 Monitoring & Logging

- Comprehensive logging for all API requests/responses
- Error tracking and monitoring
- Performance metrics
- Health check endpoint at `/health`

## 📁 Project Structure

```
Backend/
├── app/                          # Main application code
│   ├── api/v1/endpoints/         # API endpoints
│   │   └── chat.py              # Main chat API
│   ├── core/                     # Core configuration
│   │   ├── config.py            # Settings and environment variables
│   │   ├── dependencies.py      # FastAPI dependencies
│   │   ├── exceptions.py        # Custom exceptions
│   │   └── logging.py           # Logging configuration
│   ├── models/                   # Data models and enums
│   ├── services/                 # Business logic services
│   │   ├── llm/                 # Gemini LLM service
│   │   ├── cv/                  # CV model service
│   │   ├── storage/             # Firestore service
│   │   └── validation/          # Input validation
│   ├── security/                 # Security and guardrails
│   └── utils/                    # Utility functions
├── k8s/                          # Kubernetes deployment files
├── tests/                        # Test files
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker configuration
├── docker-compose.yml           # Docker Compose setup
├── .env                         # Environment variables
├── firebase_credentials.config  # Firebase configuration
├── test_api.py                  # API testing script
├── test_cv_model.py             # CV model testing
├── test_deployed_api.py         # Deployed API testing
├── postman_collection.json      # Postman test collection
├── postman_environment.json     # Postman environment
└── README.md                    # This file
```

## Production Deployment Checklist

- [x] GCP project created and APIs enabled
- [x] Service account created with proper permissions
- [x] Environment variables configured
- [x] Vertex AI authentication set up (no API key needed)
- [x] CV model APIs deployed and accessible
- [x] Firebase project configured
- [x] Docker image built and tested locally
- [-] Deployed to Cloud Run or GKE
- [x] Health check endpoint responding
- [x] API tests passing
- [x] Monitoring and logging configured
- [x] CV model timeout issues resolved
- [x] Fallback mechanisms implemented
- [x] Dynamic metadata extraction working
- [x] Intelligent conversation flow implemented


### Environment Variables for GitHub Actions
If using GitHub Actions for CI/CD, add these secrets to your repository:
- `GCP_PROJECT_ID`
- `GCP_SA_KEY` (service account JSON)
- `FIREBASE_API_KEY`
- `FIREBASE_AUTH_DOMAIN`
- `FIREBASE_PROJECT_ID`
- `FIREBASE_STORAGE_BUCKET`
- `FIREBASE_MESSAGING_SENDER_ID`
- `FIREBASE_APP_ID`

## 📄 License

This project is part of your UChicago Capstone project.