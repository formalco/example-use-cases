output "formal_oidc_audience" {
  description = "Set as `FORMAL_OIDC_AUDIENCE` in the Harness's `environmentVariables`."
  value       = formal_integration_oidc.harness.audience
}

output "formal_machine_user_id" {
  description = "Formal machine user the Connector logs the Harness's sessions as."
  value       = formal_user.harness.id
}
