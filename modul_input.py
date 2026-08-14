import streamlit as st
import pandas as pd
import os

EXCEL_INVOICE = "database_proforma_invoice.xlsx"

def muat_data_invoice():
    if os.path.exists(EXCEL_INVOICE):
        try:
            df = pd.read_excel(EXCEL_INVOICE)
            return df.to_dict(orient="records")
        except: return []
    return []

def simpan_data_invoice(data_list):
    df = pd.DataFrame(data_list)
    df.to_excel(EXCEL_INVOICE, index=False)

def jalankan():
    st.subheader("Input & Database Invoice")
    # Pindahkan seluruh logika "Input Database & Invoice" dan "Lihat Database Tersimpan" 
    # dari file app.py lama Anda ke sini.
    # Karena panjang, saya sarankan copy-paste bagian menu tersebut ke sini.