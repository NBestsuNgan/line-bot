# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

locals {
  project_ids = {
    dev = var.project_id
  }

  default_compute_roles = [
    "roles/aiplatform.user",
    "roles/cloudbuild.builds.builder",
    "roles/cloudfunctions.invoker",
    "roles/secretmanager.secretAccessor",
    "roles/aiplatform.admin"
  ]


  secrets_manager_sa_roles = [
    "roles/secretmanager.secretAccessor"
  ]


  cicd_runner_roles = [
    "roles/editor",                            # For broad resource management
    "roles/resourcemanager.projectIamAdmin",   # For managing project-level IAM
    "roles/serviceusage.serviceUsageConsumer", # For enabling APIs
    "roles/iam.serviceAccountAdmin",           # For create and manage resource
    "roles/secretmanager.secretAccessor",      # For access sescret values
    "roles/aiplatform.user",                   # For access to vertex ai
    "roles/storage.admin",                     # Required for bucket access (e.g., logs, artifacts)
    "roles/cloudbuild.connectionAdmin",        # Required if managing Cloud Build connections
    "roles/logging.logWriter",                 # For write log
    "roles/apigateway.admin"                   # For future re-config if nessecary
  ]


}

# Get the project number for the dev project
data "google_project" "project" {
  project_id = var.project_id
}


# Grant Storage Object Creator role to default compute service account
resource "google_project_iam_member" "default_compute_sa_roles" {
  for_each = toset(local.default_compute_roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"

  depends_on = [google_project_service.services]
}

# CICD runer
resource "google_service_account" "cicd_runner_sa" {
  account_id   = "${var.project_name}-cb"
  display_name = "CICD Runner SA"
  project      = var.project_id
  depends_on   = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services]
}

# Grant all specified roles to the CICD Runner SA using for_each
resource "google_project_iam_member" "cicd_runner_project_roles" {
  for_each = toset(local.cicd_runner_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.cicd_runner_sa.email}"


  depends_on = [
    google_service_account.cicd_runner_sa,
  ]
}


# Grant required permissions to Vertex AI service account
resource "google_project_iam_member" "vertex_ai_sa_permissions" {
  for_each = {
    for pair in setproduct(keys(local.project_ids), var.agentengine_sa_roles) :
    join(",", pair) => pair[1]
  }

  project    = var.project_id
  role       = each.value
  member     = google_project_service_identity.vertex_sa.member
  depends_on = [resource.google_project_service.services]
}


# Service account to run Vertex AI pipeline
resource "google_service_account" "vertexai_pipeline_app_sa" {
  for_each = local.project_ids

  account_id   = "${var.project_name}-rag"
  display_name = "Vertex AI Pipeline app SA"
  project      = each.value
  depends_on   = [resource.google_project_service.services]
}

# Special assignment: Allow the CICD SA to create tokens
resource "google_service_account_iam_member" "cicd_run_invoker_token_creator" {
  service_account_id = google_service_account.cicd_runner_sa.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${resource.google_service_account.cicd_runner_sa.email}"
  depends_on         = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services]
}
# Special assignment: Allow the CICD SA to impersonate himself for trigger creation
resource "google_service_account_iam_member" "cicd_run_invoker_account_user" {
  service_account_id = google_service_account.cicd_runner_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${resource.google_service_account.cicd_runner_sa.email}"
  depends_on         = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services]
}

resource "google_project_iam_member" "vertexai_pipeline_sa_roles" {
  for_each = {
    for pair in setproduct(keys(local.project_ids), var.pipelines_roles) :
    join(",", pair) => {
      project = local.project_ids[pair[0]]
      role    = pair[1]
    }
  }

  project    = each.value.project
  role       = each.value.role
  member     = "serviceAccount:${google_service_account.vertexai_pipeline_app_sa[split(",", each.key)[0]].email}"
  depends_on = [resource.google_project_service.services]
}


# 
# resource "google_service_account" "secrets_manager_sa" {
#   account_id   = "secrets-manager-sa"
#   display_name = "Secrets Manager Service Account"
#   project      = var.project_id
# }

# resource "google_project_iam_member" "secrets_manager_sa_secret_accessor" {
#   for_each = toset(local.secrets_manager_sa_roles)

#   project = var.project_id
#   role    = each.value
#   member  = "serviceAccount:${google_service_account.secrets_manager_sa.email}"
# }

