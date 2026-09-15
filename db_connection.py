import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

def get_db_engine():
    try:
        # Koneksi ke database phpMyAdmin ptbssatu.id
        # Sesuaikan username, password, dan nama database Anda dari cPanel
        DB_USER = "ptba8489_admin"      
        DB_PASSWORD = "ayfVy8iSw6kT91"        
        DB_HOST = "localhost"                # Atau ganti dengan domain/IP server database jika diakses dari luar
        DB_NAME = "ptba8489_invoice"

        connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
        engine = create_engine(connection_string)
        return engine
    except Exception as e:
        st.error(f"Koneksi database gagal: {e}")
        return None

def load_data_from_db(nama_tabel):
    engine = get_db_engine()
    if engine:
        try:
            df = pd.read_sql(f"SELECT * FROM {nama_tabel}", con=engine)
            return df
        except Exception as e:
            return pd.DataFrame()
    return pd.DataFrame()

def save_data_to_db(df, nama_tabel):
    engine = get_db_engine()
    if engine:
        try:
            df.to_sql(nama_tabel, con=engine, if_exists='replace', index=False)
            return True
        except Exception as e:
            st.error(f"Gagal menyimpan ke database: {e}")
            return False
    return False