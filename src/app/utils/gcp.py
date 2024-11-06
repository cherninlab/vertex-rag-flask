import json
from pathlib import Path
from typing import List, Dict
from google.cloud import storage
from google.api_core import exceptions


def get_project_id() -> str:
    """Get project ID from credentials file."""
    try:
        creds_path = Path("credentials.json")
        if creds_path.exists():
            with open(creds_path) as f:
                creds = json.load(f)
                return creds.get("project_id", "")
    except Exception as e:
        print(f"Error reading credentials: {e}")
    return ""


def get_service_account() -> str:
    """Get service account email from credentials file."""
    try:
        creds_path = Path("credentials.json")
        if creds_path.exists():
            with open(creds_path) as f:
                creds = json.load(f)
                return creds.get("client_email", "")
    except Exception as e:
        print(f"Error reading credentials: {e}")
    return ""


def check_storage_permissions(project_id: str) -> Dict[str, bool]:
    """Check what storage permissions the service account has."""
    try:
        storage_client = storage.Client(project=project_id)
        permissions = {
            "list_buckets": True,
            "create_buckets": True,
            "manage_objects": True
        }

        # Try to list buckets
        try:
            next(storage_client.list_buckets(max_results=1))
        except Exception:
            permissions["list_buckets"] = False

        # Try to check bucket creation permission
        try:
            storage_client.bucket("temp-permission-check")._get_iam_policy()
        except exceptions.Forbidden:
            permissions["create_buckets"] = False
        except Exception:
            pass  # Other errors don't necessarily mean no permission

        return permissions
    except Exception as e:
        print(f"Error checking permissions: {e}")
        return {
            "list_buckets": False,
            "create_buckets": False,
            "manage_objects": False
        }


def list_buckets(project_id: str) -> List[str]:
    """List all available buckets in the project."""
    try:
        storage_client = storage.Client(project=project_id)
        return [bucket.name for bucket in storage_client.list_buckets()]
    except Exception as e:
        print(f"Error listing buckets: {e}")
        return []


def create_bucket(project_id: str, bucket_name: str, location: str = "us-central1") -> Dict[str, any]:
    """Create a new GCS bucket."""
    try:
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)

        if not bucket.exists():
            bucket = storage_client.create_bucket(
                bucket_name, location=location)
            return {"success": True, "message": f"Bucket {bucket.name} created"}
        return {"success": False, "message": f"Bucket {bucket_name} already exists"}
    except exceptions.Forbidden as e:
        sa_email = get_service_account()
        return {
            "success": False,
            "message": "Permission denied. Required permissions:",
            "details": f"""
The service account {sa_email} needs the following permissions:
- roles/storage.admin OR
- storage.buckets.create AND storage.buckets.get

You can grant these permissions using gcloud:
gcloud projects add-iam-policy-binding {project_id} \\
    --member="serviceAccount:{sa_email}" \\
    --role="roles/storage.admin"
"""
        }
    except Exception as e:
        return {"success": False, "message": str(e)}
