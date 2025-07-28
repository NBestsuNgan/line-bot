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

provider "google" {
  region = var.region
  user_project_override = true
}

# services bucket GCS
resource "google_storage_bucket" "services_store_bucket" {
  name                        = "${var.project_id}-${var.project_name}-services-store"
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true

  depends_on = [resource.google_project_service.services]
}

# bucket store test result 
resource "google_storage_bucket" "bucket_load_test_results" {
  name                        = "${var.project_id}-${var.project_name}-load_test_results-store"
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true

  depends_on = [resource.google_project_service.services]
}

# bucket store line bot session  
resource "google_storage_bucket" "bucket_line_bot_session" {
  name                        = "${var.project_id}-${var.project_name}-line_bot_session-store"
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true

  depends_on = [resource.google_project_service.services]
}

# bucket store line bot session  
resource "google_storage_bucket" "vertex_ai_data_storage" {
  name                        = "${var.project_id}-${var.project_name}-vertex_ai_data_storage"
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true

  depends_on = [resource.google_project_service.services]
}

resource "google_storage_bucket_iam_member" "public_access" {
  bucket = google_storage_bucket.vertex_ai_data_storage.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}