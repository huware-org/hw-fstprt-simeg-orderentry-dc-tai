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

You have two options for deployment: using command-line flags or using a `service.yaml` configuration file.

### Option A: Deploy with service.yaml (Recommended for Production)

The `service.yaml` file in the project root contains all service configuration. Before deploying:

1. Update `service.yaml` with your project details:
   - Replace `PROJECT_ID` with your GCP project ID
   - Replace `PROJECT_NUMBER` with your GCP project number
   - Update `FRONTEND_URL` after frontend deployment

2. Build and push the Docker image:

```bash
# Enable required APIs
gcloud services enable containerregistry.googleapis.com run.googleapis.com

# Configure Docker to use gcloud
gcloud auth configure-docker

# Build and tag
docker build -t gcr.io/YOUR_PROJECT_ID/simeg-order-entry-backend:latest .

# Push to GCR
docker push gcr.io/YOUR_PROJECT_ID/simeg-order-entry-backend:latest
```

3. Deploy using the service.yaml:

```bash
gcloud run services replace service.yaml --region us-central1
```

### Option B: Deploy with gcloud CLI flags

Deploy directly from source code:

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

### Option C: Deploy with Docker Image

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
  --set-env-vars ENVIRONMENT=production,FRONTEND_URL=* \
  --set-secrets GEMINI_API_KEY=simeg-prototype-gemini-api-key:latest \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10
```

## Step 4: Verify Secret Access

Your API key is stored in the secret `simeg-prototype-gemini-api-key`. Verify Cloud Run can access it:

```bash
# Check if the secret exists
gcloud secrets describe simeg-prototype-gemini-api-key

# Grant Cloud Run service account access to the secret (if not already granted)
gcloud secrets add-iam-policy-binding simeg-prototype-gemini-api-key \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

To find your project number:
```bash
gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)"
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
