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
terraform init -reconfigure -backend-config=backends/backend_stg.hcl
terraform plan --var-file vars/stg_env.tfvars
terraform apply --var-file vars/stg_env.tfvars -auto-approve


# prod
gcloud storage buckets create gs://linebot-terraform-state-{prod_project-id} --project={prod_project-id} --location=us-central1
terraform init -backend-config=backends/backend_prod.hcl # first time only
terraform init -reconfigure -backend-config=backends/backend_prod.hcl
terraform plan --var-file vars/prod_env.tfvars
terraform apply --var-file vars/prod_env.tfvars -auto-approve


# optional
#destroy
terraform destroy -var-file=vars/dev_env.tfvars -auto-approve
terraform destroy -var-file=vars/stg_env.tfvars -auto-approve
terraform destroy -var-file=vars/prod_env.tfvars -auto-approve

```

 