import streamlit as st

def jalankan():
    st.subheader("Proforma Invoice & Dokumen Pendukung")
    sub_menu = st.selectbox("Pilih Jenis Dokumen:", [
        "Formulir Utama Proforma Invoice",
        "Berita Acara Mulai Pekerjaan (BAMP)",
        "Berita Acara Selesai Pekerjaan (BASP)",
        "Opname Pekerjaan",
        "Formulir TKDN"
    ])
    
    if sub_menu == "Formulir Utama Proforma Invoice":
        st.write("Isi formulir Proforma Invoice...")
    # dst...