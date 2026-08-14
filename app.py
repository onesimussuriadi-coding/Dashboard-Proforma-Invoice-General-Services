import streamlit as st
import pandas as pd

# Konfigurasi Halaman Dashboard
st.set_page_config(page_title="Dashboard Proforma Invoice & Kontrak", layout="wide")

st.title("📊 Dashboard Performa Invoice & Kontrak")
st.markdown("---")

# Sidebar untuk Navigasi Menu
menu = st.sidebar.selectbox("Pilih Menu", ["Input Transaksi & Invoice", "Provisional Sum (Add Cost)", "Master Kontrak"])

if menu == "Master Kontrak":
    st.subheader("📁 Data Master Kontrak (Source of Truth)")
    st.write("Daftar template item pekerjaan yang mengacu ke dalam kontrak utama.")
    
    # Data Template Kontrak & Item Berdasarkan Rujukan PDF
    data_master = {
        "Contract No.": ["7207250142", "7207250142", "7207250142"],
        "Tender No": ["S250551FLD-R1", "S250551FLD-R1", "S250551FLD-R1"],
        "Contract Title": ["Jasa Sewa Alat Berat Pendukung Operasional Senoro dan Tiaka"] * 3,
        "Kode Item": ["001", "002", "003"],
        "Kategori": ["SAFETY", "TRANSPORT", "EQUIPMENT"],
        "Deskripsi": ["Safety Boot", "Double Cabin 4x4 + Driver + BBM", "Backhoe Loader (Operation & Maintenance)"],
        "Satuan": ["ea", "days", "months"],
        "Harga Satuan (IDR)": [500000, 1600000, 15000000]
    }
    df_master = pd.DataFrame(data_master)
    st.dataframe(df_master, use_container_width=True)

elif menu == "Provisional Sum (Add Cost)":
    st.subheader("⚙️ Input Pekerjaan Luar Kontrak (Provisional Sum)")
    st.write("Modul khusus add cost dengan tambahan fee otomatis 15% berdasarkan rujukan kontrak.")
    
    with st.form("form_ps"):
        no_kontrak_ps = st.selectbox("Pilih Rujukan Contract No.", ["7207250142"])
        deskripsi_ps = st.text_input("Deskripsi Pekerjaan / Material")
        nilai_add_cost = st.number_input("Nilai Add Cost (IDR)", min_value=0.0, step=100000.0)
        
        submitted = st.form_submit_button("Hitung & Simpan Provisional Sum")
        
        if submitted:
            fee_15 = nilai_add_cost * 0.15
            total_ps = nilai_add_cost + fee_15
            st.success(f"Berhasil ditambahkan untuk Kontrak: {no_kontrak_ps}!")
            st.info(f"Nilai Add Cost: Rp {nilai_add_cost:,.0f} | Fee 15%: Rp {fee_15:,.0f} | **Total Tagihan: Rp {total_ps:,.0f}**")

elif menu == "Input Transaksi & Invoice":
    st.subheader("📝 Buat Proforma Invoice Berdasarkan Rujukan Data")
    
    with st.form("form_proforma_invoice"):
        st.markdown("#### A. Identitas Kontrak & Tender (Item 1 - 5)")
        col1, col2 = st.columns(2)
        with col1:
            contract_no = st.text_input("1. Contract No.", "7207250142")[cite: 1]
            tender_no = st.text_input("2. Tender No", "S250551FLD-R1")[cite: 1]
            contract_title = st.text_input("3. Contract Title", "Jasa Sewa Alat Berat Pendukung Operasional Senoro dan Tiaka")[cite: 1]
        with col2:
            tanggal_contract = st.text_input("4. Tanggal Contract", "16 Desember 2025")[cite: 1]
            contract_period = st.text_input("5. Contract Period", "24 Month")[cite: 1]

        st.markdown("---")
        st.markdown("#### B. Dokumen Proforma Invoice & PO (Item 6 - 10)")
        col3, col4 = st.columns(2)
        with col3:
            pi_no = st.text_input("6. Proforma Invoice No.", "042/BSS-JOB/AB/VII/2026")[cite: 1]
            tgl_pi = st.text_input("7. Tanggal Proforma Invoice", "31 Jul 2026")[cite: 1]
            no_po = st.text_input("8. No PO", "4500011424")[cite: 1]
        with col4:
            tgl_po = st.text_input("9. Tanggal PO", "1 Jul 2026")[cite: 1]
            keterangan_po = st.text_area("10. Keterangan PO", "Jasa Sewa Backhoe Loader Untuk support Kegiatan Operation & Maintenance di Area Senoro dan Tiaka Periode Juli - September 2026, Refer CTR No. 7207250142-BSS-CTR-2026-019")[cite: 1]

        st.markdown("---")
        st.markdown("#### C. Pihak Pertama & Pihak Kedua (Item 11 - 18)")
        col5, col6 = st.columns(2)
        with col5:
            pihak_pertama = st.text_input("11. Pihak Pertama", "JOB Pertamina - Medco E&P Tomori Sulawesi")[cite: 1]
            alamat_p1 = st.text_area("12. Alamat Pihak Pertama", "Bidakara Office Tower I 4Th Floor, Jl. Gatot Subroto Kav. 71 - 73, Jakarta 12870, Indonesia")[cite: 1]
            diwakili_p1 = st.text_input("13. Diwakili Oleh (Pihak Pertama)", "Ronny Dwi Purnomo / Rafik Hidayat")[cite: 1]
            selaku_p1 = st.text_input("14. Selaku (Pihak Pertama)", "Maintenance Support Supervisor")[cite: 1]
        with col6:
            pihak_kedua = st.text_input("15. Pihak Kedua", "PT Banggai Sentral Sulawesi")[cite: 1]
            alamat_p2 = st.text_area("16. Alamat Pihak Kedua", "Jl. Urip Sumorharjo No. 53, Luwuk, Kabupaten Banggai, Provinsi Sulawesi Tengah (94715), Indonesia")[cite: 1]
            diwakili_p2 = st.text_input("17. Diwakili Oleh (Pihak Kedua)", "Ir. Ferry Tatimu")[cite: 1]
            selaku_p2 = st.text_input("18. Selaku (Pihak Kedua)", "Director")[cite: 1]

        st.markdown("---")
        st.markdown("#### D. Detail Pelaksanaan, WCC & Penandatangan (Item 19 - 26)")
        col7, col8 = st.columns(2)
        with col7:
            period_exec = st.text_input("19. Period", "01 s/d 31 Juli 2026")[cite: 1]
            certificate_no = st.text_input("20. Certificate No. (Cover WCC No.)", "7207250142-BSS-WCC-2026-019")[cite: 1]
            wcc_date = st.text_input("21. WCC Date", "31 Jul 2026")[cite: 1]
            wo_no = st.text_input("22. WO No.", "7207250142-BSS-WO-2026-019")[cite: 1]
        with col8:
            wo_title = st.text_input("23. WO Title", "Jasa Sewa Backhoe Loader untuk Support Kegiatan Operation dan Maintenance di Area Senoro dan Tiaka")[cite: 1]
            ctr_no = st.text_input("24. CTR No.", "7207250142-BSS-CTR-2026-019")[cite: 1]
            prepared_name = st.text_input("25. Prepared by Name", "Onesimus Suriadi")[cite: 1]
            prepared_title = st.text_input("26. Prepared by Title", "General Service Manager")[cite: 1]

        submitted_invoice = st.form_submit_button("💾 Simpan & Terbitkan Proforma Invoice")
        
        if submitted_invoice:
            st.balloons()
            st.success(f"Proforma Invoice No. [{pi_no}] untuk Kontrak [{contract_no}] berhasil disimpan ke database sistem!")