locals {
    re_roles = [
        "roles/discoveryengine.user"
    ]
}

# Grant the 'Discovery Engine User' role to Reasoning Engine
resource "google_project_iam_member" "discovery_engine_sa_access" {
  for_each = toset(local.re_roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
  depends_on = [google_project_service_identity.vertex_sa]
}