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

# 1. Create PR checks trigger (only for staging)
resource "google_cloudbuild_trigger" "pr_checks" {
  count = var.env == "stagging" ? 1 : 0

  name            = "pr-${var.project_name}"
  project         = var.project_id
  location        = var.region
  description     = "Trigger for PR checks"
  service_account = resource.google_service_account.cicd_runner_sa.id

  repository_event_config {
    repository = google_cloudbuildv2_repository.repo.id
    pull_request {
      branch = "main"
    }
  }

  filename = "deployment/ci/pr_checks.yaml"
  included_files = [
    "app/**",
    "data_ingestion/**",
    "tests/**",
    "deployment/**",
    "uv.lock",
    "data_ingestion/**",
  ]
  include_build_logs = "INCLUDE_BUILD_LOGS_WITH_STATUS"
  substitutions = {
    _BUCKET_NAME_LOAD_TEST_RESULTS = resource.google_storage_bucket.bucket_load_test_results.name
    _REGION                        = var.region

  }
  depends_on = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services, google_cloudbuildv2_repository.repo]
}

# 2. Create Deploy to production trigger (only for prod)
resource "google_cloudbuild_trigger" "deploy_to_prod_pipeline" {
  count = var.env == "prod" ? 1 : 0

  name            = "deploy-${var.project_name}"
  project         = var.project_id
  location        = var.region
  description     = "Trigger for deployment to production"
  service_account = resource.google_service_account.cicd_runner_sa.id
  
  repository_event_config {
    repository = google_cloudbuildv2_repository.repo.id
    push {
      branch = "main"
    }
  }
  
  filename = "deployment/cd/deploy-to-prod.yaml"
  included_files = [
    "app/**",
    "tests/**",
    "deployment/**",
    "uv.lock"
  ]
  include_build_logs = "INCLUDE_BUILD_LOGS_WITH_STATUS"
  
  approval_config {
    approval_required = true
  }
  
  substitutions = {
    _PROD_PROJECT_ID             = var.project_id
    _REGION                      = var.region

    # Your other Deploy to Prod Pipeline substitutions
  }
  depends_on = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services, google_cloudbuildv2_repository.repo]
}