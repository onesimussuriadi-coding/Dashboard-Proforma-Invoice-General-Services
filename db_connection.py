import streamlit as st
import pandas as pd
import os
import json
import mysql.connector
from mysql.connector import Error

DIR_DATABASE = "database_penyimpanan_aman"
if not os.path.exists(DIR_DATABASE):
    os.makedirs(DIR_DATABASE)

def get_db_connection():
    """
    Koneksi MySQL dengan penanganan error senyap (silent fallback),
    sehingga tidak memunculkan kotak merah timed out di layar Streamlit Cloud.
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
        # Error koneksi ditangkap diam-diam tanpa memunculkan st.error di layar
        pass
    return None

def muat_data_from_db(nama_tabel):
    """
    Memuat data dari database MySQL hosting, langsung beralih ke file lokal
    jika koneksi cloud mengalami timed out secara senyap.
    """
    connection = get_db_connection()
    if connection is not None:
        try:
            query = f"SELECT * FROM `{nama_tabel}`;"
            df = pd.read_sql(query, connection)
            if df is not None and not df.empty:
                rename_map = {}
                for col in df.columns:
                    col_str = str(col).strip()
                    if col_str.isdigit():
                        rename_map[col] = int(col_str)
                if rename_map:
                    df = df.rename(columns=rename_map)

                # Simpan backup lokal
                file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
                df.to_excel(file_path, index=False, engine='openpyxl')
                return df.to_dict(orient="records")
        except Error:
            pass
        finally:
            try:
                if connection.is_connected():
                    connection.close()
            except Exception:
                pass
    
    # Fallback mulus ke file lokal tanpa pesan error mengganggu
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
    Penyimpanan aman dengan pencadangan otomatis ke file Excel lokal.
    """
    if data_list is None:
        data_list = []

    df = pd.DataFrame(data_list)
    
    # Simpan backup lokal terlebih dahulu
    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    try:
        df.to_excel(file_path, index=False, engine='openpyxl')
    except Exception:
        pass

    if df.empty:
        return True

    # Sinkronisasi ke Cloud MySQL cPanel jika jalur memungkinkan
    connection = get_db_connection()
    if connection is not None:
        cursor = None
        try:
            cursor = connection.cursor()
            
            for col in df.columns:
                df[col] = df[col].astype(str).replace(['nan', 'None', 'NAT'], '')

            pi_col = 0 if 0 in df.columns else ("Proforma Invoice No." if "Proforma Invoice No." in df.columns else None)

            cols_def_list = []
            for col in df.columns:
                col_str = str(col)
                if pi_col is not None and col == pi_col:
                    cols_def_list.append(f"`{col_str}` VARCHAR(255) PRIMARY KEY")
                else:
                    cols_def_list.append(f"`{col_str}` TEXT")
            
            cols_def_str = ", ".join(cols_def_list)
            cursor.execute(f"CREATE TABLE IF NOT EXISTS `{nama_tabel}` ({cols_def_str}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;")

            if pi_col is not None:
                try:
                    cursor.execute(f"ALTER TABLE `{nama_tabel}` ADD PRIMARY KEY (`{pi_col}`);")
                except Exception:
                    pass

            for _, row in df.iterrows():
                cols = [f"`{str(c)}`" for c in df.columns]
                vals = tuple(row)
                placeholders = ", ".join(["%s"] * len(df.columns))
                cols_str = ", ".join(cols)
                
                updates = []
                for c in df.columns:
                    c_str = str(c)
                    if pi_col is not None and c == pi_col:
                        continue
                    updates.append(f"`{c_str}` = VALUES(`{c_str}`)")
                update_str = ", ".join(updates) if updates else f"`{str(df.columns[0])}` = VALUES(`{str(df.columns[0])}`)"

                sql_upsert = f"""
                    INSERT INTO `{nama_tabel}` ({cols_str}) VALUES ({placeholders})
                    ON DUPLICATE KEY UPDATE {update_str};
                """
                cursor.execute(sql_upsert, vals)
            
            connection.commit()
            return True
        except Error:
            if connection:
                connection.rollback()
            return False
        finally:
            try:
                if cursor:
                    cursor.close()
                if connection and connection.is_connected():
                    connection.close()
            except Exception:
                pass
                
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
    except Exception:
        pass
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
                    return json.loads(res[0])
            cursor.close()
            connection.close()
    except Exception:
        pass
    return None