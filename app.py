import streamlit as st
import pandas as pd
import os
import sys
import io
import base64
from datetime import datetime, timedelta, date
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Menambahkan path folder root dan modul
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# --- IMPORT KONEKSI DATABASE MYSQL ---
try:
    from db_connection import muat_data_from_db, simpan_data_to_db
except ImportError as e:
    st.error(f"Gagal memuat db_connection: {e}")

# --- IMPORT MODUL INPUT TERPISAH (MODULAR) ---
try:
    from modul_input.modul_0_referensi import tampilkan_modul_0_referensi
except ImportError as e:
    st.error(f"Gagal memuat modul_0_referensi: {e}")

try:
    from modul_input.modul_1_database import tampilkan_modul_1_database
except ImportError as e:
    st.error(f"Gagal memuat modul_1_database: {e}")

try:
    from modul_input.modul_2_rincian import tampilkan_modul_2_rincian
except ImportError as e:
    st.error(f"Gagal memuat modul_2_rincian: {e}")

try:
    from modul_input.modul_2_akumulasi import tampilkan_akumulasi_riwayat_transaksi
except ImportError as e:
    st.error(f"Gagal memuat modul_2_akumulasi: {e}")

# --- IMPORT MODUL DOKUMEN & KEUANGAN ---
try:
    from modul_dokumen.rincian_pekerjaan import tampilkan_rincian_pekerjaan
except ImportError: pass

try:
    from modul_dokumen.proforma_invoice import tampilkan_proforma_invoice
except ImportError: pass

try:
    from modul_dokumen.bamp import tampilkan_bamp
except ImportError: pass

try:
    from modul_dokumen.basp import tampilkan_basp
except ImportError: pass

try:
    from modul_dokumen.wcc import tampilkan_wcc
except ImportError: pass

try:
    from modul_dokumen.tkdn import tampilkan_tkdn
except ImportError: pass

try:
    from modul_dokumen.timesheet import tampilkan_timesheet
except ImportError: pass

try:
    from modul_dokumen.opname_pekerjaan import tampilkan_opname
except ImportError: pass

try:
    from modul_dokumen.bastb import tampilkan_bastb
except ImportError: pass

try:
    from modul_dokumen.arsip_pendukung import tampilkan_arsip_pendukung
except ImportError: pass

try:
    from modul_dokumen.paket_dokumen_lengkap import tampilkan_paket_lengkap
except ImportError: pass

try:
    from modul_dokumen.rekap_transaksi import tampilkan_rekap_transaksi
except ImportError: pass

try:
    from modul_keuangan.faktur_pajak import tampilkan_faktur_pajak
except ImportError: pass

try:
    from modul_keuangan.pemantauan_pembayaran import tampilkan_pemantauan_pembayaran
except ImportError: pass

try:
    from modul_keuangan.modul_billing_tax import tampilkan_billing_tax
except ImportError: pass

# --- IMPORT MODUL KEAMANAN (AUTENTIKASI & PANEL MANAJEMEN) ---
try:
    from modul_keamanan.autentikasi import (
        form_login_sistem, 
        render_panel_manajemen_akun
    )
except ImportError as e:
    st.error(f"Gagal memuat modul autentikasi: {e}")

# --- KONFIGURASI HALAMAN STREAMLIT ---
st.set_page_config(page_title="Dashboard Terintegrasi - PT. BANGGAI SENTRAL SULAWESI", layout="wide", initial_sidebar_state="expanded")

# --- PERSISTENT SESSION STATE (MENCEGAH TERLEMPAR KE LOGIN SAAT REFRESH) ---
query_params = st.query_params
if query_params.get("session") == "active_bss_corporate" and query_params.get("user"):
    st.session_state["logged_in"] = True
    st.session_state["current_user"] = query_params.get("user")

# --- UTILS & HELPER FUNCTIONS ---
def bersih_angka(val):
    if val is None: return ""
    s = str(val).strip()
    if s.endswith(".0"): s = s[:-2]
    if s.lower() == "nan": return ""
    return s

def sort_pi_key(pi_str):
    try:
        parts = str(pi_str).split('/')
        if parts:
            digits = "".join([c for c in parts[0] if c.isdigit()])
            return int(digits) if digits else 0
    except: pass
    return 0

def parse_date_safely(val_str):
    if not val_str or str(val_str).strip().lower() == "nan": return date.today()
    val_cleaned = str(val_str).strip()
    formats = ["%d %b %Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%b %d, %Y", "%d %B %Y", "%Y-%m-%d %H:%M:%S"]
    for fmt in formats:
        try: return datetime.strptime(val_cleaned, fmt).date()
        except ValueError: continue
    try: return pd.to_datetime(val_cleaned).date()
    except: pass
    return date.today()

# --- MAPPING HEADER RESMI KANTOR (31 KOLOM) ---
MAPPING_HEADER_INVOICE = {
    "0": "Proforma Invoice No.", "1": "Nomor Kontrak", "2": "Nomor Tender", "3": "Lingkup Pekerjaan",
    "4": "Tanggal Kontrak", "5": "Jangka Waktu Kontrak", "6": "Tanggal Performa Invoice", "7": "Judul Kontrak",
    "8": "Nomor Purchase Order", "9": "Tanggal Purchase Order", "10": "Pihak Pertama", "11": "Alamat Pihak Pertama",
    "12": "Diwakili Oleh", "13": "Selaku", "14": "Pihak Kedua", "15": "Alamat Pihak Kedua", "16": "Diwakili Oleh (P2)",
    "17": "Selaku (P2)", "18": "Periode Pekerjaan", "19": "Nomor WCC", "20": "Tanggal WCC", "21": "Nomor WO",
    "22": "Keterangan WO", "23": "Nomor CTR", "24": "Progress Pekerjaan", "25": "Prepared by Name",
    "26": "Prepared by Title", "27": "Approved by 1", "28": "Approved by Title 1", "29": "Approved by 2", "30": "Approved by Title 2"
}
REVERSE_MAPPING_HEADER = {v: k for k, v in MAPPING_HEADER_INVOICE.items()}

# --- TABEL DATABASE MYSQL ---
TABEL_DB_INVOICE = "database_proforma_invoice"
TABEL_DB_TRANSAKSI = "database_transaksi_rincian"
TABEL_DB_MASTER_REF = "database_master_referensi"
TABEL_DB_BANK = "database_master_bank"

def muat_data_invoice():
    db_data = muat_data_from_db(TABEL_DB_INVOICE)
    if db_data:
        normalized_records = []
        for rec in db_data:
            new_rec = {}
            for k, v in rec.items():
                val_c = bersih_angka(v) if pd.notnull(v) else ""
                key_str = str(k).strip()
                idx_key = REVERSE_MAPPING_HEADER.get(key_str, key_str)
                try: new_rec[int(idx_key)] = val_c
                except ValueError: new_rec[idx_key] = val_c
            normalized_records.append(new_rec)
        st.session_state["db_tersimpan"] = normalized_records
        return normalized_records
    return st.session_state.get("db_tersimpan", [])

def simpan_data_invoice(data_list):
    waktu_sekarang = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
    processed_data = []
    for item in data_list:
        if isinstance(item, dict):
            item_copy = item.copy()
            item_copy["Update Terakhir"] = waktu_sekarang
            formatted_item = {}
            for k, v in item_copy.items():
                key_str = str(k).strip()
                header_name = MAPPING_HEADER_INVOICE.get(key_str, key_str)
                formatted_item[header_name] = bersih_angka(v) if pd.notnull(v) else ""
            processed_data.append(formatted_item)
    success = simpan_data_to_db(TABEL_DB_INVOICE, processed_data)
    if success:
        st.session_state["db_tersimpan"] = data_list
        return True
    return False

def muat_data_transaksi():
    db_data = muat_data_from_db(TABEL_DB_TRANSAKSI)
    if db_data:
        st.session_state["db_transaksi"] = db_data
        return db_data
    return st.session_state.get("db_transaksi", [])

def simpan_data_transaksi(data_list):
    waktu_sekarang = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
    processed_tx = []
    for item in data_list:
        if isinstance(item, dict):
            item_copy = item.copy()
            item_copy["Update Terakhir"] = waktu_sekarang
            for k, v in item_copy.items():
                if pd.isnull(v) or str(v).strip().lower() == "nan":
                    if k not in ['Qty', 'Harga Satuan', 'Total Harga', 'Percent']: 
                        item_copy[k] = ""
            processed_tx.append(item_copy)
    success = simpan_data_to_db(TABEL_DB_TRANSAKSI, processed_tx)
    if success:
        st.session_state["db_transaksi"] = data_list
        return True
    return False

def muat_master_referensi():
    db_data = muat_data_from_db(TABEL_DB_MASTER_REF)
    if db_data:
        st.session_state["db_master_ref"] = db_data
        return db_data
    return st.session_state.get("db_master_ref", [])

def simpan_master_referensi(data_list):
    waktu_sekarang = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
    for item in data_list:
        if isinstance(item, dict):
            item["Update Terakhir"] = waktu_sekarang
            for k, v in item.items():
                if pd.isnull(v) or str(v).strip().lower() == "nan":
                    if k != 'Harga Satuan': item[k] = ""
    success = simpan_data_from_db(TABEL_DB_MASTER_REF, data_list)
    if success:
        st.session_state["db_master_ref"] = data_list
        return True
    return False

def muat_master_bank():
    default_banks = [{"Bank Name": "BANK RAKYAT INDONESIA (PERSERO) Tbk.", "Bank Branch": "Cabang Luwuk", "Account No": "0167 0167 8888 303", "Account Name": "PT. BANGGAI SENTRAL SULAWESI", "Attn": "Accounts Payable - Finance Department"}]
    db_data = muat_data_from_db(TABEL_DB_BANK)
    if db_data:
        st.session_state["db_master_bank"] = db_data
        return db_data
    return st.session_state.get("db_master_bank", default_banks)

def simpan_master_bank(data_list):
    success = simpan_data_to_db(TABEL_DB_BANK, data_list)
    if success:
        st.session_state["db_master_bank"] = data_list
        return True
    return False

# --- LOAD DATA KETIKA APLIKASI PERTAMA BUKA ---
st.session_state["db_tersimpan"] = muat_data_invoice()
st.session_state["db_transaksi"] = muat_data_transaksi()
st.session_state["db_master_ref"] = muat_master_referensi()
st.session_state["db_master_bank"] = muat_master_bank()

# --- AUTENTIKASI LOGIN KREDENSIAL DENGAN PERSISTEN URL ---
if form_login_sistem():
    if st.session_state.get("logged_in", False) and st.session_state.get("current_user"):
        st.query_params["session"] = "active_bss_corporate"
        st.query_params["user"] = st.session_state.get("current_user")

    user_role = str(st.session_state.get('current_role', 'Staff')).strip().lower()
    
    # Penanda khusus hak akses
    is_management = user_role in ["management", "direksi"]
    is_finance_tax = user_role in ["finance & tax", "finance", "tax"]
    is_project_manager = user_role in ["project manager", "pm"]
    is_project_support = user_role in ["project support"]
    is_admin_support = user_role in ["admin support"]
    is_super_admin = user_role in ["super admin", "admin"]

    # Injeksi session state global untuk izin modul privat arsip dokumen
    is_privileged_role = is_super_admin or is_finance_tax or is_project_manager or is_management
    st.session_state["is_privileged_role"] = is_privileged_role

    # Styling CSS UI Rapi & Tegas
    st.markdown("""
        <style>
        .stApp { background-color: #f8fafc; color: #0f172a; font-size: 15px !important; }
        label, .stSelectbox label, .stTextInput label, .stNumberInput label, .stDateInput label, .stTextArea label { color: #0f172a !important; font-weight: 700 !important; font-size: 14px !important; }
        div[data-baseweb="base-input"], div[data-baseweb="textarea"], div[data-baseweb="select"] { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; color: #000000 !important; font-size: 14px !important; }
        input, textarea { background-color: #ffffff !important; color: #000000 !important; font-size: 14px !important; }
        .company-header-centered { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #ffffff; padding: 18px 25px; border-radius: 10px; text-align: center; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-bottom: 3px solid #10b981; margin-bottom: 25px; }
        .stButton>button { width: 100%; border-radius: 6px; font-weight: 600; font-size: 14px !important; background-color: #10b981; color: white; }
        .stButton>button:hover { background-color: #059669; color: white; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="company-header-centered">
            <h2 style="margin:0; font-size: 24px; font-weight: 700; color: #ffffff;">PT. BANGGAI SENTRAL SULAWESI</h2>
            <p style="margin:4px 0 0 0; font-size: 13px; color: #34d399; font-weight: 500;">General Contractor and Suppliers | Dashboard Terintegrasi Utama (Cloud MySQL)</p>
        </div>
    """, unsafe_allow_html=True)

    # --- SIDEBAR NAVIGASI BERDASARKAN ROLE KREDENSIAL ---
    st.sidebar.markdown("### 🗂️ Navigasi Dashboard Utama")
    st.sidebar.markdown(f"🕒 **Waktu Sistem (WITA):**<br>`{(datetime.utcnow() + timedelta(hours=8)).strftime('%d %b %Y, %H:%M:%S')}`", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    daftar_modul_tersedia = []

    if is_admin_support:
        daftar_modul_tersedia = ["Timesheet Peralatan", "📁 Arsip Dokumen Customer & Pendukung"]
    elif is_finance_tax:
        daftar_modul_tersedia = ["💰 Modul 3: Invoice & Tax Management", "📁 Arsip Dokumen Customer & Pendukung"]
    elif is_project_manager:
        daftar_modul_tersedia = [
            "📁 Modul 1: Database & Master Kontrak", 
            "📄 Modul 2: Invoice & Dokumen Turunan", 
            "💰 Modul 3: Invoice & Tax Management",
            "📁 Arsip Dokumen Customer & Pendukung"
        ]
    elif is_project_support:
        daftar_modul_tersedia = ["📁 Modul 1: Database & Master Kontrak", "📄 Modul 2: Invoice & Dokumen Turunan", "📁 Arsip Dokumen Customer & Pendukung"]
    elif is_management:
        daftar_modul_tersedia = [
            "💰 Modul 3: Invoice & Tax Management",
            "📄 Modul 2: Invoice & Dokumen Turunan",
            "📁 Arsip Dokumen Customer & Pendukung"
        ]
    else: 
        daftar_modul_tersedia = [
            "📁 Modul 0: Master Referensi Harga & Pekerjaan",
            "📁 Modul 1: Database & Master Kontrak",
            "📄 Modul 2: Invoice & Dokumen Turunan",
            "💰 Modul 3: Invoice & Tax Management",
            "📁 Arsip Dokumen Customer & Pendukung"
        ]

    if is_super_admin:
        daftar_modul_tersedia.append("⚙️ Manajemen Akun & Hak Akses")

    # --- SINKRONISASI URL QUERY PARAMS UNTUK MODUL UTAMA ---
    url_modul = st.query_params.get("modul", None)
    if url_modul and url_modul in daftar_modul_tersedia:
        default_modul_idx = daftar_modul_tersedia.index(url_modul)
    else:
        default_modul_idx = 0

    if "nav_modul_utama" not in st.session_state or st.session_state["nav_modul_utama"] not in daftar_modul_tersedia:
        st.session_state["nav_modul_utama"] = daftar_modul_tersedia[default_modul_idx]

    modul_pilihan = st.sidebar.selectbox("Pilih Modul Utama:", daftar_modul_tersedia, key="nav_modul_utama")
    st.query_params["modul"] = modul_pilihan

    st.sidebar.markdown("---")

    # --- SINKRONISASI URL QUERY PARAMS UNTUK SUB-MENU ---
    if is_admin_support and modul_pilihan == "Timesheet Peralatan": 
        menu = "Timesheet"
    elif modul_pilihan == "⚙️ Manajemen Akun & Hak Akses":
        menu = "Manajemen Akun"
    elif is_finance_tax:
        if modul_pilihan == "💰 Modul 3: Invoice & Tax Management":
            list_menu_fin = [
                "Input Data Invoice Resmi", 
                "Input & Cetak Faktur Pajak", 
                "Pemantauan Proses Pembayaran", 
                "Pratinjau, Cetak & Download PDF Invoice", 
                "Lihat Daftar Invoice & Pajak Tersimpan"
            ]
            url_menu = st.query_params.get("menu", None)
            def_idx = list_menu_fin.index(url_menu) if url_menu in list_menu_fin else 0
            if "nav_menu_finance" not in st.session_state:
                st.session_state["nav_menu_finance"] = list_menu_fin[def_idx]
            menu = st.sidebar.radio("Pilih Menu (Finance & Tax):", list_menu_fin, key="nav_menu_finance")
            st.query_params["menu"] = menu
        else:
            menu = "Arsip Dokumen Customer & Pendukung"
    elif is_project_manager:
        if modul_pilihan == "📁 Modul 1: Database & Master Kontrak":
            menu = st.sidebar.selectbox("Pilih Menu:", ["Lihat Database Tersimpan"], key="nav_menu_pm_m1")
        elif modul_pilihan == "📄 Modul 2: Invoice & Dokumen Turunan":
            list_menu_pm2 = ["Pratinjau, Cetak & Download PDF Dokumen", "Lihat Akumulasi Riwayat Transaksi", "Lihat Master Rekap Transaksi"]
            url_menu = st.query_params.get("menu", None)
            def_idx = list_menu_pm2.index(url_menu) if url_menu in list_menu_pm2 else 0
            if "nav_menu_pm_m2" not in st.session_state:
                st.session_state["nav_menu_pm_m2"] = list_menu_pm2[def_idx]
            menu = st.sidebar.selectbox("Pilih Menu:", list_menu_pm2, key="nav_menu_pm_m2")
            st.query_params["menu"] = menu
        elif modul_pilihan == "💰 Modul 3: Invoice & Tax Management":
            list_menu_pm3 = ["Pemantauan Proses Pembayaran", "Lihat Daftar Invoice & Pajak Tersimpan"]
            url_menu = st.query_params.get("menu", None)
            def_idx = list_menu_pm3.index(url_menu) if url_menu in list_menu_pm3 else 0
            if "nav_menu_pm_m3" not in st.session_state:
                st.session_state["nav_menu_pm_m3"] = list_menu_pm3[def_idx]
            menu = st.sidebar.selectbox("Pilih Menu:", list_menu_pm3, key="nav_menu_pm_m3")
            st.query_params["menu"] = menu
        else:
            menu = "Arsip Dokumen Customer & Pendukung"
    elif is_management:
        if modul_pilihan == "💰 Modul 3: Invoice & Tax Management":
            list_menu_mg3 = ["Pemantauan Proses Pembayaran", "Lihat Daftar Invoice & Pajak Tersimpan"]
            url_menu = st.query_params.get("menu", None)
            def_idx = list_menu_mg3.index(url_menu) if url_menu in list_menu_mg3 else 0
            if "nav_menu_mg_m3" not in st.session_state:
                st.session_state["nav_menu_mg_m3"] = list_menu_mg3[def_idx]
            menu = st.sidebar.selectbox("Pilih Menu (Read-Only):", list_menu_mg3, key="nav_menu_mg_m3")
            st.query_params["menu"] = menu
        elif modul_pilihan == "📄 Modul 2: Invoice & Dokumen Turunan":
            list_menu_mg2 = ["Pratinjau, Cetak & Download PDF Dokumen", "Lihat Akumulasi Riwayat Transaksi", "Lihat Master Rekap Transaksi"]
            url_menu = st.query_params.get("menu", None)
            def_idx = list_menu_mg2.index(url_menu) if url_menu in list_menu_mg2 else 0
            if "nav_menu_mg_m2" not in st.session_state:
                st.session_state["nav_menu_mg_m2"] = list_menu_mg2[def_idx]
            menu = st.sidebar.selectbox("Pilih Menu (Read-Only):", list_menu_mg2, key="nav_menu_mg_m2")
            st.query_params["menu"] = menu
        else:
            menu = "Arsip Dokumen Customer & Pendukung"
    else:
        if modul_pilihan == "📁 Modul 0: Master Referensi Harga & Pekerjaan": 
            list_menu_m0 = ["Input & Kelola Master Referensi", "Lihat Daftar Master Referensi Tersimpan"]
            url_menu = st.query_params.get("menu", None)
            def_idx = list_menu_m0.index(url_menu) if url_menu in list_menu_m0 else 0
            if "nav_menu_m0" not in st.session_state:
                st.session_state["nav_menu_m0"] = list_menu_m0[def_idx]
            menu = st.sidebar.radio("Pilih Menu:", list_menu_m0, key="nav_menu_m0")
            st.query_params["menu"] = menu
        elif modul_pilihan == "📁 Modul 1: Database & Master Kontrak": 
            list_menu_m1 = ["Input Database & Invoice (31 Kolom)", "Lihat Database Tersimpan"]
            url_menu = st.query_params.get("menu", None)
            def_idx = list_menu_m1.index(url_menu) if url_menu in list_menu_m1 else 0
            if "nav_menu_m1" not in st.session_state:
                st.session_state["nav_menu_m1"] = list_menu_m1[def_idx]
            menu = st.sidebar.radio("Pilih Menu:", list_menu_m1, key="nav_menu_m1")
            st.query_params["menu"] = menu
        elif modul_pilihan == "💰 Modul 3: Invoice & Tax Management": 
            list_menu_m3 = ["Input Data Invoice Resmi", "Input & Cetak Faktur Pajak", "Pemantauan Proses Pembayaran", "Pratinjau, Cetak & Download PDF Invoice", "Lihat Daftar Invoice & Pajak Tersimpan"]
            url_menu = st.query_params.get("menu", None)
            def_idx = list_menu_m3.index(url_menu) if url_menu in list_menu_m3 else 0
            if "nav_menu_m3" not in st.session_state:
                st.session_state["nav_menu_m3"] = list_menu_m3[def_idx]
            menu = st.sidebar.radio("Pilih Menu:", list_menu_m3, key="nav_menu_m3")
            st.query_params["menu"] = menu
        elif modul_pilihan == "📁 Arsip Dokumen Customer & Pendukung": 
            menu = "Arsip Dokumen Customer & Pendukung"
        else: 
            list_menu_m2_staff = [
                "Input & Proses Rincian Pekerjaan", 
                "Pratinjau, Cetak & Download PDF Dokumen", 
                "Lihat Akumulasi Riwayat Transaksi", 
                "Lihat Master Rekap Transaksi"
            ]
            url_menu = st.query_params.get("menu", None)
            def_idx = list_menu_m2_staff.index(url_menu) if url_menu in list_menu_m2_staff else 0
            if "nav_menu_m2_staff" not in st.session_state:
                st.session_state["nav_menu_m2_staff"] = list_menu_m2_staff[def_idx]
            
            menu = st.sidebar.radio("Pilih Menu:", list_menu_m2_staff, key="nav_menu_m2_staff")
            st.query_params["menu"] = menu

    st.sidebar.markdown("---")

    if st.sidebar.button("🔄 Reload / Refresh Data Cloud MySQL"):
        st.cache_data.clear()
        muat_data_invoice(); muat_data_transaksi(); muat_master_referensi(); muat_master_bank()
        st.sidebar.success("✅ Data tersinkronisasi dengan Database MySQL.")

    if st.sidebar.button("🔒 Keluar / Logout Sistem"):
        st.session_state.logged_in = False
        st.query_params.clear()
        st.rerun()

    # --- BANNER NOTIFIKASI POSISI / PERAN AKTIF ---
    if is_management:
        st.markdown("""
            <div style="background-color: #fef3c7; border: 1px solid #f59e0b; padding: 12px 18px; border-radius: 8px; margin-bottom: 20px;">
                <h4 style="margin:0; color: #b45309; font-size: 15px;">🔒 Mode Direksi / Management (Read-Only Aktif)</h4>
                <p style="margin:4px 0 0 0; font-size: 13px; color: #78350f;">Anda memiliki akses penuh untuk memantau data, menelusuri arsip, dan mengunduh laporan.</p>
            </div>
        """, unsafe_allow_html=True)
    elif is_project_manager:
        st.markdown("""
            <div style="background-color: #e0f2fe; border: 1px solid #0284c7; padding: 12px 18px; border-radius: 8px; margin-bottom: 20px;">
                <h4 style="margin:0; color: #0369a1; font-size: 15px;">📊 Panel Project Manager</h4>
                <p style="margin:4px 0 0 0; font-size: 13px; color: #0c4a6e;">Akses pengawasan kontrak, progres dokumen turunan, dan pemantauan pembayaran proyek.</p>
            </div>
        """, unsafe_allow_html=True)
    elif is_finance_tax:
        st.markdown("""
            <div style="background-color: #ecfdf5; border: 1px solid #10b981; padding: 12px 18px; border-radius: 8px; margin-bottom: 20px;">
                <h4 style="margin:0; color: #047857; font-size: 15px;">💰 Panel Finance & Tax</h4>
                <p style="margin:4px 0 0 0; font-size: 13px; color: #065f46;">Akses pengelolaan faktur pajak, billing, pemantauan pembayaran, dan manajemen keuangan.</p>
            </div>
        """, unsafe_allow_html=True)
    elif is_project_support:
        st.markdown("""
            <div style="background-color: #f1f5f9; border: 1px solid #64748b; padding: 12px 18px; border-radius: 8px; margin-bottom: 20px;">
                <h4 style="margin:0; color: #334155; font-size: 15px;">📁 Panel Project Support</h4>
                <p style="margin:4px 0 0 0; font-size: 13px; color: #475569;">Akses pengelolaan database kontrak, rincian pekerjaan, dan pembuatan dokumen turunan.</p>
            </div>
        """, unsafe_allow_html=True)
    elif is_admin_support:
        st.markdown("""
            <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 12px 18px; border-radius: 8px; margin-bottom: 20px;">
                <h4 style="margin:0; color: #475569; font-size: 15px;">📋 Panel Admin Support</h4>
                <p style="margin:4px 0 0 0; font-size: 13px; color: #64748b;">Akses pengelolaan administrasi pendukung dan timesheet peralatan.</p>
            </div>
        """, unsafe_allow_html=True)
    elif is_super_admin:
        st.markdown("""
            <div style="background-color: #f3e8ff; border: 1px solid #a855f7; padding: 12px 18px; border-radius: 8px; margin-bottom: 20px;">
                <h4 style="margin:0; color: #7e22ce; font-size: 15px;">⚙️ Panel Super Admin</h4>
                <p style="margin:4px 0 0 0; font-size: 13px; color: #581c87;">Akses penuh sistem, pengelolaan hak akses, dan manajemen kredensial pengguna.</p>
            </div>
        """, unsafe_allow_html=True)

    # --- ROUTER MODUL UTAMA ---
    if modul_pilihan == "⚙️ Manajemen Akun & Hak Akses":
        render_panel_manajemen_akun()

    elif is_admin_support and modul_pilihan == "Timesheet Peralatan": 
        tampilkan_timesheet(muat_data_transaksi())

    elif modul_pilihan == "📁 Modul 0: Master Referensi Harga & Pekerjaan":
        if is_management or is_project_manager:
            st.warning("⚠️ Akses Terbatas pada modul ini.")
        else:
            tampilkan_modul_0_referensi(
                menu=menu,
                muat_master_referensi_func=muat_master_referensi,
                simpan_master_referensi_func=simpan_master_referensi,
                muat_data_invoice_func=muat_data_invoice,
                bersih_angka_func=bersih_angka
            )

    elif modul_pilihan == "📁 Arsip Dokumen Customer & Pendukung":
        tampilkan_arsip_pendukung()

    elif modul_pilihan == "💰 Modul 3: Invoice & Tax Management":
        tx = muat_data_transaksi()
        if is_management or is_project_manager:
            if menu == "Pemantauan Proses Pembayaran":
                tampilkan_pemantauan_pembayaran()
            else:
                tampilkan_billing_tax(tx, "Lihat Daftar Invoice & Pajak Tersimpan")
        elif is_finance_tax:
            if menu == "Input & Cetak Faktur Pajak": tampilkan_faktur_pajak(tx, menu)
            elif menu == "Pemantauan Proses Pembayaran": tampilkan_pemantauan_pembayaran()
            else: tampilkan_billing_tax(tx, menu)
        else:
            if menu == "Input & Cetak Faktur Pajak": tampilkan_faktur_pajak(tx, menu)
            elif menu == "Pemantauan Proses Pembayaran": tampilkan_pemantauan_pembayaran()
            else: tampilkan_billing_tax(tx, menu)

    elif modul_pilihan == "📁 Modul 1: Database & Master Kontrak":
        if is_management:
            st.warning("⚠️ Akses Terbatas: Modul input database kontrak hanya dapat dikelola oleh Project Support.")
        elif is_project_manager:
            tampilkan_modul_1_database(
                menu="Lihat Database Tersimpan",
                saved_db_list=muat_data_invoice(),
                bersih_angka_func=bersih_angka,
                parse_date_func=parse_date_safely,
                sort_pi_key_func=sort_pi_key,
                simpan_data_invoice_func=simpan_data_invoice,
                muat_data_invoice_func=muat_data_invoice
            )
        else:
            tampilkan_modul_1_database(
                menu=menu,
                saved_db_list=muat_data_invoice(),
                bersih_angka_func=bersih_angka,
                parse_date_func=parse_date_safely,
                sort_pi_key_func=sort_pi_key,
                simpan_data_invoice_func=simpan_data_invoice,
                muat_data_invoice_func=muat_data_invoice
            )

    elif modul_pilihan == "📄 Modul 2: Invoice & Dokumen Turunan":
        if menu == "Input & Proses Rincian Pekerjaan" and (is_management or is_project_manager):
            st.warning("⚠️ Akses Terbatas untuk peran ini.")
        elif menu == "Input & Proses Rincian Pekerjaan":
            tampilkan_modul_2_rincian(
                saved_db=muat_data_invoice(),
                master_ref_data=muat_master_referensi(),
                bersih_angka_func=bersih_angka,
                sort_pi_key_func=sort_pi_key,
                muat_data_transaksi_func=muat_data_transaksi,
                simpan_data_transaksi_func=simpan_data_transaksi,
                muat_master_bank_func=muat_master_bank,
                simpan_master_bank_func=simpan_master_bank
            )
        elif menu == "Pratinjau, Cetak & Download PDF Dokumen" or is_management or is_project_manager:
            tx_data = muat_data_transaksi()
            if tx_data:
                kontrak_list = sorted(list(set([t.get("Nomor Kontrak") for t in tx_data if t.get("Nomor Kontrak")])))
                sel_k = st.selectbox("Pilih Kontrak:", kontrak_list)
                pi_list = sorted(list(set([t.get("PI No.") for t in tx_data if t.get("Nomor Kontrak") == sel_k])), key=sort_pi_key, reverse=True)
                sel_pi = st.selectbox("Pilih PI:", pi_list)
                target_tx = [t for t in tx_data if t.get("Nomor Kontrak") == sel_k and t.get("PI No.") == sel_pi]
                
                # --- PENYARINGAN DINAMIS OPSI DOKUMEN BERDASARKAN KATEGORI ITEM ---
                ada_item_jasa = False
                ada_item_barang = False

                for t in target_tx:
                    kategori_str = str(t.get('Kategori', '')).lower()
                    excluded_keywords = ["material", "barang", "safety equipment", "pengadaan", "alat", "sparepart", "tools"]
                    if any(kw in kategori_str for kw in excluded_keywords):
                        ada_item_barang = True
                    else:
                        ada_item_jasa = True

                # Buat daftar dokumen secara dinamis (menyembunyikan BAMP, BASP, WCC jika murni barang)
                daftar_dokumen_tersedia = ["Rincian Pekerjaan", "Proforma Invoice"]
                
                if ada_item_jasa:
                    daftar_dokumen_tersedia.extend(["BAMP", "BASP", "WCC"])
                
                if ada_item_barang:
                    daftar_dokumen_tersedia.append("BASTB")

                daftar_dokumen_tersedia.extend(["TKDN", "Opname", "Master Paket Batch"])

                doc_type = st.selectbox("Jenis Dokumen:", daftar_dokumen_tersedia)
                
                if doc_type == "Rincian Pekerjaan": tampilkan_rincian_pekerjaan(target_tx)
                elif doc_type == "Proforma Invoice": tampilkan_proforma_invoice(target_tx)
                elif doc_type == "BAMP": tampilkan_bamp(target_tx)
                elif doc_type == "BASP": tampilkan_basp(target_tx)
                elif doc_type == "WCC": tampilkan_wcc(target_tx)
                elif doc_type == "TKDN": tampilkan_tkdn(target_tx)
                elif doc_type == "Opname": tampilkan_opname(target_tx)
                elif doc_type == "Master Paket Batch": tampilkan_paket_lengkap(target_tx)
                elif doc_type == "BASTB": tampilkan_bastb(target_tx)
        elif menu == "Lihat Akumulasi Riwayat Transaksi":
            tampilkan_akumulasi_riwayat_transaksi(
                tx_data=muat_data_transaksi(),
                bersih_angka_func=bersih_angka,
                sort_pi_key_func=sort_pi_key,
                simpan_data_transaksi_func=simpan_data_transaksi,
                muat_data_transaksi_func=muat_data_transaksi
            )
        elif menu == "Lihat Master Rekap Transaksi":
            tampilkan_rekap_transaksi(muat_data_transaksi())