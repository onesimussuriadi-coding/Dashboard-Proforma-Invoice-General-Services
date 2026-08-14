import streamlit as st
import pandas as pd

# Konfigurasi Halaman Dashboard
st.set_page_config(page_title="Dashboard Proforma Invoice & Kontrak", layout="wide")

st.title("📊 Dashboard Performa Invoice & Kontrak")
st.markdown("---")

# Sidebar untuk Navigasi Menu
menu = st.sidebar.selectbox("Pilih Menu", ["Input Database & Invoice", "Master Kontrak"])

if menu == "Master Kontrak":
    st.subheader("📁 Data Master Kontrak (Source of Truth)")
    st.write("Daftar template item pekerjaan yang tersimpan dalam sistem.")
    
    data_master = {
        "Contract No.": ["", "", ""],
        "Tender No": ["", "", ""],
        "Contract Title": [""] * 3,
        "Kode Item": ["001", "002", "003"],
        "Deskripsi": ["", "", ""],
        "Satuan": ["", "", ""],
        "Harga Satuan (IDR)": [0, 0, 0]
    }
    df_master = pd.DataFrame(data_master)
    st.dataframe(df_master, use_container_width=True)

elif menu == "Input Database & Invoice":
    st.subheader("📝 Input Database Identifikasi Proforma Invoice")
    st.write("Silakan isi kolom kosong di bawah ini secara manual. Data ini akan tersimpan dan menjadi rujukan pembuatan Proforma Invoice.")

    # Membuat Form Input Interaktif Kosong Menyerupai Excel
    with st.form("form_input_database"):
        
        # Header Tabel
        col_no, col_item, col_colon, col_input = st.columns([0.5, 3, 0.2, 5])
        with col_no:
            st.markdown("**No**")
        with col_item:
            st.markdown("**Item**")
        with col_colon:
            st.markdown("**:**")
        with col_input:
            st.markdown("**Input (Kosong/Siap Diisi)**")
        
        st.markdown("---")

        # Daftar Isian Item 1 sampai 26 (Dibuat Kosong / "" agar Anda bebas mengetik)
        def baris_input(no, label):
            c1, c2, c3, c4 = st.columns([0.5, 3, 0.2, 5])
            with c1:
                st.write(str(no))
            with c2:
                st.write(label)
            with c3:
                st.write(":")
            with c4:
                return st.text_input(f"input_{no}", value="", label_visibility="collapsed")

        val_1 = baris_input(1, "Contract No.")
        val_2 = baris_input(2, "Tender No")
        val_3 = baris_input(3, "Contract Title")
        val_4 = baris_input(4, "Tanggal Contract")
        val_5 = baris_input(5, "Contract Period")
        val_6 = baris_input(6, "Proforma Invoice No.")
        val_7 = baris_input(7, "Tanggal Performa Invoice")
        val_8 = baris_input(8, "No PO")
        val_9 = baris_input(9, "Tanggal PO")
        val_10 = baris_input(10, "Keterangan PO")
        val_11 = baris_input(11, "Pihak Pertama")
        val_12 = baris_input(12, "Alamat Pihak Pertama")
        val_13 = baris_input(13, "Diwakili Oleh")
        val_14 = baris_input(14, "Selaku")
        val_15 = baris_input(15, "Pihak Kedua")
        val_16 = baris_input(16, "Alamat Pihak Kedua")
        val_17 = baris_input(17, "Diwakili Oleh")
        val_18 = baris_input(18, "Selaku")
        val_19 = baris_input(19, "Period")
        val_20 = baris_input(20, "Certificate No. (Cover WCC No.)")
        val_21 = baris_input(21, "WCC Date")
        val_22 = baris_input(22, "WO No.")
        val_23 = baris_input(23, "WO Title")
        val_24 = baris_input(24, "CTR No.")
        val_25 = baris_input(25, "Prepared by Name")
        val_26 = baris_input(26, "Prepared by Title")

        st.markdown("---")
        
        # Tombol Simpan Database
        submit_db = st.form_submit_button("💾 Simpan & Jadikan Rujukan Database")
        
        if submit_db:
            st.balloons()
            st.success("Data identitas berhasil disimpan dan siap digunakan sebagai rujukan pembuatan Proforma Invoice!")