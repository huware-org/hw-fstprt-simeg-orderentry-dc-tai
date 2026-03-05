#!/bin/bash
# Simple deployment script without Git checks
# Use this if you just want to deploy quickly

set -e

PROJECT_ID="poc-huware-ai"
SERVICE_NAME="simeg-order-entry-backend"
REGION="europe-west1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🔨 Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .

echo "📤 Pushing to GCR..."
docker push ${IMAGE_NAME}:latest

echo "🚀 Deploying to Cloud Run..."
gcloud run services replace service.yaml --region ${REGION}

echo "✅ Deployment complete!"
echo ""
echo "Service URL:"
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format="value(status.url)"
