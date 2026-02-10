#!/bin/bash
# IPPOC GCP Quick Deploy Script
# Usage: ./scripts/gcp-deploy.sh [production|staging]

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project)}"
REGION="${GCP_REGION:-europe-west1}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/ippoc"
SERVICE_NAME="${1:-ippoc-production}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo_step() {
    echo -e "${GREEN}🚀 $1${NC}"
}

echo_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prereqs() {
    echo_step "Checking prerequisites..."

    if ! command -v gcloud &> /dev/null; then
        echo_error "gcloud CLI not installed. Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi

    if [ -z "$PROJECT_ID" ]; then
        echo_error "GCP_PROJECT_ID not set. Run: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    fi

    echo_step "Prerequisites OK (Project: $PROJECT_ID)"
}

# Enable APIs
enable_apis() {
    echo_step "Enabling required APIs..."
    gcloud services enable \
        run.googleapis.com \
        containerregistry.googleapis.com \
        cloudbuild.googleapis.com \
        secretmanager.googleapis.com \
        --quiet
}

# Build and push image
build_image() {
    echo_step "Building Docker image..."
    docker build -t "$IMAGE_NAME:latest" -t "$IMAGE_NAME:$(git rev-parse --short HEAD)" -f Dockerfile.cloudrun .

    echo_step "Pushing to Container Registry..."
    docker push "$IMAGE_NAME:latest"
    docker push "$IMAGE_NAME:$(git rev-parse --short HEAD)"
}

# Deploy to Cloud Run
deploy_cloudrun() {
    echo_step "Deploying to Cloud Run ($SERVICE_NAME)..."

    local ENV_VARS="INSTANCE=${1:-production},LOG_LEVEL=${LOG_LEVEL:-INFO}"

    gcloud run deploy "$SERVICE_NAME" \
        --image "$IMAGE_NAME:latest" \
        --platform managed \
        --region "$REGION" \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 2 \
        --min-instances 1 \
        --max-instances 10 \
        --concurrency 80 \
        --set-env-vars "$ENV_VARS" \
        --timeout 300s \
        --quiet

    echo_step "Deployed! Getting URL..."
    gcloud run services describe "$SERVICE_NAME" \
        --platform managed \
        --region "$REGION" \
        --format 'value(status.url)'
}

# Create secrets
create_secrets() {
    echo_step "Creating secrets in Secret Manager..."

    # API Key
    if ! gcloud secrets describe "ippoc-api-key-${1:-production}" &> /dev/null; then
        echo "Generating API key..."
        openssl rand -hex 32 | gcloud secrets create "ippoc-api-key-${1:-production}" --data-file=- --quiet
    fi

    echo_step "Secrets configured"
}

# Main
main() {
    echo "=============================================="
    echo "  IPPOC GCP Deployment"
    echo "=============================================="
    echo "Project: $PROJECT_ID"
    echo "Region: $REGION"
    echo "Service: $SERVICE_NAME"
    echo "=============================================="

    check_prereqs
    enable_apis
    create_secrets "$1"
    build_image
    deploy_cloudrun "$1"

    echo ""
    echo_step "✅ Deployment complete!"
    echo ""
    echo "Next steps:"
    echo "  - Set up GitHub Actions (see .github/workflows/gcp-deploy.yml)"
    echo "  - Configure custom domain (optional)"
    echo "  - Set up monitoring (see docs/GCP_DEPLOYMENT.md)"
}

main "$1"
