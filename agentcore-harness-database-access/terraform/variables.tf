variable "execution_role_name" {
  description = "Name of your Harness's existing IAM execution role."
  type        = string
}

variable "name" {
  description = "Name of the Formal machine user, OIDC integration, and Permission."
  type        = string
  default     = "agentcore-harness"
}

variable "oidc_issuer" {
  description = "Your account's outbound web identity federation issuer URL, from `aws iam get-outbound-web-identity-federation-info`."
  type        = string
}
