variable "api_key" {
  description = "The secret API key for authenticating with the gateway"
  type        = string
  sensitive   = true # This hides the value from Terraform's console output
}