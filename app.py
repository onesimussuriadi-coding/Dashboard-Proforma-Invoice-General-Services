import streamlit as st
import pandas as pd

# Konfigurasi Halaman Dashboard dengan Layout Wide (Lebar penuh)
st.set_page_config(page_title="Dashboard Proforma Invoice & Kontrak", layout="wide")

st.title("📊 Dashboard Performa Invoice & Kontrak")
st.markdown("---")

# Inisialisasi Session State untuk menyimpan database sementara agar tidak hilang saat berpindah menu
if "db_tersimpan" not in st.session_state:
    st.session_state["db_tersimpan"] = []

# Sidebar untuk Navigasi Menu
menu = st.sidebar.selectbox("Pilih Menu", ["Input Database & Invoice", "Lihat Database Tersimpan", "Master Kontrak"])

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
    st.write("Silakan isi kolom di bawah ini. Kolom input dibuat lebih luas dan nyaman agar tulisan panjang tidak terpotong.")

    # Membuat Form Input Interaktif Kosong dengan Lebar Kolom Proporsional
    with st.form("form_input_database"):
        
        # Header Tabel
        col_no, col_item, col_colon, col_input = st.columns([0.5, 3, 0.2, 8.5])
        with col_no:
            st.markdown("**No**")
        with col_item:
            st.markdown("**Item**")
        with col_colon:
            st.markdown("**:**")
        with col_input:
            st.markdown("**Input (Kolom Luas / Text Area & Text Input)**")
        
        st.markdown("---")

        # Fungsi helper baris input dengan ukuran kolom yang dilebarkan
        def baris_input_teks(no, label, is_area=False):
            c1, c2, c3, c4 = st.columns([0.5, 3, 0.2, 8.5])
            with c1:
                st.write(str(no))
            with c2:
                st.write(label)
            with c3:
                st.write(":")
            with c4:
                if is_area:
                    return st.text_area(f"input_{no}", value="", label_visibility="collapsed", height=70)
                else:
                    return st.text_input(f"input_{no}", value="", label_visibility="collapsed")

        # 26 Item Identifikasi (Menggunakan text_area untuk item teks panjang agar tidak terpotong)
        val_1 = baris_input_teks(1, "Contract No.")
        val_2 = baris_input_teks(2, "Tender No")
        val_3 = baris_input_teks(3, "Contract Title", is_area=True)
        val_4 = baris_input_teks(4, "Tanggal Contract")
        val_5 = baris_input_teks(5, "Contract Period")
        val_6 = baris_input_teks(6, "Proforma Invoice No.")
        val_7 = baris_input_teks(7, "Tanggal Performa Invoice")
        val_8 = baris_input_teks(8, "No PO")
        val_9 = baris_input_teks(9, "Tanggal PO")
        val_10 = baris_input_teks(10, "Keterangan PO", is_area=True)
        val_11 = baris_input_teks(11, "Pihak Pertama")
        val_12 = baris_input_teks(12, "Alamat Pihak Pertama", is_area=True)
        val_13 = baris_input_teks(13, "Diwakili Oleh")
        val_14 = baris_input_teks(14, "Selaku")
        val_15 = baris_input_teks(15, "Pihak Kedua")
        val_16 = baris_input_teks(16, "Alamat Pihak Kedua", is_area=True)
        val_17 = baris_input_teks(17, "Diwakili Oleh")
        val_18 = baris_input_teks(18, "Selaku")
        val_19 = baris_input_teks(19, "Period")
        val_20 = baris_input_teks(20, "Certificate No. (Cover WCC No.)")
        val_21 = baris_input_teks(21, "WCC Date")
        val_22 = baris_input_teks(22, "WO No.")
        val_23 = baris_input_teks(23, "WO Title", is_area=True)
        val_24 = baris_input_teks(24, "CTR No.")
        val_25 = baris_input_teks(25, "Prepared by Name")
        val_26 = baris_input_teks(26, "Prepared by Title")

        st.markdown("---")
        
        # Tombol Simpan Database
        submit_db = st.form_submit_button("💾 Simpan & Masukkan ke Database")
        
        if submit_db:
            data_baru = {
                "Contract No.": val_1,
                "Tender No": val_2,
                "Contract Title": val_3,
                "Tanggal Contract": val_4,
                "Contract Period": val_5,
                "Proforma Invoice No.": val_6,
                "Tanggal PI": val_7,
                "No PO": val_8,
                "Tanggal PO": val_9,
                "Keterangan PO": val_10,
                "Pihak Pertama": val_11,
                "Alamat Pihak Pertama": val_12,
                "Diwakili Oleh (P1)": val_13,
                "Selaku (P1)": val_14,
                "Pihak Kedua": val_15,
                "Alamat Pihak Kedua": val_16,
                "Diwakili Oleh (P2)": val_17,
                "Selaku (P2)": val_18,
                "Period": val_19,
                "Certificate No.": val_20,
                "WCC Date": val_21,
                "WO No.": val_22,
                "WO Title": val_23,
                "CTR No.": val_24,
                "Prepared by Name": val_25,
                "Prepared by Title": val_26
            }
            st.session_state["db_tersimpan"].append(data_baru)
            st.balloons()
            st.success("Data identitas berhasil disimpan! Anda dapat melihatnya melalui menu 'Lihat Database Tersimpan'.")

elif menu == "Lihat Database Tersimpan":
    st.subheader("📂 Daftar Database Identifikasi Tersimpan")
    st.write("Berikut adalah data identitas kontrak dan proforma invoice yang telah Anda input dan simpan.")
    
    if len(st.session_state["db_tersimpan"]) > 0:
        df_saved = pd.DataFrame(st.session_state["db_tersimpan"])
        # Menggunakan use_container_width agar tabel melebar dan pas di layar
        st.dataframe(df_saved, use_container_width=True)
    else:
        st.info("Belum ada data yang tersimpan. Silakan isi form pada menu **'Input Database & Invoice'** terlebih dahulu.")