# utils/google_drive_utils.py
import streamlit as st
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os
import json
from io import BytesIO

# Path to store client_secrets.json (downloaded from Google Cloud Console)
# For production, consider using Streamlit Secrets for credentials.
CLIENT_SECRETS_PATH = "client_secrets.json" # You need to create this file in your project root

# Path to store authenticated credentials
CREDENTIALS_PATH = "credentials.json"

def get_gdrive_auth():
    """
    Authenticates with Google Drive and returns a GoogleDrive object.
    Handles initial authentication flow and subsequent credential loading.
    """
    gauth = GoogleAuth()

    # Try to load saved client credentials
    if os.path.exists(CREDENTIALS_PATH):
        gauth.LoadCredentialsFile(CREDENTIALS_PATH)

    if gauth.credentials is None:
        # Authenticate if they're not there
        gauth.LocalWebserverAuth() # Creates a local webserver for authentication
    elif gauth.access_token_expired:
        # Refresh them if expired
        gauth.Refresh()
    else:
        # Initialize the saved creds
        gauth.Authorize()

    # Save the current credentials to a file
    gauth.SaveCredentialsFile(CREDENTIALS_PATH)
    
    return GoogleDrive(gauth)

@st.cache_resource # Cache the drive object to avoid re-authenticating on every rerun
def get_gdrive_service():
    """Provides a cached GoogleDrive service."""
    try:
        return get_gdrive_auth()
    except Exception as e:
        st.error(f"Google Drive authentication failed: {e}. Please ensure 'client_secrets.json' is correctly configured and you have granted permissions.")
        st.info("For local development, you might need to delete 'credentials.json' to re-authenticate.")
        return None

def list_gdrive_files(drive_service, folder_id=None):
    """
    Lists files and folders in a specified Google Drive folder.
    If folder_id is None, lists files in My Drive root.
    """
    if not drive_service:
        return []

    query = "'root' in parents and trashed=false"
    if folder_id:
        query = f"'{folder_id}' in parents and trashed=false"

    file_list = drive_service.ListFile({'q': query}).GetList()
    return file_list

def download_gdrive_file(drive_service, file_id, file_name):
    """Downloads a file from Google Drive by ID."""
    if not drive_service:
        return None

    file_obj = drive_service.CreateFile({'id': file_id})
    file_obj.FetchMetadata(fields='title,mimeType') # Fetch metadata to get title and mimeType

    # Use BytesIO to store content in memory
    file_content_buffer = BytesIO()
    file_obj.GetContentIO(file_content_buffer)
    file_content_buffer.seek(0) # Rewind to the beginning

    return file_content_buffer.getvalue(), file_obj['title'] # Return bytes content and actual file name

def upload_gdrive_file(drive_service, file_bytes, file_name, mime_type, parent_folder_id=None):
    """Uploads a file to Google Drive."""
    if not drive_service:
        return False

    file_metadata = {'title': file_name, 'mimeType': mime_type}
    if parent_folder_id:
        file_metadata['parents'] = [{'id': parent_folder_id}]

    file_obj = drive_service.CreateFile(file_metadata)
    file_obj.SetContentString(file_bytes.decode('latin-1')) # Use latin-1 for binary data
    file_obj.Upload()
    return True

# --- Modifications to data_import.py and reporting.py will use these functions ---