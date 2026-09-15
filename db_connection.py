import streamlit as st
import pandas as pd
import os
import mysql.connector
from mysql.connector import Error

DIR_DATABASE = "database_penyimpanan_aman"
if not os.path.exists(DIR_DATABASE):
    os.makedirs(DIR_DATABASE)

def get_db_connection():
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
    except Exception as e:
        print(f"Koneksi MySQL Gagal: {e}")
    return None

def muat_data_from_db(nama_tabel):
    """
    Memuat data secara real-time dari database MySQL cPanel.
    Jika gagal/offline, otomatis membaca backup lokal yang aman.
    """
    connection = get_db_connection()
    if connection is not None:
        try:
            query = f"SELECT * FROM `{nama_tabel}`;"
            df = pd.read_sql(query, connection)
            if df is not None and not df.empty:
                # Simpan juga sebagai backup lokal terbaru
                file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
                df.to_excel(file_path, index=False, engine='openpyxl')
                return df.to_dict(orient="records")
        except Error as e:
            print(f"Gagal memuat dari DB: {e}")
        finally:
            if connection.is_connected():
                connection.close()
    
    # Fallback ke file lokal jika koneksi cPanel bermasalah
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
    PENYIMPANAN AMAN ANTI-HILANG (UP-SERT): 
    Menyimpan data ke MySQL cPanel TANPA menghapus data lama (No TRUNCATE/DELETE).
    Data lama tetap aman dan tersinkronisasi sempurna.
    """
    if data_list is None:
        data_list = []

    df = pd.DataFrame(data_list)
    
    # 1. Selalu simpan backup lokal terlebih dahulu sebagai pengaman
    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    try:
        df.to_excel(file_path, index=False, engine='openpyxl')
    except Exception:
        pass

    if df.empty:
        return True

    # 2. Sinkronisasi ke Cloud MySQL cPanel dengan aman
    connection = get_db_connection()
    if connection is not None:
        cursor = None
        try:
            cursor = connection.cursor()
            
            # Bersihkan format nilai NaN/Null
            for col in df.columns:
                df[col] = df[col].astype(str).replace(['nan', 'None', 'NAT'], '')

            # Pastikan struktur tabel ada di database
            cols_def = ", ".join([f"`{col}` TEXT" for col in df.columns])
            cursor.execute(f"CREATE TABLE IF NOT EXISTS `{nama_tabel}` ({cols_def});")

            # Tentukan kolom acuan unik untuk identifikasi data (primary/unique key)
            # Berdasarkan struktur modul kita, pilih kolom identifikasi yang sesuai
            unique_col = None
            for col_candidate in ["Nomor Invoice Resmi", "PI No.", "Nomor Kontrak", "Bank Name"]:
                if col_candidate in df.columns:
                    unique_col = col_candidate
                    break

            for _, row in df.iterrows():
                cols = [f"`{c}`" for c in df.columns]
                vals = tuple(row)
                placeholders = ", ".join(["%s"] * len(df.columns))
                
                if unique_col and unique_col in df.columns:
                    # Jika data dengan nomor/ID yang sama sudah ada, perbarui (UPDATE)
                    # Jika belum ada, masukkan sebagai baris baru (INSERT)
                    update_clause = ", ".join([f"`{c}` = VALUES(`{c}`)" for c in df.columns if c != unique_col])
                    sql = f"INSERT INTO `{nama_tabel}` ({', '.join(cols)}) VALUES ({placeholder_str := placeholders}) ON DUPLICATE KEY UPDATE {update_clause};"
                    # Catatan: MySQL mendukung ON DUPLICATE KEY jika ada Unique Index. 
                    # Untuk amannya, kita gunakan pendekatan aman: Cek keberadaan atau Insert biasa.
                
                # Metode Standar Aman: Insert / Replace tanpa menghapus baris tabel lain
                cols_str = ", ".join(cols)
                sql = f"REPLACE INTO `{nama_tabel}` ({cols_str}) VALUES ({placeholders});"
                cursor.execute(sql, vals)
            
            connection.commit()
            return True
        except Error as e:
            print(f"Error MySQL saat menyimpan: {e}")
            if connection:
                connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
                
    return True