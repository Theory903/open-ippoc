# IPPOC Full System Architecture

## Overview

This document describes the complete IPPOC system deployment on Google Cloud Platform.

## Services Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Google Cloud Platform                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     Cloud Run (Microservices)                    │   │
│  │                                                                  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │   │
│  │  │   OpenClaw  │  │    Cortex   │  │    Soma     │             │   │
│  │  │   (Kernel)  │  │  (Gateway)  │  │  (Identity) │             │   │
│  │  │  :8080      │  │  :8081      │  │  :8082      │             │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘             │   │
│  │                                                                  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │   │
│  │  │  Mnemosyne  │  │   Body      │  │  Maksad     │             │   │
│  │  │  (Memory)   │  │  (Economy)  │  │  (Planner)  │             │   │
│  │  │  :8083      │  │  :8084      │  │  :8085      │             │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘             │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────┐  ┌──────────────────────┐                     │
│  │    Cloud SQL         │  │   Memorystore       │                     │
│  │    PostgreSQL        │  │   (Redis)           │                     │
│  │    :5432             │  │   :6379             │                     │
│  │    ippoc_prod        │  │   ippoc-cache       │                     │
│  └──────────────────────┘  └──────────────────────┘                     │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Virtual Private Cloud                       │   │
│  │                   (Serverless VPC Access)                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Service Descriptions

| Service | Port | Description | Type |
|---------|------|-------------|------|
| OpenClaw | 8080 | Kernel / Plugin System | Node.js |
| Cortex | 8081 | Main Gateway / Router | Python |
| Soma | 8082 | Identity & Auth | Python |
| Mnemosyne | 8083 | Memory & Knowledge Graph | Python |
| Body | 8084 | Economy & Resources | Python |
| Maksad | 8085 | Planning & Goals | Python |

## Infrastructure Components

### Cloud SQL (PostgreSQL)
- **Instance**: `ippoc-main-db`
- **Database**: `ippoc`
- **User**: `ippoc_admin`
- **Version**: PostgreSQL 15
- **Tier**: db-f1-micro (dev) → db-custom-4-16384 (prod)

### Cloud Memorystore (Redis)
- **Instance**: `ippoc-cache`
- **Tier**: Standard (1GB)
- **Purpose**: Session storage, caching, pub/sub

### Cloud Run Services
- **Region**: asia-south1 (Mumbai)
- **Memory**: 1Gi per service
- **CPU**: 1 per service
- **Min Instances**: 1
- **Max Instances**: 10
- **Concurrency**: 80

## Environment Variables

### Required for All Services
```
ENVIRONMENT=production
PROJECT_ID=<gcp-project-id>
REGION=asia-south1
DATABASE_URL=postgresql://<user>:<pass>@<host>:5432/ippoc
REDIS_URL=redis://<host>:6379
```

### Per-Service Variables
| Service | Required Variables |
|---------|-------------------|
| OpenClaw | PLUGIN_PATH, NODE_ENV |
| Cortex | SOMA_URL, MNEMOSYNE_URL, BODY_URL |
| Soma | JWT_SECRET, API_KEY |
| Mnemosyne | GOOGLE_API_KEY, EMBEDDING_MODEL |
| Body | ECONOMY_INITIAL_BUDGET |
| Maksad | PLANNING_MODEL |

## Deployment Strategy

### 1. Infrastructure (Terraform)
```bash
cd infra/gcp
terraform init
terraform apply -var="environment=prod"
```

### 2. Container Images (Cloud Build)
- Each service has its own Dockerfile
- Images stored in Artifact Registry
- Automatic builds on push to main

### 3. Deploy Services (Cloud Run)
```bash
./scripts/deploy-all.sh prod
```

### 4. Database Migration
```bash
./scripts/migrate-db.sh
```

## Networking

### VPC Connector
- **Name**: `ippoc-serverless-vpc`
- **Subnet**: `10.0.0.0/28`

### Firewall Rules
- Allow ingress from Cloud Run to Cloud SQL
- Allow ingress from Cloud Run to Memorystore
- Internal traffic only (no public IPs)

## Security

### Secrets (Secret Manager)
- `ippoc-db-password`
- `ippoc-redis-password`
- `ippoc-jwt-secret`
- `ippoc-api-key`
- `ippoc-google-api-key`

### Service Accounts
- `ippoc-cloudrun-sa`: For Cloud Run services
- `ippoc-db-sa`: For database operations
- `ippoc-build-sa`: For CI/CD

## Monitoring

### Cloud Logging
- Structured logs from all services
- Log-based metrics for error rates

### Cloud Monitoring
- Uptime checks for each service
- Custom dashboards for system health

### Alerts
- Error rate > 1%
- Latency > 500ms
- Memory > 80%
