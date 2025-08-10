# Project name used for resource naming
project_name = "linebot"

# Your Production Google Cloud project id
project_id = "{stg-project-id}"

# Environment (dev, stagging, prod)
env = "stagging"

# Name of the host connection you created in Cloud Build
host_connection_name = "git-linebot"

# Name of the repository you added to Cloud Build
repository_name = "line-bot"

# The Google Cloud region you will use to deploy the infrastructure
region = "us-central1"

#The value can only be one of "global", "us" and "eu".
data_store_region          = "us"
repository_owner           = "XXXX"
github_app_installation_id = "XXXX"
github_pat_secret_id       = "git-line-bot-github-oauthtoken-XXXX"
connection_exists          = true
repository_exists          = true
