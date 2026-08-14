import streamlit as st
import pandas as pd

# Konfigurasi Halaman Dashboard
st.set_page_config(page_title="Dashboard Performa Invoice", layout="wide")

st.title("📊 Dashboard Performa Invoice & Kontrak")
st.markdown("---")

# Sidebar untuk Navigasi Menu
menu = st.sidebar.selectbox("Pilih Menu", ["Input Transaksi & Invoice", "Provisional Sum (Add Cost)", "Master Kontrak"])

if menu == "Master Kontrak":
    st.subheader("📁 Data Master Kontrak (Source of Truth)")
    st.write("Berikut adalah daftar item pekerjaan yang mengacu ke dalam kontrak utama.")
    
    # Contoh Data Dummy Master Kontrak (Nanti bisa di-load dari file Excel Anda)
    data_master = {
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
    st.write("Modul khusus untuk memasukkan add cost dengan tambahan fee otomatis 15%.")
    
    with st.form("form_ps"):
        deskripsi_ps = st.text_input("Deskripsi Pekerjaan / Material")
        nilai_add_cost = st.number_input("Nilai Add Cost (IDR)", min_value=0.0, step=100000.0)
        
        submitted = st.form_submit_button("Hitung & Simpan Provisional Sum")
        
        if submitted:
            fee_15 = nilai_add_cost * 0.15
            total_ps = nilai_add_cost + fee_15
            st.success(f"Berhasil ditambahkan!")
            st.info(f"Nilai Add Cost: Rp {nilai_add_cost:,.0f} | Fee 15%: Rp {fee_15:,.0f} | **Total Tagihan: Rp {total_ps:,.0f}**")

elif menu == "Input Transaksi & Invoice":
    st.subheader("📝 Buat Proforma Invoice Baru")
    
    col1, col2 = st.columns(2)
    with col1:
        no_invoice = st.text_input("No. Proforma Invoice", "014/BSS-JOB/WS/VIII/2026")
        no_po = st.text_input("No. Purchase Order (PO)", "4500010362")
    with col2:
        tgl_po = st.date_input("Tanggal PO")
        pihak_pertama = st.text_input("Pihak Pertama", "JOB Pertamina - Medco E&P Tomori Sulawesi")
        
    st.markdown("### Rincian Item Pekerjaan")
    st.write("Pilih item dari kontrak dan masukkan kuantitas (Qty).")
    
    # Simulasi baris input interaktif
    qty = st.number_input("Kuantitas (Qty)", min_value=1, value=1)harga_satuan = 1600000 # Contoh dari mastertotal_harga = qty * harga_satuan
    
    st.metric(label="Estimasi Total Nilai Baris Ini", value=f"Rp {total_harga:,.0f}")
    
    if st.button("Terbitkan & Cetak Proforma Invoice"):
        st.balloons()
        st.success(f"Invoice {no_invoice} berhasil diproses secara otomatis!")