---
name: formal-connector
description: Query databases through the Formal Connector. The agent has no database credentials; this skill mints short-lived Formal credentials from the Harness's AWS identity.
---

# Formal Connector access

You have no database credentials. The only path to data is the Formal
Connector, which authenticates you, applies policy, injects the database
credentials, and logs the session.

The Harness sets the Connector and audience in `FORMAL_CONNECTOR_HOST`,
`FORMAL_CONNECTOR_PORT`, and `FORMAL_OIDC_AUDIENCE`.

## Run a query

From this skill's directory:

```bash
python3 scripts/formal_pg.py "SELECT current_user"
```

Add `--database <NAME>` to query a database other than `postgres` (or the
`FORMAL_DATABASE` default). Output is tab-separated with a header row.

Use `--whoami` to print only the Formal identity and token expiry.

The script verifies the Connector's TLS certificate. Do not change
`--sslmode` unless the Harness configuration sets `FORMAL_SSLMODE`.

The first run in a session takes about ten seconds: it installs the pinned
packages in `scripts/requirements.txt` into a virtualenv under `/tmp`.

The script:
1. Calls AWS STS `GetWebIdentityToken` with the Harness execution role to get
   an AWS-signed JWT for the Formal audience.
2. Exchanges it at Formal `CreateFederationToken` for a short-lived Formal
   username and token, kept in memory only.
3. Connects to the Connector as the Formal username, with the token as the
   password, and runs the SQL.

## Rules

- Run the script as is. Do not edit it or change the database username: the
  Connector only enforces Formal auth for the Formal username the script sends.
- Only use this script for database access. Do not look for or ask for
  database passwords.
- Never print the token.
