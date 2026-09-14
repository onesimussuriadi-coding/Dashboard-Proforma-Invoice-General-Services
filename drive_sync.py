import os
import io
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# ID Folder Utama Google Drive 2 TB Anda
FOLDER_ID_DRIVE = "1HsHoGeHA0KRZqDkmKOy4lhdJXbp-Gkdt"

@st.cache_resource
def get_drive_service():
    """Inisialisasi koneksi ke Google Drive API menggunakan Streamlit Secrets."""
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"⚠️ Gagal menghubungkan ke Google Drive API: {e}")
        return None

def find_file_id_by_name(filename):
    """Mencari ID File Excel di dalam Folder Google Drive 2 TB."""
    service = get_drive_service()
    if not service:
        return None
    try:
        query = f"'{FOLDER_ID_DRIVE}' in parents and name = '{filename}' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])
        if items:
            return items[0]['id']
    except Exception as e:
        st.warning(f"⚠️ Gagal pencarian file '{filename}' di Drive: {e}")
    return None

def sync_download_from_drive(filename, local_path):
    """Mengunduh versi terbaru file Excel dari Google Drive ke lokal server saat aplikasi dibuka."""
    file_id = find_file_id_by_name(filename)
    if file_id:
        try:
            service = get_drive_service()
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            
            # Buat folder penyimpanan lokal jika belum ada
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(fh.getvalue())
            return True
        except Exception as e:
            st.warning(f"⚠️ Gagal mengunduh '{filename}' dari Google Drive: {e}")
            return False
    return False

def sync_upload_to_drive(local_path, filename):
    """Mengunggah dan MENIMPA (overwrite) file Excel di Google Drive secara REAL-TIME."""
    if not os.path.exists(local_path):
        return False
        
    service = get_drive_service()
    if not service:
        return False

    try:
        file_id = find_file_id_by_name(filename)
        media = MediaFileUpload(
            local_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            resumable=True
        )
        
        if file_id:
            # Overwrite file lama di Google Drive
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            # Jika file belum ada, upload baru ke folder tersebut
            file_metadata = {
                'name': filename,
                'parents': [FOLDER_ID_DRIVE]
            }
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            
        return True
    except Exception as e:
        st.error(f"❌ Gagal sinkronisasi '{filename}' ke Google Drive: {e}")
        return False