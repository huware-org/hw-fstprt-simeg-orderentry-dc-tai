# Cloud Run service.yaml Configuration Guide

## Overview

The `service.yaml` file is a declarative configuration for your Cloud Run service. It's similar to App Engine's `app.yaml` but uses the Knative Serving API format that Cloud Run is built on.

## Benefits of Using service.yaml

1. **Version Control**: Configuration is tracked in Git alongside your code
2. **Reproducibility**: Same configuration across environments
3. **CI/CD Friendly**: Easy to integrate into deployment pipelines
4. **Documentation**: Self-documenting infrastructure
5. **Declarative**: Describe what you want, not how to get there

## service.yaml vs gcloud CLI

### Using service.yaml
```bash
gcloud run services replace service.yaml --region us-central1
```

**Pros:**
- All configuration in one file
- Easy to review changes in Git
- Better for CI/CD pipelines
- Can be templated for multiple environments

**Cons:**
- Need to build and push Docker image separately
- Must update PROJECT_ID and PROJECT_NUMBER manually

### Using gcloud CLI
```bash
gcloud run deploy simeg-order-entry-backend \
  --source . \
  --set-secrets GEMINI_API_KEY=simeg-prototype-gemini-api-key:latest \
  ...
```

**Pros:**
- Quick for one-off deployments
- Can deploy directly from source
- No need to manage Docker images manually

**Cons:**
- Configuration scattered across command-line flags
- Harder to track changes
- Must remember all flags for each deployment

## service.yaml Structure Explained

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: simeg-order-entry-backend          # Service name
  annotations:
    run.googleapis.com/ingress: all        # Allow all traffic
    run.googleapis.com/launch-stage: BETA  # Use beta features
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: '10'      # Max instances
        autoscaling.knative.dev/minScale: '0'       # Min instances (scale to zero)
        run.googleapis.com/cpu-throttling: 'true'   # Throttle CPU when idle
        run.googleapis.com/startup-cpu-boost: 'true' # Boost CPU during startup
    spec:
      containerConcurrency: 80              # Max concurrent requests per instance
      timeoutSeconds: 300                   # Request timeout (5 minutes)
      serviceAccountName: PROJECT_NUMBER-compute@developer.gserviceaccount.com
      containers:
      - image: gcr.io/PROJECT_ID/simeg-order-entry-backend:latest
        ports:
        - name: http1
          containerPort: 8080               # Must match Dockerfile EXPOSE
        env:
        - name: ENVIRONMENT
          value: production
        - name: FRONTEND_URL
          value: "*"                        # Update after frontend deployment
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: simeg-prototype-gemini-api-key  # Your existing secret
              key: latest                           # Secret version
        resources:
          limits:
            cpu: '1'                        # 1 vCPU
            memory: 1Gi                     # 1 GB RAM
  traffic:
  - percent: 100
    latestRevision: true                    # Route 100% traffic to latest revision
```

## Before First Deployment

### 1. Find your Project ID
```bash
gcloud config get-value project
```

### 2. Find your Project Number (only if using default service account)
```bash
gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)"
```

### 3. Choose Service Account Strategy

#### Option A: Use Default Service Account (Quickest)
Cloud Run automatically uses the default Compute Engine service account if you don't specify one.

**In service.yaml:** Comment out or omit the `serviceAccountName` line (already done in the template).

**Verify it exists:**
```bash
gcloud iam service-accounts list | grep compute@developer
```

**Grant secret access:**
```bash
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding simeg-prototype-gemini-api-key \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

#### Option B: Create Custom Service Account (Recommended for Production)
Create a dedicated service account with minimal permissions (principle of least privilege).

```bash
# 1. Create service account
gcloud iam service-accounts create simeg-backend-sa \
  --display-name="Simeg Order Entry Backend Service Account"

# 2. Grant only the permissions needed
gcloud secrets add-iam-policy-binding simeg-prototype-gemini-api-key \
  --member="serviceAccount:simeg-backend-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# 3. Update service.yaml
# Uncomment and update the serviceAccountName line:
# serviceAccountName: simeg-backend-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

**Benefits of custom service account:**
- Follows security best practices (least privilege)
- Easier to audit permissions
- Can be different per environment (dev, staging, prod)
- Limits blast radius if compromised

### 4. Update service.yaml
- Replace `PROJECT_ID` with your project ID (in the image URL)
- If using custom service account, uncomment and update `serviceAccountName`

### 5. Verify secret exists
```bash
gcloud secrets describe simeg-prototype-gemini-api-key
```

## Deployment Workflow

### Initial Deployment

```bash
# 1. Build Docker image
docker build -t gcr.io/YOUR_PROJECT_ID/simeg-order-entry-backend:latest .

# 2. Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/simeg-order-entry-backend:latest

# 3. Deploy using service.yaml
gcloud run services replace service.yaml --region us-central1
```

### Subsequent Deployments

```bash
# 1. Build and push new image
docker build -t gcr.io/YOUR_PROJECT_ID/simeg-order-entry-backend:latest .
docker push gcr.io/YOUR_PROJECT_ID/simeg-order-entry-backend:latest

# 2. Deploy (Cloud Run will detect the new image)
gcloud run services replace service.yaml --region us-central1
```

## Service Accounts Explained

### What is a Service Account?

A service account is an identity that your Cloud Run service uses to:
- Access Google Cloud resources (like Secret Manager)
- Make authenticated API calls
- Interact with other Google Cloud services

### Default vs Custom Service Accounts

| Aspect | Default Service Account | Custom Service Account |
|--------|------------------------|------------------------|
| **Name** | `PROJECT_NUMBER-compute@developer.gserviceaccount.com` | `your-name@PROJECT_ID.iam.gserviceaccount.com` |
| **Creation** | Automatic (when Compute Engine enabled) | Manual |
| **Permissions** | Editor role (broad permissions) | Only what you grant (least privilege) |
| **Best For** | Development, quick testing | Production, security-conscious deployments |
| **Setup Time** | None (already exists) | 2-3 minutes |

### Check Your Service Accounts

```bash
# List all service accounts in your project
gcloud iam service-accounts list

# Check if default Compute Engine SA exists
gcloud iam service-accounts list --filter="email:compute@developer"

# Check permissions on your secret
gcloud secrets get-iam-policy simeg-prototype-gemini-api-key
```

### When to Use Which?

**Use Default Service Account when:**
- Rapid prototyping or development
- You trust the default permissions
- You want minimal setup

**Use Custom Service Account when:**
- Deploying to production
- Following security best practices
- Need to audit or limit permissions
- Compliance requirements

### Security Best Practice

For production, always create a custom service account with only the permissions needed:

```bash
# Create service account
gcloud iam service-accounts create simeg-backend-sa \
  --display-name="Simeg Backend"

# Grant ONLY Secret Manager access (not Editor!)
gcloud secrets add-iam-policy-binding simeg-prototype-gemini-api-key \
  --member="serviceAccount:simeg-backend-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# If you need to write logs (usually automatic)
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:simeg-backend-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"
```

## Environment-Specific Configurations

You can create multiple service.yaml files for different environments:

```
service.yaml              # Production
service.staging.yaml      # Staging
service.dev.yaml          # Development
```

Example staging configuration:

```yaml
# service.staging.yaml
metadata:
  name: simeg-order-entry-backend-staging
spec:
  template:
    spec:
      containers:
      - image: gcr.io/PROJECT_ID/simeg-order-entry-backend:staging
        env:
        - name: ENVIRONMENT
          value: staging
        - name: FRONTEND_URL
          value: "https://frontend-staging-xxx.run.app"
```

Deploy staging:
```bash
gcloud run services replace service.staging.yaml --region us-central1
```

## Updating Configuration

### Update Environment Variables

Edit `service.yaml`:
```yaml
env:
- name: FRONTEND_URL
  value: "https://your-actual-frontend.run.app"
```

Then redeploy:
```bash
gcloud run services replace service.yaml --region us-central1
```

### Update Resources

Edit `service.yaml`:
```yaml
resources:
  limits:
    cpu: '2'      # Increase to 2 vCPUs
    memory: 2Gi   # Increase to 2 GB
```

### Update Scaling

Edit `service.yaml`:
```yaml
annotations:
  autoscaling.knative.dev/maxScale: '20'  # Increase max instances
  autoscaling.knative.dev/minScale: '1'   # Keep 1 instance always warm
```

## CI/CD Integration

### GitHub Actions Example

```yaml
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
      
      - name: Build and Push
        run: |
          docker build -t gcr.io/${{ secrets.GCP_PROJECT_ID }}/simeg-order-entry-backend:${{ github.sha }} .
          docker push gcr.io/${{ secrets.GCP_PROJECT_ID }}/simeg-order-entry-backend:${{ github.sha }}
      
      - name: Update service.yaml
        run: |
          sed -i "s|:latest|:${{ github.sha }}|g" service.yaml
          sed -i "s|PROJECT_ID|${{ secrets.GCP_PROJECT_ID }}|g" service.yaml
          sed -i "s|PROJECT_NUMBER|${{ secrets.GCP_PROJECT_NUMBER }}|g" service.yaml
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run services replace service.yaml --region us-central1
```

## Troubleshooting

### Service won't start
```bash
# Check logs
gcloud run services logs read simeg-order-entry-backend --region us-central1 --limit 50
```

### Secret not accessible
```bash
# Verify IAM binding
gcloud secrets get-iam-policy simeg-prototype-gemini-api-key
```

### Image not found
```bash
# List images in GCR
gcloud container images list --repository=gcr.io/YOUR_PROJECT_ID
```

### Configuration not applying
```bash
# Describe the service to see current configuration
gcloud run services describe simeg-order-entry-backend --region us-central1
```

## Best Practices

1. **Use specific image tags** in production (not `:latest`)
2. **Version your service.yaml** in Git
3. **Use Secret Manager** for sensitive data (never in env vars)
4. **Set appropriate resource limits** based on actual usage
5. **Configure health checks** for production services
6. **Use min instances > 0** for production to avoid cold starts
7. **Monitor and adjust** autoscaling based on traffic patterns

## Related Documentation

- [Cloud Run Deployment Guide](CLOUD_RUN_DEPLOYMENT.md)
- [Deployment Commands](DEPLOYMENT_COMMANDS.md)
- [Cloud Run YAML Reference](https://cloud.google.com/run/docs/reference/yaml/v1)
