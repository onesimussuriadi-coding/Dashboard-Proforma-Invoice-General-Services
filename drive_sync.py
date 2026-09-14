import os
import io
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

FOLDER_ID_DRIVE = "1HsHoGeHA0KRZqDkmKOy4lhdJXbp-Gkdt"

# 1. Simpan koneksi Service Account di memori server (hanya 1x inisialisasi)
@st.cache_resource
def get_drive_service():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"⚠️ Gagal koneksi Google Drive API: {e}")
        return None

# 2. Cache daftar File ID agar tidak selalu querying metadata Drive API
@st.cache_data(ttl=3600)  # Simpan cache ID file selama 1 jam
def get_file_id_cached(filename):
    service = get_drive_service()
    if not service:
        return None
    try:
        query = f"'{FOLDER_ID_DRIVE}' in parents and name = '{filename}' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])
        if items:
            return items[0]['id']
    except Exception:
        pass
    return None

# 3. Fungsi membaca Excel dengan caching memori cerdas
@st.cache_data(ttl=600) # Cache data Excel selama 10 menit
def load_excel_fast(filename_excel):
    local_path = filename_excel
    service = get_drive_service()
    
    # Jika file sudah ada di lokal server temporary, baca langsung (SANGAT CEPTA)
    if os.path.exists(local_path):
        return pd.read_excel(local_path)
    
    # Jika belum ada di lokal, baru unduh 1x dari Drive
    file_id = get_file_id_cached(filename_excel)
    if file_id and service:
        try:
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            
            with open(local_path, 'wb') as f:
                f.write(fh.getvalue())
            return pd.read_excel(local_path)
        except Exception as e:
            st.warning(f"⚠️ Memuat data lokal kosong (Drive sync pending): {e}")
    
    return pd.DataFrame()

# 4. Simpan & Upload Cepat (Memperbarui Memori Lokal + Background Push ke Drive)
def save_and_push_fast(df, filename_excel):
    try:
        # A. Simpan ke lokal server dulu (sangat cepat)
        df.to_excel(filename_excel, index=False)
        
        # B. Bersihkan cache agar tampilan Streamlit langsung update data baru
        st.cache_data.clear()
        
        # C. Upload ke Google Drive
        service = get_drive_service()
        file_id = get_file_id_cached(filename_excel)
        media = MediaFileUpload(
            filename_excel,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            resumable=True
        )
        
        if file_id:
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            file_metadata = {'name': filename_excel, 'parents': [FOLDER_ID_DRIVE]}
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            # Clear cache ID jika ada file baru dibuat
            get_file_id_cached.clear()
            
        return True
    except Exception as e:
        st.error(f"❌ Gagal update ke Google Drive: {e}")
        return False