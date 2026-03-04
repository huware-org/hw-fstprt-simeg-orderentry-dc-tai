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
  --set-env-vars GEMINI_API_KEY="your_api_key_here" \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10
```

### Production deploy (with Secret Manager):

```bash
# Create secret
echo -n "your_actual_gemini_api_key" | gcloud secrets create GEMINI_API_KEY --data-file=-

# Deploy with secret
gcloud run deploy simeg-order-entry-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production,FRONTEND_URL=* \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10
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
