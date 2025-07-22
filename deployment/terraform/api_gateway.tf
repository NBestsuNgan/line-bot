locals {
  # Roles for the API Gateway Service Account itself (to invoke other services like Cloud Run)
  # This role is applied to the service account, not the API Gateway resources.
  bot_sa_invoker_roles = [
    "roles/run.invoker",
    "roles/cloudfunctions.invoker"
  ]

  # Roles for managing the API Gateway resources (API, API Config, Gateway)
  # These roles are applied ON the API Gateway resources, granting permissions
  # to the specified member to manage/view the API Gateway.
  # 'apigateway.admin' is a valid role for managing API Gateway resources.
  api_gateway_management_roles = [
    "roles/apigateway.admin"
  ]
}

resource "google_api_gateway_api" "api" {
  provider = google-beta
  api_id   = "${var.env}-api-gateway-api"
  project  = var.project_id
}


resource "google_api_gateway_api_config" "api_cfg" {
  provider      = google-beta
  api           = google_api_gateway_api.api.api_id
  api_config_id = "${var.env}-api-config-${substr(sha1(filebase64("${path.module}/other/line_bot_api_spec.yaml")), 0, 8)}"
  project       = var.project_id

  openapi_documents {
    document {
      path     = "spec.yaml"
      contents = base64encode(templatefile("${path.module}/other/line_bot_api_spec.yaml", {
        cloud_function_url = google_cloudfunctions2_function.function.service_config[0].uri
        project_id         = var.project_id
        env                = var.env
      }))
    }
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    google_api_gateway_api.api,
  ]
}

resource "google_api_gateway_gateway" "api_gw" {
  provider   = google-beta
  api_config = google_api_gateway_api_config.api_cfg.id
  gateway_id = "${var.env}-api-gateway"
  project    = var.project_id
  region     = var.region

  depends_on = [google_api_gateway_api_config.api_cfg]
}

# Create an API key for the API Gateway
resource "google_apikeys_key" "api_gateway_key" {
  name         = "${var.env}-api-gateway-key"
  display_name = "${var.env} API Gateway Key"
  project      = var.project_id

  # restrictions {
  #   api_targets {
  #     service = google_api_gateway_api.api.managed_service
  #     methods = ["POST", "GET"]
  #   }
  # }

  depends_on = [google_api_gateway_api.api]
}


###################################################### IAM ####################################################

# Create the API Gateway service account
resource "google_service_account" "api_gateway_sa" {
  account_id   = "line-bot-api-gateway-iam-gser"
  display_name = "line Bot API Gateway Service Account"
  project      = var.project_id
  depends_on   = [resource.google_project_service.services]
}

# Assign roles to the API Gateway service account
# This is where roles like 'roles/run.invoker' should be applied.
# This grants the service account permission to invoke Cloud Run services.
resource "google_project_iam_member" "bot_sa_invoker_roles" {
  for_each = toset(local.bot_sa_invoker_roles)

  project    = var.project_id
  role       = each.key
  member     = "serviceAccount:${google_service_account.api_gateway_sa.email}"
  depends_on = [google_service_account.api_gateway_sa]
}

# Assign API Gateway specific IAM roles for managing the API Gateway itself.
# These roles grant permissions to the service account to manage the API Gateway resources.
resource "google_api_gateway_api_iam_member" "api_management_member" {
  for_each = toset(local.api_gateway_management_roles)

  provider   = google-beta
  project    = google_api_gateway_api.api.project
  api        = google_api_gateway_api.api.api_id
  role       = each.key
  member     = "serviceAccount:${google_service_account.api_gateway_sa.email}"
  depends_on = [google_service_account.api_gateway_sa, google_api_gateway_api.api]
}

resource "google_api_gateway_api_config_iam_member" "api_config_management_member" {
  for_each = toset(local.api_gateway_management_roles)

  provider   = google-beta
  project    = google_api_gateway_api_config.api_cfg.project
  api        = google_api_gateway_api_config.api_cfg.api
  api_config = google_api_gateway_api_config.api_cfg.api_config_id
  role       = each.key
  member     = "serviceAccount:${google_service_account.api_gateway_sa.email}"
  depends_on = [google_service_account.api_gateway_sa, google_api_gateway_api_config.api_cfg]
}

resource "google_api_gateway_gateway_iam_member" "gateway_management_member" {
  for_each = toset(local.api_gateway_management_roles)

  provider   = google-beta
  project    = google_api_gateway_gateway.api_gw.project
  region     = google_api_gateway_gateway.api_gw.region
  gateway    = google_api_gateway_gateway.api_gw.gateway_id
  role       = each.key
  member     = "serviceAccount:${google_service_account.api_gateway_sa.email}"
  depends_on = [google_service_account.api_gateway_sa, google_api_gateway_gateway.api_gw]
}
