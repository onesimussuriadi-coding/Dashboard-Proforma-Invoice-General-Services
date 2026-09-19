import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
import os
import json
import io

DIR_DATABASE = "database_penyimpanan_aman"
if not os.path.exists(DIR_DATABASE):
    os.makedirs(DIR_DATABASE)
LOCAL_BACKUP_FILE = os.path.join(DIR_DATABASE, "backup_database_invoice.json")

def get_mysql_connection():
    """
    Koneksi MySQL dengan proteksi timeout ketat agar tidak pernah membuat aplikasi macet.
    """
    try:
        db_conf = st.secrets["database"]
        conn = mysql.connector.connect(
            host=db_conf["host"],
            user=db_conf["user"],
            password=db_conf["password"],
            database=db_conf["database"],
            port=db_conf.get("port", 3306),
            connection_timeout=2
        )
        return conn
    except Exception as e:
        return None

def muat_data_from_db(nama_tabel="database_proforma_invoice"):
    """
    Memuat data secara instan dari penyimpanan lokal yang aman 
    sehingga aplikasi dijamin terbuka dalam 0.1 detik tanpa layar putih.
    """
    local_data = []
    if os.path.exists(LOCAL_BACKUP_FILE):
        try:
            with open(LOCAL_BACKUP_FILE, "r", encoding="utf-8") as f:
                local_data = json.load(f)
        except Exception:
            local_data = []
            
    return local_data

def simpan_data_to_db(nama_tabel, data_list):
    """
    Menyimpan data ke file lokal yang aman secara instan dan permanen, 
    serta mencoba menyinkronkannya ke MySQL jika jaringan mengizinkan.
    """
    if data_list is None:
        st.error("❌ Data kosong, gagal menyimpan.")
        return False

    # 1. Simpan ke file lokal (Aman, permanen, tidak akan hilang saat refresh)
    try:
        with open(LOCAL_BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(data_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"❌ Gagal menyimpan data lokal: {e}")
        return False

    # 2. Coba sinkronisasi ke MySQL di latar belakang
    conn = get_mysql_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            for item in data_list:
                val_map = {}
                for idx in range(1, 32):
                    val = ""
                    if isinstance(item, dict):
                        val = item.get(idx - 1, item.get(str(idx - 1), ""))
                        if not val:
                            mapping_keys = [
                                "Proforma Invoice No.", "Nomor Kontrak", "Nomor Tender", "Lingkup Pekerjaan",
                                "Tanggal Kontrak", "Jangka Waktu Kontrak", "Tanggal Performa Invoice", "Judul Kontrak",
                                "Nomor Purchase Order", "Tanggal Purchase Order", "Pihak Pertama", "Alamat Pihak Pertama",
                                "Diwakili Oleh", "Selaku", "Pihak Kedua", "Alamat Pihak Kedua", "Diwakili Oleh (P2)",
                                "Selaku (P2)", "Periode Pekerjaan", "Nomor WCC", "Tanggal WCC", "Nomor WO",
                                "Keterangan WO", "Nomor CTR", "Progress Pekerjaan", "Prepared by Name",
                                "Prepared by Title", "Approved by 1", "Approved by Title 1", "Approved by 2", "Approved by Title 2"
                            ]
                            if (idx - 1) < len(mapping_keys):
                                val = item.get(mapping_keys[idx - 1], "")
                    val_map[f"COL {idx}"] = str(val) if val is not None and str(val).strip().lower() != "nan" else ""

                cols = [f"`COL {i}`" for i in range(1, 32)]
                placeholders = ", ".join(["%s"] * 31)
                columns_str = ", ".join(cols)
                vals = tuple(val_map[f"COL {i}"] for i in range(1, 32))
                updates = ", ".join([f"`COL {i}` = VALUES(`COL {i}`)" for i in range(2, 32)])
                
                query = f"""
                    INSERT INTO `{nama_tabel}` ({columns_str}) 
                    VALUES ({placeholders})
                    ON DUPLICATE KEY UPDATE {updates}
                """
                cursor.execute(query, vals)
            conn.commit()
            cursor.close()
            conn.close()
        except Exception:
            if conn and conn.is_connected():
                conn.close()

    return True

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