#!/bin/bash
# IPPOC Complete Deployment Script
# Deploys all services to Google Cloud Platform

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${1:-dev}"
PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project)}"
REGION="${GCP_REGION:-asia-south1}"

echo "=============================================="
echo "  IPPOC Full System Deployment"
echo "=============================================="
echo "Environment: $ENVIRONMENT"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "=============================================="

# Check prerequisites
check_prereqs() {
    echo -e "${GREEN}Checking prerequisites...${NC}"
    
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI not installed${NC}"
        exit 1
    fi
    
    if ! command -v terraform &> /dev/null; then
        echo -e "${YELLOW}⚠️  Terraform not installed (skipping infra)${NC}"
        TERRAFORM_INSTALLED=false
    else
        TERRAFORM_INSTALLED=true
    fi
    
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}⚠️  Docker not installed (builds will use Cloud Build)${NC}"
        DOCKER_INSTALLED=false
    else
        DOCKER_INSTALLED=true
    fi
    
    echo -e "${GREEN}✅ Prerequisites OK${NC}"
}

# Initialize GCP project
init_gcp() {
    echo -e "${GREEN}Initializing GCP project...${NC}"
    
    gcloud config set project "$PROJECT_ID"
    gcloud services enable \
        run.googleapis.com \
        artifactregistry.googleapis.com \
        cloudbuild.googleapis.com \
        sqladmin.googleapis.com \
        secretmanager.googleapis.com \
        servicenetworking.googleapis.com \
        compute.googleapis.com \
        monitoring.googleapis.com \
        logging.googleapis.com \
        storage.googleapis.com \
        --quiet
    
    echo -e "${GREEN}✅ GCP initialized${NC}"
}

# Create Artifact Registry repository
create_artifact_repo() {
    echo -e "${GREEN}Creating Artifact Registry repository...${NC}"
    
    gcloud artifacts repositories create ippoc \
        --repository-format=docker \
        --location="$REGION" \
        --description="IPPOC container images" \
        --quiet || true
    
    gcloud artifacts repositories add-iam-policy-binding ippoc \
        --location="$REGION" \
        --member=serviceAccount:"${PROJECT_ID}@cloudbuild.gserviceaccount.com" \
        --role=roles/artifactregistry.reader \
        --quiet || true
    
    echo -e "${GREEN}✅ Artifact Registry ready${NC}"
}

# Deploy infrastructure with Terraform
deploy_infra() {
    if [ "$TERRAFORM_INSTALLED" = false ]; then
        echo -e "${YELLOW}⚠️  Skipping Terraform (not installed)${NC}"
        return
    fi
    
    echo -e "${GREEN}Deploying infrastructure with Terraform...${NC}"
    
    cd infra/gcp
    
    terraform init -upgrade
    terraform apply \
        -var="environment=$ENVIRONMENT" \
        -var="project_id=$PROJECT_ID" \
        -auto-approve
    
    cd -
    
    echo -e "${GREEN}✅ Infrastructure deployed${NC}"
}

# Build and push all service images
build_images() {
    echo -e "${GREEN}Building and pushing service images...${NC}"
    
    local services=("openclaw" "cortex" "soma" "mnemosyne" "body" "maksad")
    
    for service in "${services[@]}"; do
        echo "Building $service..."
        
        local image="asia-south1-docker.pkg.dev/${PROJECT_ID}/ippoc/${service}:latest"
        
        if [ "$DOCKER_INSTALLED" = true ]; then
            docker build -t "$image" -f "${service}/Dockerfile" .
            docker push "$image"
        else
            gcloud builds submit \
                --tag "$image" \
                --project="$PROJECT_ID" \
                "${service}/"
        fi
        
        echo -e "${GREEN}✅ $service built and pushed${NC}"
    done
}

# Deploy Cloud Run services
deploy_services() {
    echo -e "${GREEN}Deploying Cloud Run services...${NC}"
    
    local services=(
        "openclaw:8080"
        "cortex:8081"
        "soma:8082"
        "mnemosyne:8083"
        "body:8084"
        "maksad:8085"
    )
    
    for service_port in "${services[@]}"; do
        IFS=':' read -r service port <<< "$service_port"
        
        echo "Deploying $service..."
        
        local image="asia-south1-docker.pkg.dev/${PROJECT_ID}/ippoc/${service}:latest"
        
        gcloud run deploy "${service}-${ENVIRONMENT}" \
            --image="$image" \
            --platform=managed \
            --region="$REGION" \
            --allow-unauthenticated \
            --memory=1Gi \
            --cpu=1 \
            --min-instances=1 \
            --max-instances=2 \
            --port="$port" \
            --set-env-vars="ENVIRONMENT=$ENVIRONMENT" \
            --set-secrets="API_KEY=ippoc-api-key-${ENVIRONMENT}:latest" \
            --quiet
        
        echo -e "${GREEN}✅ $service deployed${NC}"
    done
}

# Verify deployment
verify_deployment() {
    echo -e "${GREEN}Verifying deployment...${NC}"
    
    local services=("openclaw" "cortex" "soma" "mnemosyne" "body" "maksad")
    
    for service in "${services[@]}"; do
        local url=$(gcloud run services describe "${service}-${ENVIRONMENT}" \
            --platform=managed \
            --region="$REGION" \
            --format='value(status.url)' 2>/dev/null || echo "")
        
        if [ -n "$url" ]; then
            echo -e "${GREEN}✅ $service: $url${NC}"
            
            # Health check
            curl -sf "${url}/health" > /dev/null && echo "   Health OK" || echo "   Health FAILED"
        else
            echo -e "${YELLOW}⚠️  $service: Not deployed${NC}"
        fi
    done
}

# Show endpoints
show_endpoints() {
    echo ""
    echo -e "${GREEN}📋 Service Endpoints${NC}"
    echo "=============================================="
    
    gcloud run services list \
        --platform=managed \
        --region="$REGION" \
        --format='table[box](name:sort=1,status.url:sort=2)' \
        --filter="name~${ENVIRONMENT}\$"
    
    echo ""
    echo -e "${GREEN}💰 Free Tier Status${NC}"
    echo "=============================================="
    echo "Cloud Run: 2M requests/month, 180K vCPU-seconds, 360K GB-seconds"
    echo "Cloud SQL: db-f1-micro (30GB storage)"
    echo "Cloud Build: 120 minutes/day"
    echo "Artifact Registry: 500MB storage"
    echo "Secret Manager: 10K versions/month"
}

# Main
main() {
    echo "Starting IPPOC deployment..."
    
    check_prereqs
    init_gcp
    create_artifact_repo
    deploy_infra
    build_images
    deploy_services
    verify_deployment
    show_endpoints
    
    echo ""
    echo -e "${GREEN}🎉 Deployment complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Configure custom domain (optional)"
    echo "  2. Set up monitoring dashboards"
    echo "  3. Configure CI/CD triggers"
    echo "  4. Review budget alerts"
}

main "$1"
