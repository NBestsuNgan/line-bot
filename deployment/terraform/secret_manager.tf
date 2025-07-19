# 1.Define your secrets and their values
locals {
  secrets = {
    "APP_SECRET"             = "placeholder-value"
    "APP_PASSWORD"           = "placeholder-value"
    "REMOTE_AGENT_ENGINE_ID" = "placeholder-value"
  }
}

# 2.Create secrets (store)
resource "google_secret_manager_secret" "secrets" {
  for_each = local.secrets

  secret_id = each.key
  project   = var.project_id
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

# 3.Create versions (the actual values that create on gcp)
resource "google_secret_manager_secret_version" "versions" {
  for_each = local.secrets

  secret      = google_secret_manager_secret.secrets[each.key].id
  secret_data_wo = each.value
}
