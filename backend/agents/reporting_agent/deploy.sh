#!/bin/bash

# Dermatology Reporting Agent - Deploy to Google Cloud Run
# =========================================================

# Configuration - CHANGE THESE VALUES
PROJECT_ID="adsp-34002-ip07-visionary-ai"  # Your GCP project ID
SERVICE_NAME="reporting-agent"
REGION="us-central1"  # Change to your preferred region
GOOGLE_API_KEY="api_key"  # Your Gemini API key

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Deploying Reporting Agent${NC}"
echo -e "${BLUE}================================${NC}\n"

# Step 1: Set the project
echo -e "${GREEN}Step 1: Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Step 2: Enable required APIs
echo -e "\n${GREEN}Step 2: Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com

# Step 3: Build the container
echo -e "\n${GREEN}Step 3: Building Docker container...${NC}"
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Step 4: Deploy to Cloud Run
echo -e "\n${GREEN}Step 4: Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=$GOOGLE_API_KEY \
  --memory 1Gi \
  --timeout 300 \
  --max-instances 10

# Step 5: Get the service URL
echo -e "\n${GREEN}Step 5: Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo -e "\n${BLUE}================================${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "\nService URL: ${GREEN}$SERVICE_URL${NC}"
echo -e "\nTest your service:"
echo -e "  Health check: ${BLUE}curl $SERVICE_URL/health${NC}"
echo -e "\nAPI Endpoint: ${BLUE}$SERVICE_URL/generate_report${NC}"
echo -e "${BLUE}================================${NC}\n"