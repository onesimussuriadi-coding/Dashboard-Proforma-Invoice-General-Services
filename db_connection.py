import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error

def get_mysql_connection():
    """
    Membuat koneksi nyata dan aman ke server Cloud MySQL 
    menggunakan konfigurasi secrets dari Streamlit Cloud.
    """
    try:
        conn = mysql.connector.connect(
            host=st.secrets["database"]["host"],
            user=st.secrets["database"]["user"],
            password=st.secrets["database"]["password"],
            database=st.secrets["database"]["database"],
            port=st.secrets["database"].get("port", 3306)
        )
        return conn
    except Error as e:
        st.error(f"❌ Gagal terhubung ke Database MySQL: {e}")
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
                return df_sql.to_dict(orient="records")
        except Error as e:
            st.error(f"❌ Gagal membaca tabel {nama_tabel} dari MySQL: {e}")
        finally:
            if conn.is_connected():
                conn.close()
    return []

def simpan_data_to_db(nama_tabel, data_list):
    """
    Menyimpan atau memperbarui data ke tabel MySQL secara permanen dan real-time.
    """
    if data_list is None or len(data_list) == 0:
        st.error("❌ Data kosong, gagal menyimpan ke database.")
        return False

    conn = get_mysql_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        df_new = pd.DataFrame(data_list)
        
        if df_new.empty:
            conn.close()
            return False

        # Ambil kolom pertama sebagai kunci utama (Primary Key pencocokan, misal: Proforma Invoice No.)
        key_col = df_new.columns[0]

        for _, row in df_new.iterrows():
            # Konversi semua nilai row menjadi format yang aman untuk SQL
            cols = [f"`{str(c)}`" for c in df_new.columns]
            vals = [None if pd.isnull(val) or str(val).strip().lower() == "nan" else str(val) for val in row.values]
            
            placeholders = ", ".join(["%s"] * len(vals))
            columns_str = ", ".join(cols)
            
            # Buat klausa ON DUPLICATE KEY UPDATE agar data ter-update otomatis jika sudah ada
            updates = ", ".join([f"`{col}` = VALUES(`{col}`)" for col in df_new.columns[1:]])
            
            query = f"""
                INSERT INTO `{nama_tabel}` ({columns_str}) 
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE {updates}
            """
            
            cursor.execute(query, tuple(vals))

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
    """
    Mengunduh data langsung dalam bentuk file Excel dari data MySQL aktif.
    """
    data = muat_data_from_db(nama_tabel)
    if data:
        df_export = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, sheet_name=nama_tabel)
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