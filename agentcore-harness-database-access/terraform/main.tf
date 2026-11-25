data "aws_iam_role" "harness" {
  name = var.execution_role_name
}

# The skill exchanges this JWT for a Formal federation token. Limiting the audience keeps the role from
# minting AWS-signed JWTs for other services that trust this account's issuer. ForAllValues is also true
# when the key is absent, so the Null check requires an audience.
resource "aws_iam_role_policy" "formal" {
  name = "formal"
  role = data.aws_iam_role.harness.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "sts:GetWebIdentityToken"
      Resource = "*"
      Condition = {
        "ForAllValues:StringEquals" = { "sts:IdentityTokenAudience" = [formal_integration_oidc.harness.audience] }
        Null                        = { "sts:IdentityTokenAudience" = "false" }
      }
    }]
  })
}

resource "formal_user" "harness" {
  type = "machine"
  name = var.name
}

resource "formal_integration_oidc" "harness" {
  name            = var.name
  issuer          = var.oidc_issuer
  machine_user_id = formal_user.harness.id
  claim_condition = "claims.sub == \"${data.aws_iam_role.harness.arn}\""
  status          = "active"
}

# The Harness's JWT is accepted by every Control Plane API; the skill only needs CreateFederationToken.
resource "formal_permission" "harness" {
  name        = var.name
  description = "Restrict the AgentCore Harness machine user to CreateFederationToken"
  status      = "active"
  code        = <<-EOT
    package formal.app

    import future.keywords.if

    default allow = true

    allow = false if {
      input.user.id == "${formal_user.harness.id}"
      input.app.command.name != "CreateFederationToken"
    }
  EOT
}
