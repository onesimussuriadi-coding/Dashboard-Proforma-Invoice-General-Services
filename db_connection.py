import streamlit as st
import pandas as pd
import os
import json
import io

DIR_DATABASE = "database_penyimpanan_aman"
if not os.path.exists(DIR_DATABASE):
    os.makedirs(DIR_DATABASE)
LOCAL_BACKUP_FILE = os.path.join(DIR_DATABASE, "backup_database_invoice.json")

def get_mysql_connection():
    """Dinonaktifkan sementara untuk membebaskan aplikasi dari macet/loading."""
    return None

def muat_data_from_db(nama_tabel="database_proforma_invoice"):
    """Memuat data secara instan dan aman dari file lokal tanpa koneksi luar."""
    local_data = []
    if os.path.exists(LOCAL_BACKUP_FILE):
        try:
            with open(LOCAL_BACKUP_FILE, "r", encoding="utf-8") as f:
                local_data = json.load(f)
        except Exception:
            local_data = []
    return local_data

def simpan_data_to_db(nama_tabel, data_list):
    """Menyimpan data secara permanen dan aman ke penyimpanan lokal aplikasi."""
    if data_list is None:
        st.error("❌ Data kosong, gagal menyimpan.")
        return False

    try:
        with open(LOCAL_BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(data_list, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"❌ Gagal menyimpan data: {e}")
        return False

def render_download_button_excel(nama_tabel="database_proforma_invoice"):
    data = muat_data_from_db(nama_tabel)
    if data:
        df_export = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, header=False)
        excel_bytes = output.getvalue()

        st.markdown("---")
        st.markdown("### 📥 Unduh Data Tabel Terbaru")
        st.download_button(
            label=f"📥 Download {nama_tabel}.xlsx",
            data=excel_bytes,
            file_name=f"{nama_tabel}_terbaru.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"download_btn_local_{nama_tabel}"
        )