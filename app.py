import streamlit as st
import pandas as pd
import os
import glob
import base64
import sys
from datetime import datetime, date

from modul_dokumen import tkdn

# Menambahkan path untuk pemanggilan folder modul_dokumen
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import fungsi dokumen terisolasi dari folder modul_dokumen
try:
    from modul_dokumen.rincian_pekerjaan import tampilkan_rincian_pekerjaan
    from modul_dokumen.proforma_invoice import tampilkan_proforma_invoice
    from modul_dokumen.bamp import tampilkan_bamp
    from modul_dokumen.bastp import tampilkan_bastp
    from modul_dokumen.wcc import tampilkan_wcc
    from modul_dokumen.tkdn import tampilkan_tkdn
    from modul_dokumen.timesheet import tampilkan_timesheet
    from modul_dokumen.opname_pekerjaan import tampilkan_opname
        
except ImportError:
    pass

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

# --- FUNGSI TERBILANG OTOMATIS ---
def terbilang(n):
    n = int(n)
    if n < 0:
        return "minus " + terbilang(-n)
    
    satuan = ["", "Satu", "Dua", "Tiga", "Empat", "Lima", "Enam", "Tujuh", "Delapan", "Sembilan", "Sepuluh", "Sebelas"]
    
    if n < 12:
        return " " + satuan[n]
    elif n < 20:
        return terbilang(n - 10) + " Belas"
    elif n < 100:
        return terbilang(n // 10) + " Puluh" + terbilang(n % 10)
    elif n < 200:
        return " Seratus" + terbilang(n - 100)
    elif n < 1000:
        return terbilang(n // 100) + " Ratus" + terbilang(n % 100)
    elif n < 2000:
        return " Seribu" + terbilang(n - 1000)
    elif n < 1000000:
        return terbilang(n // 1000) + " Ribu" + terbilang(n % 1000)
    elif n < 1000000000:
        return terbilang(n // 1000000) + " Juta" + terbilang(n % 1000000)
    elif n < 1000000000000:
        return terbilang(n // 1000000000) + " Miliar" + terbilang(n % 1000000000)
    else:
        return " Angka terlalu besar"

# --- SISTEM DIREKTORI & DATABASE LOKAL AMAN ---
DIR_DATABASE = "database_penyimpanan_aman"
if not os.path.exists(DIR_DATABASE):
    os.makedirs(DIR_DATABASE)

EXCEL_INVOICE = os.path.join(DIR_DATABASE, "database_proforma_invoice.xlsx")
EXCEL_TRANSAKSI = os.path.join(DIR_DATABASE, "database_transaksi_rincian.xlsx")
EXCEL_MASTER_REF = os.path.join(DIR_DATABASE, "database_master_referensi.xlsx")

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
    df_baru.to_excel(EXCEL_TRANSAKSI, index=False)
    st.session_state["db_transaksi"] = data_list

def muat_master_referensi():
    if os.path.exists(EXCEL_MASTER_REF):
        try:
            df = pd.read_excel(EXCEL_MASTER_REF)
            if df is not None and not df.empty:
                return df.to_dict(orient="records")
        except:
            pass
    return []

def simpan_master_referensi(data_list):
    waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in data_list:
        if not item.get("Update Terakhir"):
            item["Update Terakhir"] = waktu_sekarang
    df_baru = pd.DataFrame(data_list)
    df_baru.to_excel(EXCEL_MASTER_REF, index=False)
    st.session_state["db_master_ref"] = data_list

# Inisialisasi Session State
if "db_tersimpan" not in st.session_state:
    st.session_state["db_tersimpan"] = muat_data_invoice()

if "db_transaksi" not in st.session_state:
    st.session_state["db_transaksi"] = muat_data_transaksi()

if "db_master_ref" not in st.session_state:
    st.session_state["db_master_ref"] = muat_master_referensi()

if "edit_index" not in st.session_state:
    st.session_state["edit_index"] = None

if "edit_tx_index" not in st.session_state:
    st.session_state["edit_tx_index"] = None

if "edit_master_index" not in st.session_state:
    st.session_state["edit_master_index"] = None

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
    "📁 Modul 0: Master Referensi Harga & Pekerjaan",
    "📁 Modul 1: Database & Master Kontrak",
    "📄 Modul 2: Invoice & Dokumen Turunan"
])

st.sidebar.markdown("---")

if modul_pilihan == "📁 Modul 0: Master Referensi Harga & Pekerjaan":
    menu = st.sidebar.radio("Pilih Menu:", [
        "Input & Kelola Master Referensi",
        "Lihat Daftar Master Referensi Tersimpan"
    ])
elif modul_pilihan == "📁 Modul 1: Database & Master Kontrak":
    menu = st.sidebar.radio("Pilih Menu:", [
        "Input Database & Invoice (29 Kolom)",
        "Lihat Database Tersimpan"
    ])
else:
    menu = st.sidebar.radio("Pilih Menu:", [
        "Input & Proses Rincian Pekerjaan",
        "Pratinjau, Cetak & Download PDF Dokumen",
        "Lihat Akumulasi Riwayat Transaksi"
    ])

st.sidebar.markdown("---")
st.sidebar.success("📂 **Status Sistem:** Terhubung ke Folder Aman (`database_penyimpanan_aman`)")

# =========================================================================
# LOGIKA MODUL 0: MASTER REFERENSI HARGA & PEKERJAAN
# =========================================================================
if modul_pilihan == "📁 Modul 0: Master Referensi Harga & Pekerjaan":
    if menu == "Input & Kelola Master Referensi":
        st.markdown("""
            <div class="dashboard-card">
                <h3 style="margin-top:0; color:#065f46; font-size:18px;">📌 Input & Panggil Kembali Master Referensi Harga Tetap</h3>
            </div>
        """, unsafe_allow_html=True)

        master_data_live = muat_master_referensi()
        opsi_panggil_uraian = ["-- Buat Data Referensi Baru --"] + [f"{m.get('Uraian Pekerjaan', '')[:60]}... (Kontrak: {m.get('Nomor Kontrak','')})" for m in master_data_live]
        
        col_p_ref, col_b_ref = st.columns([3, 1])
        with col_p_ref:
            pilihan_panggil_uraian = st.selectbox("Panggil Ulang Berdasarkan Uraian Pekerjaan:", opsi_panggil_uraian)
        with col_b_ref:
            if st.button("🔄 Panggil Data Ini"):
                if pilihan_panggil_uraian == "-- Buat Data Referensi Baru --":
                    st.session_state["edit_master_index"] = None
                else:
                    for idx, m in enumerate(master_data_live):
                        prefix_Str = f"{m.get('Uraian Pekerjaan', '')[:60]}... (Kontrak: {m.get('Nomor Kontrak','')})"
                        if prefix_Str == pilihan_panggil_uraian:
                            st.session_state["edit_master_index"] = idx
                            break
                st.rerun()

        def_ref = {}
        if st.session_state["edit_master_index"] is not None and st.session_state["edit_master_index"] < len(master_data_live):
            def_ref = master_data_live[st.session_state["edit_master_index"]]
            st.info("📋 **Mode Edit Aktif:** Anda sedang mengubah data referensi yang dipanggil.")

        saved_db = muat_data_invoice()
        list_kontrak_db = list(set([str(item.get("Nomor Kontrak", "")) for item in saved_db if item.get("Nomor Kontrak")]))

        with st.form("form_master_referensi"):
            col1, col2 = st.columns(2)
            with col1:
                def_kontrak_val = def_ref.get("Nomor Kontrak", list_kontrak_db[0] if list_kontrak_db else "")
                nomor_kontrak_ref = st.text_input("Nomor Kontrak Rujukan", value=def_kontrak_val)
                
                kat_opts = ["MONTHLY BASIS", "ON-CALL BASIS", "JASA MOBILISASI", "PROFESSIONAL SUM", "LAINNYA"]
                def_kat_val = def_ref.get("Kategori", kat_opts[0])
                idx_kat_ref = kat_opts.index(def_kat_val) if def_kat_val in kat_opts else 0
                kategori_ref = st.selectbox("Kategori Pekerjaan", kat_opts, index=idx_kat_ref)
                
                unit_opts = ["Month", "Day", "Ls", "Unit", "Trip", "Jam"]
                def_unit_val = def_ref.get("Unit", unit_opts[0])
                idx_unit_ref = unit_opts.index(def_unit_val) if def_unit_val in unit_opts else 0
                unit_ref = st.selectbox("Satuan Unit", unit_opts, index=idx_unit_ref)
            with col2:
                uraian_ref = st.text_area("Uraian Pekerjaan / Spesifikasi Alat", value=def_ref.get("Uraian Pekerjaan", ""), height=105)
                harga_satuan_ref = st.number_input("Harga Satuan Tetap (Rp)", min_value=0.0, value=float(def_ref.get("Harga Satuan", 0.0)), step=1000.0, format="%.2f")

            st.markdown("---")
            col_sb1, col_sb2 = st.columns(2)
            with col_sb1:
                submit_master_baru = st.form_submit_button("💾 Simpan Master Baru")
            with col_sb2:
                submit_master_update = st.form_submit_button("📝 Update Data Dipanggil / Save As")

            if submit_master_baru or submit_master_update:
                if not nomor_kontrak_ref or not uraian_ref:
                    st.error("⚠️ Nomor Kontrak dan Uraian Pekerjaan tidak boleh kosong!")
                else:
                    master_data = muat_master_referensi()
                    item_baru = {
                        "Nomor Kontrak": nomor_kontrak_ref,
                        "Kategori": kategori_ref,
                        "Uraian Pekerjaan": uraian_ref,
                        "Unit": unit_ref,
                        "Harga Satuan": harga_satuan_ref,
                        "Update Terakhir": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    if submit_master_update and st.session_state["edit_master_index"] is not None and st.session_state["edit_master_index"] < len(master_data):
                        master_data[st.session_state["edit_master_index"]] = item_baru
                        st.success("✨ Data Master Referensi berhasil di-update!")
                    else:
                        master_data.append(item_baru)
                        st.success("🎉 Data Master Referensi baru berhasil disimpan!")
                    
                    simpan_master_referensi(master_data)
                    st.session_state["edit_master_index"] = None
                    st.rerun()

    elif menu == "Lihat Daftar Master Referensi Tersimpan":
        st.markdown("""
            <div class="dashboard-card">
                <h3 style="margin-top:0; color:#065f46; font-size:18px;">📂 Tabel Master Referensi Harga & Pekerjaan (Tampilan Satu Baris)</h3>
            </div>
        """, unsafe_allow_html=True)

        master_records = muat_master_referensi()
        if master_records:
            for idx, item in enumerate(master_records):
                c_no, c_kon, c_kat, c_pek, c_unit, c_hrg, c_act1, c_act2 = st.columns([0.6, 1.8, 1.8, 4.0, 0.8, 1.5, 0.7, 0.7])
                c_no.write(f"**{idx+1}**")
                c_kon.write(str(item.get('Nomor Kontrak', '')))
                c_kat.write(str(item.get('Kategori', '')))
                c_pek.write(str(item.get('Uraian Pekerjaan', '')))
                c_unit.write(str(item.get('Unit', '')))
                c_hrg.write(f"Rp {item.get('Harga Satuan', 0):,.2f}")
                
                with c_act1:
                    if st.button("✏️", key=f"edit_m_{idx}", help="Edit baris ini"):
                        st.session_state["edit_master_index"] = idx
                        st.rerun()
                with c_act2:
                    if st.button("🗑️", key=f"del_m_{idx}", help="Hapus baris ini"):
                        master_records.pop(idx)
                        simpan_master_referensi(master_records)
                        st.rerun()
                st.markdown("<hr style='margin:4px 0; border-color:#e2e8f0;'>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Reset / Hapus Semua Master Referensi"):
                if os.path.exists(EXCEL_MASTER_REF):
                    os.remove(EXCEL_MASTER_REF)
                st.session_state["db_master_ref"] = []
                st.success("Semua data master berhasil direset.")
                st.rerun()
        else:
            st.info("Belum ada data master referensi tersimpan di folder aman.")

# =========================================================================
# LOGIKA MODUL 1: DATABASE & MASTER KONTRAK
# =========================================================================
elif modul_pilihan == "📁 Modul 1: Database & Master Kontrak":
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
            st.info("📌 Belum ada data database tersimpan di folder aman.")

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

                current_data = muat_data_invoice()

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
                <h3 style="margin-top:0; color:#065f46; font-size:18px;">📂 Daftar Database Identifikasi Tersimpan (Dengan Penomoran Kolom Presisi)</h3>
            </div>
        """, unsafe_allow_html=True)
        
        saved_records = muat_data_invoice()
        if len(saved_records) > 0:
            df_saved = pd.DataFrame(saved_records)
            
            # Bersihkan kolom Update Terakhir
            if "Update Terakhir" in df_saved.columns:
                df_saved = df_saved.drop(columns=["Update Terakhir"])
                
            # Susun prioritas kolom
            cols_prioritas = ["Proforma Invoice No.", "Nomor Kontrak", "Nomor Tender", "Lingkup Pekerjaan"]
            sisa_cols = [c for c in df_saved.columns if c not in cols_prioritas]
            df_saved = df_saved[[c for c in cols_prioritas if c in df_saved.columns] + sisa_cols]
            
            # MEMBERIKAN PENOMORAN URUT PADA NAMA KOLOM (HEADER)
            df_saved.columns = [f"{i}: {col}" for i, col in enumerate(df_saved.columns)]
            
            st.dataframe(df_saved, use_container_width=True)
        else:
            st.info("Belum ada data database identifikasi di dalam folder penyimpanan aman.")

        # TOMBOL HAPUS EKSKLUSIF DI MODUL 1 -> LIHAT DATABASE TERSIMPAN
        st.markdown("---")
        st.markdown("#### 🗑️ Pengelolaan Data: Hapus Baris yang Salah / Duplikat")

        try:
            current_db_list = muat_data_invoice()
        except:
            current_db_list = []

        if current_db_list:
            pilihan_hapus = []
            for idx, item in enumerate(current_db_list):
                pi_val = str(item.get('Proforma Invoice No.') or item.get('PI No.') or 'Tanpa Nomor PI')
                kontrak_val = str(item.get('Nomor Kontrak') or 'Tanpa Kontrak')
                pilihan_hapus.append(f"Index {idx} | PI: {pi_val} | Kontrak: {kontrak_val}")

            col_h1, col_h2 = st.columns([2, 1])
            with col_h1:
                target_hapus_idx = st.selectbox(
                    "Pilih Baris Data yang Ingin Dihapus Secara Permanen:",
                    range(len(pilihan_hapus)),
                    format_func=lambda x: pilihan_hapus[x],
                    key="select_row_to_delete_saved"
                )
            with col_h2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("❌ Hapus Baris Terpilih", use_container_width=True, type="primary"):
                    try:
                        deleted_item = current_db_list.pop(target_hapus_idx)
                        simpan_data_invoice(current_db_list)
                        pi_terhapus = deleted_item.get('Proforma Invoice No.') or deleted_item.get('PI No.') or 'Baris Kosong'
                        st.success(f"✅ Berhasil menghapus data (PI: {pi_terhapus}) secara permanen!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Terjadi kesalahan saat menghapus data: {e}")
# =========================================================================
# LOGIKA MODUL 2: INVOICE & DOKUMEN TURUNAN
# =========================================================================
elif modul_pilihan == "📄 Modul 2: Invoice & Dokumen Turunan":
    if menu == "Input & Proses Rincian Pekerjaan":
        st.markdown("""
            <div class="dashboard-card">
                <h3 style="margin-top:0; color:#065f46; font-size:18px;">📝 Lembar Kerja & Pemrosesan Rincian Pekerjaan</h3>
            </div>
        """, unsafe_allow_html=True)

        saved_db = muat_data_invoice()
        master_ref_data = muat_master_referensi()
        
        if not saved_db:
            st.warning("⚠️ Belum ada data di Database Modul 1. Harap lakukan input data kontrak & PI terlebih dahulu pada Modul 1.")
        elif not master_ref_data:
            st.warning("⚠️ Belum ada data di Master Referensi Harga (Modul 0). Silakan input data harga tetap di Modul 0 terlebih dahulu.")
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
                alamat_pihak_pertama = matched_record.get("Alamat Pihak Pertama", "")
                jangka_waktu = matched_record.get("Jangka Waktu Kontrak", "")
            
            with col2:
                nomor_po = st.text_input("Nomor PO", matched_record.get("Nomor Purchase Order", ""))
                tanggal_po = st.text_input("Tanggal PO", matched_record.get("Tanggal Purchase Order", ""))
                mata_uang = st.text_input("Mata Uang", "IDR")
                desc_po = st.text_area("Lingkup Pekerjaan", matched_record.get("Lingkup Pekerjaan", ""))

            st.markdown("---")
            st.markdown("#### ⚙️ Pengaturan Khusus Bank & Pembayaran Proforma Invoice")
            
            pilihan_bank_preset = [
                "BANK RAKYAT INDONESIA (PERSERO) Tbk.",
                "BANK MANDIRI (PERSERO) Tbk.",
                "BANK NEGARA INDONESIA (PERSERO) Tbk.",
                "BANK BCA (CENTRAL ASIA)",
                "-- Ketik Manual Sendiri --"
            ]
            
            c_bank1, c_bank2 = st.columns(2)
            with c_bank1:
                pilih_preset_bank = st.selectbox("Pilih Bank Cepat", pilihan_bank_preset)
                if pilih_preset_bank == "-- Ketik Manual Sendiri --":
                    bank_name = st.text_input("Nama Bank Manual", value=get_tval("Bank Name", ""))
                else:
                    bank_name = pilih_preset_bank
                    st.text_input("Nama Bank Terpilih", value=bank_name, disabled=True)
                
                bank_branch = st.text_input("Cabang Bank", value=get_tval("Bank Branch", "Cabang Luwuk"))
            with c_bank2:
                bank_acc_no = st.text_input("Nomor Rekening", value=get_tval("Account No", "0167 0167 8888 303"))
                bank_acc_name = st.text_input("Atas Nama Rekening", value=get_tval("Account Name", "PT. BANGGAI SENTRAL SULAWESI"))
                attn_to = st.text_input("Attn. (Penerima Invoice)", value=get_tval("Attn", "Accounts Payable - Finance Department"))
                persen_val = st.number_input("Persentase Tagihan (%)", min_value=1.0, max_value=100.0, value=float(get_tval("Percent", 100.0)))

            st.markdown("---")
            st.markdown("#### ⚙️ Pemilihan Kategori & Uraian Pekerjaan (Dinamis & Terhubung)")
            
            df_ref = pd.DataFrame(master_ref_data)
            df_ref_kontrak = df_ref[df_ref["Nomor Kontrak"].astype(str).str.strip() == str(selected_kontrak).strip()]
            if df_ref_kontrak.empty:
                df_ref_kontrak = df_ref 

            list_kat = df_ref_kontrak["Kategori"].dropna().unique().tolist()
            def_kat = get_tval("Kategori", list_kat[0] if list_kat else "")
            idx_kat = list_kat.index(def_kat) if def_kat in list_kat else 0
            kategori_pilih = st.selectbox("Kategori Pekerjaan", list_kat if list_kat else ["-"], index=idx_kat)

            df_filtered_kat = df_ref_kontrak[df_ref_kontrak["Kategori"].astype(str).str.strip() == str(kategori_pilih).strip()]
            list_spek = df_filtered_kat["Uraian Pekerjaan"].dropna().unique().tolist() if not df_filtered_kat.empty else df_ref_kontrak["Uraian Pekerjaan"].dropna().unique().tolist()
            
            def_spek = get_tval("Deskripsi Pekerjaan", list_spek[0] if list_spek else "")
            idx_spek = list_spek.index(def_spek) if def_spek in list_spek else 0
            deskripsi_pekerjaan = st.selectbox("Uraian Pekerjaan / Spesifikasi", list_spek if list_spek else ["-"], index=idx_spek)

            harga_satuan_otomatis = 0.0
            unit_otomatis = "Month"

            if not df_filtered_kat.empty:
                matched_row = df_filtered_kat[df_filtered_kat["Uraian Pekerjaan"].astype(str).str.strip() == str(deskripsi_pekerjaan).strip()]
                if not matched_row.empty:
                    row_m = matched_row.iloc[0]
                    try:
                        harga_satuan_otomatis = float(row_m.get("Harga Satuan", 0.0))
                    except:
                        harga_satuan_otomatis = 0.0
                    unit_otomatis = str(row_m.get("Unit", "Month"))

            with st.form("form_proses_rincian_sub"):
                c_item1, c_item2, c_item3, c_item4 = st.columns([1, 1, 1, 1])
                with c_item1:
                    qty = st.number_input("Qty Out", value=float(get_tval("Qty", 1.0)))
                with c_item2:
                    def_unit = get_tval("Unit", unit_otomatis)
                    u_opts = ["Month", "Day", "Ls", "Unit", "Trip", "Jam"]
                    idx_u = u_opts.index(def_unit) if def_unit in u_opts else 0
                    unit = st.selectbox("Unit", u_opts, index=idx_u)
                with c_item3:
                    tgl_mulai = st.date_input("Tanggal Mulai", value=date(2026, 7, 1))
                with c_item4:
                    tgl_selesai = st.date_input("Tanggal Selesai", value=date(2026, 7, 31))

                def_hs = float(get_tval("Harga Satuan", harga_satuan_otomatis))
                
                st.markdown(f"""
                    <div style="font-weight:600; font-size:13px; margin-bottom:5px; color:#0f172a;">Harga Satuan Tetap (Rp - Dinamis Mengikuti Uraian Terpilih)</div>
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
                    total_harga = (qty * harga_satuan) * (persen_val / 100.0)
                    data_transaksi = {
                        "Nomor Kontrak": selected_kontrak,
                        "Nama Kontrak": nama_kontrak,
                        "Nomor Tender": nomor_tender,
                        "PI No.": selected_pi,
                        "Tanggal PI": tanggal_pi,
                        "Ditujukan Kepada": ditujukan_kepada,
                        "Alamat Pihak Pertama": alamat_pihak_pertama,
                        "Jangka Waktu Kontrak": jangka_waktu,
                        "Nomor PO": nomor_po,
                        "Deskripsi PO": desc_po,
                        "Tanggal PO": tanggal_po,
                        "Mata Uang": mata_uang,
                        "Kategori": kategori_pilih,
                        "Deskripsi Pekerjaan": deskripsi_pekerjaan,
                        "Qty": qty,
                        "Unit": unit,
                        "Percent": persen_val,
                        "Tanggal Mulai": tgl_mulai.strftime("%d %b %Y"),
                        "Tanggal Selesai": tgl_selesai.strftime("%d %b %Y"),
                        "Harga Satuan": harga_satuan,
                        "Total Harga": total_harga,
                        "Bank Name": bank_name,
                        "Bank Branch": bank_branch,
                        "Account No": bank_acc_no,
                        "Account Name": bank_acc_name,
                        "Attn": attn_to,
                        "Keterangan": keterangan_pekerjaan,
                        "Update Terakhir": waktu_aksi
                    }
                    
                    existing_tx = muat_data_transaksi()
                    pi_baru = str(selected_pi).strip()
                    existing_tx = [t for t in existing_tx if str(t.get("PI No.")).strip() != pi_baru]
                    existing_tx.append(data_transaksi)
                    simpan_data_transaksi(existing_tx)
                    
                    st.session_state["edit_tx_index"] = None
                    st.success(f"🎉 Data Transaksi untuk PI [{pi_baru}] Berhasil Diproses & Disimpan!")

    elif menu == "Pratinjau, Cetak & Download PDF Dokumen":
        transaksi_list = muat_data_transaksi()
        if not transaksi_list:
            st.warning("⚠️ Belum ada data transaksi rincian pekerjaan yang diproses di Modul 2. Silakan input transaksi terlebih dahulu.")
        else:
            doc_type = st.selectbox("Pilih Jenis Dokumen Resmi:", [
                "Rincian Pekerjaan",
                "Proforma Invoice",
                "Berita Acara Mulai Pekerjaan (BAMP)",
                "Berita Acara Selesai Pekerjaan (BASTP)",
                "Work Completion Certificate (WCC)",
                "Berita Acara Mulai & Selesai Pekerjaan (BASTP)",
                "Formulir tkdn",
                "Timesheet Peralatan",
                "Berita Acara Opname pekerjaan",
            ])

            # Pemanggilan Modul Terisolasi Berdasarkan Data Excel Riil
            if doc_type == "Rincian Pekerjaan":
                tampilkan_rincian_pekerjaan(transaksi_list)
            elif doc_type == "Proforma Invoice":
                tampilkan_proforma_invoice(transaksi_list)
            elif doc_type == "Berita Acara Mulai Pekerjaan (BAMP)":
                 tampilkan_bamp(transaksi_list)
            elif doc_type == "Berita Acara Mulai & Selesai Pekerjaan (BASTP)" or doc_type == "Berita Acara Selesai Pekerjaan (BASTP)":
                 tampilkan_bastp(transaksi_list)
            elif doc_type == "Work Completion Certificate (WCC)":
                 tampilkan_wcc(transaksi_list)
            elif doc_type.lower() == "formulir tkdn":
                 tkdn.tampilkan_tkdn(transaksi_list)
            elif doc_type == "Berita Acara Opname pekerjaan":
                 tampilkan_opname(transaksi_list)
            elif doc_type.lower() == "timesheet peralatan" or doc_type.lower() == "timesheet":
                 tampilkan_timesheet(transaksi_list)

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
