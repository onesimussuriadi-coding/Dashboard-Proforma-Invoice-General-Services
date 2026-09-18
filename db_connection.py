import streamlit as st
import pandas as pd
import os
import json

DIR_DATABASE = "database_penyimpanan_aman"
if not os.path.exists(DIR_DATABASE):
    os.makedirs(DIR_DATABASE)

def muat_data_from_db(nama_tabel):
    """
    Memuat data secara instan dari file Excel lokal server Streamlit.
    """
    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    if os.path.exists(file_path):
        try:
            df_local = pd.read_excel(file_path, engine='openpyxl')
            if df_local is not None and not df_local.empty:
                return df_local.to_dict(orient="records")
        except Exception as e:
            st.error(f"Error membaca file lokal: {e}")
    return []

def simpan_data_to_db(nama_tabel, data_list):
    """
    Menyimpan dan memperbarui data secara mutlak ke file Excel lokal server Streamlit,
    disertai validasi fisik untuk memastikan data benar-benar tertulis.
    """
    if data_list is None or len(data_list) == 0:
        st.error("❌ Data kosong, tidak dapat disimpan.")
        return False

    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    
    try:
        df_new = pd.DataFrame(data_list)

        # Jika file lama sudah ada, gabungkan atau perbarui baris secara akurat
        if os.path.exists(file_path):
            try:
                df_old = pd.read_excel(file_path, engine='openpyxl')
                if not df_old.empty:
                    key_col = df_old.columns[0] # Kolom pertama (Nomor Proforma Invoice)
                    if key_col in df_new.columns:
                        df_old[key_col] = df_old[key_col].astype(str).str.strip()
                        df_new[key_col] = df_new[key_col].astype(str).str.strip()
                        
                        df_old = df_old.set_index(key_col)
                        df_new = df_new.set_index(key_col)
                        
                        # Timpa/update data lama dengan data baru
                        df_old.update(df_new)
                        df_final = pd.concat([df_new[~df_new.index.isin(df_old.index)], df_old])
                        df_new = df_final.reset_index()
            except Exception as e:
                st.warning(adi := f"Catatan penyesuaian baris: {e}")

        # Tulis fisik ke file Excel server
        df_new.to_excel(file_path, index=False, engine='openpyxl')
        
        # Validasi fisik: Pastikan file benar-benar ada dan ukurannya valid
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return True
        else:
            st.error("❌ Gagal: File fisik gagal dibuat di server.")
            return False
            
    except Exception as e:
        st.error(f"❌ Gagal menyimpan data: {e}")
        return False

def render_download_button_excel(nama_tabel="database_proforma_invoice"):
    """
    Menampilkan tombol unduh file Excel secara jelas di antarmuka web,
    sehingga Bapak bisa mendownload file paling update dari server cloud kapan saja.
    """
    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    
    st.markdown("### 📥 Unduh File Excel Server Terbaru")
    st.info("Gunakan tombol di bawah ini untuk mendownload file Excel yang berisi data paling update langsung dari server cloud Streamlit ke komputer/Google Drive Anda.")
    
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            excel_bytes = f.read()
        st.download_button(
            label=f"📥 Download {nama_tabel}.xlsx Sekarang",
            data=excel_bytes,
            file_name=f"{nama_tabel}_terbaru.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"download_btn_{nama_tabel}"
        )
    else:
        st.warning(f"⚠️ File data untuk tabel '{nama_tabel}' belum ditemukan di server.")

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