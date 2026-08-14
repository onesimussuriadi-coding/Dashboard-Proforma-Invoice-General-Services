import streamlit as st
import pandas as pd

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Proforma Invoice & Kontrak - PT. Banggai Sentral Sulawesi", layout="centered")

# CSS Styling Tema Gelap & Hijau Muda dengan Sticky Header Nama Perusahaan
st.markdown("""
    <style>
    /* Latar belakang utama */
    .main {
        background-color: #f1f5f9;
    }
    
    /* Sticky Header Nama Perusahaan (Statis di atas, tidak ikut bergerak) */
    .company-sticky-header {
        position: fixed;
        top: 0;
        right: 0;
        left: 0;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); /* Warna Gelap Elegan */
        color: #ffffff;
        z-index: 9999;
        padding: 12px 30px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        border-bottom: 3px solid #10b981; /* Aksen Hijau Muda */
    }
    
    /* Jarak agar konten di bawahnya tidak tertutup header statis */
    .content-spacer {
        margin-top: 90px;
    }
    
    /* Kartu Dashboard dengan nuansa hijau muda */
    .dashboard-card {
        background-color: #ecfdf5; /* Hijau muda yang lembut dan segar */
        border: 1px solid #a7f3d0;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    /* Tombol kustom */
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        font-weight: 600;
        background-color: #10b981;
        color: white;
    }
    .stButton>button:hover {
        background-color: #059669;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Inisialisasi Session State
if "db_tersimpan" not in st.session_state:
    st.session_state["db_tersimpan"] = []
if "edit_index" not in st.session_state:
    st.session_state["edit_index"] = None

# --- HEADER STATIS NAMA PERUSAHAAN (SELALU DI ATAS & TIDAK BERGERAK) ---
st.markdown("""
    <div class="company-sticky-header">
        <h2 style="margin:0; font-size: 22px; font-weight: 700; letter-spacing: 0.5px;">PT. BANGGAI SENTRAL SULAWESI</h2>
        <p style="margin:2px 0 0 0; font-size: 12px; color: #34d399; font-weight: 500;">General Contractor and Suppliers | Dashboard Proforma Invoice & Kontrak</p>
    </div>
""", unsafe_allow_html=True)

# Spacer untuk konten bawah
st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)

# Sidebar Navigasi Menu
st.sidebar.markdown("### 🗂️ Navigasi Menu")
menu = st.sidebar.selectbox("Pilih Menu Utama", ["Input Database & Invoice", "Lihat Database Tersimpan", "Master Kontrak"])
st.sidebar.markdown("---")
st.sidebar.info("💡 **Tips:** Gunakan panel panggil ulang untuk mengoreksi data kontrak yang sudah pernah disimpan.")

if menu == "Master Kontrak":
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46;">📁 Data Master Kontrak</h3>
            <p style="color:#047857; font-size:14px;">Daftar template item pekerjaan yang tersimpan dalam sistem.</p>
        </div>
    """, unsafe_allow_html=True)
    
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
    
    # --- PANEL KONTROL & PANGGIL ULANG ---
    st.markdown("""
        <div class="dashboard-card">
            <h4 style="margin-top:0; color:#065f46;">🔍 Panel Kontrol & Panggil Ulang Data</h4>
            <p style="color:#047857; font-size:13px; margin-bottom:10px;">Pilih data di bawah ini jika ingin melakukan koreksi atau edit.</p>
        </div>
    """, unsafe_allow_html=True)

    if len(st.session_state["db_tersimpan"]) > 0:
        opsi_panggil = ["-- Formulir Kosong (Buat Data Baru) --"]
        for i, data in enumerate(st.session_state["db_tersimpan"]):
            opsi_panggil.append(f"Data {i+1} | PI: {data.get('Proforma Invoice No.', '-')} | Kontrak: {data.get('Contract No.', '-')}")
        
        col_pilih, col_btn_panggil = st.columns([3, 1])
        with col_pilih:
            pilihan_edit = st.selectbox("Pilih data untuk diedit:", opsi_panggil, label_visibility="collapsed")
        with col_btn_panggil:
            if st.button("🔄 Panggil Ulang"):
                if pilihan_edit == "-- Formulir Kosong (Buat Data Baru) --":
                    st.session_state["edit_index"] = None
                else:
                    idx_str = pilihan_edit.split(" ")[1]
                    st.session_state["edit_index"] = int(idx_str) - 1
                st.rerun()
    else:
        st.info("📌 Belum ada data tersimpan. Silakan isi formulir di bawah ini untuk membuat data baru.")

    if st.session_state["edit_index"] is not None and st.session_state["edit_index"] < len(st.session_state["db_tersimpan"]):
        st.warning(f"⚠️ **MODE EDIT AKTIF:** Sedang mengoreksi Data ke-{st.session_state['edit_index'] + 1}. Klik tombol *Simpan Kembali (Update)* di bagian bawah jika selesai.")

    st.markdown("---")

    # Mengambil data default untuk form
    def_data = {}
    if st.session_state["edit_index"] is not None and st.session_state["edit_index"] < len(st.session_state["db_tersimpan"]):
        def_data = st.session_state["db_tersimpan"][st.session_state["edit_index"]]
    
    def get_val(key):
        return def_data.get(key, "")

    # --- LEMBAR KERJA UTAMA FORM INPUT ---
    st.markdown("""
        <div class="dashboard-card">
            <h4 style="margin-top:0; color:#065f46;">📝 Lembar Kerja Input Database Identifikasi</h4>
        </div>
    """, unsafe_allow_html=True)

    with st.form("form_input_database"):
        
        col_no, col_item, col_input = st.columns([0.8, 3.5, 7])
        with col_no: st.markdown("**No**")
        with col_item: st.markdown("**Item**")
        with col_input: st.markdown("**Kolom Input Data**")
        st.markdown("---")

        def baris_input_teks(no, label, val="", is_area=False):
            c1, c2, c3 = st.columns([0.8, 3.5, 7])
            with c1: st.write(f"**{no}.**")
            with c2: st.write(label)
            with c3:
                if is_area:
                    return st.text_area(f"input_{no}", value=val, label_visibility="collapsed", height=80)
                else:
                    return st.text_input(f"input_{no}", value=val, label_visibility="collapsed")

        # 26 Item Form
        val_1 = baris_input_teks(1, "Contract No.", val=get_val("Contract No."))
        val_2 = baris_input_teks(2, "Tender No", val=get_val("Tender No"))
        val_3 = baris_input_teks(3, "Contract Title", val=get_val("Contract Title"), is_area=True)
        val_4 = baris_input_teks(4, "Tanggal Contract", val=get_val("Tanggal Contract"))
        val_5 = baris_input_teks(5, "Contract Period", val=get_val("Contract Period"))
        val_6 = baris_input_teks(6, "Proforma Invoice No.", val=get_val("Proforma Invoice No."))
        val_7 = baris_input_teks(7, "Tanggal Performa Invoice", val=get_val("Tanggal PI"))
        val_8 = baris_input_teks(8, "No PO", val=get_val("No PO"))
        val_9 = baris_input_teks(9, "Tanggal PO", val=get_val("Tanggal PO"))
        val_10 = baris_input_teks(10, "Keterangan PO", val=get_val("Keterangan PO"), is_area=True)
        val_11 = baris_input_teks(11, "Pihak Pertama", val=get_val("Pihak Pertama"))
        val_12 = baris_input_teks(12, "Alamat Pihak Pertama", val=get_val("Alamat Pihak Pertama"), is_area=True)
        val_13 = baris_input_teks(13, "Diwakili Oleh", val=get_val("Diwakili Oleh (P1)"))
        val_14 = baris_input_teks(14, "Selaku", val=get_val("Selaku (P1)"))
        val_15 = baris_input_teks(15, "Pihak Kedua", val=get_val("Pihak Kedua"))
        val_16 = baris_input_teks(16, "Alamat Pihak Kedua", val=get_val("Alamat Pihak Kedua"), is_area=True)
        val_17 = baris_input_teks(17, "Diwakili Oleh", val=get_val("Diwakili Oleh (P2)"))
        val_18 = baris_input_teks(18, "Selaku", val=get_val("Selaku (P2)"))
        val_19 = baris_input_teks(19, "Period", val=get_val("Period"))
        val_20 = baris_input_teks(20, "Certificate No. (Cover WCC No.)", val=get_val("Certificate No."))
        val_21 = baris_input_teks(21, "WCC Date", val=get_val("WCC Date"))
        val_22 = baris_input_teks(22, "WO No.", val=get_val("WO No."))
        val_23 = baris_input_teks(23, "WO Title", val=get_val("WO Title"), is_area=True)
        val_24 = baris_input_teks(24, "CTR No.", val=get_val("CTR No."))
        val_25 = baris_input_teks(25, "Prepared by Name", val=get_val("Prepared by Name"))
        val_26 = baris_input_teks(26, "Prepared by Title", val=get_val("Prepared by Title"))

        st.markdown("---")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submit_baru = st.form_submit_button("💾 Simpan Sebagai Data Baru")
        with col_btn2:
            submit_update = st.form_submit_button("📝 Simpan Kembali (Update Data Terpilih)")
        
        if submit_baru or submit_update:
            data_terinput = {
                "Contract No.": val_1, "Tender No": val_2, "Contract Title": val_3, 
                "Tanggal Contract": val_4, "Contract Period": val_5, 
                "Proforma Invoice No.": val_6, "Tanggal PI": val_7, 
                "No PO": val_8, "Tanggal PO": val_9, "Keterangan PO": val_10,
                "Pihak Pertama": val_11, "Alamat Pihak Pertama": val_12, 
                "Diwakili Oleh (P1)": val_13, "Selaku (P1)": val_14,
                "Pihak Kedua": val_15, "Alamat Pihak Kedua": val_16, 
                "Diwakili Oleh (P2)": val_17, "Selaku (P2)": val_18,
                "Period": val_19, "Certificate No.": val_20, "WCC Date": val_21, 
                "WO No.": val_22, "WO Title": val_23, "CTR No.": val_24, 
                "Prepared by Name": val_25, "Prepared by Title": val_26
            }

            if submit_update:
                if st.session_state["edit_index"] is not None:
                    st.session_state["db_tersimpan"][st.session_state["edit_index"]] = data_terinput
                    st.success("✨ Perubahan data berhasil diperbarui!")
                else:
                    st.error("⚠️ Anda belum memanggil data untuk diedit!")
            elif submit_baru:
                st.session_state["db_tersimpan"].append(data_terinput)
                st.success("🎉 Data baru berhasil disimpan ke dalam sistem!")
                st.session_state["edit_index"] = None

elif menu == "Lihat Database Tersimpan":
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46;">📂 Daftar Database Identifikasi Tersimpan</h3>
            <p style="color:#047857; font-size:14px;">Berikut adalah rekapitulasi seluruh data identitas yang telah Anda masukkan.</p>
        </div>
    """, unsafe_allow_html=True)
    
    if len(st.session_state["db_tersimpan"]) > 0:
        df_saved = pd.DataFrame(st.session_state["db_tersimpan"])
        st.dataframe(df_saved, use_container_width=True)
    else:
        st.info("Belum ada data yang tersimpan. Silakan isi formulir di menu *Input Database & Invoice* terlebih dahulu.")