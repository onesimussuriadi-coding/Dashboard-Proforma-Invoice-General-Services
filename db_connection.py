import streamlit as st
import pandas as pd
import os
import json

DIR_DATABASE = "database_penyimpanan_aman"
if not os.path.exists(DIR_DATABASE):
    os.makedirs(DIR_DATABASE)

def muat_data_from_db(nama_tabel):
    """
    Memuat data secara instan, aman, dan real-time dari file Excel lokal server.
    """
    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    if os.path.exists(file_path):
        try:
            df_local = pd.read_excel(file_path, engine='openpyxl')
            if df_local is not None and not df_local.empty:
                return df_local.to_dict(orient="records")
        except Exception:
            pass
    return []

def simpan_data_to_db(nama_tabel, data_list):
    """
    Menyimpan dan memperbarui data secara aman ke file Excel lokal 
    tanpa kendala tipe data.
    """
    if data_list is None:
        data_list = []

    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    
    try:
        df_new = pd.DataFrame(data_list)
        if df_new.empty:
            return True

        # Jika file lama sudah ada, gabungkan atau perbarui dengan aman
        if os.path.exists(file_path):
            try:
                df_old = pd.read_excel(file_path, engine='openpyxl')
                if not df_old.empty:
                    # Identifikasi kolom kunci (biasanya kolom pertama / nomor invoice)
                    key_col = df_old.columns[0]
                    if key_col in df_new.columns:
                        # Ubah ke string untuk pencocokan yang akurat
                        df_old[key_col] = df_old[key_col].astype(str).str.strip()
                        df_new[key_col] = df_new[key_col].astype(str).str.strip()
                        
                        # Hapus duplikat dari data baru yang memiliki key sama dengan data lama
                        keys_to_update = df_new[key_col].tolist()
                        df_old = df_old[~df_old[key_col].isin(keys_to_update)]
                        
                        # Gabungkan data lama yang tersisa dengan data baru yang di-update
                        df_new = pd.concat([df_old, df_new], ignore_index=True)
            except Exception:
                pass

        # Simpan hasil akhir ke file Excel lokal
        df_new.to_excel(file_path, index=False, engine='openpyxl')
        return True
    except Exception as e:
        st.error(f"❌ Gagal menyimpan data: {e}")
        return False

def render_download_button_excel(nama_tabel):
    """
    Tombol unduh file Excel cadangan untuk arsip ke Google Drive/komputer.
    """
    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            excel_bytes = f.read()
        st.download_button(
            label=f"📥 Download File Excel Terbaru ({nama_tabel})",
            data=excel_bytes,
            file_name=f"{nama_tabel}_terbaru.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"download_{nama_tabel}"
        )

# =====================================================================
# FUNGSI PARAMETER DOKUMEN BAMP
# =====================================================================

TABEL_DB_DOKUMEN_PARAM = "database_dokumen_parameter"

def simpan_parameter_dokumen_to_db(doc_key, data_dict):
    file_path = os.path.join(DIR_DATABASE, f"{TABEL_DB_DOKUMEN_PARAM}.json")
    try:
        data_all = {}
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data_all = json.load(f)
        data_all[doc_key] = data_dict
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_all, f, default=str, ensure_ascii=False, indent=4)
        return True
    except Exception:
        pass
    return False

def muat_parameter_dokumen_from_db(doc_key):
    file_path = os.path.join(DIR_DATABASE, f"{TABEL_DB_DOKUMEN_PARAM}.json")
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data_all = json.load(f)
                return data_all.get(doc_key, None)
    except Exception:
        pass
    return None