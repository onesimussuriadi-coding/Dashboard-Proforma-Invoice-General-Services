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
    Menyimpan dan memperbarui (Update/Upsert) data secara presisi 
    langsung ke file Excel lokal server.
    """
    if data_list is None:
        data_list = []

    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    
    try:
        df_new = pd.DataFrame(data_list)
        if df_new.empty:
            return True

        # Jika file lama sudah ada, lakukan pembaruan baris (Update) secara akurat
        if os.path.exists(file_path):
            try:
                df_old = pd.read_excel(file_path, engine='openpyxl')
                if not df_old.empty and not df_new.empty:
                    # Ambil nama kolom pertama sebagai kunci unik (biasanya Nomor Proforma Invoice)
                    key_col = df_old.columns[0]
                    
                    if key_col in df_new.columns:
                        # Standardisasi nilai kunci ke string untuk pencocokan yang tepat
                        df_old[key_col] = df_old[key_col].astype(str).str.strip()
                        df_new[key_col] = df_new[key_col].astype(str).str.strip()
                        
                        # Set index untuk memudahkan proses update baris
                        df_old = df_old.set_index(key_col)
                        df_new = df_new.set_index(key_col)
                        
                        # Timpa data lama dengan data baru yang memiliki key yang sama
                        df_old.update(df_new)
                        
                        # Gabungkan kembali sisa data baru yang belum ada di data lama
                        df_final = pd.concat([df_new[~df_new.index.isin(df_old.index)], df_old])
                        df_new = df_final.reset_index()
            except Exception as e:
                print(f"Catatan saat update baris: {e}")

        # Simpan hasil pembaruan mutlak ke file Excel lokal
        df_new.to_excel(file_path, index=False, engine='openpyxl')
        return True
    except Exception as e:
        st.error(f"❌ Gagal menyimpan data: {e}")
        return False

def render_download_button_excel(nama_tabel):
    """
    Tombol unduh file Excel cadangan untuk arsip ke komputer/Google Drive.
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