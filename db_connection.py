import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error

def get_db_connection():
    """
    Membuat koneksi ke database MySQL dengan mengambil konfigurasi dari st.secrets.
    Jika berjalan di lokal dan secrets belum ada, menggunakan konfigurasi default cPanel.
    """
    try:
        # Coba ambil dari st.secrets (baik format [mysql] maupun [database])
        db_config = {}
        if "mysql" in st.secrets:
            db_config = st.secrets["mysql"]
        elif "database" in st.secrets:
            db_config = st.secrets["database"]
        else:
            # Fallback otomatis untuk testing lokal jika st.secrets kosong
            db_config = {
                "host": "localhost",
                "database": "ptba8489_invoice",
                "user": "ptba8489_admin",
                "password": "ayfVy8iSw6kT91",
                "port": 3306
            }

        connection = mysql.connector.connect(
            host=db_config.get("host", "localhost"),
            database=db_config.get("database", "ptba8489_invoice"),
            user=db_config.get("user", "ptba8489_admin"),
            password=db_config.get("password", "ayfVy8iSw6kT91"),
            port=int(db_config.get("port", 3306))
        )
        if connection.is_connected():
            return connection
    except Exception as e:
        # Jika st.secrets sama sekali belum ada (di lokal), gunakan langsung kredensial default
        try:
            connection = mysql.connector.connect(
                host="localhost",
                database="ptba8489_invoice",
                user="ptba8489_admin",
                password="ayfVy8iSw6kT91",
                port=3306
            )
            if connection.is_connected():
                return connection
        except Error as err:
            st.error(f"❌ Kesalahan koneksi ke Database MySQL: {err}")
    return None

def muat_data_from_db(nama_tabel):
    """
    Mengambil seluruh data dari tabel MySQL tertentu dan mengembalikannya sebagai list of dictionaries.
    """
    connection = get_db_connection()
    if connection is None:
        return []
    
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
    return []

def simpan_data_to_db(nama_tabel, data_list):
    """
    Menyimpan data (list of dictionaries) ke tabel MySQL.
    """
    if data_list is None:
        data_list = []

    connection = get_db_connection()
    if connection is None:
        st.error("❌ Gagal menyimpan data: Koneksi database terputus.")
        return False

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
        else:
            # Jika dataframe kosong, pastikan tabel tetap ada atau dibersihkan
            cursor.execute(f"CREATE TABLE IF NOT EXISTS `{nama_tabel}` (`id` INT AUTO_INCREMENT PRIMARY KEY);")
            cursor.execute(f"TRUNCATE TABLE `{nama_tabel}`;")
            connection.commit()
            return True
    except Error as e:
        st.error(f"❌ Gagal menyimpan ke database MySQL: {e}")
        connection.rollback()
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    return False