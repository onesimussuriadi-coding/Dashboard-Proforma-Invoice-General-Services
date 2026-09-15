import streamlit as st
import pandas as pd
import os
import mysql.connector
from mysql.connector import Error

# Tentukan direktori penyimpanan lokal sebagai fallback
DIR_DATABASE = "database_penyimpanan_aman"
if not os.path.exists(DIR_DATABASE):
    os.makedirs(DIR_DATABASE)

def is_in_cloud():
    """Mendeteksi apakah aplikasi berjalan di Streamlit Cloud atau di lokal."""
    # Streamlit Cloud biasanya tidak memiliki direktori file lokal yang persisten atau mendeteksi environment tertentu
    return "mysql" in st.secrets and st.secrets["mysql"].get("host") != "localhost"

def get_db_connection():
    """
    Membuat koneksi ke database MySQL jika di cloud. 
    Jika di lokal, kembalikan None agar menggunakan penyimpanan lokal.
    """
    if not is_in_cloud():
        return None  # Berjalan di lokal, gunakan file Excel

    try:
        db_config = st.secrets.get("mysql", st.secrets.get("database", {}))
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
    except Error:
        pass
    return None

def muat_data_from_db(nama_tabel):
    """
    Mengambil data dari MySQL jika online, atau dari file Excel lokal jika offline.
    """
    connection = get_db_connection()
    
    # Jika koneksi database tersedia (di Cloud)
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
    
    # Fallback ke penyimpanan Excel lokal jika di komputer lokal
    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    if os.path.exists(file_path):
        try:
            df_local = pd.read_excel(file_path, engine='openpyxl')
            if df_local is not None and not df_local.empty:
                return df_local.to_dict(orient="records")
        except:
            pass
    return []

def simpan_data_to_db(nama_tabel, data_list):
    """
    Menyimpan data ke MySQL jika online, dan selalu menyalinnya ke Excel lokal sebagai cadangan.
    """
    if data_list is None:
        data_list = []

    # Selalu simpan ke file Excel lokal agar aman di komputer lokal
    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    try:
        df_local = pd.DataFrame(data_list)
        df_local.to_excel(file_path, index=False, engine='openpyxl')
    except Exception as e:
        print(f"Gagal simpan lokal: {e}")

    # Coba simpan ke MySQL jika online
    connection = get_db_connection()
    if connection is not None:
        try:
            cursor = connection.cursor()
            df = pd.DataFrame(data_list)
            if not df.empty:
                for col in df.columns:
                    df[col] = df[col].astype(str).replace('nan', '')

                cols_def = ", ".join([f"`{col}` TEXT" for col in df.columns])
                cursor.execute(f"CREATE TABLE IF NOT EXISTS `{nama_tabel}` ({cols_def});")
                cursor.execute(f"TRUNCATE TABLE `{nama_tabel}`;")
                
                for _, row in df.iterrows():
                    cols = ", ".join([f"`{c}`" for c in df.columns])
                    placeholders = ", ".join(["%s"] * len(df.columns))
                    sql = f"INSERT INTO `{nama_tabel}` ({cols}) VALUES ({placeholders});"
                    cursor.execute(sql, tuple(row))
                
                connection.commit()
            return True
        except Error:
            connection.rollback()
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                
    return True # Tetap mengembalikan True karena data sudah tersimpan di lokal