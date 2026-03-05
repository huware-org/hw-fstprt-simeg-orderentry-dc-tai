# Deployment Scripts

## Quick Answer: Which Code Gets Deployed?

**Docker builds from your local filesystem, NOT from Git!**

- ✅ Includes uncommitted changes
- ✅ Includes untracked files (if not in .dockerignore)
- ❌ Git branch doesn't matter
- ❌ Remote repository state doesn't matter

**Best Practice:** Always commit and push to Git before deploying to production!

## Available Scripts

### `deploy.sh` - Full Deployment (Recommended)

Interactive deployment script with safety checks:
- ✅ Checks for uncommitted changes
- ✅ Shows Git branch and commit
- ✅ Asks for confirmation before deploying
- ✅ Tags images with Git commit hash
- ✅ Shows service URL after deployment

**Usage:**
```bash
./scripts/deploy.sh
```

**What it does:**
1. Checks if you're in the right directory
2. Warns about uncommitted changes
3. Shows deployment info (branch, commit, etc.)
4. Builds Docker image (tagged with `:latest` and `:commit-hash`)
5. Pushes to Google Container Registry
6. Deploys to Cloud Run using `service.yaml`
7. Shows service URL and helpful commands

### `deploy-simple.sh` - Quick Deployment

No-questions-asked deployment:
- ⚡ Fast and simple
- ❌ No safety checks
- ❌ No Git info

**Usage:**
```bash
./scripts/deploy-simple.sh
```

**What it does:**
1. Builds Docker image
2. Pushes to GCR
3. Deploys to Cloud Run
4. Shows service URL

### `start_backend.sh` - Local Development

Starts the backend locally for development:

**Usage:**
```bash
./scripts/start_backend.sh
```

### `inspect_scavolini_table.py` - Debug Tool

Inspects the Scavolini transcodification table:

**Usage:**
```bash
python scripts/inspect_scavolini_table.py
```

## Configuration

Both deployment scripts use these settings (edit the scripts to change):

```bash
PROJECT_ID="poc-huware-ai"
SERVICE_NAME="simeg-order-entry-backend"
REGION="europe-west1"
```

## Deployment Workflow

### Development Workflow
```bash
# 1. Make changes to code
# 2. Test locally
./scripts/start_backend.sh

# 3. Commit changes
git add .
git commit -m "Your changes"

# 4. Deploy
./scripts/deploy.sh
```

### Quick Fix Workflow
```bash
# Make a quick fix
# Deploy immediately (includes uncommitted changes)
./scripts/deploy-simple.sh

# Then commit
git add .
git commit -m "Quick fix"
git push
```

## Understanding Docker Build Context

When you run `docker build`, it:
1. Reads files from your **current working directory**
2. Sends them to Docker daemon
3. Builds image from those files

**Example:**
```bash
# You're on branch 'feature-x' with uncommitted changes
git status
# On branch feature-x
# Changes not staged for commit:
#   modified:   app/main.py

# Docker will build with the modified main.py!
docker build -t myimage .
```

## Best Practices

### ✅ DO:
- Commit and push before deploying to production
- Use `deploy.sh` for production deployments
- Tag images with meaningful versions
- Test locally before deploying

### ❌ DON'T:
- Deploy uncommitted changes to production
- Deploy from a dirty working directory
- Forget which code you're deploying
- Skip testing

## Troubleshooting

### "service.yaml not found"
You're not in the project root. Run:
```bash
cd /path/to/hw-fstprt-simeg-orderentry-dc-tai
./scripts/deploy.sh
```

### "Docker build failed"
Check the error message. Common issues:
- Syntax error in code
- Missing dependencies in requirements
- Dockerfile issues

### "Docker push failed"
Authenticate Docker with GCR:
```bash
gcloud auth configure-docker gcr.io
```

### "Deployment failed"
Check Cloud Run logs:
```bash
gcloud run services logs read simeg-order-entry-backend --region europe-west1
```

## Advanced: Custom Deployment

If you need to customize the deployment:

```bash
# Build with custom tag
docker build -t gcr.io/poc-huware-ai/simeg-order-entry-backend:v1.2.3 .

# Push
docker push gcr.io/poc-huware-ai/simeg-order-entry-backend:v1.2.3

# Update service.yaml to use the new tag
# Then deploy
gcloud run services replace service.yaml --region europe-west1
```

## CI/CD Integration

For automated deployments, use `deploy-simple.sh` in your CI/CD pipeline:

```yaml
# GitHub Actions example
- name: Deploy to Cloud Run
  run: |
    ./scripts/deploy-simple.sh
```

Or build your own pipeline using the commands from the scripts.
