# Visionary AI - Healthcare Diagnostic Application

A comprehensive AI-powered healthcare diagnostic platform that combines advanced computer vision models with large language models to provide intelligent medical assistance for skin and dental health analysis.

## 🌟 Overview

Visionary AI is a full-stack healthcare application that leverages cutting-edge AI technologies to provide accurate medical diagnostics and recommendations. The platform consists of a React Native mobile frontend and a FastAPI backend, integrated with Google Cloud Platform services and Firebase for a seamless user experience.

## 🏗️ Architecture

```
Visionary-AI-App/
├── backend/          # FastAPI backend with AI services
├── frontend/         # React Native mobile application
└── README.md         # This file
```

### Backend (FastAPI)
- **AI-Powered Analysis**: Integration with Gemini 2.0 LLM and custom CV models
- **Intelligent Conversation Flow**: Dynamic metadata collection → Image analysis → Report generation
- **Robust Fallback System**: Automatic fallback to Gemini when CV models fail
- **Production Ready**: Comprehensive error handling, logging, and monitoring

### Frontend (React Native)
- **Cross-Platform Mobile App**: iOS and Android support with Expo
- **AI Chat Interface**: Interactive medical consultations with Gemini AI
- **Doctor Recommendations**: Location-based healthcare provider search
- **User Authentication**: Secure Firebase Authentication
- **Medical Profiles**: Comprehensive health history management

## 🚀 Key Features

### 🤖 AI-Powered Diagnostics
- **Skin Disease Analysis**: Computer vision models for dermatological conditions
- **Dental Health Assessment**: Oral health analysis and recommendations
- **Intelligent Conversation**: Dynamic metadata collection and empathetic responses
- **Anti-Hallucination Validation**: Confidence score validation to prevent false positives

### 📱 Mobile Application
- **Real-time Chat**: Live messaging with AI medical assistant
- **Image Upload**: Photo capture and analysis for medical conditions
- **Speech-to-Text**: Voice input capabilities for hands-free interaction
- **Cross-platform**: Native iOS and Android support

### 🔧 Backend Services
- **FastAPI Framework**: High-performance async API
- **Firebase Integration**: Real-time database with exact schema matching
- **Google Cloud Platform**: Vertex AI, Firestore, and Cloud Storage
- **Rate Limiting**: Production-ready security and performance controls

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **AI/ML**: Google Gemini 2.0, Custom CV Models
- **Database**: Firebase Firestore
- **Cloud**: Google Cloud Platform (Vertex AI, Cloud Storage)
- **Deployment**: Docker, Cloud Run
- **Testing**: Pytest, Postman Collections

### Frontend
- **Framework**: React Native with Expo
- **Navigation**: Expo Router
- **State Management**: React Hooks
- **Authentication**: Firebase Auth
- **Database**: Firebase Firestore
- **Styling**: React Native StyleSheet

## 📋 Prerequisites

### Backend Requirements
- Python 3.9+
- Google Cloud Platform account
- Firebase project
- Vertex AI access
- Docker (for containerized deployment)

### Frontend Requirements
- Node.js (v16 or higher)
- npm or yarn
- Expo CLI
- iOS Simulator (for iOS development)
- Android Studio (for Android development)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Mahenderreddyp/Visionary-AI-App.git
cd Visionary-AI-App
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
conda create -n backend python=3.11
conda activate backend

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp firebase_credentials.config .env
# Edit .env with your specific values

# Run the application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Fill in your Firebase and Gemini API keys

# Start the development server
npx expo start
```

## 🔧 Configuration

### Backend Environment Variables
```env
# GCP Configuration
GCP_PROJECT_ID=your-firebase-project-id
GCP_CREDENTIALS_PATH=./service-account.json

# Firebase Configuration
FIREBASE_API_KEY=your-firebase-api-key
FIREBASE_AUTH_DOMAIN=your-firebase-auth-domain
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_STORAGE_BUCKET=your-firebase-storage-bucket
FIREBASE_MESSAGING_SENDER_ID=your-firebase-messaging-sender-id
FIREBASE_APP_ID=your-firebase-app-id

# CV Model API Endpoints
SKIN_CV_API=https://your-skin-cv-model-api.com/predict
ORAL_CV_API=https://your-oral-cv-model-api.com/predict

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=60
```

### Frontend Environment Variables
```env
EXPO_PUBLIC_FIREBASE_API_KEY=your_firebase_api_key
EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
EXPO_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET=your_project.firebasestorage.app
EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
EXPO_PUBLIC_FIREBASE_APP_ID=your_app_id
GEMINI_API_KEY=your_gemini_api_key
```

## 📊 API Documentation

### Main Endpoint: `POST /api/v1/chat/process`

**Request:**
```json
{
  "message": "I have a mole on my arm that's been growing",
  "image_url": "https://example.com/image.jpg",
  "user_id": "user_123",
  "chat_id": "chat_456",
  "type": "image",
  "speciality": "skin"
}
```

**Response:**
```json
{
  "response": "# Skin Health Assessment Report\n\n## Analysis Results\n- **Predicted Condition**: Actinic keratosis\n- **Confidence**: 88.52%\n- **Severity**: Moderate\n\n## Recommendations\n1. Consult a dermatologist for definitive diagnosis\n2. Monitor any changes in the affected area\n3. Protect skin from sun exposure",
  "status": "report",
  "metadata": {
    "predicted_class": "Actinic keratosis",
    "confidence": 0.8852,
    "disease_type": "Pre-cancerous lesion",
    "severity": "Moderate"
  }
}
```

## 🧪 Testing

### Backend Testing
```bash
cd backend

# Run API tests
python test_api.py

# Run CV model tests
python test_cv_model.py

# Run deployed API tests
python test_deployed_api.py

# Run unit tests
pytest

# Run with coverage
pytest --cov=app tests/
```

### Frontend Testing
```bash
cd frontend

# Run tests
npm test

# Run linting
npm run lint
```

### Postman Collection
Import `backend/postman_collection.json` and `backend/postman_environment.json` for comprehensive API testing.

## 🐳 Docker Deployment

### Backend
```bash
cd backend

# Build Docker image
docker build -t healthcare-diagnostic-api .

# Run container
docker run -d \
  --name healthcare-api \
  -p 8080:8080 \
  -e GCP_PROJECT_ID=your-project-id \
  healthcare-diagnostic-api
```

### Frontend
```bash
cd frontend

# Build for production
npx expo build:android
npx expo build:ios
```

## ☁️ Cloud Deployment

### Google Cloud Run (Backend)
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/healthcare-diagnostic-api
gcloud run deploy healthcare-diagnostic-api \
  --image gcr.io/YOUR_PROJECT_ID/healthcare-diagnostic-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Expo Application Services (Frontend)
```bash
cd frontend

# Deploy to EAS
npx eas build --platform all
npx eas submit --platform all
```

## 🔍 Monitoring & Logging

- **Health Check**: `/health` endpoint for API status
- **Comprehensive Logging**: Request/response logging with performance metrics
- **Error Tracking**: Custom exception handling with detailed error reporting
- **Rate Limiting**: Production-ready request throttling

## 📁 Project Structure

### Backend Structure
```
backend/
├── app/
│   ├── api/v1/endpoints/     # API endpoints
│   ├── core/                 # Configuration and dependencies
│   ├── models/               # Database models and enums
│   ├── services/             # Business logic services
│   │   ├── llm/             # Gemini LLM integration
│   │   ├── cv/              # Computer vision services
│   │   ├── storage/          # Firestore and GCS
│   │   └── validation/       # Input validation
│   ├── security/             # Authentication and guardrails
│   └── utils/                # Utility functions
├── tests/                    # Test files
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker configuration
└── README.md                # Backend documentation
```

### Frontend Structure
```
frontend/
├── app/                     # Main application screens
│   ├── (tabs)/             # Tab navigation screens
│   ├── chat/               # Chat-related screens
│   └── ...
├── components/             # Reusable UI components
├── assets/                 # Images, fonts, and static files
├── utils/                  # Utility functions
├── types/                  # TypeScript type definitions
├── firebaseConfig.ts       # Firebase configuration
└── README.md               # Frontend documentation
```

## 🔒 Security Features

- **Input Validation**: Comprehensive validation for all user inputs
- **Output Sanitization**: Safe response generation
- **Rate Limiting**: Protection against abuse
- **Authentication**: Secure Firebase Authentication
- **Medical Guardrails**: Specialized safety checks for medical content
- **Image Safety**: Validation and safety checks for uploaded images

## 🎯 Key Capabilities

### Intelligent Conversation Flow
1. **Metadata Collection**: Dynamic collection of patient information
2. **Image Request**: Contextual requests for medical images
3. **Analysis & Reporting**: CV model analysis with AI-generated reports

### Fallback Mechanisms
- **CV Model Timeout**: Automatic retry with 15s timeout
- **CV Model Failure**: Gemini image analysis fallback
- **Error Recovery**: Graceful handling of service failures

### Performance Optimizations
- **LLM Caching**: LangChain caching for efficient context retrieval
- **Fast Response**: Sub-second CV model analysis
- **Async Processing**: Non-blocking API operations

## 📄 License

This project is part of a UChicago Capstone project. All rights reserved.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For support and questions, please open an issue in the GitHub repository or contact the development team.

---

**Note**: This application is designed for educational and research purposes. It should not be used as a substitute for professional medical advice, diagnosis, or treatment.
