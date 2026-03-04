# Quick Deployment Commands

## Step 1: Add pydantic-settings dependency

```bash
uv add pydantic-settings
```

## Step 2: Test locally (optional)

```bash
# Build Docker image
docker build -t simeg-order-entry-backend .

# Run locally
docker run -p 8080:8080 \
  -e GEMINI_API_KEY="your_api_key_here" \
  -e FRONTEND_URL="*" \
  simeg-order-entry-backend
```

## Step 3: Deploy to Cloud Run

### Quick deploy (from source):

```bash
gcloud run deploy simeg-order-entry-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production,FRONTEND_URL=* \
  --set-secrets GEMINI_API_KEY=simeg-prototype-gemini-api-key:latest \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10
```

### Deploy with service.yaml (Recommended):

```bash
# 1. Update service.yaml with your PROJECT_ID and PROJECT_NUMBER

# 2. Build and push image
docker build -t gcr.io/YOUR_PROJECT_ID/simeg-order-entry-backend:latest .
docker push gcr.io/YOUR_PROJECT_ID/simeg-order-entry-backend:latest

# 3. Deploy
gcloud run services replace service.yaml --region us-central1
```

### Verify secret access:

```bash
# Check secret exists
gcloud secrets describe simeg-prototype-gemini-api-key

# Grant access if needed
gcloud secrets add-iam-policy-binding simeg-prototype-gemini-api-key \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Step 4: Update CORS after frontend deployment

```bash
gcloud run services update simeg-order-entry-backend \
  --region us-central1 \
  --set-env-vars FRONTEND_URL="https://your-frontend-service.run.app"
```

## Useful commands

```bash
# View logs
gcloud run services logs read simeg-order-entry-backend --region us-central1

# Get service URL
gcloud run services describe simeg-order-entry-backend --region us-central1 --format="value(status.url)"

# Update environment variables
gcloud run services update simeg-order-entry-backend \
  --region us-central1 \
  --set-env-vars KEY=VALUE
```
