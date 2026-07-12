# ================================================================
#  BANCONOVA — Infraestructura con Terraform
#  Crea namespaces y resource quotas en Kubernetes (Minikube)
# ================================================================

terraform {
  required_version = ">= 1.0.0"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

provider "kubernetes" {
  config_path    = var.kube_config_path
  config_context = var.kube_context
}

# ── Namespace desarrollo ─────────────────────────────────────────
resource "kubernetes_namespace" "desarrollo" {
  metadata {
    name = "banconova-desarrollo"
    labels = {
      proyecto = "banconova"
      ambiente = "desarrollo"
      version  = var.app_version
    }
  }
}

# ── Namespace produccion ─────────────────────────────────────────
resource "kubernetes_namespace" "produccion" {
  metadata {
    name = "banconova-produccion"
    labels = {
      proyecto = "banconova"
      ambiente = "produccion"
      version  = var.app_version
    }
  }
}

# ── Resource Quota desarrollo ────────────────────────────────────
resource "kubernetes_resource_quota" "desarrollo" {
  metadata {
    name      = "banconova-desarrollo-quota"
    namespace = kubernetes_namespace.desarrollo.metadata[0].name
  }
  spec {
    hard = {
      "pods"            = "5"
      "requests.cpu"    = "500m"
      "requests.memory" = "512Mi"
      "limits.cpu"      = "1"
      "limits.memory"   = "1Gi"
    }
  }
}

# ── Resource Quota produccion ────────────────────────────────────
resource "kubernetes_resource_quota" "produccion" {
  metadata {
    name      = "banconova-produccion-quota"
    namespace = kubernetes_namespace.produccion.metadata[0].name
  }
  spec {
    hard = {
      "pods"            = "10"
      "requests.cpu"    = "2"
      "requests.memory" = "2Gi"
      "limits.cpu"      = "4"
      "limits.memory"   = "4Gi"
    }
  }
}
