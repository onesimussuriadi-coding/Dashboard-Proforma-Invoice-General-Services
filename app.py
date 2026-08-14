import streamlit as st
import pandas as pd
import os

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Proforma Invoice & Kontrak - PT. Banggai Sentral Sulawesi", layout="centered")

# CSS Styling
st.markdown("""
    <style>
    .main {
        background-color: #f1f5f9;
    }
    .company-header-centered {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        padding: 18px 25px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border-bottom: 3px solid #10b981;
        margin-bottom: 25px;
    }
    .dashboard-card {
        background-color: #ecfdf5;
        border: 1px solid #a7f3d0;
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
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

# --- SISTEM DATABASE EXCEL LOKAL UNTUK INVOICE ---
EXCEL_FILE = "database_proforma_invoice.xlsx"

def muat_data_excel():
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE)
            return df.to_dict(orient="records")
        except:
            return []
    return []

def simpan_data_excel(data_list):
    df = pd.DataFrame(data_list)
    cols_prioritas = ["Proforma Invoice No.", "Contract No.", "Tender No", "Keterangan PO"]
    sisa_cols = [c for c in df.columns if c not in cols_prioritas]
    df = df[cols_prioritas + sisa_cols]
    df.to_excel(EXCEL_FILE, index=False)

if "db_tersimpan" not in st.session_state:
    st.session_state["db_tersimpan"] = muat_data_excel()
if "edit_index" not in st.session_state:
    st.session_state["edit_index"] = None

# --- HEADER NAMA PERUSAHAAN DI TENGAH ---
st.markdown("""
    <div class="company-header-centered">
        <h2 style="margin:0; font-size: 24px; font-weight: 700; letter-spacing: 0.5px;">PT. BANGGAI SENTRAL SULAWESI</h2>
        <p style="margin:4px 0 0 0; font-size: 13px; color: #34d399; font-weight: 500;">General Contractor and Suppliers | Dashboard Proforma Invoice & Kontrak</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar Navigasi Menu
st.sidebar.markdown("### 🗂️ Navigasi Menu")
menu = st.sidebar.selectbox("Pilih Menu Utama", ["Input Database & Invoice", "Lihat Database Tersimpan", "Master Kontrak"])
st.sidebar.markdown("---")
st.sidebar.success("📂 **Status Database:** Terhubung ke Excel Lokal")

if menu == "Master Kontrak":
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📁 Upload & Data Master Kontrak (Multi-Sheet)</h3>
            <p style="color:#047857; font-size:13px; margin:0;">Unggah file Excel Anda yang berisi banyak sheet, lalu masukkan nama sheet khusus untuk master kontrak.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # --- FITUR UPLOAD EXCEL MASTER KONTRAK ---
    uploaded_master = st.file_uploader("Pilih file Excel Master Kontrak (.xlsx)", type=["xlsx"])
    
    if uploaded_master is not None:
        try:
            # Membaca daftar nama sheet yang ada di dalam file Excel tersebut
            xl_file = pd.ExcelFile(uploaded_master)
            daftar_sheet = xl_file.sheet_names
            
            st.info(f"📂 File berhasil diunggah! Ditemukan sheet di dalam file: **{', '.join(daftar_sheet)}**")
            
            # Pilihan sheet yang ingin dibaca
            pilih_sheet = st.selectbox("Pilih nama sheet yang berisi Data Master Kontrak:", daftar_sheet)
            
            if pilih_sheet:
                df_master_uploaded = pd.read_excel(uploaded_master, sheet_name=pilih_sheet)
                st.success(f"✨ Berhasil memuat data dari sheet **{pilih_sheet}**!")
                st.dataframe(df_master_uploaded, use_container_width=True)
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membaca file Excel: {e}")
    else:
        # Tampilan tabel kosong jika belum mengunggah file
        st.write("Daftar template item pekerjaan akan muncul di sini setelah Anda mengunggah file Excel.")
        data_master_default = {
            "Contract No.": [""], "Tender No": [""], "Contract Title": [""], 
            "Kode Item": ["001"], "Deskripsi": [""], "Satuan": [""], "Harga Satuan (IDR)": [0]
        }
        st.dataframe(pd.DataFrame(data_master_default), use_container_width=True)

elif menu == "Input Database & Invoice":
    st.markdown("""
        <div class="dashboard-card">
            <h4 style="margin-top:0; color:#065f46; font-size:15px;">🔍 Panggil Ulang Data Berdasarkan Nomor PI</h4>
        </div>
    """, unsafe_allow_html=True)

    st.session_state["db_tersimpan"] = muat_data_excel()

    if len(st.session_state["db_tersimpan"]) > 0:
        opsi_panggil = ["-- Buat Data Baru (Formulir Kosong) --"]
        for i, data in enumerate(st.session_state["db_tersimpan"]):
            pi_num = data.get('Proforma Invoice No.', '-')
            kontrak_num = data.get('Contract No.', '-')
            opsi_panggil.append(f"PI: {pi_num} | Kontrak: {kontrak_num} (Data {i+1})")
        
        col_pilih, col_btn_panggil = st.columns([3, 1])
        with col_pilih:
            pilihan_edit = st.selectbox("Pilih Nomor PI untuk dipanggil:", opsi_panggil, label_visibility="collapsed")
        with col_btn_panggil:
            if st.button("🔄 Panggil Ulang"):
                if pilihan_edit == "-- Buat Data Baru (Formulir Kosong) --":
                    st.session_state["edit_index"] = None
                else:
                    idx_part = pilihan_edit.split("(Data ")[1].replace(")", "")
                    st.session_state["edit_index"] = int(idx_part) - 1
                st.rerun()
    else:
        st.info("📌 Belum ada data tersimpan di Excel. Silakan isi formulir di bawah ini untuk membuat data baru.")

    if st.session_state["edit_index"] is not None and st.session_state["edit_index"] < len(st.session_state["db_tersimpan"]):
        st.info(f"📋 **DATA DIPANGGIL:** Silakan ubah nomor PI atau isian lainnya, lalu gunakan tombol **'Save As (Buat PI Baru)'** di bawah.")

    def_data = {}
    if st.session_state["edit_index"] is not None and st.session_state["edit_index"] < len(st.session_state["db_tersimpan"]):
        def_data = st.session_state["db_tersimpan"][st.session_state["edit_index"]]
    
    def get_val(key):
        return def_data.get(key, "")

    st.markdown("""
        <div class="dashboard-card" style="margin-top: 10px;">
            <h4 style="margin:0; color:#065f46; font-size:16px;">📝 Lembar Kerja Input & Koreksi Database Identifikasi</h4>
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
                    return st.text_area(f"input_{no}", value=val, label_visibility="collapsed", height=75)
                else:
                    return st.text_input(f"input_{no}", value=val, label_visibility="collapsed")

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
        
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            submit_baru = st.form_submit_button("💾 Simpan Data Baru")
        with col_btn2:
            submit_save_as = st.form_submit_button("📥 Save As (Buat PI Baru)")
        with col_btn3:
            submit_update = st.form_submit_button("📝 Update Data Ini")
        
        if submit_baru or submit_save_as or submit_update:
            data_terinput = {
                "Proforma Invoice No.": val_6, "Contract No.": val_1, "Tender No": val_2, "Keterangan PO": val_10,
                "Contract Title": val_3, "Tanggal Contract": val_4, "Contract Period": val_5, "Tanggal PI": val_7, 
                "No PO": val_8, "Tanggal PO": val_9, "Pihak Pertama": val_11, "Alamat Pihak Pertama": val_12, 
                "Diwakili Oleh (P1)": val_13, "Selaku (P1)": val_14, "Pihak Kedua": val_15, "Alamat Pihak Kedua": val_16, 
                "Diwakili Oleh (P2)": val_17, "Selaku (P2)": val_18, "Period": val_19, "Certificate No.": val_20, 
                "WCC Date": val_21, "WO No.": val_22, "WO Title": val_23, "CTR No.": val_24, 
                "Prepared by Name": val_25, "Prepared by Title": val_26
            }

            current_data = muat_data_excel()

            if submit_update:
                if st.session_state["edit_index"] is not None and st.session_state["edit_index"] < len(current_data):
                    current_data[st.session_state["edit_index"]] = data_terinput
                    simpan_data_excel(current_data)
                    st.success("✨ Data berhasil diperbarui!")
                else:
                    st.error("⚠️ Belum ada data valid yang dipanggil untuk diupdate!")
            elif submit_save_as:
                current_data.append(data_terinput)
                simpan_data_excel(current_data)
                st.success(f"📥 Berhasil Save As! Proforma Invoice [{val_6}] tersimpan sebagai data baru.")
                st.session_state["edit_index"] = None
            elif submit_baru:
                current_data.append(data_terinput)
                simpan_data_excel(current_data)
                st.success("🎉 Data baru berhasil disimpan!")
                st.session_state["edit_index"] = None

elif menu == "Lihat Database Tersimpan":
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📂 Daftar Database Identifikasi Tersimpan (Excel)</h3>
            <p style="color:#047857; font-size:13px; margin:0;">Data di bawah ini dimuat otomatis secara utuh langsung dari file Excel lokal Anda.</p>
        </div>
    """, unsafe_allow_html=True)
    
    saved_records = muat_data_excel()
    if len(saved_records) > 0:
        df_saved = pd.DataFrame(saved_records)
        cols_prioritas = ["Proforma Invoice No.", "Contract No.", "Tender No", "Keterangan PO"]
        sisa_cols = [c for c in df_saved.columns if c not in cols_prioritas]
        df_saved = df_saved[cols_prioritas + sisa_cols]
        st.dataframe(df_saved, use_container_width=True)
    else:
        st.info("Belum ada data di dalam file Excel.")