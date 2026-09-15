import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error

def get_db_connection():
    """
    Membuat koneksi ke database MySQL menggunakan konfigurasi dari st.secrets 
    atau fallback ke parameter default cPanel.
    """
    try:
        # Mengambil konfigurasi dari Streamlit Secrets (aman untuk Streamlit Cloud)
        db_config = st.secrets.get("mysql", {
            "host": "localhost",
            "database": "ptba8489_invoice", # Sesuaikan dengan nama database cPanel Bapak
            "user": "ptba8489_user",       # Sesuaikan dengan username database cPanel
            "password": "PASSWORD_ANDA",   # Masukkan password database cPanel
            "port": 3306
        })

        connection = mysql.connector.connect(
            host=db_config.get("host", "localhost"),
            database=db_config.get("database"),
            user=db_config.get("user"),
            password=db_config.get("password"),
            port=int(db_config.get("port", 3306))
        )
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"❌ Kesalahan koneksi ke Database MySQL: {e}")
    return None

def muat_data_from_db(nama_tabel):
    """
    Mengambil seluruh data dari tabel MySQL tertentu dan mengembalikannya sebagai list of dictionaries (records).
    Jika tabel belum ada atau kosong, mengembalikan list kosong.
    """
    connection = get_db_connection()
    if connection is None:
        return []
    
    try:
        query = f"SELECT * FROM `{nama_tabel}`;"
        df = pd.read_sql(query, connection)
        if df is not None and not df.empty:
            # Konversi kolom tanggal atau format khusus jika diperlukan
            return df.to_dict(orient="records")
    except Error as e:
        # Jika tabel belum ada, abaikan atau kembalikan list kosong
        pass
    finally:
        if connection.is_connected():
            connection.close()
    return []

def simpan_data_to_db(nama_tabel, data_list):
    """
    Menyimpan data (list of dictionaries) ke tabel MySQL.
    Metode ini melakukan overwrite (menghapus isi lama dan memasukkan data baru) 
    atau menyelaraskan dengan struktur DataFrame modul Bapak.
    """
    if not data_list:
        # Jika data kosong, buat tabel kosong atau bersihkan
        data_list = []

    connection = get_db_connection()
    if connection is None:
        st.error("❌ Gagal menyimpan data: Koneksi database terputus.")
        return False

    try:
        cursor = connection.cursor()
        df = pd.DataFrame(data_list)
        
        # Buat tabel secara otomatis jika belum ada berdasarkan struktur DataFrame
        if not df.empty:
            # Konversi tipe data object/dict ke string agar aman disimpan ke SQL
            for col in df.columns:
                df[col] = df[col].astype(str).replace('nan', '')

            # Gunakan pandas to_sql melalui sqlalchemy engine atau manual insert
            # Untuk kesederhanaan dan kestabilan dengan mysql.connector:
            # Kita buat tabel sederhana atau drop & create ulang untuk sinkronisasi penuh
            cols_def = ", ".join([f"`{col}` TEXT" for col in df.columns])
            cursor.execute(f"CREATE TABLE IF NOT EXISTS `{nama_tabel}` ({cols_def});")
            cursor.execute(f"TRUNCATE TABLE `{nama_tabel}`;") # Bersihkan data lama
            
            for _, row in df.iterrows():
                cols = ", ".join([f"`{c}`" for c in df.columns])
                placeholders = ", ".join(["%s"] * len(df.columns))
                sql = f"INSERT INTO `{nama_tabel}` ({cols}) VALUES ({placeholders});"
                cursor.execute(sql, tuple(row))
            
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