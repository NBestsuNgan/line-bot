data "archive_file" "function_zip" {
  type        = "zip"
  source_dir = "${path.module}/../../line-bot-framework"
  output_path = "${path.module}/other/function.zip"
}

resource "google_storage_bucket_object" "code_upload" {
  name   = "function-code.zip"
  bucket = google_storage_bucket.services_store_bucket.name
  source = data.archive_file.function_zip.output_path
}

resource "google_cloudfunctions2_function" "function" {
  name     = "${var.env}-crf-chat-${var.project_id}"
  location = var.region
  project  = var.project_id

  build_config {
    runtime     = "python312"
    entry_point = "bot_webhook"
    source {
      storage_source {
        bucket = google_storage_bucket.services_store_bucket.name
        object = google_storage_bucket_object.code_upload.name
      }
    }

  }

  service_config {
    available_memory      = "1024M"
    timeout_seconds       = 60
    ingress_settings      = "ALLOW_ALL"
    service_account_email = "${data.google_project.project.number}-compute@developer.gserviceaccount.com"

    dynamic "secret_environment_variables" {
      for_each = local.secrets
      content {
        key        = upper(replace(secret_environment_variables.key, "-", "_")) # e.g. API_KEY_1
        project_id = var.project_id
        secret     = google_secret_manager_secret.secrets[secret_environment_variables.key].secret_id
        version    = "latest"
      }
    }
  }

  labels = {
    env      = var.env
    function = "chat"
  }

  depends_on = [
    google_secret_manager_secret_version.versions,
    google_storage_bucket_object.code_upload
  ]
}


# IAM entry for a single user to invoke the function
resource "google_cloudfunctions2_function_iam_member" "invoker" {
  project        = var.project_id
  location       = var.region
  cloud_function = google_cloudfunctions2_function.function.name

  role   = "roles/cloudfunctions.invoker"
  member = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}


