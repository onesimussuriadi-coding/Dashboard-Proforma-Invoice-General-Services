import os
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE = 'credentials.json'

# FOLDER ID GOOGLE DRIVE 2 TB BAPAK
GOOGLE_DRIVE_FOLDER_ID = '1HsHoGeHA0KRZqDkmKOy4IhdJXbp-Gkdt'

def get_drive_service():
    if not os.path.exists(CREDENTIALS_FILE):
        return None
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def sync_download_from_drive(filename, local_path):
    """Mengunduh file database terbaru dari Google Drive ke lokal"""
    try:
        service = get_drive_service()
        if not service:
            return False
            
        query = f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and name='{filename}' and trashed=false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        if files:
            file_id = files[0]['id']
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(fh.getvalue())
            return True
    except Exception as e:
        print(f"Gagal mengunduh dari Drive: {e}")
    return False

def sync_upload_to_drive(local_path, filename):
    """Mengunggah dan memperbarui file database lokal ke Google Drive 2 TB"""
    try:
        service = get_drive_service()
        if not service or not os.path.exists(local_path):
            return False

        query = f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and name='{filename}' and trashed=false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        media = MediaFileUpload(local_path, resumable=True)

        if files:
            file_id = files[0]['id']
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            file_metadata = {
                'name': filename,
                'parents': [GOOGLE_DRIVE_FOLDER_ID]
            }
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return True
    except Exception as e:
        print(f"Gagal mengunggah ke Drive: {e}")
    return False