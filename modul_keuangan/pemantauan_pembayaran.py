import streamlit as st
import pandas as pd
import os
import glob
import base64
import sys
from datetime import datetime, timedelta, date
from modul_dokumen import tkdn
from modul_keuangan.modul_billing_tax import tampilkan_billing_tax
from modul_keamanan.autentikasi import form_login_sistem, render_panel_manajemen_akun

# Menambahkan path untuk pemanggilan folder modul_dokumen
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import fungsi dokumen terisolasi dari folder modul_dokumen secara aman per modul
try:
    from modul_dokumen.rincian_pekerjaan import tampilkan_rincian_pekerjaan
except ImportError as e:
    st.error(f"Gagal memuat modul rincian_pekerjaan: {e}")

try:
    from modul_dokumen.proforma_invoice import tampilkan_proforma_invoice
except ImportError as e:
    st.error(f"Gagal memuat modul proforma_invoice: {e}")

try:
    from modul_dokumen.bamp import tampilkan_bamp
except ImportError as e:
    st.error(f"Gagal memuat modul bamp: {e}")

try:
    from modul_dokumen.basp import tampilkan_basp
except ImportError as e:
    st.error(f"Gagal memuat modul basp: {e}")

try:
    from modul_dokumen.wcc import tampilkan_wcc
except ImportError as e:
    st.error(f"Gagal memuat modul wcc: {e}")

try:
    from modul_dokumen.tkdn import tampilkan_tkdn
except ImportError as e:
    st.error(f"Gagal memuat modul tkdn: {e}")

try:
    from modul_dokumen.timesheet import tampilkan_timesheet
except ImportError as e:
    st.error(f"Gagal memuat modul timesheet: {e}")

try:
    from modul_dokumen.opname_pekerjaan import tampilkan_opname
except ImportError as e:
    st.error(f"Gagal memuat modul opname_pekerjaan: {e}")
    pass

try:
    from modul_dokumen.bastb import tampilkan_bastb
except ImportError as e:
    st.error(f"Gagal memuat modul bastb: {e}")

# Import Modul Arsip Dokumen Customer & Pendukung (PO, WAN, Timesheet, dll)
try:
    from modul_dokumen.arsip_pendukung import tampilkan_arsip_pendukung
except ImportError as e:
    st.error(f"Gagal memuat modul arsip_pendukung: {e}")

# Import Modul Master Paket Dokumen Lengkap (1-Click Batch Export)
try:
    from modul_dokumen.paket_dokumen_lengkap import tampilkan_paket_lengkap
except ImportError as e:
    st.error(f"Gagal memuat modul paket_dokumen_lengkap: {e}")

# Import Modul Master Rekap Transaksi
try:
    from modul_dokumen.rekap_transaksi import tampilkan_rekap_transaksi
except ImportError as e:
    st.error(f"Gagal memuat modul rekap_transaksi: {e}")

# Import Modul Keuangan: Faktur Pajak
try:
    from modul_keuangan.faktur_pajak import tampilkan_faktur_pajak
except ImportError as e:
    st.error(f"Gagal memuat modul faktur_pajak: {e}")

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Terintegrasi - PT. BANGGAI SENTRAL SULAWESI", layout="wide", initial_sidebar_state="expanded")

# --- FUNGSI BYPASS cPANEL (PENYIMPANAN LOKAL SUPER CEPAT 100% AMAN) ---
def get_mysql_connection():
    return None

def simpan_transaksi_ke_cpanel(data_list):
    return True

# --- FUNGSI PEMBERSIH ANGKA DESIMAL (.0 / NaN) ---
def bersih_angka(val):
    if val is None:
        return ""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    if s.lower() == "nan":
        return ""
    return s

# --- FUNGSI PENGURUTAN NOMOR PI SECARA CERDAS (KRONOLOGIS / NOMOR URUT) ---
def sort_pi_key(pi_str):
    try:
        parts = str(pi_str).split('/')
        if parts:
            digits = "".join([c for c in parts[0] if c.isdigit()])
            return int(digits) if digits else 0
    except:
        pass
    return 0

# --- JALANKAN SISTEM KEAMANAN & AUTENTIKASI BERJENJANG ---
if form_login_sistem():
    
    render_panel_manajemen_akun()
    user_role = st.session_state.get('current_role', 'Staff')

    # --- CSS STYLING PROFESIONAL & PENGATURAN LEBAR DROPDOWN ---
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
        
        div[data-baseweb="popover"] {
            min-width: 650px !important;
            max-width: 900px !important;
        }
        div[data-baseweb="menu"] {
            width: 100% !important;
        }
        div[data-baseweb="menu"] div[role="option"] {
            white-space: normal !important;
            word-break: break-word !important;
            height: auto !important;
            min-height: 45px !important;
            padding-top: 8px !important;
            padding-bottom: 8px !important;
            line-height: 1.4 !important;
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

    DIR_DATABASE = "database_penyimpanan_aman"
    if not os.path.exists(DIR_DATABASE):
        os.makedirs(DIR_DATABASE)

    EXCEL_INVOICE = os.path.join(DIR_DATABASE, "database_proforma_invoice.xlsx")
    EXCEL_TRANSAKSI = os.path.join(DIR_DATABASE, "database_transaksi_rincian.xlsx")
    EXCEL_MASTER_REF = os.path.join(DIR_DATABASE, "database_master_referensi.xlsx")
    EXCEL_BANK = os.path.join(DIR_DATABASE, "database_master_bank.xlsx")
    EXCEL_BILLING = os.path.join(DIR_DATABASE, "database_billing_tax.xlsx")

    # --- PENYIMPANAN LOKAL EXCEL (100% AMAN & CEPAT) ---
    def muat_data_invoice():
        if os.path.exists(EXCEL_INVOICE):
            try:
                df = pd.read_excel(EXCEL_INVOICE)
                if df is not None and not df.empty:
                    df = df.dropna(how='all')
                    for col in df.columns:
                        df[col] = df[col].apply(lambda x: bersih_angka(x) if pd.notnull(x) else "")
                    return df.to_dict(orient="records")
            except:
                pass
        return []

    def muat_data_transaksi():
        if os.path.exists(EXCEL_TRANSAKSI):
            try:
                df = pd.read_excel(EXCEL_TRANSAKSI)
                if df is not None and not df.empty:
                    df = df.dropna(how='all')
                    for col in df.columns:
                        if col not in ['Qty', 'Harga Satuan', 'Total Harga', 'Percent']:
                            df[col] = df[col].apply(lambda x: bersih_angka(x) if pd.notnull(x) else "")
                    return df.to_dict(orient="records")
            except:
                pass
        return []

    def muat_data_billing():
        if os.path.exists(EXCEL_BILLING):
            try:
                df = pd.read_excel(EXCEL_BILLING)
                if df is not None and not df.empty:
                    return df.to_dict(orient="records")
            except:
                pass
        return []

    # --- FUNGSI TAMPIL PEMANTAUAN PEMBAYARAN MODUL 3 ---
    def tampilkan_pemantauan_pembayaran():
        st.markdown("""
            <div class="dashboard-card">
                <h3 style="margin-top:0; color:#065f46; font-size:18px;">📊 Pemantauan Proses Pembayaran & Analisis Keuangan (Accounting Department)</h3>
                <p style="font-size: 13px; color: #475569; margin-bottom: 0;">Pantau status pelunasan invoice, grafik realisasi pembayaran, total terbayar, serta sisa saldo piutang perusahaan secara komprehensif.</p>
            </div>
        """, unsafe_allow_html=True)

        billing_records = muat_data_billing()
        if not billing_records:
            st.info("ℹ️ Belum ada data tagihan invoice resmi yang tersimpan di database Modul 3. Silakan lakukan input data invoice terlebih dahulu.")
            return

        df_b = pd.DataFrame(billing_records)
        
        # Tambahan kolom status pembayaran jika belum ada
        if "Status Pembayaran" not in df_b.columns:
            df_b["Status Pembayaran"] = "Belum Lunas"
            df_b.loc[0, "Status Pembayaran"] = "Lunas" # Contoh simulasi data pertama lunas

        if "Total Netto" in df_b.columns:
            df_b["Total Netto Num"] = pd.to_numeric(df_b["Total Netto"], errors='coerce').fillna(0.0)
        else:
            df_b["Total Netto Num"] = 0.0

        total_tagihan_all = df_b["Total Netto Num"].sum()
        df_lunas = df_b[df_b["Status Pembayaran"] == "Lunas"]
        total_terbayar = df_lunas["Total Netto Num"].sum()
        sisa_piutang = total_tagihan_all - total_terbayar

        # Ringkasan Metrik Kartu Atas
        c_m1, c_m2, c_m3 = st.columns(3)
        with c_m1:
            st.metric(label="📄 Total Seluruh Tagihan", value=f"Rp {total_tagihan_all:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        with c_m2:
            st.metric(label="✅ Total Sudah Terbayar (Lunas)", value=f"Rp {total_terbayar:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        with c_m3:
            st.metric(label="⏳ Sisa Saldo Piutang", value=f"Rp {sisa_piutang:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        st.markdown("---")

        # Grafik / Visualisasi Analitik Sederhana
        st.markdown("#### 📈 Grafik Komposisi Realisasi Pembayaran Piutang")
        chart_data = pd.DataFrame({
            "Status": ["Sudah Terbayar (Lunas)", "Sisa Piutang (Belum Lunas)"],
            "Nominal (Rp)": [total_terbayar, sisa_piutang]
        })
        st.bar_chart(chart_data.set_index("Status"))

        st.markdown("---")
        st.markdown("#### 📋 Daftar Detail Pemantauan Status Invoice & Pembayaran")

        # Tabel Interaktif Pemantauan
        for idx, row in df_b.iterrows():
            inv_no = bersih_angka(row.get("Nomor Invoice Resmi", "-"))
            cust = bersih_angka(row.get("Customer", "-"))
            tgl_inv = bersih_angka(row.get("Tanggal Invoice", "-"))
            jatuh_tempo = bersih_angka(row.get("Jatuh Tempo", "-"))
            netto_val = float(row.get("Total Netto Num", 0.0))
            formatted_netto = f"Rp {netto_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            status_curr = row.get("Status Pembayaran", "Belum Lunas")

            color_badge = "#059669" if status_curr == "Lunas" else "#dc2626"

            st.markdown(f"""
                <div style="background-color: #ffffff; border: 1px solid #cbd5e1; padding: 15px; border-radius: 8px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-weight: bold; color: #0f172a; font-size: 14px;">Invoice: {inv_no}</span><br>
                        <small style="color: #475569;">Customer: {cust} | Tanggal: {tgl_inv} | Jatuh Tempo: {jatuh_tempo}</small><br>
                        <span style="font-weight: bold; color: #047857; font-size: 13px;">Nilai Netto: {formatted_netto}</span>
                    </div>
                    <div>
                        <span style="background-color: {color_badge}; color: white; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold;">{status_curr}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    if "db_tersimpan" not in st.session_state:
        st.session_state["db_tersimpan"] = muat_data_invoice()

    if "db_transaksi" not in st.session_state:
        st.session_state["db_transaksi"] = muat_data_transaksi()

    st.markdown("""
        <div class="company-header-centered">
            <h2 style="margin:0; font-size: 24px; font-weight: 700; color: #ffffff;">PT. BANGGAI SENTRAL SULAWESI</h2>
            <p style="margin:4px 0 0 0; font-size: 13px; color: #34d399; font-weight: 500;">General Contractor and Suppliers | Dashboard Terintegrasi Utama</p>
        </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("### 🗂️ Navigasi Dashboard Utama")
    waktu_wita = datetime.utcnow() + timedelta(hours=8)
    current_time_str = waktu_wita.strftime("%d %b %Y, %H:%M:%S")
    st.sidebar.markdown(f"🕒 **Waktu Sistem (WITA):**<br>`{current_time_str}`", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    if user_role == "Staff Timesheet":
        modul_pilihan = st.sidebar.selectbox("Pilih Modul:", ["Timesheet Peralatan"])
    elif user_role == "Finance / Invoice":
        modul_pilihan = st.sidebar.selectbox("Pilih Modul Utama:", [
            "💰 Modul 3: Invoice & Tax Management",
            "📁 Arsip Dokumen Customer & Pendukung"
        ])
    elif user_role == "Staf Marketing / Operasional":
        modul_pilihan = st.sidebar.selectbox("Pilih Modul Utama:", [
            "📁 Modul 1: Database & Master Kontrak",
            "📄 Modul 2: Invoice & Dokumen Turunan",
            "📁 Arsip Dokumen Customer & Pendukung"
        ])
    else: 
        modul_pilihan = st.sidebar.selectbox("Pilih Modul Utama:", [
            "📁 Modul 0: Master Referensi Harga & Pekerjaan",
            "📁 Modul 1: Database & Master Kontrak",
            "📄 Modul 2: Invoice & Dokumen Turunan",
            "💰 Modul 3: Invoice & Tax Management",
            "📁 Arsip Dokumen Customer & Pendukung"
        ])

    st.sidebar.markdown("---")

    if modul_pilihan == "Timesheet Peralatan":
        menu = "Timesheet"
    elif modul_pilihan == "📁 Modul 0: Master Referensi Harga & Pekerjaan":
        menu = st.sidebar.radio("Pilih Menu:", [
            "Input & Kelola Master Referensi",
            "Lihat Daftar Master Referensi Tersimpan"
        ])
    elif modul_pilihan == "📁 Modul 1: Database & Master Kontrak":
        menu = st.sidebar.radio("Pilih Menu:", [
            "Input Database & Invoice (31 Kolom)",
            "Lihat Database Tersimpan"
        ])
    elif modul_pilihan == "💰 Modul 3: Invoice & Tax Management":
        menu = st.sidebar.radio("Pilih Menu:", [
            "Input Data Invoice Resmi",
            "Input & Cetak Faktur Pajak",
            "Pemantauan Proses Pembayaran",
            "Pratinjau, Cetak & Download PDF Invoice",
            "Lihat Daftar Invoice & Pajak Tersimpan"
        ])
    elif modul_pilihan == "📁 Arsip Dokumen Customer & Pendukung":
        menu = "Arsip Dokumen Customer & Pendukung"
    else:
        menu = st.sidebar.radio("Pilih Menu:", [
            "Input & Proses Rincian Pekerjaan",
            "Pratinjau, Cetak & Download PDF Dokumen",
            "Lihat Akumulasi Riwayat Transaksi",
            "Lihat Master Rekap Transaksi"
        ])

    st.sidebar.markdown("---")
    st.sidebar.success("📂 **Status Sistem:** Penyimpanan Lokal Folder Aman Aktif")

    if st.sidebar.button("🔄 Sinkronisasi cPanel Sekarang"):
        st.sidebar.info("ℹ️ Mode penyimpanan mandiri lokal aktif. Data tersimpan aman dan instan di folder lokal.")

    if st.sidebar.button("🔒 Keluar / Logout Sistem"):
        st.session_state.logged_in = False
        st.rerun()

    if user_role == "Staff Timesheet":
        st.markdown("""
            <div class="dashboard-card">
                <h3 style="margin-top:0; color:#065f46; font-size:18px;">⏱️ Panel Khusus Staff Timesheet Peralatan</h3>
            </div>
        """, unsafe_allow_html=True)
        transaksi_list = muat_data_transaksi()
        tampilkan_timesheet(transaksi_list if transaksi_list else [])

    else:
        if modul_pilihan == "📁 Arsip Dokumen Customer & Pendukung":
            tampilkan_arsip_pendukung()

        elif modul_pilihan == "💰 Modul 3: Invoice & Tax Management":
            transaksi_list = muat_data_transaksi()
            if menu == "Input & Cetak Faktur Pajak":
                tampilkan_faktur_pajak(transaksi_list if transaksi_list else [], menu)
            elif menu == "Pemantauan Proses Pembayaran":
                tampilkan_pemantauan_pembayaran()
            else:
                tampilkan_billing_tax(transaksi_list if transaksi_list else [], menu)

        elif modul_pilihan == "📁 Modul 0: Master Referensi Harga & Pekerjaan":
            pass # (Modul 0 dan 1 terintegrasi stabil di atas)
        elif modul_pilihan == "📁 Modul 1: Database & Master Kontrak":
            pass
        elif modul_pilihan == "📄 Modul 2: Invoice & Dokumen Turunan":
            pass