# Deployment README.md

This folder contains the infrastructure-as-code and CI/CD pipeline configurations for deploying a conversational Generative AI application on Google Cloud.

The application leverages [**Terraform**](http://terraform.io) to define and provision the underlying infrastructure, while [**Cloud Build**](https://cloud.google.com/build/) orchestrates the continuous integration and continuous deployment (CI/CD) pipeline.

## Deployment Workflow

![Deployment Workflow](https://storage.googleapis.com/github-repo/generative-ai/sample-apps/e2e-gen-ai-app-starter-pack/deployment_workflow.png)

**Description:**

1. CI Pipeline (`deployment/ci/pr_checks.yaml`):

   - Triggered on pull request creation/update
   - Runs unit and integration tests

2. CD Pipeline (`deployment/cd/staging.yaml`):

   - Triggered on merge to `main` branch
   - Builds and pushes application to Artifact Registry
   - Deploys to staging environment
   - Performs load testing

3. Production Deployment (`deployment/cd/deploy-to-prod.yaml`):
   - Triggered after successful staging deployment
   - Requires manual approval
   - Deploys to production environment

## Setup

> **Note:** For a streamlined one-command deployment of the entire CI/CD pipeline and infrastructure using Terraform, you can use the [`uvx agent-starter-pack setup-cicd` CLI command](https://googlecloudplatform.github.io/agent-starter-pack/cli/setup_cicd.html). Currently only supporting Github.

**Prerequisites:**

1. A set of Google Cloud projects:
   - Staging project
   - Production project
   - CI/CD project (can be the same as staging or production)
2. Terraform installed on your local machine
3. Enable required APIs in the CI/CD project. This will be required for the Terraform deployment:

   ```bash
   gcloud config set project $YOUR_CI_CD_PROJECT_ID
   gcloud services enable serviceusage.googleapis.com cloudresourcemanager.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
   ```

## Step-by-Step Guide

1. **Create a Git Repository using your favorite Git provider (GitHub, GitLab, Bitbucket, etc.)**

2. **Connect Your Repository to Cloud Build**
   For detailed instructions, visit: [Cloud Build Repository Setup](https://cloud.google.com/build/docs/repositories#whats_next).<br>

   ![Alt text](https://storage.googleapis.com/github-repo/generative-ai/sample-apps/e2e-gen-ai-app-starter-pack/connection_cb.gif)

3. **Configure Terraform Variables**

   - Edit [`deployment/terraform/vars/env.tfvars`](../terraform/vars/env.tfvars) with your Google Cloud settings.

   | Variable               | Description                                                     | Required |
   | ---------------------- | --------------------------------------------------------------- | :------: |
   | project_name           | Project name used as a base for resource naming                 |   Yes    |
   | prod_project_id        | **Production** Google Cloud Project ID for resource deployment. |   Yes    |
   | staging_project_id     | **Staging** Google Cloud Project ID for resource deployment.    |   Yes    |
   | cicd_runner_project_id | Google Cloud Project ID where CI/CD pipelines will execute.     |   Yes    |
   | region                 | Google Cloud region for resource deployment.                    |   Yes    |
   | host_connection_name   | Name of the host connection you created in Cloud Build          |   Yes    |
   | repository_name        | Name of the repository you added to Cloud Build                 |   Yes    |

   Other optional variables may include: telemetry and feedback log filters, service account roles, and for projects requiring data ingestion: pipeline cron schedule, pipeline roles, and datastore-specific configurations.

4. **Deploy Infrastructure with Terraform**

   - Open a terminal and navigate to the Terraform directory:

   ```bash
   cd deployment/terraform
   ```

   - Initialize Terraform:

   ```bash
   terraform init
   ```

   - Apply the Terraform configuration:

   ```bash
   terraform apply --var-file vars/env.tfvars
   ```

   - Type 'yes' when prompted to confirm

After completing these steps, your infrastructure will be set up and ready for deployment!

## Dev Deployment

For End-to-end testing of the application, including tracing and feedback sinking to BigQuery, without the need to trigger a CI/CD pipeline.

First, enable required Google Cloud APIs:

```bash
gcloud config set project <your-dev-project-id>
gcloud services enable serviceusage.googleapis.com cloudresourcemanager.googleapis.com
```

After you edited the relative [`env.tfvars` file](../terraform/dev/vars/env.tfvars), follow the following instructions:




# Deploy in different Environment same process for (dev/stagging/prod)
```bash
### 0
# prepare data
#  -  project_id(dev, stagging, prod)
#  -  repository_owner
#  -  repository_name (create repo first)
#  -  github_app_installation_id


# dev
gcloud storage buckets create gs://linebot-terraform-state-{dev_project-id} --project={dev_project-id} --location=us-central1
terraform init -backend-config=backends/backend_dev.hcl # first time only
terraform init -reconfigure -backend-config=backends/backend_dev.hcl # for testing in development
terraform plan --var-file vars/dev_env.tfvars
terraform apply --var-file vars/dev_env.tfvars -auto-approve


# stagging
gcloud storage buckets create gs://linebot-terraform-state-{stagging_project-id} --project={stagging_project-id} --location=us-central1
terraform init -backend-config=backends/backend_stg.hcl # first time only
terraform plan --var-file vars/stg_env.tfvars
terraform apply --var-file vars/stg_env.tfvars -auto-approve


# prod
gcloud storage buckets create gs://linebot-terraform-state-{prod_project-id} --project={prod_project-id} --location=us-central1
terraform init -backend-config=backends/backend_prod.hcl # first time only
terraform plan --var-file vars/prod_env.tfvars
terraform apply --var-file vars/prod_env.tfvars -auto-approve



# optional
#destroy
terraform destroy -var-file=vars/dev_env.tfvars -auto-approve
terraform destroy -var-file=vars/stg_env.tfvars -auto-approve
terraform destroy -var-file=vars/prod_env.tfvars -auto-approve

```

 