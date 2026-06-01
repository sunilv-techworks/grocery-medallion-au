"""Quick SPN auth verification. Lists Fabric workspaces accessible to the SPN.

Usage:
    AZURE_TENANT_ID=... AZURE_CLIENT_ID=... AZURE_CLIENT_SECRET=... \
        python tools/verify-spn.py
"""

import os
import sys

import requests
from azure.identity import ClientSecretCredential


def main() -> None:
    required = ["AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        sys.exit(f"Missing env vars: {missing}")

    cred = ClientSecretCredential(
        tenant_id=os.environ["AZURE_TENANT_ID"],
        client_id=os.environ["AZURE_CLIENT_ID"],
        client_secret=os.environ["AZURE_CLIENT_SECRET"],
    )
    token = cred.get_token("https://api.fabric.microsoft.com/.default").token

    resp = requests.get(
        "https://api.fabric.microsoft.com/v1/workspaces",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()

    workspaces = resp.json().get("value", [])
    print(f"SPN authenticated. {len(workspaces)} workspace(s) visible:")
    for ws in workspaces:
        print(f"  - {ws['displayName']} ({ws['id']})")


if __name__ == "__main__":
    main()
