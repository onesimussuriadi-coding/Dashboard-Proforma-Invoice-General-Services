import streamlit as st
import pandas as pd
import os
import glob
import base64
from datetime import datetime, date

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Terintegrasi - PT. BANGGAI SENTRAL SULAWESI", layout="wide", initial_sidebar_state="expanded")

# --- CSS STYLING PROFESIONAL ---
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; color: #0f172a; }
    
    label, .stSelectbox label, .stTextInput label, .stNumberInput label, .stDateInput label, .stTextArea label {
        color: #0f172a !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }
    
    div[data-baseweb="base-input"], div[data-baseweb="textarea"], div[data-baseweb="select"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        color: #000000 !important;
    }
    input, textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
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
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 15px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
        color: #0f172a;
    }
    .document-preview {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        border: 1px solid #94a3b8;
        color: #0f172a;
        margin-bottom: 20px;
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
    @media print {
        [data-testid="stSidebar"] { display: none; }
        .stButton { display: none; }
        .dashboard-card { display: none; }
        .company-header-centered { display: none; }
        .document-preview { border: none; box-shadow: none; padding: 0; width: 100%; }
    }
    </style>
""", unsafe_allow_html=True)

# --- SISTEM DATABASE EXCEL LOKAL (AMAN & TIMESTAMP DI EXCEL) ---
EXCEL_INVOICE = "database_proforma_invoice.xlsx"
EXCEL_TRANSAKSI = "database_transaksi_rincian.xlsx"

def muat_data_invoice():
    if os.path.exists(EXCEL_INVOICE):
        try:
            df = pd.read_excel(EXCEL_INVOICE)
            if df is not None and not df.empty:
                df = df.dropna(how='all')
                return df.to_dict(orient="records")
        except:
            pass
    return []

def simpan_data_invoice(data_list):
    waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in data_list:
        if not item.get("Update Terakhir"):
            item["Update Terakhir"] = waktu_sekarang

    df_baru = pd.DataFrame(data_list)
    cols_prioritas = ["Proforma Invoice No.", "Nomor Kontrak", "Nomor Tender", "Keterangan PO"]
    sisa_cols = [c for c in df_baru.columns if c not in cols_prioritas]
    df_baru = df_baru[[c for c in cols_prioritas if c in df_baru.columns] + sisa_cols]
    
    if os.path.exists(EXCEL_INVOICE):
        try:
            df_lama = pd.read_excel(EXCEL_INVOICE)
            if df_lama is not None and not df_lama.empty:
                df_gabung = pd.concat([df_lama, df_baru]).drop_duplicates(subset=["Proforma Invoice No."], keep="last")
                df_gabung.to_excel(EXCEL_INVOICE, index=False)
                st.session_state["db_tersimpan"] = df_gabung.to_dict(orient="records")
                return
        except:
            pass
            
    df_baru.to_excel(EXCEL_INVOICE, index=False)
    st.session_state["db_tersimpan"] = data_list

def muat_data_transaksi():
    if os.path.exists(EXCEL_TRANSAKSI):
        try:
            df = pd.read_excel(EXCEL_TRANSAKSI)
            if df is not None and not df.empty:
                df = df.dropna(how='all')
                return df.to_dict(orient="records")
        except:
            pass
    return []

def simpan_data_transaksi(data_list):
    waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in data_list:
        if not item.get("Update Terakhir"):
            item["Update Terakhir"] = waktu_sekarang

    df_baru = pd.DataFrame(data_list)
    if os.path.exists(EXCEL_TRANSAKSI):
        try:
            df_lama = pd.read_excel(EXCEL_TRANSAKSI)
            if df_lama is not None and not df_lama.empty:
                df_gabung = pd.concat([df_lama, df_baru]).drop_duplicates(subset=["PI No."], keep="last")
                df_gabung.to_excel(EXCEL_TRANSAKSI, index=False)
                st.session_state["db_transaksi"] = df_gabung.to_dict(orient="records")
                return
        except:
            pass
    df_baru.to_excel(EXCEL_TRANSAKSI, index=False)
    st.session_state["db_transaksi"] = data_list

def muat_master_kontrak():
    files = [f for f in glob.glob("*.xlsx") if f not in [EXCEL_INVOICE, EXCEL_TRANSAKSI] and not f.startswith("~$")]
    if not files:
        return pd.DataFrame()
    try:
        xl = pd.ExcelFile(files[0])
        df = xl.parse(xl.sheet_names[0])
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        if 'No.' in df.columns:
            df = df.dropna(subset=['No.'], how='all')
        return df
    except:
        return pd.DataFrame()

# Inisialisasi Session State
if "db_tersimpan" not in st.session_state:
    disk_data = muat_data_invoice()
    st.session_state["db_tersimpan"] = disk_data if disk_data else []

if "db_transaksi" not in st.session_state:
    disk_tx = muat_data_transaksi()
    st.session_state["db_transaksi"] = disk_tx if disk_tx else []

if "edit_index" not in st.session_state:
    st.session_state["edit_index"] = None

if "edit_tx_index" not in st.session_state:
    st.session_state["edit_tx_index"] = None

# --- HEADER UTAMA ---
st.markdown("""
    <div class="company-header-centered">
        <h2 style="margin:0; font-size: 24px; font-weight: 700; color: #ffffff;">PT. BANGGAI SENTRAL SULAWESI</h2>
        <p style="margin:4px 0 0 0; font-size: 13px; color: #34d399; font-weight: 500;">General Contractor and Suppliers | Dashboard Terintegrasi Utama</p>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR: NAVIGASI & WAKTU LOKAL ---
st.sidebar.markdown("### 🗂️ Navigasi Dashboard Utama")
current_time_str = datetime.now().strftime("%d %b %Y, %H:%M:%S")
st.sidebar.markdown(f"🕒 **Waktu Sistem:**<br>`{current_time_str}`", unsafe_allow_html=True)
st.sidebar.markdown("---")

modul_pilihan = st.sidebar.selectbox("Pilih Modul Utama:", [
    "📁 Modul 1: Database & Master Kontrak",
    "📄 Modul 2: Invoice & Dokumen Turunan"
])

st.sidebar.markdown("---")

if modul_pilihan == "📁 Modul 1: Database & Master Kontrak":
    menu = st.sidebar.radio("Pilih Menu:", [
        "Input Database & Invoice (29 Kolom)",
        "Lihat Database Tersimpan",
        "Master Kontrak"
    ])
else:
    menu = st.sidebar.radio("Pilih Menu:", [
        "Input & Proses Rincian Pekerjaan",
        "Pratinjau, Cetak & Download PDF Dokumen",
        "Lihat Akumulasi Riwayat Transaksi"
    ])

st.sidebar.markdown("---")
st.sidebar.success("📂 **Status Sistem:** Terhubung ke Database Lokal Aman")

# =========================================================================
# LOGIKA MODUL 1: DATABASE & MASTER KONTRAK
# =========================================================================
if menu == "Input Database & Invoice (29 Kolom)":
    st.markdown("""
        <div class="dashboard-card">
            <h4 style="margin-top:0; color:#065f46; font-size:15px;">🔍 Panggil Ulang atau Buat Database Identifikasi Kontrak & PI</h4>
        </div>
    """, unsafe_allow_html=True)

    disk_check = muat_data_invoice()
    if disk_check and len(disk_check) > len(st.session_state["db_tersimpan"]):
        st.session_state["db_tersimpan"] = disk_check

    if len(st.session_state["db_tersimpan"]) > 0:
        opsi_panggil = ["-- Buat Data Baru (Formulir Kosong) --"]
        for i, data in enumerate(st.session_state["db_tersimpan"]):
            pi_num = data.get('Proforma Invoice No.', '-')
            kontrak_num = data.get('Nomor Kontrak', '-')
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
        st.info("📌 Belum ada data database tersimpan di Excel atau data kosong.")

    if st.session_state["edit_index"] is not None and st.session_state["edit_index"] < len(st.session_state["db_tersimpan"]):
        st.info(f"📋 **DATA DIPANGGIL:** Silakan ubah isian, lalu gunakan tombol **'Save As (Buat PI Baru)'** atau **'Update Data Ini'**.")

    def_data = {}
    if st.session_state["edit_index"] is not None and st.session_state["edit_index"] < len(st.session_state["db_tersimpan"]):
        def_data = st.session_state["db_tersimpan"][st.session_state["edit_index"]]
    
    def get_val(key):
        return def_data.get(key, "")

    st.markdown("""
        <div class="dashboard-card" style="margin-top: 10px;">
            <h4 style="margin:0; color:#065f46; font-size:16px;">📝 Lembar Kerja 29 Kolom Identifikasi Kontrak & PI</h4>
        </div>
    """, unsafe_allow_html=True)

    with st.form("form_input_database"):
        col_no, col_item, col_input = st.columns([0.8, 3.5, 7])
        with col_no: st.markdown("**No**")
        with col_item: st.markdown("**Item**")
        with col_input: st.markdown("**Kolom Input Data (Bersih & Standar)**")
        st.markdown("---")

        def baris_input_bersih(no, label, default_val="", is_area=False):
            c1, c2, c3 = st.columns([0.8, 3.5, 7])
            with c1: c1.write(f"**{no}.**")
            with c2: c2.write(label)
            with c3:
                if is_area:
                    return st.text_area(f"input_{no}", value=str(default_val), label_visibility="collapsed", height=75)
                else:
                    return st.text_input(f"input_{no}", value=str(default_val), label_visibility="collapsed")

        val_1 = baris_input_bersih(1, "Nomor Kontrak", default_val=get_val("Nomor Kontrak"))
        val_2 = baris_input_bersih(2, "Nomor Tender", default_val=get_val("Nomor Tender"))
        val_3 = baris_input_bersih(3, "Judul Kontrak", default_val=get_val("Judul Kontrak"), is_area=True)
        val_4 = baris_input_bersih(4, "Tanggal Kontrak", default_val=get_val("Tanggal Kontrak"))
        val_5 = baris_input_bersih(5, "Jangka Waktu Kontrak", default_val=get_val("Jangka Waktu Kontrak"))
        val_6 = baris_input_bersih(6, "Proforma Invoice No.", default_val=get_val("Proforma Invoice No."))
        val_7 = baris_input_bersih(7, "Tanggal Performa Invoice", default_val=get_val("Tanggal Performa Invoice"))
        val_8 = baris_input_bersih(8, "Nomor Purchase Order", default_val=get_val("Nomor Purchase Order"))
        val_9 = baris_input_bersih(9, "Tanggal Purchase Order", default_val=get_val("Tanggal Purchase Order"))
        val_10 = baris_input_bersih(10, "Lingkup Pekerjaan", default_val=get_val("Lingkup Pekerjaan"), is_area=True)
        val_11 = baris_input_bersih(11, "Pihak Pertama", default_val=get_val("Pihak Pertama"))
        val_12 = baris_input_bersih(12, "Alamat Pihak Pertama", default_val=get_val("Alamat Pihak Pertama"), is_area=True)
        
        c1, c2, c3 = st.columns([0.8, 3.5, 7])
        c1.write("**13.**")
        c2.write("Diwakili Oleh")
        pilihan_p1 = [
            "Ronny Dwi Purnomo / Rafik Hidayat",
            "Rafik Hidayat / Ronny Dwi Purnomo"
        ]
        def_p1 = get_val("Diwakili Oleh")
        idx_p1 = pilihan_p1.index(def_p1) if def_p1 in pilihan_p1 else 0
        val_13 = c3.selectbox("Diwakili Oleh P1", pilihan_p1, index=idx_p1, label_visibility="collapsed")

        val_14 = baris_input_bersih(14, "Selaku", default_val=get_val("Selaku"))
        val_15 = baris_input_bersih(15, "Pihak Kedua", default_val=get_val("Pihak Kedua"))
        val_16 = baris_input_bersih(16, "Alamat Pihak Kedua", default_val=get_val("Alamat Pihak Kedua"), is_area=True)
        val_17 = baris_input_bersih(17, "Diwakili Oleh (P2)", default_val=get_val("Diwakili Oleh (P2)"))
        val_18 = baris_input_bersih(18, "Selaku (P2)", default_val=get_val("Selaku (P2)"))
        val_19 = baris_input_bersih(19, "Periode Pekerjaan", default_val=get_val("Periode Pekerjaan"))
        val_20 = baris_input_bersih(20, "Nomor WCC", default_val=get_val("Nomor WCC"))
        val_21 = baris_input_bersih(21, "Tanggal WCC", default_val=get_val("Tanggal WCC"))
        val_22 = baris_input_bersih(22, "Nomor WO", default_val=get_val("Nomor WO"))
        val_23 = baris_input_bersih(23, "Keterangan WO", default_val=get_val("Keterangan WO"), is_area=True)
        val_24 = baris_input_bersih(24, "Nomor CTR", default_val=get_val("Nomor CTR"))
        val_25 = baris_input_bersih(25, "Progress Pekerjaan", default_val=get_val("Progress Pekerjaan"))
        val_27 = baris_input_bersih(27, "Prepared by Name", default_val=get_val("Prepared by Name"))
        val_28_title = baris_input_bersih(28, "Prepared by Title", default_val=get_val("Prepared by Title"))

        c1, c2, c3 = st.columns([0.8, 3.5, 7])
        c1.write("**29.**")
        c2.write("Pejabat berwenang")
        pilihan_pj = [
            "Imron Maulana / Moh Bazarul Aqhsa",
            "Moh Bazarul Aqhsa / Imron Maulana"
        ]
        def_pj = get_val("Pejabat berwenang")
        idx_pj = pilihan_pj.index(def_pj) if def_pj in pilihan_pj else 0
        val_29 = c3.selectbox("Pejabat berwenang", pilihan_pj, index=idx_pj, label_visibility="collapsed")

        val_30 = baris_input_bersih(30, "Jabatan Field Manager", default_val=get_val("Jabatan Field Manager"))

        st.markdown("---")
        
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            submit_baru = st.form_submit_button("💾 Simpan Data Baru")
        with col_btn2:
            submit_save_as = st.form_submit_button("📥 Save As (Buat PI Baru)")
        with col_btn3:
            submit_update = st.form_submit_button("📝 Update Data Ini")
        
        if submit_baru or submit_save_as or submit_update:
            waktu_aksi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data_terinput = {
                "Proforma Invoice No.": val_6, "Nomor Kontrak": val_1, "Nomor Tender": val_2, "Judul Kontrak": val_3,
                "Tanggal Kontrak": val_4, "Jangka Waktu Kontrak": val_5, "Tanggal Performa Invoice": val_7, 
                "Nomor Purchase Order": val_8, "Tanggal Purchase Order": val_9, "Lingkup Pekerjaan": val_10, 
                "Pihak Pertama": val_11, "Alamat Pihak Pertama": val_12, "Diwakili Oleh": val_13, "Selaku": val_14, 
                "Pihak Kedua": val_15, "Alamat Pihak Kedua": val_16, "Diwakili Oleh (P2)": val_17, "Selaku (P2)": val_18, 
                "Periode Pekerjaan": val_19, "Nomor WCC": val_20, "Tanggal WCC": val_21, "Nomor WO": val_22, "Keterangan WO": val_23, 
                "Nomor CTR": val_24, "Progress Pekerjaan": val_25, "Prepared by Name": val_27, "Prepared by Title": val_28_title,
                "Pejabat berwenang": val_29, "Jabatan Field Manager": val_30, "Update Terakhir": waktu_aksi
            }

            current_data = st.session_state["db_tersimpan"]

            if submit_update:
                if st.session_state["edit_index"] is not None and st.session_state["edit_index"] < len(current_data):
                    current_data[st.session_state["edit_index"]] = data_terinput
                    simpan_data_invoice(current_data)
                    st.success("✨ Data berhasil diperbarui!")
                else:
                    st.error("⚠️ Belum ada data valid yang dipanggil untuk diupdate!")
            elif submit_save_as:
                current_data.append(data_terinput)
                simpan_data_invoice(current_data)
                st.success(f"📥 Berhasil Save As! Proforma Invoice [{val_6}] tersimpan sebagai data baru.")
                st.session_state["edit_index"] = None
            elif submit_baru:
                current_data.append(data_terinput)
                simpan_data_invoice(current_data)
                st.success("🎉 Data baru berhasil disimpan!")
                st.session_state["edit_index"] = None

elif menu == "Lihat Database Tersimpan":
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📂 Daftar Database Identifikasi Tersimpan (Excel)</h3>
        </div>
    """, unsafe_allow_html=True)
    
    saved_records = muat_data_invoice()
    if len(saved_records) > 0:
        df_saved = pd.DataFrame(saved_records)
        cols_prioritas = ["Proforma Invoice No.", "Nomor Kontrak", "Nomor Tender", "Lingkup Pekerjaan", "Update Terakhir"]
        sisa_cols = [c for c in df_saved.columns if c not in cols_prioritas]
        df_saved = df_saved[[c for c in cols_prioritas if c in df_saved.columns] + sisa_cols]
        st.dataframe(df_saved, use_container_width=True)
    else:
        st.info("Belum ada data database identifikasi di dalam file Excel.")

elif menu == "Master Kontrak":
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📁 Rincian Master Kontrak</h3>
        </div>
    """, unsafe_allow_html=True)
    semua_file_excel = [f for f in glob.glob("*.xlsx") if f != EXCEL_INVOICE and f != EXCEL_TRANSAKSI]
    if semua_file_excel:
        pilih_file = st.selectbox("Pilih File Master Kontrak:", semua_file_excel)
        if pilih_file:
            xl_f = pd.ExcelFile(pilih_file)
            sheet_pilih = st.selectbox("Pilih Sheet:", xl_f.sheet_names)
            st.dataframe(muat_master_kontrak(), use_container_width=True)
    else:
        st.warning("⚠️ Belum ada file Master Kontrak di folder.")# =========================================================================
# LOGIKA MODUL 2: INVOICE & DOKUMEN TURUNAN (DENGAN VLOOKUP BERBASIS KONTRAK)
# =========================================================================
elif menu == "Input & Proses Rincian Pekerjaan":
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📝 Lembar Kerja & Pemrosesan Rincian Pekerjaan</h3>
        </div>
    """, unsafe_allow_html=True)

    saved_db = muat_data_invoice()
    df_master = muat_master_kontrak()
    
    if not saved_db:
        st.warning("⚠️ Belum ada data di Database Modul 1. Harap lakukan input data kontrak & PI terlebih dahulu pada Modul 1.")
    else:
        st.markdown("#### 🔄 Panggil Data Transaksi untuk Edit & Update")
        existing_tx_list = muat_data_transaksi()
        
        unique_pi_list = sorted(list(set([str(t.get("PI No.", "")) for t in existing_tx_list if t.get("PI No.")])))
        opsi_panggil_tx = ["-- Buat / Input Data Baru --"] + [f"PI: {pi}" for pi in unique_pi_list]
        
        col_p_tx, col_b_tx = st.columns([3, 1])
        with col_p_tx:
            pilihan_edit_tx = st.selectbox("Pilih Nomor PI yang ingin diedit:", opsi_panggil_tx, label_visibility="collapsed")
        with col_b_tx:
            if st.button("📥 Panggil Data Ini"):
                if pilihan_edit_tx == "-- Buat / Input Data Baru --":
                    st.session_state["edit_tx_index"] = None
                else:
                    target_pi = pilihan_edit_tx.replace("PI: ", "")
                    for idx, tx in enumerate(existing_tx_list):
                        if str(tx.get("PI No.")) == target_pi:
                            st.session_state["edit_tx_index"] = idx
                            break
                st.rerun()

        def_tx = {}
        if st.session_state["edit_tx_index"] is not None and st.session_state["edit_tx_index"] < len(existing_tx_list):
            def_tx = existing_tx_list[st.session_state["edit_tx_index"]]

        def get_tval(key, default=""):
            return def_tx.get(key, default)

        list_kontrak = list(set([str(item.get("Nomor Kontrak", "")) for item in saved_db if item.get("Nomor Kontrak")]))
        list_pi = list(set([str(item.get("Proforma Invoice No.", "")) for item in saved_db if item.get("Proforma Invoice No.")]))

        with st.form("form_proses_rincian"):
            col1, col2 = st.columns(2)
            with col1:
                def_kontrak = get_tval("Nomor Kontrak", list_kontrak[0] if list_kontrak else "")
                idx_k = list_kontrak.index(def_kontrak) if def_kontrak in list_kontrak else 0
                selected_kontrak = st.selectbox("Nomor Kontrak", list_kontrak if list_kontrak else [""], index=idx_k)
                
                filtered_pi = [str(item.get("Proforma Invoice No.", "")) for item in saved_db if str(item.get("Nomor Kontrak")) == str(selected_kontrak)]
                if not filtered_pi:
                    filtered_pi = list_pi
                
                def_pi_val = get_tval("PI No.", filtered_pi[0] if filtered_pi else "")
                idx_pi = filtered_pi.index(def_pi_val) if def_pi_val in filtered_pi else 0
                selected_pi = st.selectbox("Nomor Proforma Invoice (PI)", filtered_pi if filtered_pi else [""], index=idx_pi)
                
                matched_record = next((item for item in saved_db if str(item.get("Nomor Kontrak")) == str(selected_kontrak) and str(item.get("Proforma Invoice No.")) == str(selected_pi)), saved_db[0])

                nama_kontrak = matched_record.get("Judul Kontrak", "")
                nomor_tender = matched_record.get("Nomor Tender", "")
                tanggal_pi = matched_record.get("Tanggal Performa Invoice", "")
                ditujukan_kepada = matched_record.get("Pihak Pertama", "")
            
            with col2:
                nomor_po = st.text_input("Nomor PO", matched_record.get("Nomor Purchase Order", ""))
                tanggal_po = st.text_input("Tanggal PO", matched_record.get("Tanggal Purchase Order", ""))
                mata_uang = st.text_input("Mata Uang", "IDR")
                desc_po = st.text_area("Lingkup Pekerjaan", matched_record.get("Lingkup Pekerjaan", ""))

            st.markdown("---")
            st.markdown("#### ⚙️ Pemilihan Kategori, Uraian Pekerjaan & Rujukan Master Kontrak")
            
            if not df_master.empty:
                df_master.columns = df_master.columns.astype(str).str.strip()
                available_cols = df_master.columns.tolist()
                
                # --- DETEKSI KOLOM PRESISI SESUAI EXCEL BARU ANDA ---
                kolom_kategori = next((c for c in available_cols if 'kategori' in c.lower()), available_cols[2] if len(available_cols) > 2 else available_cols[0])
                
                # Mendeteksi 'Uraian Pekerjaan'
                kolom_spek = next((c for c in available_cols if 'uraian' in c.lower() or 'pekerjaan' in c.lower()), available_cols[4] if len(available_cols) > 4 else available_cols[3])
                
                # --- PILIHAN KATEGORI & URAIAN PEKERJAAN ---
                list_kat = df_master[kolom_kategori].dropna().unique().tolist()
                def_kat = get_tval("Kategori", list_kat[0] if list_kat else "")
                idx_kat = list_kat.index(def_kat) if def_kat in list_kat else 0
                kategori_pilih = st.selectbox("Kategori (Rujukan Master Kontrak)", list_kat if list_kat else ["(Kategori Kosong)"], index=idx_kat)
                
                df_filtered = df_master[df_master[kolom_kategori] == kategori_pilih]
                
                list_spek = df_filtered[kolom_spek].dropna().unique().tolist() if not df_filtered.empty and kolom_spek in df_filtered.columns else df_master[kolom_spek].dropna().unique().tolist()
                
                def_spek = get_tval("Deskripsi Pekerjaan", list_spek[0] if list_spek else "")
                idx_spek = list_spek.index(def_spek) if def_spek in list_spek else 0
                deskripsi_pekerjaan = st.selectbox("Uraian Pekerjaan (Rujukan Master Kontrak)", list_spek if list_spek else ["(Uraian Kosong)"], index=idx_spek)
                
                # --- VLOOKUP HARGA SATUAN OTOMATIS ---
                harga_satuan_otomatis = 0.0
                unit_otomatis = "Month"
                
                if not df_filtered.empty:
                    matched_row_df = df_filtered[df_filtered[kolom_spek] == deskripsi_pekerjaan]
                    if not matched_row_df.empty:
                        row_m = matched_row_df.iloc[0]
                        
                        # Mendeteksi kolom 'Harga Satuan' secara presisi
                        kolom_hs = next((c for c in available_cols if 'harga satuan' in c.lower() or ('harga' in c.lower() and 'satuan' in c.lower())), None)
                        if kolom_hs and kolom_hs in row_m:
                            try:
                                raw_val = str(row_m[kolom_hs]).replace("Rp", "").replace(".", "").replace(",", ".").strip()
                                harga_satuan_otomatis = float(raw_val)
                            except:
                                harga_satuan_otomatis = 0.0

                        kolom_unit = next((c for c in available_cols if 'unit' in c.lower()), None)
                        if kolom_unit and kolom_unit in row_m:
                            unit_otomatis = str(row_m.get(kolom_unit, "Month"))
            else:
                st.warning("⚠️ File Master Kontrak Excel belum ditemukan di direktori sistem.")
                kategori_pilih = "-"
                deskripsi_pekerjaan = "-"
                harga_satuan_otomatis = 0.0
                unit_otomatis = "Month"

            c_item1, c_item2, c_item3, c_item4 = st.columns([1, 1, 1, 1])
            with c_item1:
                qty = st.number_input("Qty Out", value=float(get_tval("Qty", 1.0)))
            with c_item2:
                def_unit = get_tval("Unit", unit_otomatis)
                u_opts = ["Month", "Day"]
                idx_u = u_opts.index(def_unit) if def_unit in u_opts else 0
                unit = st.selectbox("Unit", u_opts, index=idx_u)
            with c_item3:
                tgl_mulai = st.date_input("Tanggal Mulai", value=date(2026, 7, 1))
            with c_item4:
                tgl_selesai = st.date_input("Tanggal Selesai", value=date(2026, 7, 31))

            def_hs = float(get_tval("Harga Satuan", harga_satuan_otomatis))
            st.markdown(f"""
                <div style="font-weight:600; font-size:13px; margin-bottom:5px; color:#0f172a;">Harga Satuan (Rp - Membaca Master Kontrak Berdasarkan Nomor Kontrak)</div>
                <div style="background-color:#ffffff; border:1px solid #cbd5e1; padding:8px 12px; border-radius:6px; font-size:15px; font-weight:bold; color:#0f172a;">
                    Rp {def_hs:,.2f}
                </div>
            """, unsafe_allow_html=True)
            harga_satuan = def_hs  
            
            def_ket = get_tval("Keterangan", "")
            keterangan_pekerjaan = st.text_input("Keterangan / Deskripsi Tambahan", value=def_ket)

            st.markdown("---")
            submit_proses = st.form_submit_button("🚀 Proses & Distribusikan Data ke Dokumen Turunan")

            if submit_proses:
                waktu_aksi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                total_harga = qty * harga_satuan
                data_transaksi = {
                    "Nomor Kontrak": selected_kontrak,
                    "Nama Kontrak": nama_kontrak,
                    "Nomor Tender": nomor_tender,
                    "PI No.": selected_pi,
                    "Tanggal PI": tanggal_pi,
                    "Ditujukan Kepada": ditujukan_kepada,
                    "Nomor PO": nomor_po,
                    "Deskripsi PO": desc_po,
                    "Tanggal PO": tanggal_po,
                    "Mata Uang": mata_uang,
                    "Kategori": kategori_pilih,
                    "Deskripsi Pekerjaan": deskripsi_pekerjaan,
                    "Qty": qty,
                    "Unit": unit,
                    "Tanggal Mulai": tgl_mulai.strftime("%d %b %Y"),
                    "Tanggal Selesai": tgl_selesai.strftime("%d %b %Y"),
                    "Harga Satuan": harga_satuan,
                    "Total Harga": total_harga,
                    "Keterangan": keterangan_pekerjaan,
                    "Update Terakhir": waktu_aksi
                }
                
                existing_tx = muat_data_transaksi()
                pi_baru = str(selected_pi).strip()
                existing_tx = [t for t in existing_tx if str(t.get("PI No.")).strip() != pi_baru]
                existing_tx.append(data_transaksi)
                simpan_data_transaksi(existing_tx)
                
                st.session_state["edit_tx_index"] = None
                st.success(f"🎉 Data Rincian Pekerjaan untuk PI [{pi_baru}] Berhasil Diproses & Disimpan!")

elif menu == "Pratinjau, Cetak & Download PDF Dokumen":
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">🖨️ Pratinjau, Cetak & Download PDF Dokumen Resmi</h3>
        </div>
    """, unsafe_allow_html=True)

    transaksi_list = muat_data_transaksi()
    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi rincian pekerjaan yang diproses di Modul 2.")
    else:
        seen_pi_dd = set()
        unique_tx_list = []
        for t in transaksi_list:
            pi_key = str(t.get('PI No.', ''))
            if pi_key not in seen_pi_dd:
                seen_pi_dd.add(pi_key)
                unique_tx_list.append(t)

        pilihan_tx = [f"PI: {t['PI No.']} | Kontrak: {t['Nomor Kontrak']} | Total: Rp {t['Total Harga']:,.0f}" for t in unique_tx_list]
        selected_idx = st.selectbox("Pilih Dokumen Transaksi Tersimpan:", range(len(pilihan_tx)), format_func=lambda x: pilihan_tx[x])
        
        t_data = unique_tx_list[selected_idx]
        
        doc_type = st.selectbox("Pilih Jenis Dokumen:", [
            "Rincian Pekerjaan (Sheet Rincian Pek)",
            "Proforma Invoice",
            "WCC (Work Completion Certificate)",
            "Opname Pekerjaan",
            "Berita Acara Mulai Pekerjaan (BAMP)",
            "Berita Acara Selesai Pekerjaan (BASP)",
            "Formulir TKDN"
        ])

        st.markdown("---")

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{doc_type} - PT BSS</title>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; padding: 30px; margin: 0; }}
                .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px; }}
                .title {{ text-align: center; font-weight: bold; font-size: 15px; margin-bottom: 20px; text-transform: uppercase; text-decoration: underline; }}
                table.info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; border: none; }}
                table.info-table td {{ border: none; padding: 4px 6px; font-size: 11px; vertical-align: top; }}
                .label-col {{ width: 160px; font-weight: bold; }}
                .colon-col {{ width: 10px; font-weight: bold; text-align: center; }}
                table.data-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 15px; }}
                table.data-table th, table.data-table td {{ border: 1px solid #333; padding: 6px 10px; font-size: 11px; text-align: left; }}
                table.data-table th {{ background-color: #f1f5f9; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2 style="margin: 0; font-size: 16px;">PT. BANGGAI SENTRAL SULAWESI</h2>
                <p style="margin: 2px 0; font-size: 10px;">Jl. Urip Sumoharjo No. 53 Luwuk, Kabupaten Banggai, Propinsi Sulawesi Tengah</p>
            </div>
            <div class="title">{doc_type}</div>
        """

        if doc_type == "Rincian Pekerjaan (Sheet Rincian Pek)":
            html_content += f"""
            <table class="info-table">
                <tr>
                    <td class="label-col">Rincian Pekerjaan</td>
                    <td class="colon-col">:</td>
                    <td>{t_data['Nomor Kontrak']}-BSS-WCC-2026</td>
                    <td class="label-col">Ditujukan Kepada</td>
                    <td class="colon-col">:</td>
                    <td>{t_data['Ditujukan Kepada']}</td>
                </tr>
                <tr>
                    <td class="label-col">Nomor Kontrak</td>
                    <td class="colon-col">:</td>
                    <td>{t_data['Nomor Kontrak']}</td>
                    <td class="label-col">Nomor Purchase Order</td>
                    <td class="colon-col">:</td>
                    <td>{t_data['Nomor PO']}</td>
                </tr>
                <tr>
                    <td class="label-col">Nama Kontrak</td>
                    <td class="colon-col">:</td>
                    <td>{t_data['Nama Kontrak']}</td>
                    <td class="label-col">Lingkup Pekerjaan</td>
                    <td class="colon-col">:</td>
                    <td>{t_data['Deskripsi PO']}</td>
                </tr>
                <tr>
                    <td class="label-col">Nomor Tender</td>
                    <td class="colon-col">:</td>
                    <td>{t_data['Nomor Tender']}</td>
                    <td class="label-col">Tanggal Purchase Order</td>
                    <td class="colon-col">:</td>
                    <td>{t_data['Tanggal PO']}</td>
                </tr>
                <tr>
                    <td class="label-col">Tanggal Proforma</td>
                    <td class="colon-col">:</td>
                    <td>{t_data['Tanggal PI']}</td>
                    <td class="label-col">Mata Uang</td>
                    <td class="colon-col">:</td>
                    <td>{t_data['Mata Uang']}</td>
                </tr>
            </table>
            <table class="data-table">
                <tr>
                    <th>No.</th>
                    <th>Kategori</th>
                    <th>Spesifikasi / Deskripsi</th>
                    <th>Qty Out</th>
                    <th>Unit</th>
                    <th>Tanggal Mulai</th>
                    <th>Tanggal Selesai</th>
                    <th>Harga Satuan (Rp)</th>
                    <th>Total Harga (Rp)</th>
                    <th>Keterangan</th>
                </tr>
                <tr>
                    <td style="text-align: center;">1</td>
                    <td>{t_data.get('Kategori', '-')}</td>
                    <td>{t_data['Deskripsi Pekerjaan']}</td>
                    <td style="text-align: center;">{t_data['Qty']:,.2f}</td>
                    <td style="text-align: center;">{t_data['Unit']}</td>
                    <td style="text-align: center;">{t_data.get('Tanggal Mulai', '-')}</td>
                    <td style="text-align: center;">{t_data.get('Tanggal Selesai', '-')}</td>
                    <td style="text-align: right;">Rp {t_data['Harga Satuan']:,.2f}</td>
                    <td style="text-align: right;">Rp {t_data['Total Harga']:,.2f}</td>
                    <td>{t_data['Keterangan']}</td>
                </tr>
            </table>
            <p style="text-align: right; font-weight: bold; font-size: 13px;">TOTAL TAGIHAN: Rp {t_data['Total Harga']:,.2f}</p>
            <br>
            <table style="border: none; width: 100%; margin-top: 30px;">
                <tr>
                    <td style="border: none; text-align: center; width: 50%;">
                        <b>DIBUAT OLEH</b><br><br><br><br>
                        <u>Yanuar Wiranata / Ireine Langi</u><br>Supervisor
                    </td>
                    <td style="border: none; text-align: center; width: 50%;">
                        <b>DIPERIKSA</b><br><br><br><br>
                        <u>Onesimus Suriadi</u><br>Manager General Services
                    </td>
                </tr>
            </table>
            """
        else:
            html_content += f"""
            <p><b>Nomor Kontrak:</b> {t_data['Nomor Kontrak']}</p>
            <p><b>Nama Kontrak:</b> {t_data['Nama Kontrak']}</p>
            <p><b>Nilai Transaksi:</b> Rp {t_data['Total Harga']:,.2f}</p>
            <p>Dokumen resmi untuk <b>{doc_type}</b> telah terbit berdasarkan data transaksi sistem PT. Banggai Sentral Sulawesi.</p>
            """

        html_content += "</body></html>"

        st.markdown('<div class="document-preview">', unsafe_allow_html=True)
        st.components.v1.html(html_content, height=500, scrolling=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            b64_html = base64.b64encode(html_content.encode()).decode()
            print_script = f"""
                <script>
                    function printDoc() {{
                        var win = window.open('', '_blank');
                        win.document.write(atob("{b64_html}"));
                        win.document.close();
                        win.focus();
                        setTimeout(function(){{ win.print(); }}, 500);
                    }}
                </script>
                <button onclick="printDoc()" style="width: 100%; background-color: #10b981; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
                    🖨️ Cetak / Print Dokumen (Klik Disini)
                </button>
            """
            st.components.v1.html(print_script, height=50)

        with col_btn2:
            b64_pdf = base64.b64encode(html_content.encode()).decode()
            download_link = f'<a href="data:text/html;base64,{b64_pdf}" download="{doc_type.replace(" ", "_")}_{t_data["PI No."].replace("/", "-")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download Dokumen (Format PDF/HTML)</button></a>'
            st.markdown(download_link, unsafe_allow_html=True)

elif menu == "Lihat Akumulasi Riwayat Transaksi":
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📂 Akumulasi Riwayat Transaksi Rincian Pekerjaan</h3>
        </div>
    """, unsafe_allow_html=True)
    
    tx_records = muat_data_transaksi()
    if tx_records:
        st.dataframe(pd.DataFrame(tx_records), use_container_width=True)
    else:
        st.info("Belum ada riwayat transaksi rincian pekerjaan tersimpan.")