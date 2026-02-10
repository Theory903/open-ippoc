# IPPOC Google Cloud Infrastructure
# Terraform configuration for Cloud Run, Cloud SQL, and related resources

# ==============================================================================
# PROVIDER CONFIGURATION
# ==============================================================================

terraform {
  required_version = ">= 1.0"

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
    prefix = "infra"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# ==============================================================================
# VARIABLES
# ==============================================================================

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment (staging/production)"
  type        = string
  default     = "production"
}

variable "image_name" {
  description = "Docker image URL"
  type        = string
}

variable "min_instances" {
  description = "Minimum Cloud Run instances"
  type        = number
  default     = 1
}

variable "max_instances" {
  description = "Maximum Cloud Run instances"
  type        = number
  default     = 10
}

variable "memory" {
  description = "Memory allocation per instance (Gi)"
  type        = string
  default     = "1Gi"
}

variable "cpu" {
  description = "CPU allocation per instance"
  type        = number
  default     = 2
}

# ==============================================================================
# SERVICE ACCOUNTS
# ==============================================================================

resource "google_service_account" "ippoc" {
  account_id   = "ippoc-${var.environment}"
  display_name = "IPPOC ${title(var.environment)} Service Account"
  description  = "Service account for IPPOC ${var.environment} deployment"
}

resource "google_project_iam_member" "ippoc_cloudrun" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.ippoc.email}"
}

resource "google_project_iam_member" "ippoc_secretmanager" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.ippoc.email}"
}

# ==============================================================================
# CLOUD SQL (PostgreSQL) - Optional
# ==============================================================================

resource "google_sql_database_instance" "ippoc" {
  count = var.environment == "production" ? 1 : 0

  name             = "ippoc-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier             = "db-f1-micro"
    availability_type = "REGIONAL"

    ip_configuration {
      ipv4_enabled = false
      private_network = google_compute_network.ippoc.id
    }

    backup_configuration {
      enabled    = true
      start_time = "03:00"
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }
  }

  deletion_protection = var.environment == "production"
}

resource "google_sql_database" "ippoc" {
  count = var.environment == "production" ? 1 : 0

  name      = "ippoc"
  instance  = google_sql_database_instance.ippoc[0].name
  charset   = "UTF8"
  collation = "en_US.UTF8"
}

resource "google_sql_user" "ippoc" {
  count = var.environment == "production" ? 1 : 0

  name     = "ippoc"
  instance = google_sql_database_instance.ippoc[0].name
  password = random_password.db_password.result
}

# ==============================================================================
# SECRET MANAGER
# ==============================================================================

resource "google_secret_manager_secret" "ippoc_api_key" {
  secret_id = "ippoc-api-key-${var.environment}"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "ippoc_api_key_v1" {
  secret      = google_secret_manager_secret.ippoc_api_key.id
  secret_data = random_password.api_key.result
}

resource "google_secret_manager_secret" "database_url" {
  count = var.environment == "production" ? 1 : 0

  secret_id = "database-url-${var.environment}"

  replication {
    automatic = true
  }
}

# ==============================================================================
# CLOUD RUN SERVICE
# ==============================================================================

resource "google_cloud_run_service" "ippoc" {
  name     = "ippoc-${var.environment}"
  location = var.region

  template {
    spec {
      containers {
        image = var.image_name

        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
          }
        }

        env {
          name  = "INSTANCE"
          value = var.environment
        }

        env {
          name  = "LOG_LEVEL"
          value = var.environment == "production" ? "INFO" : "DEBUG"
        }

        env_from {
          secret_ref {
            name = google_secret_manager_secret.ippoc_api_key.secret_id
          }
        }

        port = 8080
      }

      service_account_name = google_service_account.ippoc.email
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.min_instances
        "autoscaling.knative.dev/maxScale" = var.max_instances
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  lifecycle {
    ignore_changes = [
      template[0].spec[0].containers[0].image,
    ]
  }
}

resource "google_cloud_run_service_iam_member" "public" {
  count = var.environment == "production" ? 1 : 0

  service  = google_cloud_run_service.ippoc.name
  location = google_cloud_run_service.ippoc.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ==============================================================================
# CLOUD SQL AUTH PROXY (Sidecar)
# ==============================================================================

resource "google_cloud_run_service" "ippoc_proxy" {
  count = var.environment == "production" ? 1 : 0

  name     = "ippoc-${var.environment}-proxy"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/cloudsql-docker/nice-proxy:2.1"

        env {
          name  = "PORT"
          value = "8081"
        }

        env {
          name  = "ENVOY_IP"
          value = "127.0.0.1"
        }
      }

      service_account_name = google_service_account.ippoc.email
    }
  }
}

# ==============================================================================
# NETWORK
# ==============================================================================

resource "google_compute_network" "ippoc" {
  name                    = "ippoc-${var.environment}"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "ippoc" {
  name          = "ippoc-${var.environment}"
  region        = var.region
  ip_cidr_range = "10.0.0.0/24"
  network       = google_compute_network.ippoc.id
}

# ==============================================================================
# OUTPUTS
# ==============================================================================

output "cloud_run_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_service.ippoc.status[0].url
}

output "service_account_email" {
  description = "Service account email"
  value       = google_service_account.ippoc.email
}

output "database_connection" {
  description = "Cloud SQL connection name"
  value       = var.environment == "production" ? google_sql_database_instance.ippoc[0].connection_name : "N/A"
  sensitive   = true
}

# ==============================================================================
# RANDOM PASSWORDS
# ==============================================================================

resource "random_password" "api_key" {
  length  = 32
  special = false
}

resource "random_password" "db_password" {
  length  = 32
  special = false
}
