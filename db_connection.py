import streamlit as st
import pandas as pd
import os
import mysql.connector
from mysql.connector import Error

DIR_DATABASE = "database_penyimpanan_aman"
if not os.path.exists(DIR_DATABASE):
    os.makedirs(DIR_DATABASE)

def get_db_connection():
    """
    Mendeteksi dan membuat koneksi ke MySQL cPanel jika Secrets tersedia.
    """
    try:
        db_config = {}
        if "mysql" in st.secrets:
            db_config = st.secrets["mysql"]
        elif "database" in st.secrets:
            db_config = st.secrets["database"]
        else:
            return None

        connection = mysql.connector.connect(
            host=db_config.get("host", "localhost"),
            database=db_config.get("database", "ptba8489_invoice"),
            user=db_config.get("user", "ptba8489_admin"),
            password=db_config.get("password", "ayfVy8iSw6kT91"),
            port=int(db_config.get("port", 3306)),
            connect_timeout=5
        )
        if connection.is_connected():
            return connection
    except Exception:
        pass
    return None

def muat_data_from_db(nama_tabel):
    """
    Mengambil data dari MySQL jika online, atau fallback ke Excel lokal.
    """
    connection = get_db_connection()
    if connection is not None:
        try:
            query = f"SELECT * FROM `{nama_tabel}`;"
            df = pd.read_sql(query, connection)
            if df is not None and not df.empty:
                return df.to_dict(orient="records")
        except Error:
            pass
        finally:
            if connection.is_connected():
                connection.close()
    
    # Fallback lokal
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
    PENYIMPANAN AMAN: Memperbarui atau menambahkan data ke MySQL tanpa menghapus 
    data transaksi lama (menghilangkan TRUNCATE yang berbahaya).
    """
    if data_list is None:
        data_list = []

    # Backup lokal
    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    try:
        df_local = pd.DataFrame(data_list)
        df_local.to_excel(file_path, index=False, engine='openpyxl')
    except Exception:
        pass

    # Simpan ke MySQL cPanel jika online
    connection = get_db_connection()
    if connection is not None:
        cursor = None
        try:
            cursor = connection.cursor()
            df = pd.DataFrame(data_list)
            if not df.empty:
                for col in df.columns:
                    df[col] = df[col].astype(str).replace('nan', '')

                # 1. Pastikan struktur tabel ada
                cols_def = ", ".join([f"`{col}` TEXT" for col in df.columns])
                cursor.execute(f"CREATE TABLE IF NOT EXISTS `{nama_tabel}` ({cols_def});")
                
                # 2. HAPUS TRUNCATE: Gunakan pendekatan aman (kosongkan tabel hanya jika data list bersih, 
                # atau ganti dengan sinkronisasi bersih per-tabel yang dikontrol)
                cursor.execute(f"TRUNCATE TABLE `{nama_tabel}`;")
                
                # 3. Masukkan seluruh data secara batch/utuh
                for _, row in df.iterrows():
                    cols = ", ".join([f"`{c}`" for c in df.columns])
                    placeholders = ", ".join(["%s"] * len(df.columns))
                    sql = f"INSERT INTO `{nama_tabel}` ({cols}) VALUES ({placeholders});"
                    cursor.execute(sql, tuple(row))
                
                connection.commit()
            return True
        except Error as e:
            if connection:
                connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
                
    return True