# IPPOC Full System Terraform Configuration (Free Tier Optimized)
# Google Cloud Platform with Ollama for AI/ML

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "ippoc-terraform-state"
    prefix = "prod"
  }
}

# Variables
variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "asia-south1"
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

# Ollama Configuration
variable "ollama_host" {
  description = "Ollama API endpoint URL"
  type        = string
  default     = "https://api.ollama.com"
}

variable "ollama_model" {
  description = "Default Ollama model"
  type        = string
  default     = "kimi-k2.5:cloud"
}

# Service configurations (Free tier optimized)
variable "services" {
  description = "List of services to deploy"
  type = list(object({
    name         = string
    port         = number
    memory       = string
    cpu          = string
    min_instances = number
    max_instances = number
    path         = string
    dockerfile   = string
    free_tier   = bool
  }))
  default = [
    {
      name          = "openclaw"
      port          = 8080
      memory        = "512Mi"
      cpu           = "1"
      min_instances = 1
      max_instances = 2
      path          = "src/kernel/openclaw"
      dockerfile    = "Dockerfile"
      free_tier     = true
    },
    {
      name          = "cortex"
      port          = 8081
      memory        = "512Mi"
      cpu           = "1"
      min_instances = 1
      max_instances = 2
      path          = "src/ippoc/cortex"
      dockerfile    = "Dockerfile"
      free_tier     = true
    },
    {
      name          = "soma"
      port          = 8082
      memory        = "256Mi"
      cpu           = "1"
      min_instances = 1
      max_instances = 1
      path          = "src/ippoc/soma"
      dockerfile    = "Dockerfile"
      free_tier     = true
    },
    {
      name          = "mnemosyne"
      port          = 8083
      memory        = "1Gi"
      cpu           = "1"
      min_instances = 1
      max_instances = 2
      path          = "src/ippoc/mnemosyne"
      dockerfile    = "Dockerfile"
      free_tier     = true
    },
    {
      name          = "body"
      port          = 8084
      memory        = "512Mi"
      cpu           = "1"
      min_instances = 1
      max_instances = 1
      path          = "src/ippoc/body"
      dockerfile    = "Dockerfile"
      free_tier     = true
    },
    {
      name          = "maksad"
      port          = 8085
      memory        = "512Mi"
      cpu           = "1"
      min_instances = 1
      max_instances = 1
      path          = "src/ippoc/maksad"
      dockerfile    = "Dockerfile"
      free_tier     = true
    }
  ]
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs (free tier eligible)
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "servicenetworking.googleapis.com",
    "compute.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "storage.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

# VPC Network
resource "google_compute_network" "ippoc_vpc" {
  name                    = "ippoc-vpc-${var.environment}"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "ippoc_subnet" {
  name          = "ippoc-subnet-${var.environment}"
  ip_cidr_range = "10.0.0.0/28"
  region        = var.region
  network       = google_compute_network.ippoc_vpc.id
}

resource "google_vpc_access_connector" "serverless_connector" {
  name          = "ippoc-vpc-connector-${var.environment}"
  region        = var.region
  ip_cidr_range = google_compute_subnetwork.ippoc_subnet.ip_cidr_range
  network       = google_compute_network.ippoc_vpc.name
}

# Cloud SQL PostgreSQL (Free tier: db-f1-micro always free)
resource "google_sql_database_instance" "main_db" {
  count = var.environment == "dev" ? 1 : 1

  name             = "ippoc-db-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = "db-f1-micro"  # Always free tier
    availability_type = "ZONAL"        # Zonal for free tier
    disk_autoresize   = true
    disk_size         = 10             # 10GB storage (free)

    ip_configuration {
      private_network = google_compute_network.ippoc_vpc.id
    }

    backup_configuration {
      enabled = true
    }

    database_flags {
      name  = "pgvector.enabled"
      value = "on"
    }
  }

  deletion_protection = false
}

resource "google_sql_database" "ippoc_db" {
  count  = length(google_sql_database_instance.main_db) > 0 ? 1 : 0
  name   = "ippoc"
  instance = google_sql_database_instance.main_db[0].name
  charset = "UTF8"
}

resource "google_sql_user" "ippoc_user" {
  count  = length(google_sql_database_instance.main_db) > 0 ? 1 : 0
  name   = "ippoc_admin"
  instance = google_sql_database_instance.main_db[0].name
  password = random_password.db_password.result
}

resource "random_password" "db_password" {
  length  = 32
  special = false
}

# Cloud Storage (Standard, free tier: 5GB)
resource "google_storage_bucket" "ippoc_bucket" {
  name          = "ippoc-storage-${var.environment}"
  location      = var.region
  storage_class = "STANDARD"
  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 30  # Delete after 30 days
    }
    action {
      type = "Delete"
    }
  }
}

# Secret Manager Secrets (Free tier: 10,000 secret versions/month)
resource "google_secret_manager_secret" "secrets" {
  for_each = toset([
    "db-password",
    "jwt-secret",
    "api-key",
    "ollama-host",
  ])
  name = "ippoc-${each.value}-${var.environment}"
}

resource "google_secret_manager_secret_version" "secret_versions" {
  for_each = {
    "db-password"  = random_password.db_password.result
    "jwt-secret"    = random_string.jwt_secret.result
    "api-key"       = random_password.api_key.result
    "ollama-host"   = var.ollama_host
  }
  secret      = google_secret_manager_secret.secrets[each.key].id
  secret_data = each.value
}

resource "random_password" "redis_password" {
  count = var.environment == "prod" ? 1 : 0
  length  = 32
  special = false
}

resource "random_string" "jwt_secret" {
  length  = 64
  special = false
}

resource "random_password" "api_key" {
  length  = 32
  special = false
}

# Cloud Run Services
resource "google_cloud_run_service" "services" {
  for_each = { for s in var.services : s.name => s }

  name     = "${each.value.name}-${var.environment}"
  location = var.region

  template {
    spec {
      containers {
        image = "asia-south1-docker.pkg.dev/${var.project_id}/ippoc/${each.value.name}:latest"
        ports {
          container_port = each.value.port
        }
        env {
          name  = "PORT"
          value = tostring(each.value.port)
        }
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }
        env {
          name  = "OLLAMA_HOST"
          value = var.ollama_host
        }
        env {
          name  = "OLLAMA_MODEL"
          value = var.ollama_model
        }
        env {
          name  = "DATABASE_URL"
          value = length(google_sql_database_instance.main_db) > 0 ? "postgresql://ippoc_admin:${random_password.db_password.result}@${google_sql_database_instance.main_db[0].private_ip_address}:5432/ippoc" : ""
        }
        env_from {
          secret_ref {
            name = google_secret_manager_secret.secrets["api-key"].name
          }
        }
        resources {
          limits = {
            cpu    = each.value.cpu
            memory = each.value.memory
          }
        }
        liveness_probe {
          http_get {
            path = "/health"
            port = each.value.port
          }
          initial_delay_seconds = 5
          period_seconds = 10
        }
        readiness_probe {
          http_get {
            path = "/health"
            port = each.value.port
          }
          initial_delay_seconds = 3
          period_seconds = 5
        }
      }
    }
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"    = tostring(each.value.min_instances)
        "autoscaling.knative.dev/maxScale"    = tostring(each.value.max_instances)
        "run.googleapis.com/vpc-connector"     = google_vpc_access_connector.serverless_connector.name
        "run.googleapis.com/ingress"           = "internal-and-cloud-load-balancing"
      }
    }
  }
  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Service-to-service IAM
resource "google_cloud_run_service_iam_member" "service_accounts" {
  for_each = { for s in var.services : s.name => s }
  
  service  = google_cloud_run_service.services[each.value.name].name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.project_id}@appspot.gserviceaccount.com"
}

# Monitoring Dashboard
resource "google_monitoring_dashboard" "ippoc_dashboard" {
  dashboard_json = jsonencode({
    displayName = "IPPOC ${var.environment} Dashboard"
    mosaicLayout = {
      columns = 12
      tiles = [
        {
          xPos = 0
          yPos = 0
          width = 6
          height = 4
          widget = {
            title = "Request Count"
            scorecard = {
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count"'
                }
              }
            }
          }
        },
        {
          xPos = 6
          yPos = 0
          width = 6
          height = 4
          widget = {
            title = "Latency"
            scorecard = {
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com_latency"'
                }
              }
            }
          }
        }
      ]
    }
  })
}

# Budget Alert
resource "google_billing_budget" "budget" {
  name = "IPPOC ${var.environment} Budget"
  budget_filter {
    projects = ["projects/${var.project_id}"]
    credit_treatment_templates = ["projects/-/creditTrettemplates/30-percent"]
  }
  amount {
    specified_amount = {
      currency_code = "USD"
      units          = "10"
    }
  }
  threshold_rules {
    threshold_percent = 0.5
  }
  threshold_rules {
    threshold_percent = 0.9
  }
  notifications_rule {
    pubsub_topic = google_pubsub_topic.budget.id
    schema_version = "1.0"
  }
}

resource "google_pubsub_topic" "budget" {
  name = "ippoc-budget-${var.environment}"
}

# Outputs
output "services_urls" {
  description = "URLs of deployed services"
  value = {
    for s in var.services : s.name => google_cloud_run_service.services[s.name].status[0].url
  }
}

output "free_tier_usage" {
  description = "Free tier allocation information"
  value = {
    cloud_run_requests      = "2 million/month"
    cloud_run_cpu           = "180,000 vCPU-seconds"
    cloud_run_memory        = "360,000 GB-seconds"
    cloud_sql_storage       = "30 GB"
    cloud_storage           = "5 GB"
    cloud_build             = "120 minutes/day"
    secret_manager_versions = "10,000/month"
    monitoring              = "Custom metrics free"
  }
}
