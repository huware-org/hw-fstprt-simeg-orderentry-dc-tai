# Deployment Documentation

This directory contains all deployment-related documentation for the Simeg Order Entry Backend.

## Quick Start

For your first deployment, use the existing secret `simeg-prototype-gemini-api-key`:

```bash
gcloud run deploy simeg-order-entry-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets GEMINI_API_KEY=simeg-prototype-gemini-api-key:latest \
  --memory 1Gi
```

## Documentation Files

### [DEPLOYMENT_COMMANDS.md](DEPLOYMENT_COMMANDS.md)
Quick reference with copy-paste commands for common deployment tasks.

**Use this when:** You need to quickly deploy or update the service.

### [CLOUD_RUN_DEPLOYMENT.md](CLOUD_RUN_DEPLOYMENT.md)
Comprehensive deployment guide covering all deployment options, configuration, monitoring, and troubleshooting.

**Use this when:** Setting up deployment for the first time or need detailed explanations.

### [SERVICE_YAML_GUIDE.md](SERVICE_YAML_GUIDE.md)
Complete guide to using `service.yaml` for declarative Cloud Run configuration.

**Use this when:** 
- Setting up CI/CD pipelines
- Managing multiple environments
- Need version-controlled infrastructure configuration

## Deployment Options Comparison

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| **gcloud CLI** | Quick deployments, testing | Fast, simple, deploys from source | Configuration not version controlled |
| **service.yaml** | Production, CI/CD | Declarative, version controlled, reproducible | Requires separate image build |
| **Docker + gcloud** | Custom workflows | Full control over build process | More steps required |

## Your Existing Setup

- **Secret Name:** `simeg-prototype-gemini-api-key`
- **Region:** us-central1 (recommended)
- **Service Name:** simeg-order-entry-backend

## Common Tasks

### Deploy from source
```bash
gcloud run deploy simeg-order-entry-backend \
  --source . \
  --region us-central1 \
  --set-secrets GEMINI_API_KEY=simeg-prototype-gemini-api-key:latest
```

### Deploy with service.yaml
```bash
# 1. Update service.yaml with your PROJECT_ID and PROJECT_NUMBER
# 2. Build and push
docker build -t gcr.io/YOUR_PROJECT_ID/simeg-order-entry-backend:latest .
docker push gcr.io/YOUR_PROJECT_ID/simeg-order-entry-backend:latest
# 3. Deploy
gcloud run services replace service.yaml --region us-central1
```

### Update environment variables
```bash
gcloud run services update simeg-order-entry-backend \
  --region us-central1 \
  --set-env-vars FRONTEND_URL="https://your-frontend.run.app"
```

### View logs
```bash
gcloud run services logs read simeg-order-entry-backend --region us-central1
```

### Get service URL
```bash
gcloud run services describe simeg-order-entry-backend \
  --region us-central1 \
  --format="value(status.url)"
```

## Next Steps After Deployment

1. **Get the backend URL** from the deployment output
2. **Update CORS** by setting `FRONTEND_URL` to your frontend domain
3. **Test the API** by visiting `https://your-backend-url.run.app`
4. **Configure your frontend** to use the backend URL
5. **Set up monitoring** in Google Cloud Console

## Need Help?

- Check [CLOUD_RUN_DEPLOYMENT.md](CLOUD_RUN_DEPLOYMENT.md) for troubleshooting
- View service logs: `gcloud run services logs read simeg-order-entry-backend --region us-central1`
- Describe service: `gcloud run services describe simeg-order-entry-backend --region us-central1`
