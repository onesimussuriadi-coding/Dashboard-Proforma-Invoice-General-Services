import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
import os
import io

DIR_DATABASE = "database_penyimpanan_aman"
if not os.path.exists(DIR_DATABASE):
    os.makedirs(DIR_DATABASE)

def get_mysql_connection():
    """
    Membuat koneksi nyata dan aman ke server Cloud MySQL 
    menggunakan kredensial langsung yang stabil.
    """
    try:
        # Kredensial langsung untuk memastikan koneksi instan tanpa kendala Secrets
        conn = mysql.connector.connect(
            host="203.175.9.146",
            user="ptba8489_admin",
            password="ayfVy8iSw6kT91",
            database="ptba8489_invoice",
            port=3306
        )
        return conn
    except Error as e:
        return None

def muat_data_from_db(nama_tabel):
    """
    Memuat seluruh data secara real-time langsung dari tabel MySQL pusat.
    """
    conn = get_mysql_connection()
    if conn is not None:
        try:
            query = f"SELECT * FROM `{nama_tabel}`"
            df_sql = pd.read_sql(query, conn)
            conn.close()
            if df_sql is not None and not df_sql.empty:
                records = []
                for _, row in df_sql.iterrows():
                    rec_dict = {}
                    for i, col_name in enumerate(df_sql.columns):
                        rec_dict[i] = str(row[col_name]) if pd.notnull(row[col_name]) and str(row[col_name]).lower() != "nan" else ""
                    records.append(rec_dict)
                return records
        except Error as e:
            pass
    return []

def simpan_data_to_db(nama_tabel, data_list):
    """
    Menyimpan atau memperbarui data ke tabel MySQL menggunakan pemetaan `COL 1`, `COL 2`, dst.
    """
    if data_list is None or len(data_list) == 0:
        st.error("❌ Data kosong, gagal menyimpan ke database.")
        return False

    conn = get_mysql_connection()
    if conn is None:
        st.error("❌ Gagal terhubung ke server database MySQL.")
        return False

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
        return True

    except Error as e:
        st.error(f"❌ Gagal menyimpan data ke MySQL: {e}")
        if conn.is_connected():
            conn.close()
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
        st.markdown("### 📥 Unduh Data Tabel MySQL Terbaru")
        st.download_button(
            label=f"📥 Download {nama_tabel}.xlsx",
            data=excel_bytes,
            file_name=f"{nama_tabel}_mysql_terbaru.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"download_btn_mysql_{nama_tabel}"
        )