variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "project" {
  type    = string
  default = "predixion-call-webhook"
}

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "crm_secret_name" {
  type    = string
  default = "predixion/call-webhook/crm"
}

variable "crm_url" {
  type      = string
  default   = "https://example.invalid/crm"
  sensitive = true
}
