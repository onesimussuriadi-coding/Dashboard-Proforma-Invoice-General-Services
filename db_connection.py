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
    Memuat data secara real-time dari database MySQL hosting dengan konversi key integer yang presisi.
    """
    connection = get_db_connection()
    if connection is not None:
        try:
            query = f"SELECT * FROM `{nama_tabel}`;"
            df = pd.read_sql(query, connection)
            if df is not None and not df.empty:
                # Normalisasi nama kolom dari string angka kembali menjadi integer (0-30) agar terbaca sempurna oleh form
                rename_map = {}
                for col in df.columns:
                    col_str = str(col).strip()
                    if col_str.isdigit():
                        rename_map[col] = int(col_str)
                if rename_map:
                    df = df.rename(columns=rename_map)

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
    PENYIMPANAN AMAN DENGAN PEMETAAN INDEKS KOLOM YANG PRESISI KE MYSQL
    """
    if data_list is None:
        data_list = []

    df = pd.DataFrame(data_list)
    
    # 1. Simpan backup lokal sebagai pengaman
    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    try:
        df.to_excel(file_path, index=False, engine='openpyxl')
    except Exception:
        pass

    if df.empty:
        return True

    # 2. Sinkronisasi mutlak ke Cloud MySQL cPanel
    connection = get_db_connection()
    if connection is not None:
        cursor = None
        try:
            cursor = connection.cursor()
            
            # Bersihkan format nilai NaN/Null
            for col in df.columns:
                df[col] = df[col].astype(str).replace(['nan', 'None', 'NAT'], '')

            # Pastikan struktur tabel di MySQL menggunakan nama kolom string dari key dictionary (misal: '0', '1', '8', dll)
            cols_def = ", ".join([f"`{str(col)}` TEXT" for col in df.columns])
            cursor.execute(f"CREATE TABLE IF NOT EXISTS `{nama_tabel}` ({cols_def}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;")

            # Tentukan kolom acuan unik (Kolom 0 / Proforma Invoice No.)
            pi_col = 0 if 0 in df.columns else ("Proforma Invoice No." if "Proforma Invoice No." in df.columns else None)

            for _, row in df.iterrows():
                cols = [f"`{str(c)}`" for c in df.columns]
                vals = tuple(row)
                placeholders = ", ".join(["%s"] * len(df.columns))
                cols_str = ", ".join(cols)
                
                if nama_tabel == "database_proforma_invoice" and pi_col is not None:
                    pi_val = str(row[pi_col]).strip()
                    if pi_val:
                        # Cek apakah nomor PI sudah ada di database MySQL
                        check_sql = f"SELECT COUNT(*) FROM `{nama_tabel}` WHERE `{str(pi_col)}` = %s;"
                        cursor.execute(check_sql, (pi_val,))
                        exists = cursor.fetchone()[0] > 0
                        
                        if exists:
                            # LAKUKAN UPDATE PRESISI BERDASARKAN KOLOM PI
                            update_parts = [f"`{str(c)}` = %s" for c in df.columns if c != pi_col]
                            update_vals = [row[c] for c in df.columns if c != pi_col] + [pi_val]
                            update_str = ", ".join(update_parts)
                            
                            sql_update = f"UPDATE `{nama_tabel}` SET {update_str} WHERE `{str(pi_col)}` = %s;"
                            cursor.execute(sql_update, tuple(update_vals))
                            continue

                # INSERT standar jika belum ada
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
# FUNGSI TAMBAHAN PARAMETER DOKUMEN BAMP
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
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