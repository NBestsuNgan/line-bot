terraform {
  backend "gcs" {
    bucket = "linebot-terraform-state"
    prefix = "linebot"
  }
}
