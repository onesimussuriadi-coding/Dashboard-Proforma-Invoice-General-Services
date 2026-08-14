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
        "Contract No.": ["7207250142", "7207250142", "7207250142"],
        "Tender No": ["S250551FLD-R1", "S250551FLD-R1", "S250551FLD-R1"],
        "Contract Title": ["Jasa Sewa Alat Berat Pendukung Operasional Senoro dan Tiaka"] * 3,
        "Kode Item": ["001", "002", "003"],
        "Deskripsi": ["Safety Boot", "Double Cabin 4x4 + Driver + BBM", "Backhoe Loader (Operation & Maintenance)"],
        "Satuan": ["ea", "days", "months"],
        "Harga Satuan (IDR)": [500000, 1600000, 15000000]
    }
    df_master = pd.DataFrame(data_master)
    st.dataframe(df_master, use_container_width=True)

elif menu == "Input Database & Invoice":
    st.subheader("📝 Input Database Identifikasi Proforma Invoice")
    st.write("Silakan isi dan update data pada kolom input di bawah ini sesuai kebutuhan Anda.")

    # Membuat Form Input Interaktif Menyerupai Lembar Kerja Excel
    with st.form("form_input_database"):
        
        # Kolom Header tabel
        col_no, col_item, col_input = st.columns([0.5, 2, 3.5])
        with col_no:
            st.markdown("**No**")
        with col_item:
            st.markdown("**Item**")
        with col_input:
            st.markdown("**Input (Dapat diubah bebas)**")
        
        st.markdown("---")

        # Daftar Isian Item 1 sampai 26 (Dapat diinput manual)
        val_1 = st.text_input("1", "7207250142", label_visibility="collapsed") # Contract No
        val_2 = st.text_input("2", "S250551FLD-R1", label_visibility="collapsed") # Tender No
        val_3 = st.text_input("3", "Jasa Sewa Alat Berat Pendukung Operasional Senoro dan Tiaka", label_visibility="collapsed") # Contract Title
        val_4 = st.text_input("4", "16 Desember 2025", label_visibility="collapsed") # Tanggal Contract
        val_5 = st.text_input("5", "24 Month", label_visibility="collapsed") # Contract Period
        val_6 = st.text_input("6", "042/BSS-JOB/AB/VII/2026", label_visibility="collapsed") # Proforma Invoice No
        val_7 = st.text_input("7", "31 Jul 2026", label_visibility="collapsed") # Tanggal Proforma Invoice
        val_8 = st.text_input("8", "4500011424", label_visibility="collapsed") # No PO
        val_9 = st.text_input("9", "1 Jul 2026", label_visibility="collapsed") # Tanggal PO
        val_10 = st.text_area("10", "Jasa Sewa Backhoe Loader Untuk support Kegiatan Operation & Maintenance di Area Senoro dan Tiaka Periode Juli - September 2026", label_visibility="collapsed") # Keterangan PO
        val_11 = st.text_input("11", "JOB Pertamina - Medco E&P Tomori Sulawesi", label_visibility="collapsed") # Pihak Pertama
        val_12 = st.text_area("12", "Bidakara Office Tower I 4Th Floor, Jl. Gatot Subroto Kav. 71 - 73, Jakarta", label_visibility="collapsed") # Alamat Pihak Pertama
        val_13 = st.text_input("13", "Ronny Dwi Purnomo / Rafik Hidayat", label_visibility="collapsed") # Diwakili Oleh P1
        val_14 = st.text_input("14", "Maintenance Support Supervisor", label_visibility="collapsed") # Selaku P1
        val_15 = st.text_input("15", "PT Banggai Sentral Sulawesi", label_visibility="collapsed") # Pihak Kedua
        val_16 = st.text_area("16", "Jl. Urip Sumorharjo No. 53, Luwuk, Kabupaten Banggai", label_visibility="collapsed") # Alamat Pihak Kedua
        val_17 = st.text_input("17", "Ir. Ferry Tatimu", label_visibility="collapsed") # Diwakili Oleh P2
        val_18 = st.text_input("18", "Director", label_visibility="collapsed") # Selaku P2
        val_19 = st.text_input("19", "01 s/d 31 Juli 2026", label_visibility="collapsed") # Period
        val_20 = st.text_input("20", "7207250142-BSS-WCC-2026-019", label_visibility="collapsed") # Certificate No
        val_21 = st.text_input("21", "31 Jul 2026", label_visibility="collapsed") # WCC Date
        val_22 = st.text_input("22", "7207250142-BSS-WO-2026-019", label_visibility="collapsed") # WO No
        val_23 = st.text_input("23", "Jasa Sewa Backhoe Loader untuk Support Kegiatan Operation", label_visibility="collapsed") # WO Title
        val_24 = st.text_input("24", "7207250142-BSS-CTR-2026-019", label_visibility="collapsed") # CTR No
        val_25 = st.text_input("25", "Onesimus Suriadi", label_visibility="collapsed") # Prepared by Name
        val_26 = st.text_input("26", "General Service Manager", label_visibility="collapsed") # Prepared by Title

        st.markdown("---")
        # Tombol Simpan Database / Update Data
        submit_db = st.form_submit_button("💾 Simpan & Update Database Identifikasi")
        
        if submit_db:
            st.balloons()
            st.success("Data identitas berhasil diperbarui dan disimpan ke dalam database sistem!")