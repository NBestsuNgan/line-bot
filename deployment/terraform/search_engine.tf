
# 1.AI Application - Data store 
resource "google_discovery_engine_data_store" "data_store" {
  location                    = var.data_store_region
  project                     = var.project_id
  data_store_id               = "${var.project_name}-datastore"
  display_name                = "${var.project_name}-datastore"
  industry_vertical           = "GENERIC"
  content_config              = "NO_CONTENT"
  solution_types              = ["SOLUTION_TYPE_SEARCH"]
  create_advanced_site_search = false
  provider                    = google.billing_override
  depends_on                  = [resource.google_project_service.services]
}

# 2.AI Application - Search engine
resource "google_discovery_engine_search_engine" "search_engine" {
  project        = var.project_id
  engine_id      = "${var.project_name}-search-engine"
  collection_id  = "default_collection"
  location       = google_discovery_engine_data_store.data_store.location
  display_name   = "Search Engine App ${title(var.env)}"
  data_store_ids = [google_discovery_engine_data_store.data_store.data_store_id]
  search_engine_config {
    search_tier = "SEARCH_TIER_ENTERPRISE"
  }
  provider = google.billing_override
}


# Grant the 'Discovery Engine User' role to Reasoning Engine
resource "google_project_iam_member" "discovery_engine_sa_access" {
  project = var.project_id
  role    = "roles/discoveryengine.user"
  member  = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"

}