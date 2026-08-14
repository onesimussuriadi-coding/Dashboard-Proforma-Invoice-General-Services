import streamlit as st
import pandas as pd
import os
import glob

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard PT. Banggai Sentral Sulawesi", layout="centered")

# CSS Styling (Tetap Sama)
st.markdown("""<style>.company-header-centered { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #ffffff; padding: 18px 25px; border-radius: 10px; text-align: center; border-bottom: 3px solid #10b981; margin-bottom: 25px; } .dashboard-card { background-color: #ecfdf5; border: 1px solid #a7f3d0; padding: 15px 20px; border-radius: 8px; margin-bottom: 15px; }</style>""", unsafe_allow_html=True)

# --- FUNGSI DATABASE ---
EXCEL_INVOICE = "database_proforma_invoice.xlsx"
def muat_data_invoice():
    if os.path.exists(EXCEL_INVOICE):
        try: return pd.read_excel(EXCEL_INVOICE).to_dict(orient="records")
        except: return []
    return []

# --- HEADER & NAVIGASI ---
st.markdown('<div class="company-header-centered"><h2>PT. BANGGAI SENTRAL SULAWESI</h2><p>Dashboard Proforma Invoice & Kontrak</p></div>', unsafe_allow_html=True)

menu = st.sidebar.selectbox("Pilih Menu Utama", [
    "Input Database & Invoice", 
    "Lihat Database Tersimpan", 
    "Master Kontrak", 
    "Proforma Invoice & Dokumen Pendukung" # Menu Baru
])

# --- LOGIKA MODUL ---
if menu == "Proforma Invoice & Dokumen Pendukung":
    st.subheader("📄 Proforma Invoice & Form Pendukung")
    sub_menu = st.selectbox("Pilih Dokumen:", [
        "Formulir Utama Proforma Invoice",
        "Berita Acara Mulai Pekerjaan (BAMP)",
        "Berita Acara Selesai Pekerjaan (BASP)",
        "Opname Pekerjaan",
        "Formulir TKDN"
    ])
    
    if sub_menu == "Formulir Utama Proforma Invoice":
        st.write("### 📝 Buat Proforma Invoice")
        st.info("Formulir ini akan terhubung dengan data Master Kontrak.")
        # Di sini nanti kita akan tambahkan input form PI
        
    elif sub_menu == "Berita Acara Mulai Pekerjaan (BAMP)":
        st.write("### 🏗️ Berita Acara Mulai Pekerjaan")
        # Nanti kita buat form BAMP di sini

elif menu == "Master Kontrak":
    # (Kode Master Kontrak yang sudah jalan sebelumnya)
    semua_file_excel = [f for f in glob.glob("*.xlsx") if f != EXCEL_INVOICE]
    if len(semua_file_excel) > 0:
        pilih_file = st.selectbox("Pilih File Master Kontrak:", semua_file_excel)
        # ... (Lanjutkan logika pembacaan file master kontrak)
    else: st.warning("Belum ada file master kontrak.")

elif menu == "Input Database & Invoice":
    # (Kode Input Database yang sudah jalan)
    st.subheader("Input Database")
    # ... 

elif menu == "Lihat Database Tersimpan":
    # (Kode Lihat Database yang sudah jalan)
    st.subheader("Lihat Database")
    # ...