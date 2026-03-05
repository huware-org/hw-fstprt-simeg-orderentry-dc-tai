#!/bin/bash
# Deploy Simeg Order Entry Backend to Google Cloud Run
# This script builds, pushes, and deploys the service using service.yaml

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="poc-huware-ai"
SERVICE_NAME="simeg-order-entry-backend"
REGION="europe-west1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Simeg Order Entry Backend Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "service.yaml" ]; then
    echo -e "${RED}Error: service.yaml not found!${NC}"
    echo "Please run this script from the project root directory."
    exit 1
fi

if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}Error: Dockerfile not found!${NC}"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Warning: You have uncommitted changes!${NC}"
    echo -e "${YELLOW}   The Docker image will include these changes.${NC}"
    echo ""
    git status --short
    echo ""
    read -p "Continue with deployment? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Deployment cancelled.${NC}"
        exit 1
    fi
fi

# Get current git info
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo -e "${BLUE}📋 Deployment Info:${NC}"
echo "  Project ID:    ${PROJECT_ID}"
echo "  Service:       ${SERVICE_NAME}"
echo "  Region:        ${REGION}"
echo "  Git Branch:    ${GIT_BRANCH}"
echo "  Git Commit:    ${GIT_COMMIT}"
echo "  Image:         ${IMAGE_NAME}:latest"
echo ""

# Confirm deployment
read -p "Proceed with deployment? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Deployment cancelled.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🔨 Step 1/3: Building Docker image...${NC}"
docker build -t ${IMAGE_NAME}:latest -t ${IMAGE_NAME}:${GIT_COMMIT} .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker build failed!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}📤 Step 2/3: Pushing image to GCR...${NC}"
docker push ${IMAGE_NAME}:latest
docker push ${IMAGE_NAME}:${GIT_COMMIT}

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker push failed!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🚀 Step 3/3: Deploying to Cloud Run...${NC}"
gcloud run services replace service.yaml --region ${REGION}

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Deployment failed!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Deployment successful!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format="value(status.url)" 2>/dev/null)

if [ -n "$SERVICE_URL" ]; then
    echo -e "${BLUE}🌐 Service URL:${NC} ${SERVICE_URL}"
    echo ""
    echo "Test the API:"
    echo "  curl ${SERVICE_URL}"
fi

echo ""
echo -e "${BLUE}📊 View logs:${NC}"
echo "  gcloud run services logs read ${SERVICE_NAME} --region ${REGION}"
echo ""
echo -e "${BLUE}📝 Service details:${NC}"
echo "  gcloud run services describe ${SERVICE_NAME} --region ${REGION}"
echo ""
