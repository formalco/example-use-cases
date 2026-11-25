#!/usr/bin/env python3
"""Mint Formal federation credentials from the Harness's AWS role and query Postgres through the Formal Connector.

The first run in a session installs the pinned packages in requirements.txt into a virtualenv under /tmp.
"""

import argparse
import base64
import hashlib
import json
import os
import shutil
import ssl
import subprocess
import sys
import warnings
from pathlib import Path

FORMAL_API = "https://api.formal.ai"
REQUIREMENTS = Path(__file__).resolve().with_name("requirements.txt")


def ensure_venv():
    digest = hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()[:12]
    venv = Path(f"/tmp/formal-connector-{digest}")
    if Path(sys.prefix) == venv:
        return
    python = venv / "bin" / "python"
    if not python.exists():
        staging = Path(f"{venv}.{os.getpid()}")
        subprocess.run([sys.executable, "-m", "venv", staging], check=True)
        subprocess.run(
            [
                staging / "bin" / "python",
                "-m",
                "pip",
                "install",
                "--quiet",
                "--disable-pip-version-check",
                "--require-hashes",
                "--only-binary",
                ":all:",
                "-r",
                REQUIREMENTS,
            ],
            check=True,
        )
        try:
            staging.rename(venv)
        except OSError:
            shutil.rmtree(staging)
    os.execv(python, [python, __file__, *sys.argv[1:]])


def ssl_context(sslmode):
    if sslmode == "disable":
        return None
    ctx = ssl.create_default_context()
    if sslmode == "require":
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def main():
    p = argparse.ArgumentParser()
    p.add_argument("sql", nargs="?")
    env = os.environ.get
    p.add_argument("--host", default=env("FORMAL_CONNECTOR_HOST"))
    p.add_argument(
        "--port", type=int, default=int(env("FORMAL_CONNECTOR_PORT") or 5432)
    )
    p.add_argument("--audience", default=env("FORMAL_OIDC_AUDIENCE"))
    p.add_argument("--database", default=env("FORMAL_DATABASE") or "postgres")
    p.add_argument(
        "--native-user",
        default=env("FORMAL_NATIVE_USER"),
        help="native user label to request (sent as <formal user>@<label>)",
    )
    p.add_argument("--region", default=env("AWS_REGION") or env("AWS_DEFAULT_REGION"))
    p.add_argument(
        "--sslmode",
        default=env("FORMAL_SSLMODE") or "verify-full",
        choices=["verify-full", "require", "disable"],
    )
    p.add_argument("--whoami", action="store_true")
    a = p.parse_args()
    if not a.host or not a.audience:
        p.error(
            "set FORMAL_CONNECTOR_HOST and FORMAL_OIDC_AUDIENCE, or pass --host and --audience"
        )

    ensure_venv()
    warnings.filterwarnings("ignore", module="urllib3")
    import boto3
    import httpx
    import pg8000.native

    jwt = boto3.client("sts", region_name=a.region).get_web_identity_token(
        Audience=[a.audience], SigningAlgorithm="RS256", DurationSeconds=900
    )["WebIdentityToken"]
    claims = json.loads(base64.urlsafe_b64decode(jwt.split(".")[1] + "=="))
    # api.formal.ai rejects HTTP/1.1 with 464.
    with httpx.Client(http2=True, timeout=10) as client:
        r = client.post(
            f"{FORMAL_API}/core.v1.ConnectorService/CreateFederationToken",
            headers={"Authorization": f"Bearer {jwt}"},
            json={},
        )
    if r.status_code != 200:
        sys.exit(f"Formal CreateFederationToken failed: {r.status_code} {r.text[:500]}")
    fed = r.json()
    print(
        f"# aws sub={claims.get('sub')} -> formal user={fed['username']} expires_at={fed.get('expiresAt') or fed.get('expires_at')}",
        file=sys.stderr,
    )
    if a.whoami:
        return

    # Must be the Formal username: any other name is passed through to the database unauthenticated by Formal.
    user = fed["username"] + (f"@{a.native_user}" if a.native_user else "")
    try:
        conn = pg8000.native.Connection(
            user,
            host=a.host,
            port=a.port,
            database=a.database,
            password=fed["token"],
            ssl_context=ssl_context(a.sslmode),
            application_name="agentcore-harness",
            timeout=30,
        )
    except pg8000.native.DatabaseError as e:
        sys.exit(f"connector auth failed: {e}")
    except pg8000.native.InterfaceError as e:
        sys.exit(f"cannot connect to the Connector: {e}")
    try:
        rows = conn.run(a.sql or "SELECT current_user")
    except pg8000.native.DatabaseError as e:
        sys.exit(f"query failed: {e}")
    if conn.columns:
        print("\t".join(c["name"] for c in conn.columns))
    for row in rows:
        print("\t".join("" if v is None else str(v) for v in row))


if __name__ == "__main__":
    main()
