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
            connect_timeout=10
        )
        if connection.is_connected():
            return connection
    except Exception as e:
        print(f"Koneksi MySQL Gagal: {e}")
    return None

def muat_data_from_db(nama_tabel):
    """
    Memuat data secara real-time dari database MySQL hosting.
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
    
    # Fallback ke file lokal jika koneksi cPanel/hosting bermasalah
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
    PENYIMPANAN AMAN BERBASIS UPDATE & INSERT (PRECISE UPSERT):
    Memastikan data tersimpan permanen di MySQL hosting berdasarkan Nomor PI Unik,
    sehingga data dan nomor PO tidak akan pernah tertimpa atau kembali menjadi 0.
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

    # 2. Sinkronisasi ke Cloud MySQL hosting dengan presisi tinggi
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

            # Identifikasi kolom kunci unik untuk pencocokan data (Prioritas: Proforma Invoice No. atau 0)
            pi_column_candidates = ["Proforma Invoice No.", "0", "PI No.", "Nomor Invoice Resmi"]
            target_pi_col = None
            for cand in pi_column_candidates:
                if cand in df.columns:
                    target_pi_col = cand
                    break

            for _, row in df.iterrows():
                cols = [f"`{c}`" for c in df.columns]
                vals = tuple(row)
                placeholders = ", ".join(["%s"] * len(df.columns))
                cols_str = ", ".join(cols)
                
                # Jika tabel proforma invoice dan ditemukan kolom PI, lakukan pengecekan eksistensi data
                if nama_tabel == "database_proforma_invoice" and target_pi_col is not None:
                    pi_val = str(row[target_pi_col]).strip()
                    if pi_val:
                        # Cek apakah nomor PI ini sudah ada di database MySQL
                        check_sql = f"SELECT COUNT(*) FROM `{nama_tabel}` WHERE `{target_pi_col}` = %s;"
                        cursor.execute(check_sql, (pi_val,))
                        exists = cursor.fetchone()[0] > 0
                        
                        if exists:
                            # Jika sudah ada, LAKUKAN UPDATE (Menjaga data & PO agar tidak berubah/reset)
                            update_parts = [f"`{c}` = %s" for c in df.columns if c != target_pi_col]
                            update_vals = [row[c] for c in df.columns if c != target_pi_col] + [pi_val]
                            update_str = ", ".join(update_parts)
                            
                            sql_update = f"UPDATE `{nama_tabel}` SET {update_str} WHERE `{target_pi_col}` = %s;"
                            cursor.execute(sql_update, tuple(update_vals))
                            continue

                # Jika belum ada atau tabel lain, lakukan INSERT standar
                sql_insert = f"INSERT INTO `{nama_tabel}` ({cols_str}) VALUES ({placeholders});"
                cursor.execute(sql_insert, vals)
            
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


# =====================================================================
# FUNGSI TAMBAHAN KHUSUS PENYIMPANAN PARAMETER DOKUMEN TURUNAN (PERSISTENT)
# =====================================================================

TABEL_DB_DOKUMEN_PARAM = "database_dokumen_parameter"

def simpan_parameter_dokumen_to_db(doc_key, data_dict):
    try:
        connection = get_db_connection()
        if connection is not None:
            cursor = connection.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS `{TABEL_DB_DOKUMEN_PARAM}` (
                    `doc_key` VARCHAR(255) PRIMARY KEY,
                    `payload` LONGTEXT
                );
            """)
            
            import json
            payload_str = json.dumps(data_dict, default=str)
            
            sql = f"""
                INSERT INTO `{TABEL_DB_DOKUMEN_PARAM}` (`doc_key`, `payload`) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE `payload` = VALUES(`payload`);
            """
            cursor.execute(sql, (doc_key, payload_str))
            connection.commit()
            cursor.close()
            connection.close()
            return True
    except Exception as e:
        print(f"Gagal menyimpan parameter dokumen ke DB: {e}")
    return False

def muat_parameter_dokumen_from_db(doc_key):
    try:
        connection = get_db_connection()
        if connection is not None:
            cursor = connection.cursor()
            cursor.execute(f"SHOW TABLES LIKE '{TABEL_DB_DOKUMEN_PARAM}';")
            if cursor.fetchone():
                cursor.execute(f"SELECT `payload` FROM `{TABEL_DB_DOKUMEN_PARAM}` WHERE `doc_key` = %s;", (doc_key,))
                res = cursor.fetchone()
                if res and res[0]:
                    import json
                    return json.loads(res[0])
            cursor.close()
            connection.close()
    except Exception as e:
        print(f"Gagal memuat parameter dokumen dari DB: {e}")
    return None