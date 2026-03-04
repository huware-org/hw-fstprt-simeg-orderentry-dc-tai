# Google Cloud Run Deployment Guide

## Prerequisites

1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
2. Authenticate: `gcloud auth login`
3. Set your project: `gcloud config set project YOUR_PROJECT_ID`

## Step 1: Add pydantic-settings Dependency

Run this command to add the required dependency:

```bash
uv add pydantic-settings
```

This will update your `pyproject.toml` and `uv.lock` files.

## Step 2: Build and Test Locally (Optional)

Build the Docker image:

```bash
docker build -t simeg-order-entry-backend .
```

Test locally with environment variables:

```bash
docker run -p 8080:8080 \
  -e GEMINI_API_KEY="your_api_key_here" \
  -e FRONTEND_URL="*" \
  simeg-order-entry-backend
```

Visit http://localhost:8080 to verify the health check endpoint.

## Step 3: Deploy to Cloud Run

### Option A: Deploy with gcloud (Recommended)

```bash
gcloud run deploy simeg-order-entry-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10
```

Note: This assumes you've stored your `GEMINI_API_KEY` in Google Secret Manager.

### Option B: Deploy with Docker Image

1. Build and push to Google Container Registry:

```bash
# Enable required APIs
gcloud services enable containerregistry.googleapis.com run.googleapis.com

# Configure Docker to use gcloud
gcloud auth configure-docker

# Build and tag
docker build -t gcr.io/YOUR_PROJECT_ID/simeg-order-entry-backend .

# Push to GCR
docker push gcr.io/YOUR_PROJECT_ID/simeg-order-entry-backend

# Deploy
gcloud run deploy simeg-order-entry-backend \
  --image gcr.io/YOUR_PROJECT_ID/simeg-order-entry-backend \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10
```

## Step 4: Configure Environment Variables

### Using Google Secret Manager (Recommended for Production)

1. Create a secret for your API key:

```bash
echo -n "your_actual_gemini_api_key" | gcloud secrets create GEMINI_API_KEY --data-file=-
```

2. Grant Cloud Run access to the secret:

```bash
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

3. Update the service to use the secret (already included in deploy command above).

### Using Environment Variables Directly (Development Only)

```bash
gcloud run services update simeg-order-entry-backend \
  --region us-central1 \
  --set-env-vars GEMINI_API_KEY="your_api_key_here",FRONTEND_URL="https://your-frontend-url.run.app"
```

## Step 5: Update CORS for Production

Once your frontend is deployed, update the `FRONTEND_URL`:

```bash
gcloud run services update simeg-order-entry-backend \
  --region us-central1 \
  --set-env-vars FRONTEND_URL="https://your-frontend-service.run.app"
```

## Step 6: Get Your Backend URL

After deployment, Cloud Run will provide a URL like:

```
https://simeg-order-entry-backend-XXXXX-uc.a.run.app
```

Use this URL in your frontend configuration.

## Monitoring and Logs

View logs:

```bash
gcloud run services logs read simeg-order-entry-backend --region us-central1
```

View service details:

```bash
gcloud run services describe simeg-order-entry-backend --region us-central1
```

## Cost Optimization

Cloud Run charges only for actual usage. To optimize costs:

1. Set `--min-instances 0` (default) to scale to zero when idle
2. Adjust `--memory` and `--cpu` based on actual needs
3. Set `--max-instances` to prevent unexpected scaling costs
4. Use `--concurrency` to handle multiple requests per instance

## Troubleshooting

### Container fails to start

Check logs for startup errors:

```bash
gcloud run services logs read simeg-order-entry-backend --region us-central1 --limit 50
```

### GEMINI_API_KEY not found

Verify the secret is accessible:

```bash
gcloud secrets versions access latest --secret="GEMINI_API_KEY"
```

### CORS errors

Update `FRONTEND_URL` to match your frontend domain exactly (no trailing slash).

## CI/CD Integration

For automated deployments, add this to your GitHub Actions or Cloud Build:

```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - uses: google-github-actions/deploy-cloudrun@v1
        with:
          service: simeg-order-entry-backend
          region: us-central1
          source: .
```
