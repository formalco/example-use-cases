# AgentCore Harness database access

Files for [Give AgentCore Harness Agents Database Access](https://docs.formal.ai/docs/guides/example-use-cases/agentcore-harness-database-access).
See the guide for setup.

| Path | Contents |
|---|---|
| [`skill/`](skill) | Harness skill that gets a Formal federation token with the execution role and queries Postgres through a Connector |
| [`terraform/`](terraform) | Grants the execution role `sts:GetWebIdentityToken` for the Formal audience only, and creates the Formal machine user, OIDC integration, and Permission |
