import streamlit as st
import pandas as pd
import os

# Tentukan direktori penyimpanan lokal
DIR_DATABASE = "database_penyimpanan_aman"
if not os.path.exists(DIR_DATABASE):
    os.makedirs(DIR_DATABASE)

def muat_data_from_db(nama_tabel):
    """
    Mengambil data dari penyimpanan Excel lokal saat uji coba di komputer lokal.
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
    Menyimpan data ke file Excel lokal dengan aman tanpa memicu error koneksi MySQL di komputer lokal.
    """
    if data_list is None:
        data_list = []

    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    try:
        df_local = pd.DataFrame(data_list)
        df_local.to_excel(file_path, index=False, engine='openpyxl')
        return True
    except Exception as e:
        st.error(f"⚠️ Gagal menyimpan data lokal: {e}")
        return False