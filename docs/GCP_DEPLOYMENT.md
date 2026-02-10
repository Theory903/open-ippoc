# IPPOC Google Cloud Platform Deployment Guide

## Overview

This guide covers deploying IPPOC to Google Cloud Platform using:
- **Cloud Run** - Serverless container hosting
- **Cloud SQL** - Managed PostgreSQL
- **Secret Manager** - Secure credential storage
- **Cloud Build** - CI/CD pipeline
- **Terraform** - Infrastructure as Code

## Prerequisites

```bash
# Install required tools
brew install google-cloud-sdk terraform docker

# Authenticate
gcloud auth login
gcloud auth application-default login

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  sql.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com
```

## Quick Start (5 minutes)

### 1. Set Variables

```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export ENVIRONMENT="production"  # or "staging"
```

### 2. Deploy Infrastructure

```bash
cd infra/gcp

# Initialize Terraform
terraform init

# Plan deployment
terraform plan \
  -var="project_id=$PROJECT_ID" \
  -var="region=$REGION" \
  -var="environment=$ENVIRONMENT" \
  -var="image_name=gcr.io/$PROJECT_ID/ippoc:latest"

# Apply (creates Cloud Run, Cloud SQL, Secrets)
terraform apply \
  -var="project_id=$PROJECT_ID" \
  -var="region=$REGION" \
  -var="environment=$ENVIRONMENT" \
  -var="image_name=gcr.io/$PROJECT_ID/ippoc:latest"
```

### 3. Deploy Application

```bash
# Build and push Docker image
gcloud builds submit --config cloudbuild.yaml .

# Deploy to Cloud Run
gcloud run deploy ippoc-$ENVIRONMENT \
  --image gcr.io/$PROJECT_ID/ippoc:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --service-account ippoc-$ENVIRONMENT@$PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars "INSTANCE=$ENVIRONMENT,LOG_LEVEL=INFO" \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10 \
  --concurrency 100
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Google Cloud Platform                    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Cloud Run Service                      │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │          IPPOC Container                    │    │    │
│  │  │  ┌─────────┐ ┌─────────┐ ┌─────────────┐    │    │    │
│  │  │  │   Soma  │ │ Cortex  │ │  Mnemosyne  │    │    │    │
│  │  │  │ (:8081) │ │ (:8001) │ │   (:8003)   │    │    │    │
│  │  │  └─────────┘ └─────────┘ └─────────────┘    │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────┘    │
│                              │                              │
│              ┌─────────────┼─────────────┐                  │
│              │             │             │                  │
│     ┌────────▼─────┐ ┌────▼─────┐ ┌────▼─────────┐          │
│     │  Cloud SQL   │ │ Secrets  │ │ Cloud Build  │       │
│     │  PostgreSQL  │ │ Manager  │ │   (CI/CD)    │       │
│     └──────────────┘ └──────────┘ └─────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `INSTANCE` | Yes | Environment name (production/staging) |
| `LOG_LEVEL` | No | Logging level (DEBUG/INFO/WARNING) |
| `IPPOC_API_KEY` | Yes | API key for authentication |
| `CLOUD_SQL_CONNECTION` | No | Cloud SQL connection string |
| `DATABASE_URL` | No | Full database connection URL |

## Configuration Files

### `Dockerfile.cloudrun`
Multi-stage Docker build:
- Stage 1: Rust builder (Soma components)
- Stage 2: Python dependencies
- Stage 3: Production runtime (distroless)

### `cloudbuild.yaml`
Cloud Build pipeline:
- Builds Rust + Python
- Runs unit tests
- Scans for vulnerabilities
- Deploys to Cloud Run

### `.github/workflows/gcp-deploy.yml`
GitHub Actions CI/CD:
- Linting & security scans
- Unit tests
- Docker build & push
- Staging deployment
- Production deployment
- Integration tests

### `infra/gcp/main.tf`
Terraform infrastructure:
- Cloud Run service
- Cloud SQL instance
- Secret Manager secrets
- Service accounts
- IAM permissions

## Scaling

### Auto-scaling Configuration

```yaml
# Minimum instances
min-instances: 1

# Maximum instances  
max-instances: 10

# Concurrency per instance
concurrency: 100

# Resources
memory: 2Gi
cpu: 2
```

### Cold Start Optimization

The container uses:
- Distroless base image (~50MB)
- Pre-compiled Rust binaries
- Layer caching

Typical cold start: < 500ms

## Monitoring

### Cloud Logging

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ippoc-production" --limit 50

# Tail logs
gcloud logging tail "resource.type=cloud_run_revision" --limit 50
```

### Cloud Monitoring

```bash
# View metrics
gcloud monitoring dashboards list

# Create custom dashboard
gcloud monitoring dashboards create --config-from-file=dashboard.json
```

## Troubleshooting

### Container fails to start

```bash
# Check logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ippoc" --limit 100

# Check Cloud Run events
gcloud run services describe ippoc --region $REGION
```

### Health check failing

```bash
# Test health endpoint locally
curl http://localhost:8080/health

# Check health check configuration
gcloud run services describe ippoc --region $REGION | grep -A5 "HealthCheck"
```

### Database connection issues

```bash
# Test Cloud SQL proxy
gcloud sql connect ippoc-production --user=postgres

# Check connection string
gcloud secrets versions access latest --secret="database-url-production"
```

## Security

### IAM Roles Required

```bash
# Service account roles
roles/run.admin
roles/secretmanager.admin  
roles/cloudsql.admin
roles/storage.admin
roles/logging.logWriter
roles/monitoring.metricWriter
```

### Secrets Management

All sensitive configuration stored in Secret Manager:
- `ippoc-api-key-production`
- `database-url-production`

Access via environment variables:
```yaml
env_from:
  secret_ref:
    name: ippoc-api-key-production
```

## Cost Estimation

| Resource | Quantity | Monthly Cost |
|----------|----------|--------------|
| Cloud Run | 1M requests | ~$1.00 |
| Cloud SQL (db-f1-micro) | 1 instance | ~$8.50 |
| Cloud Storage | 10GB | ~$0.20 |
| Cloud Build | 100 builds | ~$1.00 |
| Secret Manager | 2 secrets | ~$0.12 |
| **Total** | | **~$10.82/mo** |

## CI/CD Pipeline

### Automated Flow

```
1. Push to main branch
   ↓
2. GitHub Actions triggers
   ↓
3. Lint + Security Scan
   ↓
4. Build Docker image
   ↓
5. Vulnerability scan (Trivy)
   ↓
6. Push to Container Registry
   ↓
7. Deploy to Cloud Run (staging)
   ↓
8. Integration tests
   ↓
9. Manual approval (production)
   ↓
10. Deploy to Cloud Run (production)
```

### Manual Deployment

```bash
# Deploy specific image
gcloud run deploy ippoc-production \
  --image gcr.io/$PROJECT_ID/ippoc:$TAG \
  --region $REGION

# Rollback to previous version
gcloud run services update-traffic ippoc-production \
  --to-revisions=LATEST=90,LATEST-1=10
```
