"""Deploy Fabric items to a workspace via fabric-cicd.

Usage:
    python deploy.py --workspace orchestration --environment dev --auth spn
    python deploy.py --workspace orchestration --environment dev --auth az-login

Reads the target workspace GUID from config/fabric-ids.yaml.
SPN credentials are read from environment variables (load .env first).
"""

import argparse
import os
import sys
from pathlib import Path

import yaml
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from fabric_cicd import FabricWorkspace, publish_all_items, unpublish_all_orphan_items

REPO_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = REPO_ROOT / "config" / "fabric-ids.yaml"


def get_credential(auth_mode: str):
    if auth_mode == "spn":
        required = ["AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET"]
        missing = [v for v in required if not os.environ.get(v)]
        if missing:
            sys.exit(f"SPN auth requires env vars: {missing}. Load .env or pass them in.")
        return ClientSecretCredential(
            tenant_id=os.environ["AZURE_TENANT_ID"],
            client_id=os.environ["AZURE_CLIENT_ID"],
            client_secret=os.environ["AZURE_CLIENT_SECRET"],
        )
    if auth_mode == "az-login":
        return DefaultAzureCredential()
    sys.exit(f"Unknown auth mode: {auth_mode}")


def load_workspace_id(workspace_key: str, environment: str) -> str:
    if not CONFIG_PATH.exists():
        sys.exit(f"Missing {CONFIG_PATH}. Copy config/fabric-ids.example.yaml and fill in.")
    with CONFIG_PATH.open() as f:
        config = yaml.safe_load(f)
    try:
        return config["environments"][environment]["workspaces"][workspace_key]
    except KeyError as e:
        sys.exit(
            f"Missing config entry: environments.{environment}.workspaces.{workspace_key} ({e})"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--workspace",
        required=True,
        help="Workspace key: orchestration, storage, engineering, semantic, bi, ai",
    )
    parser.add_argument(
        "--environment",
        required=True,
        choices=["dev"],
        help="Target environment (Phase 7 adds prod)",
    )
    parser.add_argument("--auth", default="spn", choices=["spn", "az-login"])
    parser.add_argument(
        "--include",
        nargs="+",
        default=["Notebook", "DataPipeline", "Environment"],
        help="Item types to deploy",
    )
    parser.add_argument(
        "--unpublish-orphans",
        action="store_true",
        help="Remove items in the workspace that are not in the repo",
    )
    args = parser.parse_args()

    workspace_id = load_workspace_id(args.workspace, args.environment)
    credential = get_credential(args.auth)

    repository_dir = (REPO_ROOT / "fabric" / args.workspace).resolve()
    parameter_path = REPO_ROOT / "parameter.yml"

    if not repository_dir.is_dir():
        sys.exit(f"No items to deploy: {repository_dir} does not exist")

    print(
        f"Deploying to workspace {args.workspace} ({workspace_id}) "
        f"as {args.environment} using {args.auth} auth"
    )
    print(f"  Repository: {repository_dir}")
    print(f"  Parameter file: {parameter_path if parameter_path.exists() else '(none)'}")

    fw = FabricWorkspace(
        workspace_id=workspace_id,
        repository_directory=str(repository_dir),
        environment=args.environment,
        item_type_in_scope=args.include,
        token_credential=credential,
    )

    publish_all_items(fw)

    if args.unpublish_orphans:
        print("Unpublishing orphan items...")
        unpublish_all_orphan_items(fw)

    print("Deploy complete.")


if __name__ == "__main__":
    main()
