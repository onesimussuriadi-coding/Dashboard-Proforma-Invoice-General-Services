import streamlit as st
import pandas as pd

# Konfigurasi Halaman Dashboard
st.set_page_config(page_title="Dashboard Performa Invoice", layout="wide")

st.title("📊 Dashboard Performa Invoice & Kontrak")
st.markdown("---")

# Sidebar untuk Navigasi Menu berdasarkan Alur Rujukan
menu = st.sidebar.selectbox("Pilih Menu", ["Input Transaksi & Invoice", "Provisional Sum (Add Cost)", "Master Kontrak"])

if menu == "Master Kontrak":
    st.subheader("📁 Data Master Kontrak (Source of Truth)")
    st.write("Daftar item pekerjaan yang mengacu ke dalam kontrak utama.")
    
    # Contoh Data Dummy Master Kontrak
    data_master = {
        "No. Kontrak": ["KONTRAK-001/BSS/2026", "KONTRAK-001/BSS/2026", "KONTRAK-002/BSS/2026"],
        "Kode Item": ["001", "002", "003"],
        "Kategori": ["SAFETY", "TRANSPORT", "EQUIPMENT"],
        "Deskripsi": ["Safety Boot", "Double Cabin 4x4 + Driver + BBM", "Forklift Loader min 5 Ton"],
        "Satuan": ["ea", "days", "month"],
        "Harga Satuan (IDR)": [500000, 1600000, 3500000]
    }
    df_master = pd.DataFrame(data_master)
    st.dataframe(df_master, use_container_width=True)

elif menu == "Provisional Sum (Add Cost)":
    st.subheader("⚙️ Input Pekerjaan Luar Kontrak (Provisional Sum)")
    st.write("Modul khusus add cost dengan tambahan fee otomatis 15% berdasarkan rujukan kontrak.")
    
    with st.form("form_ps"):
        no_kontrak_ps = st.selectbox("Pilih Rujukan No. Kontrak", ["KONTRAK-001/BSS/2026", "KONTRAK-002/BSS/2026"])
        deskripsi_ps = st.text_input("Deskripsi Pekerjaan / Material")
        nilai_add_cost = st.number_input("Nilai Add Cost (IDR)", min_value=0.0, step=100000.0)
        
        submitted = st.form_submit_button("Hitung & Simpan Provisional Sum")
        
        if submitted:
            fee_15 = nilai_add_cost * 0.15
            total_ps = nilai_add_cost + fee_15
            st.success(f"Berhasil ditambahkan untuk Kontrak: {no_kontrak_ps}!")
            st.info(f"Nilai Add Cost: Rp {nilai_add_cost:,.0f} | Fee 15%: Rp {fee_15:,.0f} | **Total Tagihan: Rp {total_ps:,.0f}**")

elif menu == "Input Transaksi & Invoice":
    st.subheader("📝 Buat Proforma Invoice Berdasarkan Rujukan")
    
    # Rujukan Utama: Nomor Kontrak & Nomor PI / PO
    st.markdown("#### 1. Rujukan Dokumen Utama")
    col_ref1, col_ref2 = st.columns(2)
    with col_ref1:
        pilih_kontrak = st.selectbox("Pilih No. Kontrak Rujukan", ["KONTRAK-001/BSS/2026", "KONTRAK-002/BSS/2026"])
        no_invoice = st.text_input("No. Proforma Invoice Baru", "014/BSS-JOB/WS/VIII/2026")
    with col_ref2:
        no_po = st.text_input("No. Purchase Order (PO) / PI", "4500010362")
        tgl_po = st.date_input("Tanggal PO")
        
    pihak_pertama = st.text_input("Pihak Pertama", "JOB Pertamina - Medco E&P Tomori Sulawesi")
        
    st.markdown("---")
    st.markdown("#### 2. Rincian Item Pekerjaan")
    st.write(f"Menampilkan item yang terikat pada Kontrak: **{pilih_kontrak}**")
    
    # Simulasi input rincian
    qty = st.number_input("Kuantitas (Qty)", min_value=1, value=1)
    harga_satuan = 1600000 # Contoh mengambil dari master kontrak terpilih
    total_harga = qty * harga_satuan
    
    st.metric(label="Estimasi Total Nilai Baris Ini", value=f"Rp {total_harga:,.0f}")
    
    if st.button("Terbitkan & Cetak Proforma Invoice"):
        st.balloons()
        st.success(f"Proforma Invoice [{no_invoice}] dengan rujukan PO [{no_po}] berhasil diproses!")