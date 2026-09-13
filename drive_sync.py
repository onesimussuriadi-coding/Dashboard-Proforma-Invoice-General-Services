import os
import io
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    """Fungsi fleksibel: membaca kredensial dari Streamlit Secrets (Cloud) 
    atau dari file credentials.json lokal (Komputer)."""
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        # Memperbaiki format newline private_key jika ada escape character
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    elif os.path.exists("credentials.json"):
        creds = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    else:
        st.error("⚠️ Credentials Google Drive tidak ditemukan di Secrets maupun lokal.")
        return None
    
    return build('drive', 'v3', credentials=creds)

def sync_download_from_drive(filename, local_path):
    try:
        service = get_drive_service()
        if not service:
            return False
        
        # Cari file berdasarkan nama di Google Drive
        query = f"name = '{filename}' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        if not files:
            return False
        
        file_id = files[0]['id']
        request = service.files().get_media(fileId=file_id)
        
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        return True
    except Exception as e:
        print(f"Error download {filename}: {e}")
        return False

def sync_upload_to_drive(local_path, filename):
    try:
        service = get_drive_service()
        if not service or not os.path.exists(local_path):
            return False
        
        # Cek apakah file sudah ada di Drive untuk update / create
        query = f"name = '{filename}' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        media = MediaFileUpload(local_path, resumable=True)
        
        if files:
            file_id = files[0]['id']
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            file_metadata = {'name': filename}
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return True
    except Exception as e:
        print(f"Error upload {filename}: {e}")
        return False