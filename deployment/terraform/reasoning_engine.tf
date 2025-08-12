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