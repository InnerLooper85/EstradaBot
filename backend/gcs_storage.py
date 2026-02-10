"""
Google Cloud Storage helper for EstradaBot.
Handles uploading, downloading, and listing files in GCS bucket.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from google.cloud import storage
from google.cloud.exceptions import NotFound


# Bucket name - can be overridden via environment variable
BUCKET_NAME = os.environ.get('GCS_BUCKET', 'estradabot-files')

# Folders in the bucket
UPLOADS_FOLDER = 'uploads'
OUTPUTS_FOLDER = 'outputs'


def get_client():
    """Get GCS client. Uses default credentials in Cloud Run."""
    return storage.Client()


def get_bucket():
    """Get the EstradaBot bucket."""
    client = get_client()
    return client.bucket(BUCKET_NAME)


def upload_file(local_path: str, filename: str, folder: str = UPLOADS_FOLDER) -> str:
    """
    Upload a file to GCS.

    Args:
        local_path: Path to local file
        filename: Name to use in GCS
        folder: Folder in bucket (uploads or outputs)

    Returns:
        GCS blob path
    """
    bucket = get_bucket()
    blob_path = f"{folder}/{filename}"
    blob = bucket.blob(blob_path)
    blob.upload_from_filename(local_path)
    print(f"[GCS] Uploaded {filename} to gs://{BUCKET_NAME}/{blob_path}")
    return blob_path


def upload_file_object(file_obj, filename: str, folder: str = UPLOADS_FOLDER) -> str:
    """
    Upload a file object (like Flask's FileStorage) to GCS.

    Args:
        file_obj: File-like object with read() method
        filename: Name to use in GCS
        folder: Folder in bucket (uploads or outputs)

    Returns:
        GCS blob path
    """
    bucket = get_bucket()
    blob_path = f"{folder}/{filename}"
    blob = bucket.blob(blob_path)
    blob.upload_from_file(file_obj)
    print(f"[GCS] Uploaded {filename} to gs://{BUCKET_NAME}/{blob_path}")
    return blob_path


def download_file(filename: str, local_path: str, folder: str = UPLOADS_FOLDER) -> bool:
    """
    Download a file from GCS to local path.

    Args:
        filename: Name of file in GCS
        local_path: Local path to save to
        folder: Folder in bucket

    Returns:
        True if successful, False if not found
    """
    bucket = get_bucket()
    blob_path = f"{folder}/{filename}"
    blob = bucket.blob(blob_path)

    try:
        blob.download_to_filename(local_path)
        print(f"[GCS] Downloaded {filename} to {local_path}")
        return True
    except NotFound:
        print(f"[GCS] File not found: {blob_path}")
        return False


def download_to_temp(filename: str, folder: str = UPLOADS_FOLDER) -> Optional[str]:
    """
    Download a file from GCS to a temporary file.

    Args:
        filename: Name of file in GCS
        folder: Folder in bucket

    Returns:
        Path to temp file, or None if not found
    """
    # Create temp file with same extension
    suffix = Path(filename).suffix
    fd, temp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)

    if download_file(filename, temp_path, folder):
        return temp_path
    else:
        os.unlink(temp_path)
        return None


def list_files(folder: str = UPLOADS_FOLDER, pattern: str = None) -> List[Dict]:
    """
    List files in a GCS folder.

    Args:
        folder: Folder in bucket
        pattern: Optional pattern to filter (e.g., "Core Mapping" to match files containing that string)

    Returns:
        List of dicts with name, modified, size
    """
    bucket = get_bucket()
    prefix = f"{folder}/"

    files = []
    blobs = bucket.list_blobs(prefix=prefix)

    for blob in blobs:
        # Skip the folder itself
        if blob.name == prefix:
            continue

        filename = blob.name[len(prefix):]  # Remove prefix

        # Apply pattern filter if specified
        if pattern and pattern.lower() not in filename.lower():
            continue

        files.append({
            'name': filename,
            'modified': blob.updated,
            'size': blob.size
        })

    # Sort by modified time, newest first
    files.sort(key=lambda x: x['modified'], reverse=True)
    return files


def get_uploaded_files_info() -> Dict[str, Optional[Dict]]:
    """
    Get info about uploaded files, categorized by type.
    Similar to the original get_uploaded_files() but for GCS.

    Returns:
        Dict with keys: sales_order, shop_dispatch, hot_list, core_mapping, process_map
    """
    files = {
        'sales_order': None,
        'shop_dispatch': None,
        'hot_list': None,
        'core_mapping': None,
        'process_map': None
    }

    all_files = list_files(UPLOADS_FOLDER)

    for file_info in all_files:
        filename = file_info['name']
        fname_lower = filename.lower().replace('_', ' ')

        if 'open sales order' in fname_lower:
            if files['sales_order'] is None or file_info['modified'] > files['sales_order']['modified']:
                files['sales_order'] = file_info
        elif 'shop dispatch' in fname_lower:
            if files['shop_dispatch'] is None or file_info['modified'] > files['shop_dispatch']['modified']:
                files['shop_dispatch'] = file_info
        elif 'hot list' in fname_lower or 'hot_list' in fname_lower:
            if files['hot_list'] is None or file_info['modified'] > files['hot_list']['modified']:
                files['hot_list'] = file_info
        elif 'core mapping' in fname_lower or 'core_mapping' in fname_lower:
            if files['core_mapping'] is None or file_info['modified'] > files['core_mapping']['modified']:
                files['core_mapping'] = file_info
        elif 'stators process' in fname_lower or 'process vsm' in fname_lower:
            if files['process_map'] is None or file_info['modified'] > files['process_map']['modified']:
                files['process_map'] = file_info

    return files


def find_most_recent_file(pattern: str, folder: str = UPLOADS_FOLDER) -> Optional[str]:
    """
    Find the most recent file matching a pattern.

    Args:
        pattern: Pattern to match (e.g., "Core Mapping", "Open Sales Order")
        folder: Folder in bucket

    Returns:
        Filename of most recent match, or None
    """
    files = list_files(folder, pattern)
    if files:
        return files[0]['name']
    return None


def download_files_for_processing(local_dir: str) -> Dict[str, Optional[str]]:
    """
    Download all uploaded files to a local directory for processing.

    Args:
        local_dir: Local directory to download to

    Returns:
        Dict mapping file type to local path (or None if not found)
    """
    os.makedirs(local_dir, exist_ok=True)

    files_info = get_uploaded_files_info()
    local_paths = {}

    for file_type, info in files_info.items():
        if info:
            local_path = os.path.join(local_dir, info['name'])
            if download_file(info['name'], local_path, UPLOADS_FOLDER):
                local_paths[file_type] = local_path
            else:
                local_paths[file_type] = None
        else:
            local_paths[file_type] = None

    return local_paths


def delete_file(filename: str, folder: str = UPLOADS_FOLDER) -> bool:
    """
    Delete a file from GCS.

    Args:
        filename: Name of file in GCS
        folder: Folder in bucket

    Returns:
        True if deleted, False if not found
    """
    bucket = get_bucket()
    blob_path = f"{folder}/{filename}"
    blob = bucket.blob(blob_path)

    try:
        blob.delete()
        print(f"[GCS] Deleted {blob_path}")
        return True
    except NotFound:
        print(f"[GCS] File not found for deletion: {blob_path}")
        return False


# ============== Schedule State Persistence ==============

SCHEDULE_STATE_FILE = 'state/current_schedule.json'


def save_schedule_state(schedule_data: dict) -> bool:
    """
    Save the current schedule state to GCS as JSON.

    Args:
        schedule_data: Dict with stats, reports, generated_at, and serialized orders

    Returns:
        True if saved successfully
    """
    import json

    bucket = get_bucket()
    blob = bucket.blob(SCHEDULE_STATE_FILE)

    try:
        json_data = json.dumps(schedule_data, default=str)
        blob.upload_from_string(json_data, content_type='application/json')
        print(f"[GCS] Saved schedule state to {SCHEDULE_STATE_FILE}")
        return True
    except Exception as e:
        print(f"[GCS] Failed to save schedule state: {e}")
        return False


def load_schedule_state() -> Optional[dict]:
    """
    Load the current schedule state from GCS.

    Returns:
        Schedule data dict, or None if not found
    """
    import json

    bucket = get_bucket()
    blob = bucket.blob(SCHEDULE_STATE_FILE)

    try:
        json_data = blob.download_as_text()
        data = json.loads(json_data)
        print(f"[GCS] Loaded schedule state from {SCHEDULE_STATE_FILE}")
        return data
    except NotFound:
        print(f"[GCS] No schedule state found")
        return None
    except Exception as e:
        print(f"[GCS] Failed to load schedule state: {e}")
        return None


# ============== User Feedback Persistence ==============

FEEDBACK_FILE = 'state/user_feedback.json'


def save_feedback(feedback_entry: dict) -> bool:
    """
    Append a feedback entry to the feedback JSON file in GCS.

    Args:
        feedback_entry: Dict with category, priority, page, message, username, submitted_at

    Returns:
        True if saved successfully
    """
    import json

    # Load existing feedback
    existing = load_feedback()

    # Append new entry
    existing.append(feedback_entry)

    # Save back
    bucket = get_bucket()
    blob = bucket.blob(FEEDBACK_FILE)

    try:
        json_data = json.dumps(existing, default=str)
        blob.upload_from_string(json_data, content_type='application/json')
        print(f"[GCS] Saved feedback ({len(existing)} total entries)")
        return True
    except Exception as e:
        print(f"[GCS] Failed to save feedback: {e}")
        return False


def load_feedback() -> list:
    """
    Load all feedback entries from GCS.

    Returns:
        List of feedback dicts, newest first
    """
    import json

    bucket = get_bucket()
    blob = bucket.blob(FEEDBACK_FILE)

    try:
        json_data = blob.download_as_text()
        data = json.loads(json_data)
        return data if isinstance(data, list) else []
    except NotFound:
        return []
    except Exception as e:
        print(f"[GCS] Failed to load feedback: {e}")
        return []
