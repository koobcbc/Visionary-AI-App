#!/bin/bash

# =============================================================================
# Deployment Script for Skin Specialist Agent
# =============================================================================

set -e  # Exit on error

# Configuration
PROJECT_ID="adsp-34002-ip07-visionary-ai"
REGION="us-central1"
SERVICE_NAME="skin-specialist-agent"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "================================================"
echo "Deploying Skin Specialist Agent to Cloud Run"
echo "================================================"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo "================================================"

# Step 1: Set the project
echo ""
echo "📋 Step 1: Setting Google Cloud project..."
gcloud config set project ${PROJECT_ID}

# Step 2: Enable required APIs
echo ""
echo "🔧 Step 2: Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    aiplatform.googleapis.com \
    --project=${PROJECT_ID}

echo "✅ APIs enabled"

# Step 3: Build the Docker image
echo ""
echo "🏗️ Step 3: Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME} \
    --project=${PROJECT_ID} \
    --timeout=20m

echo "✅ Docker image built: ${IMAGE_NAME}"

# Step 4: Deploy to Cloud Run
echo ""
echo "🚀 Step 4: Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --set-env-vars GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION} \
    --project=${PROJECT_ID}

echo ""
echo "✅ Deployment complete!"

# Step 5: Get the service URL
echo ""
echo "📍 Step 5: Getting service URL..."
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --format 'value(status.url)' \
    --project=${PROJECT_ID})

echo ""
echo "================================================"
echo "✅ DEPLOYMENT SUCCESSFUL!"
echo "================================================"
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "Test endpoints:"
echo "  Health Check: ${SERVICE_URL}/health"
echo "  Start Consultation: ${SERVICE_URL}/start"
echo "  Chat: ${SERVICE_URL}/chat"
echo "  Get State: ${SERVICE_URL}/state/<thread_id>"
echo ""
echo "Example curl commands:"
echo ""
echo "# Health check"
echo "curl ${SERVICE_URL}/health"
echo ""
echo "# Start consultation"
echo "curl -X POST ${SERVICE_URL}/start \\"
echo "  -H 'Content-Type: application/json'"
echo ""
echo "# Send message"
echo "curl -X POST ${SERVICE_URL}/chat \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"thread_id\": \"your-thread-id\", \"message\": \"I am 45 years old male\"}'"
echo "================================================"