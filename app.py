import streamlit as st
import pandas as pd
import os
import glob
import base64
import sys
from datetime import datetime, timedelta, date
from modul_dokumen import tkdn
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

# Import Modul Master Paket Dokumen Lengkap (1-Click Batch Export)
try:
    from modul_dokumen.paket_dokumen_lengkap import tampilkan_paket_lengkap
except ImportError as e:
    st.error(f"Gagal memuat modul paket_dokumen_lengkap: {e}")

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Terintegrasi - PT. BANGGAI SENTRAL SULAWESI", layout="wide", initial_sidebar_state="expanded")

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

# --- JALANKAN SISTEM KEAMANAN & AUTENTIKASI BERJENJANG ---
if form_login_sistem():
    
    # Tampilkan panel manajemen akun di sidebar (berdasarkan role)
    render_panel_manajemen_akun()
    
    # Dapatkan level akses role pengguna yang sedang aktif
    user_role = st.session_state.get('current_role', 'Staff')

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
    EXCEL_BANK = os.path.join(DIR_DATABASE, "database_master_bank.xlsx")

    def muat_data_invoice():
        if os.path.exists(EXCEL_INVOICE):
            try:
                df = pd.read_excel(EXCEL_INVOICE)
                if df is not None and not df.empty:
                    df = df.dropna(how='all')
                    # Pembersihan global format .0 pada semua kolom string/angka
                    for col in df.columns:
                        df[col] = df[col].apply(lambda x: bersih_angka(x) if pd.notnull(x) else x)
                    return df.to_dict(orient="records")
            except:
                pass
        return []

    def simpan_data_invoice(data_list):
        waktu_sekarang = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
        for item in data_list:
            if isinstance(item, dict):
                item["Update Terakhir"] = waktu_sekarang
        df_baru = pd.DataFrame(data_list)
        df_baru.to_excel(EXCEL_INVOICE, index=False)
        st.session_state["db_tersimpan"] = data_list

    def muat_data_transaksi():
        if os.path.exists(EXCEL_TRANSAKSI):
            try:
                df = pd.read_excel(EXCEL_TRANSAKSI)
                if df is not None and not df.empty:
                    df = df.dropna(how='all')
                    # Pembersihan global format .0 pada semua kolom transaksi
                    for col in df.columns:
                        if col not in ['Qty', 'Harga Satuan', 'Total Harga', 'Percent']:
                            df[col] = df[col].apply(lambda x: bersih_angka(x) if pd.notnull(x) else x)
                    return df.to_dict(orient="records")
            except:
                pass
        return []

    def simpan_data_transaksi(data_list):
        waktu_sekarang = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
        for item in data_list:
            if isinstance(item, dict):
                item["Update Terakhir"] = waktu_sekarang
        df_baru = pd.DataFrame(data_list)
        df_baru.to_excel(EXCEL_TRANSAKSI, index=False)
        st.session_state["db_transaksi"] = data_list

    def muat_master_referensi():
        if os.path.exists(EXCEL_MASTER_REF):
            try:
                df = pd.read_excel(EXCEL_MASTER_REF)
                if df is not None and not df.empty:
                    for col in df.columns:
                        if col not in ['Harga Satuan']:
                            df[col] = df[col].apply(lambda x: bersih_angka(x) if pd.notnull(x) else x)
                    return df.to_dict(orient="records")
            except:
                pass
        return []

    def simpan_master_referensi(data_list):
        waktu_sekarang = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
        for item in data_list:
            if isinstance(item, dict):
                item["Update Terakhir"] = waktu_sekarang
        df_baru = pd.DataFrame(data_list)
        df_baru.to_excel(EXCEL_MASTER_REF, index=False)
        st.session_state["db_master_ref"] = data_list

    def muat_master_bank():
        default_banks = [
            {
                "Bank Name": "BANK RAKYAT INDONESIA (PERSERO) Tbk.",
                "Bank Branch": "Cabang Luwuk",
                "Account No": "0167 0167 8888 303",
                "Account Name": "PT. BANGGAI SENTRAL SULAWESI",
                "Attn": "Accounts Payable - Finance Department"
            }
        ]
        if os.path.exists(EXCEL_BANK):
            try:
                df = pd.read_excel(EXCEL_BANK)
                if df is not None and not df.empty:
                    for col in df.columns:
                        df[col] = df[col].apply(lambda x: bersih_angka(x) if pd.notnull(x) else x)
                    return df.to_dict(orient="records")
            except:
                pass
        return default_banks

    def simpan_master_bank(data_list):
        df_baru = pd.DataFrame(data_list)
        df_baru.to_excel(EXCEL_BANK, index=False)
        st.session_state["db_master_bank"] = data_list

    # Inisialisasi Session State
    if "db_tersimpan" not in st.session_state:
        st.session_state["db_tersimpan"] = muat_data_invoice()

    if "db_transaksi" not in st.session_state:
        st.session_state["db_transaksi"] = muat_data_transaksi()

    if "db_master_ref" not in st.session_state:
        st.session_state["db_master_ref"] = muat_master_referensi()

    if "db_master_bank" not in st.session_state:
        st.session_state["db_master_bank"] = muat_master_bank()

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

    # --- SIDEBAR: NAVIGASI & WAKTU LOKAL (WITA / UTC+8) ---
    st.sidebar.markdown("### 🗂️ Navigasi Dashboard Utama")
    waktu_wita = datetime.utcnow() + timedelta(hours=8)
    current_time_str = waktu_wita.strftime("%d %b %Y, %H:%M:%S")
    st.sidebar.markdown(f"🕒 **Waktu Sistem (WITA):**<br>`{current_time_str}`", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    # --- PEMBATASAN MENU BERJENJANG BERDASARKAN ROLE ---
    if user_role == "Staff Timesheet":
        modul_pilihan = st.sidebar.selectbox("Pilih Modul:", ["Timesheet Peralatan"])
    elif user_role == "Finance / Invoice":
        modul_pilihan = st.sidebar.selectbox("Pilih Modul Utama:", [
            "📁 Modul 1: Database & Master Kontrak",
            "📄 Modul 2: Invoice & Dokumen Turunan"
        ])
    else: # Manajer Operasional (Akses Penuh)
        modul_pilihan = st.sidebar.selectbox("Pilih Modul Utama:", [
            "📁 Modul 0: Master Referensi Harga & Pekerjaan",
            "📁 Modul 1: Database & Master Kontrak",
            "📄 Modul 2: Invoice & Dokumen Turunan"
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
    else:
        menu = st.sidebar.radio("Pilih Menu:", [
            "Input & Proses Rincian Pekerjaan",
            "Pratinjau, Cetak & Download PDF Dokumen",
            "Lihat Akumulasi Riwayat Transaksi"
        ])

    st.sidebar.markdown("---")
    st.sidebar.success("📂 **Status Sistem:** Terhubung ke Folder Aman (`database_penyimpanan_aman`)")

    if st.sidebar.button("🔒 Keluar / Logout Sistem"):
        st.session_state.logged_in = False
        st.rerun()

    # =========================================================================
    # LOGIKA KHUSUS STAFF TIMESHEET
    # =========================================================================
    if user_role == "Staff Timesheet":
        st.markdown("""
            <div class="dashboard-card">
                <h3 style="margin-top:0; color:#065f46; font-size:18px;">⏱️ Panel Khusus Staff Timesheet Peralatan</h3>
            </div>
        """, unsafe_allow_html=True)
        transaksi_list = muat_data_transaksi()
        tampilkan_timesheet(transaksi_list if transaksi_list else [])

    else:
        # =========================================================================
        # LOGIKA MODUL 0: MASTER REFERENSI HARGA & PEKERJAAN
        # =========================================================================
        if modul_pilihan == "📁 Modul 0: Master Referensi Harga & Pekerjaan":
            
            query_params = st.query_params
            if "delete_master_idx" in query_params:
                try:
                    del_idx = int(query_params["delete_master_idx"])
                    all_m = muat_master_referensi()
                    if 0 <= del_idx < len(all_m):
                        all_m.pop(del_idx)
                        simpan_master_referensi(all_m)
                        st.success("✅ Berhasil menghapus baris master referensi secara permanen!")
                        st.query_params.clear()
                        st.rerun()
                except:
                    pass

            if "edit_master_idx" in query_params:
                try:
                    ed_idx = int(query_params["edit_master_idx"])
                    all_m = muat_master_referensi()
                    if 0 <= ed_idx < len(all_m):
                        st.session_state["edit_master_index"] = ed_idx
                        st.query_params.clear()
                        st.rerun()
                except:
                    pass

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
                
                kontrak_from_invoice = [str(item.get(1, item.get("Nomor Kontrak", ""))) for item in saved_db if item.get(1) or item.get("Nomor Kontrak")]
                kontrak_from_master = [str(m.get("Nomor Kontrak", "")) for m in master_data_live if m.get("Nomor Kontrak")]
                combined_kontrak_list = sorted(list(set(kontrak_from_invoice + kontrak_from_master))) + ["-- Ketik Nomor Kontrak Baru --"]

                default_kat_list = ["MONTHLY BASIS", "ON-CALL BASIS", "JASA MOBILISASI", "PROFESSIONAL SUM", "PROVISIONAL SUM", "LAINNYA"]
                existing_kat_from_db = list(set([str(m.get("Kategori")) for m in master_data_live if m.get("Kategori")]))
                combined_kat_list = sorted(list(set(default_kat_list + existing_kat_from_db))) + ["-- Ketik Kategori Baru --"]

                default_unit_list = ["Month", "Day", "Ls", "Unit", "Trip", "Jam", "EA", "AU"]
                existing_unit_from_db = list(set([str(m.get("Unit")) for m in master_data_live if m.get("Unit")]))
                combined_unit_list = sorted(list(set(default_unit_list + existing_unit_from_db))) + ["-- Ketik Satuan Baru --"]

                with st.form("form_master_referensi"):
                    col1, col2 = st.columns(2)
                    with col1:
                        def_kontrak_val = def_ref.get("Nomor Kontrak", combined_kontrak_list[0] if combined_kontrak_list else "")
                        idx_kontrak_ref = combined_kontrak_list.index(def_kontrak_val) if def_kontrak_val in combined_kontrak_list else 0
                        kontrak_pilih = st.selectbox("Nomor Kontrak Rujukan", combined_kontrak_list, index=idx_kontrak_ref)
                        
                        kontrak_manual = st.text_input("✍️ Ketik Nomor Kontrak Baru (Jika memilih opsi 'Kontrak Baru' di atas):")
                        
                        def_kat_val = def_ref.get("Kategori", combined_kat_list[0])
                        idx_kat_ref = combined_kat_list.index(def_kat_val) if def_kat_val in combined_kat_list else 0
                        kategori_pilih = st.selectbox("Kategori Pekerjaan", combined_kat_list, index=idx_kat_ref)
                        
                        kategori_manual = st.text_input("✍️ Ketik Nama Kategori Baru (Jika memilih 'Kategori Baru' di atas):")

                        def_unit_val = def_ref.get("Unit", combined_unit_list[0])
                        idx_unit_ref = combined_unit_list.index(def_unit_val) if def_unit_val in combined_unit_list else 0
                        unit_pilih = st.selectbox("Satuan Unit", combined_unit_list, index=idx_unit_ref)
                        
                        unit_manual = st.text_input("✍️ Ketik Nama Satuan Baru (Jika memilih 'Satuan Baru' di atas, misal: m3, EA, AU):")

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
                        if kontrak_pilih == "-- Ketik Nomor Kontrak Baru --":
                            final_kontrak = kontrak_manual.strip()
                        else:
                            final_kontrak = kontrak_pilih

                        if kategori_pilih == "-- Ketik Kategori Baru --":
                            final_kategori = kategori_manual.strip()
                        else:
                            final_kategori = kategori_pilih

                        if unit_pilih == "-- Ketik Satuan Baru --":
                            final_unit = unit_manual.strip()
                        else:
                            final_unit = unit_pilih

                        if not final_kontrak or not uraian_ref or not final_kategori or not final_unit:
                            st.error("⚠️ Nomor Kontrak, Kategori, Satuan, dan Uraian Pekerjaan tidak boleh kosong!")
                        else:
                            master_data = muat_master_referensi()
                            item_baru = {
                                "Nomor Kontrak": final_kontrak,
                                "Kategori": final_kategori.upper(),
                                "Uraian Pekerjaan": uraian_ref,
                                "Unit": final_unit,
                                "Harga Satuan": harga_satuan_ref,
                                "Update Terakhir": (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            if submit_master_update and st.session_state["edit_master_index"] is not None and st.session_state["edit_master_index"] < len(master_data):
                                master_data[st.session_state["edit_master_index"]] = item_baru
                                st.success("✨ Data Master Referensi berhasil di-update!")
                            else:
                                master_data.append(item_baru)
                                st.success("🎉 Data Master Referensi baru beserta riwayat kontrak fleksibel berhasil disimpan!")
                            
                            simpan_master_referensi(master_data)
                            st.session_state["edit_master_index"] = None
                            st.rerun()

            elif menu == "Lihat Daftar Master Referensi Tersimpan":
                st.markdown("""
                    <div class="dashboard-card">
                        <h3 style="margin-top:0; color:#065f46; font-size:18px;">📂 Daftar Master Referensi Harga & Pekerjaan Tersimpan (Dengan Tombol Edit & Hapus per Baris)</h3>
                    </div>
                """, unsafe_allow_html=True)

                master_records = muat_master_referensi()
                if not master_records:
                    st.info("ℹ️ Belum ada data master referensi harga tersimpan di folder aman.")
                else:
                    df_master = pd.DataFrame(master_records)

                    kolom_kontrak = None
                    for col in ['Nomor Kontrak', 'No Kontrak', 'Kontrak']:
                        if col in df_master.columns:
                            kolom_kontrak = col
                            break

                    if kolom_kontrak:
                        list_kontrak = ["-- Semua Kontrak --"] + list(df_master[kolom_kontrak].dropna().unique())
                        selected_kontrak = st.selectbox("🔍 Filter Berdasarkan Nomor Kontrak:", list_kontrak, key="filter_kontrak_master")

                        if selected_kontrak != "-- Semua Kontrak --":
                            df_filtered = df_master[df_master[kolom_kontrak] == selected_kontrak]
                        else:
                            df_filtered = df_master
                    else:
                        df_filtered = df_master
                        selected_kontrak = "-- Semua Kontrak --"

                    html_table_rows = ""
                    for original_idx, row in df_filtered.iterrows():
                        html_table_rows += "<tr>"
                        html_table_rows += f"<td style='border: 1px solid #cbd5e1; padding: 10px; text-align: center; font-size: 13px;'>{original_idx+1}</td>"
                        for col_name, val in row.items():
                            val_clean = bersih_angka(val)
                            if any(k in str(col_name).lower() for k in ['harga', 'satuan', 'total', 'nominal', 'nilai']):
                                try:
                                    num_val = float(val)
                                    val_str = f"{num_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                                except:
                                    val_str = val_clean
                            else:
                                val_str = val_clean
                                
                            if 'uraian' in str(col_name).lower() or 'deskripsi' in str(col_name).lower():
                                html_table_rows += f"<td style='border: 1px solid #cbd5e1; padding: 10px; font-size: 13px; min-width: 400px; white-space: normal; word-wrap: break-word;'>{val_str}</td>"
                            else:
                                html_table_rows += f"<td style='border: 1px solid #cbd5e1; padding: 10px; font-size: 13px; white-space: nowrap;'>{val_str}</td>"
                        
                        action_buttons = f"""
                            <td style='border: 1px solid #cbd5e1; padding: 8px; text-align: center; white-space: nowrap;'>
                                <a href='?edit_master_idx={original_idx}' target='_self' style='text-decoration: none;'>
                                    <button style='background-color: #3b82f6; color: white; border: none; padding: 5px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; cursor: pointer; margin-right: 4px;'>✏️ Edit</button>
                                </a>
                                <a href='?delete_master_idx={original_idx}' target='_self' style='text-decoration: none;'>
                                    <button style='background-color: #ef4444; color: white; border: none; padding: 5px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; cursor: pointer;'>🗑️ Hapus</button>
                                </a>
                            </td>
                        """
                        html_table_rows += action_buttons
                        html_table_rows += "</tr>"

                    headers_html = "<th style='border: 1px solid #cbd5e1; padding: 10px; background-color: #1e293b; color: white; font-size: 13px;'>No</th>"
                    for col in df_filtered.columns:
                        headers_html += f"<th style='border: 1px solid #cbd5e1; padding: 10px; background-color: #1e293b; color: white; font-size: 13px;'>{col}</th>"
                    headers_html += "<th style='border: 1px solid #cbd5e1; padding: 10px; background-color: #1e293b; color: white; font-size: 13px; text-align: center;'>Aksi</th>"

                    full_interactive_table_html = f"""
                    <div style="max-height: 550px; overflow-y: auto; border: 1px solid #cbd5e1; border-radius: 8px; margin-bottom: 20px;">
                        <table style="width: 100%; border-collapse: collapse; background-color: #ffffff; color: #0f172a;">
                            <thead>
                                <tr>{headers_html}</tr>
                            </thead>
                            <tbody>
                                {html_table_rows}
                            </tbody>
                        </table>
                    </div>
                    """
                    st.components.v1.html(full_interactive_table_html, height=500, scrolling=True)

        # =========================================================================
        # LOGIKA MODUL 1: DATABASE & MASTER KONTRAK (DENGAN DATE PICKER DINAMIS)
        # =========================================================================
        elif modul_pilihan == "📁 Modul 1: Database & Master Kontrak":
            if menu == "Input Database & Invoice (31 Kolom)":
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
                        pi_num = bersih_angka(data.get(0, data.get('Proforma Invoice No.', '-')))
                        kontrak_num = bersih_angka(data.get(1, data.get('Nomor Kontrak', '-')))
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

                def_data = {}
                if st.session_state["edit_index"] is not None and st.session_state["edit_index"] < len(st.session_state["db_tersimpan"]):
                    def_data = st.session_state["db_tersimpan"][st.session_state["edit_index"]]
                
                def get_val(idx_key, text_key):
                    if idx_key in def_data:
                        return bersih_angka(def_data[idx_key])
                    return bersih_angka(def_data.get(text_key, ""))

                def parse_date_safely(val_str):
                    if not val_str:
                        return date.today()
                    for fmt in ("%d %b %Y", "%Y-%m-%d", "%d/%m/%Y"):
                        try:
                            return datetime.strptime(str(val_str).strip(), fmt).date()
                        except ValueError:
                            continue
                    return date.today()

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

                    def baris_input_tanggal(no, label, default_str=""):
                        c1, c2, c3 = st.columns([0.8, 3.5, 7])
                        with c1: c1.write(f"**{no}.**")
                        with c2: c2.write(label)
                        with c3:
                            d_val = parse_date_safely(default_str)
                            dt_res = st.date_input(f"input_{no}", value=d_val, label_visibility="collapsed")
                            return dt_res.strftime("%d %b %Y")

                    val_1  = baris_input_bersih(1, "Nomor Kontrak", default_val=get_val(1, "Nomor Kontrak"))
                    val_2  = baris_input_bersih(2, "Nomor Tender", default_val=get_val(2, "Nomor Tender"))
                    val_3  = baris_input_bersih(3, "Judul Kontrak", default_val=get_val(7, "Judul Kontrak"), is_area=True)
                    val_4  = baris_input_tanggal(4, "Tanggal Kontrak", default_str=get_val(4, "Tanggal Kontrak"))
                    val_5  = baris_input_bersih(5, "Jangka Waktu Kontrak", default_val=get_val(5, "Jangka Waktu Kontrak"))
                    val_6  = baris_input_bersih(6, "Proforma Invoice No.", default_val=get_val(0, "Proforma Invoice No."))
                    val_7  = baris_input_tanggal(7, "Tanggal Performa Invoice", default_str=get_val(6, "Tanggal Performa Invoice"))
                    val_8  = baris_input_bersih(8, "Nomor Purchase Order", default_val=get_val(8, "Nomor Purchase Order"))
                    val_9  = baris_input_tanggal(9, "Tanggal Purchase Order", default_str=get_val(9, "Tanggal Purchase Order"))
                    val_10 = baris_input_bersih(10, "Lingkup Pekerjaan", default_val=get_val(3, "Lingkup Pekerjaan"), is_area=True)
                    val_11 = baris_input_bersih(11, "Pihak Pertama", default_val=get_val(10, "Pihak Pertama"))
                    val_12 = baris_input_bersih(12, "Alamat Pihak Pertama", default_val=get_val(11, "Alamat Pihak Pertama"), is_area=True)
                    
                    c1, c2, c3 = st.columns([0.8, 3.5, 7])
                    c1.write("**13.**")
                    c2.write("Diwakili Oleh")
                    pilihan_p1 = [
                        "Ronny Dwi Purnomo / Rafik Hidayat",
                        "Rafik Hidayat / Ronny Dwi Purnomo",
                        "Irwan / Budi Bernadi",
                        "Budi Bernadi / Irwan",
                        "Aldito Fauzi Roe / Aryanto Yoga",
                        "Aryanto Yoga / Aldito Fauzi Roe",
                    ]
                    def_p1 = get_val(12, "Diwakili Oleh")
                    idx_p1 = pilihan_p1.index(def_p1) if def_p1 in pilihan_p1 else 0
                    val_13 = c3.selectbox("Diwakili Oleh P1", pilihan_p1, index=idx_p1, label_visibility="collapsed")

                    val_14 = baris_input_bersih(14, "Selaku", default_val=get_val(13, "Selaku"))
                    val_15 = baris_input_bersih(15, "Pihak Kedua", default_val=get_val(14, "Pihak Kedua"))
                    val_16 = baris_input_bersih(16, "Alamat Pihak Kedua", default_val=get_val(15, "Alamat Pihak Kedua"), is_area=True)
                    val_17 = baris_input_bersih(17, "Diwakili Oleh (P2)", default_val=get_val(16, "Diwakili Oleh (P2)"))
                    val_18 = baris_input_bersih(18, "Selaku (P2)", default_val=get_val(17, "Selaku (P2)"))
                    val_19 = baris_input_bersih(19, "Periode Pekerjaan", default_val=get_val(18, "Periode Pekerjaan"))
                    val_20 = baris_input_bersih(20, "Nomor WCC", default_val=get_val(19, "Nomor WCC"))
                    val_21 = baris_input_tanggal(21, "Tanggal WCC", default_str=get_val(20, "Tanggal WCC"))
                    val_22 = baris_input_bersih(22, "Nomor WO", default_val=get_val(21, "Nomor WO"))
                    val_23 = baris_input_bersih(23, "Keterangan WO", default_val=get_val(22, "Keterangan WO"), is_area=True)
                    val_24 = baris_input_bersih(24, "Nomor CTR", default_val=get_val(23, "Nomor CTR"))
                    val_25 = baris_input_bersih(25, "Progress Pekerjaan", default_val=get_val(24, "Progress Pekerjaan"))
                    val_26 = baris_input_bersih(26, "Prepared by Name", default_val=get_val(25, "Prepared by Name"))
                    val_27 = baris_input_bersih(27, "Prepared by Title", default_val=get_val(26, "Prepared by Title"))

                    # --- APPROVED BY 1 (DENGAN OPSI KOSONG) ---
                    c1, c2, c3 = st.columns([0.8, 3.5, 7])
                    c1.write("**28.**")
                    c2.write("Approved by 1")
                    pilihan_app1 = [
                        "--- (Tidak Ada / Kosong) ---",
                        "Imron Maulana / Moh Bazarul Aqhsa",
                        "Moh Bazarul Aqhsa / Imron Maulana",
                        "Irwan / Budi Bernadi",
                        "Budi Bernadi / Irwan",
                        "Aldito Fauzi Roe / Aryanto Yoga",
                        "Aryanto Yoga / Aldito Fauzi Roe"
                    ]
                    def_app1 = get_val(27, "Approved by 1")
                    idx_app1 = pilihan_app1.index(def_app1) if def_app1 in pilihan_app1 else 0
                    val_28 = c3.selectbox("Approved by 1", pilihan_app1, index=idx_app1, label_visibility="collapsed")

                    val_29 = baris_input_bersih(29, "Approved by Title 1", default_val=get_val(28, "Approved by Title 1"))

                    # --- APPROVED BY 2 (DENGAN OPSI KOSONG) ---
                    c1, c2, c3 = st.columns([0.8, 3.5, 7])
                    c1.write("**30.**")
                    c2.write("Approved by 2")
                    pilihan_app2 = [
                        "--- (Tidak Ada / Kosong) ---",
                        "Abidsar",
                        "Imron Maulana",
                        "Moh Bazarul Aqhsa"
                    ]
                    def_app2 = get_val(29, "Approved by 2")
                    idx_app2 = pilihan_app2.index(def_app2) if def_app2 in pilihan_app2 else 0
                    val_30 = c3.selectbox("Approved by 2", pilihan_app2, index=idx_app2, label_visibility="collapsed")

                    val_31 = baris_input_bersih(31, "Approved by Title 2", default_val=get_val(30, "Approved by Title 2"))

                    st.markdown("---")
                    
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    with col_btn1:
                        submit_baru = st.form_submit_button("💾 Simpan Data Baru")
                    with col_btn2:
                        submit_save_as = st.form_submit_button("📥 Save As (Buat PI Baru)")
                    with col_btn3:
                        submit_update = st.form_submit_button("📝 Update Data Ini")
                    
                    if submit_baru or submit_save_as or submit_update:
                        waktu_aksi = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
                        data_terinput = {
                            0: bersih_angka(val_6), 1: bersih_angka(val_1), 2: bersih_angka(val_2), 3: val_10, 4: val_4, 5: val_5, 6: val_7, 7: val_3, 
                            8: bersih_angka(val_8), 9: val_9, 10: val_11, 11: val_12, 12: val_13, 13: val_14, 14: val_15, 
                            15: val_16, 16: val_17, 17: val_18, 18: val_19, 19: bersih_angka(val_20), 20: val_21, 21: bersih_angka(val_22), 
                            22: val_23, 23: bersih_angka(val_24), 24: val_25, 25: val_26, 26: val_27, 27: val_28, 28: val_29,
                            29: val_30, 30: val_31,
                            "Update Terakhir": waktu_aksi
                        }
                        current_data = muat_data_invoice()
                        if submit_update:
                            if st.session_state["edit_index"] is not None and st.session_state["edit_index"] < len(current_data):
                                current_data[st.session_state["edit_index"]] = data_terinput
                                simpan_data_invoice(current_data)
                                st.success("✨ Data berhasil diperbarui!")
                        elif submit_save_as or submit_baru:
                            current_data.append(data_terinput)
                            simpan_data_invoice(current_data)
                            st.success("🎉 Data berhasil disimpan!")
                            st.session_state["edit_index"] = None

            elif menu == "Lihat Database Tersimpan":
                st.markdown("""
                    <div class="dashboard-card">
                        <h3 style="margin-top:0; color:#065f46; font-size:18px;">📂 Daftar Database Identifikasi Tersimpan</h3>
                    </div>
                """, unsafe_allow_html=True)
                saved_records = muat_data_invoice()
                if len(saved_records) > 0:
                    cleaned_records = []
                    for rec in saved_records:
                        cleaned_rec = {k: bersih_angka(v) for k, v in rec.items()}
                        cleaned_records.append(cleaned_rec)
                    df_saved = pd.DataFrame(cleaned_records)
                    if "Update Terakhir" in df_saved.columns:
                        df_saved = df_saved.drop(columns=["Update Terakhir"])
                    df_saved.columns = [f"{col}" if str(col).isdigit() else f"{i}: {col}" for i, col in enumerate(df_saved.columns)]
                    st.dataframe(df_saved, use_container_width=True)

        # =========================================================================
        # LOGIKA MODUL 2: INVOICE & DOKUMEN TURUNAN (DENGAN PROVISIONAL SUM)
        # =========================================================================
        elif modul_pilihan == "📄 Modul 2: Invoice & Dokumen Turunan":
            if menu == "Input & Proses Rincian Pekerjaan":
                st.markdown("""
                    <div class="dashboard-card">
                        <h3 style="margin-top:0; color:#065f46; font-size:18px;">📝 Lembar Kerja & Pemrosesan Rincian Pekerjaan (Dukungan Panggil Ulang Presisi & Rekening Bank Dinamis)</h3>
                    </div>
                """, unsafe_allow_html=True)

                saved_db = muat_data_invoice()
                master_ref_data = muat_master_referensi()
                
                if not saved_db:
                    st.warning("⚠️ Belum ada data di Database Modul 1. Harap lakukan input data kontrak & PI terlebih dahulu.")
                elif not master_ref_data:
                    st.warning("⚠️ Belum ada data di Master Referensi Harga (Modul 0).")
                else:
                    existing_tx_list = muat_data_transaksi()
                    
                    list_kontrak = list(set([bersih_angka(item.get(1, item.get("Nomor Kontrak", ""))) for item in saved_db if item.get(1) or item.get("Nomor Kontrak")]))
                    list_pi = list(set([bersih_angka(item.get(0, item.get("Proforma Invoice No.", ""))) for item in saved_db if item.get(0) or item.get("Proforma Invoice No.")]))

                    # --- FITUR PANGGIL ULANG TRANSAKSI BERDASARKAN PI (OTOMATIS 100%) ---
                    st.markdown("#### 🔄 Panggil Ulang / Load Data Transaksi Berdasarkan PI")
                    pi_tersedia_transaksi = list(set([bersih_angka(t.get("PI No.")) for t in existing_tx_list if t.get("PI No.")]))
                    opsi_panggil_tx = ["-- Buat Baru / Input Baru --"] + [f"PI: {pi}" for pi in pi_tersedia_transaksi]
                    
                    col_load1, col_load2 = st.columns([3, 1])
                    with col_load1:
                        pilihan_load_tx = st.selectbox("Pilih Proforma Invoice untuk Diperiksa/Direvisi:", opsi_panggil_tx, label_visibility="collapsed")
                    with col_load2:
                        if st.button("📥 Panggil Data Ini"):
                            if pilihan_load_tx != "-- Buat Baru / Input Baru --":
                                pi_target = pilihan_load_tx.replace("PI: ", "").strip()
                                st.session_state["loaded_pi_target"] = pi_target
                                
                                matched_tx_items = [t for t in existing_tx_list if bersih_angka(t.get("PI No.")) == pi_target]
                                if matched_tx_items:
                                    st.session_state["forced_kontrak"] = bersih_angka(matched_tx_items[0].get("Nomor Kontrak", ""))
                                    st.session_state["forced_pi"] = bersih_angka(matched_tx_items[0].get("PI No.", ""))
                                    st.session_state["num_rows"] = len(matched_tx_items)
                                
                                st.success(f"✅ Data untuk PI [{pi_target}] berhasil dipanggil secara otomatis dan presisi!")
                                st.rerun()
                            else:
                                st.session_state["loaded_pi_target"] = None
                                st.session_state.pop("forced_kontrak", None)
                                st.session_state.pop("forced_pi", None)
                                st.session_state["num_rows"] = 1
                                st.rerun()

                    loaded_tx_items = []
                    active_pi_load = st.session_state.get("loaded_pi_target", None)
                    if active_pi_load:
                        loaded_tx_items = [t for t in existing_tx_list if bersih_angka(t.get("PI No.")) == str(active_pi_load).strip()]
                        if loaded_tx_items:
                            st.info(f"📋 **Mode Revisi Aktif:** Menampilkan data tersimpan untuk PI `{active_pi_load}` ({len(loaded_tx_items)} baris item).")

                    col1, col2 = st.columns(2)
                    with col1:
                        forced_k = st.session_state.get("forced_kontrak", None)
                        if not forced_k and loaded_tx_items:
                            forced_k = bersih_angka(loaded_tx_items[0].get("Nomor Kontrak", ""))
                        
                        default_kontrak_val = forced_k if forced_k in list_kontrak else (list_kontrak[0] if list_kontrak else "")
                        idx_k = list_kontrak.index(default_kontrak_val) if default_kontrak_val in list_kontrak else 0
                        
                        selected_kontrak = st.selectbox("Nomor Kontrak", list_kontrak if list_kontrak else [""], index=idx_k, key="main_sel_kontrak")
                        
                        filtered_pi = [bersih_angka(item.get(0, item.get("Proforma Invoice No.", ""))) for item in saved_db if bersih_angka(item.get(1, item.get("Nomor Kontrak"))) == str(selected_kontrak)]
                        if not filtered_pi:
                            filtered_pi = list_pi
                        
                        forced_pi_val = st.session_state.get("forced_pi", None)
                        if not forced_pi_val and active_pi_load:
                            forced_pi_val = active_pi_load
                        
                        default_pi_val = forced_pi_val if forced_pi_val in filtered_pi else (filtered_pi[0] if filtered_pi else "")
                        idx_pi = filtered_pi.index(default_pi_val) if default_pi_val in filtered_pi else 0
                        
                        selected_pi = st.selectbox("Nomor Proforma Invoice (PI)", filtered_pi if filtered_pi else [""], index=idx_pi, key="main_sel_pi")
                        
                        matched_record = next((item for item in saved_db if bersih_angka(item.get(1, item.get("Nomor Kontrak"))) == str(selected_kontrak) and bersih_angka(item.get(0, item.get("Proforma Invoice No."))) == str(selected_pi)), saved_db[0] if saved_db else {})

                        nama_kontrak = matched_record.get(7, matched_record.get("Judul Kontrak", ""))
                        nomor_tender = bersih_angka(matched_record.get(2, matched_record.get("Nomor Tender", "")))
                        tanggal_pi = matched_record.get(6, matched_record.get("Tanggal Performa Invoice", ""))
                        ditujukan_kepada = matched_record.get(10, matched_record.get("Pihak Pertama", ""))
                        alamat_pihak_pertama = matched_record.get(11, matched_record.get("Alamat Pihak Pertama", ""))
                        jangka_waktu = matched_record.get(5, matched_record.get("Jangka Waktu Kontrak", ""))
                    
                    with col2:
                        raw_po_num = loaded_tx_items[0].get("Nomor PO", matched_record.get(8, matched_record.get("Nomor Purchase Order", ""))) if loaded_tx_items else matched_record.get(8, matched_record.get("Nomor Purchase Order", ""))
                        def_po_num = bersih_angka(raw_po_num)
                        
                        raw_po_date = loaded_tx_items[0].get("Tanggal PO", matched_record.get(9, matched_record.get("Tanggal Purchase Order", ""))) if loaded_tx_items else matched_record.get(9, matched_record.get("Tanggal Purchase Order", ""))
                        def_po_date = bersih_angka(raw_po_date)

                        def_desc_po = loaded_tx_items[0].get("Deskripsi PO", matched_record.get(3, matched_record.get("Lingkup Pekerjaan", ""))) if loaded_tx_items else matched_record.get(3, matched_record.get("Lingkup Pekerjaan", ""))

                        nomor_po = st.text_input("Nomor PO", def_po_num)
                        tanggal_po = st.text_input("Tanggal PO", def_po_date)
                        mata_uang = st.text_input("Mata Uang", "IDR")
                        desc_po = st.text_area("Lingkup Pekerjaan", def_desc_po)

                    st.markdown("---")
                    st.markdown("#### ⚙️ Pengaturan Khusus Bank & Rekening Pembayaran (Dinamis)")

                    bank_records = muat_master_bank()
                    bank_names_list = [b.get("Bank Name") for b in bank_records] + ["➕ Tambah Rekening Bank Baru..."]
                    
                    def_b_name = loaded_tx_items[0].get("Bank Name", bank_records[0].get("Bank Name")) if loaded_tx_items else bank_records[0].get("Bank Name")
                    idx_b = bank_names_list.index(def_b_name) if def_b_name in bank_names_list else 0

                    c_bank1, c_bank2 = st.columns(2)
                    with c_bank1:
                        pilih_bank_dropdown = st.selectbox("Pilih Rekening Bank Tujuan", bank_names_list, index=idx_b)
                        
                        if pilih_bank_dropdown == "➕ Tambah Rekening Bank Baru...":
                            st.markdown("##### ✍️ Form Input Rekening Bank Baru")
                            new_b_name = st.text_input("Nama Bank Baru (Contoh: BANK MANDIRI)")
                            new_b_branch = st.text_input("Cabang Bank Baru", value="Cabang Luwuk")
                            new_b_acc_no = st.text_input("Nomor Rekening Baru")
                            new_b_acc_name = st.text_input("Atas Nama Rekening Baru", value="PT. BANGGAI SENTRAL SULAWESI")
                            new_b_attn = st.text_input("Attn. Departemen", value="Accounts Payable - Finance Department")
                            
                            if st.button("💾 Simpan Rekening Bank Baru"):
                                if new_b_name and new_b_acc_no:
                                    bank_records.append({
                                        "Bank Name": new_b_name.upper(),
                                        "Bank Branch": new_b_branch,
                                        "Account No": new_b_acc_no,
                                        "Account Name": new_b_acc_name,
                                        "Attn": new_b_attn
                                    })
                                    simpan_master_bank(bank_records)
                                    st.success("✅ Rekening bank baru berhasil disimpan! Silakan pilih di dropdown.")
                                    st.rerun()
                                else:
                                    st.error("⚠️ Nama Bank dan Nomor Rekening wajib diisi!")
                            
                            bank_name = def_b_name
                            bank_branch = loaded_tx_items[0].get("Bank Branch", "Cabang Luwuk") if loaded_tx_items else "Cabang Luwuk"
                            bank_acc_no = bersih_angka(loaded_tx_items[0].get("Account No", "")) if loaded_tx_items else ""
                            bank_acc_name = loaded_tx_items[0].get("Account Name", "PT. BANGGAI SENTRAL SULAWESI") if loaded_tx_items else "PT. BANGGAI SENTRAL SULAWESI"
                            attn_to = loaded_tx_items[0].get("Attn", "Accounts Payable - Finance Department") if loaded_tx_items else "Accounts Payable - Finance Department"
                        else:
                            bank_name = pilih_bank_dropdown
                            selected_bank_obj = next((b for b in bank_records if b.get("Bank Name") == bank_name), bank_records[0])
                            bank_branch = selected_bank_obj.get("Bank Branch", "Cabang Luwuk")
                            bank_acc_no = bersih_angka(selected_bank_obj.get("Account No", ""))
                            bank_acc_name = selected_bank_obj.get("Account Name", "PT. BANGGAI SENTRAL SULAWESI")
                            attn_to = selected_bank_obj.get("Attn", "Accounts Payable - Finance Department")

                            st.text_input("Cabang Bank", value=bank_branch, disabled=True)
                            st.text_input("Nomor Rekening", value=bank_acc_no, disabled=True)

                    with c_bank2:
                        st.text_input("Atas Nama Rekening", value=bank_acc_name, disabled=True)
                        attn_to = st.text_input("Attn. (Penerima Invoice)", value=attn_to)
                        def_percent = float(loaded_tx_items[0].get("Percent", 100.0)) if loaded_tx_items else 100.0
                        persen_val = st.number_input("Persentase Tagihan (%)", min_value=1.0, max_value=100.0, value=def_percent)

                    st.markdown("---")
                    st.markdown("#### 📋 Item / Baris Pekerjaan Proforma Invoice (Multi-Baris / Mutasi)")

                    df_ref = pd.DataFrame(master_ref_data)
                    df_ref["Nomor Kontrak Clean"] = df_ref["Nomor Kontrak"].astype(str).str.strip()
                    df_ref["Kategori Clean"] = df_ref["Kategori"].astype(str).str.strip()
                    df_ref["Uraian Clean"] = df_ref["Uraian Pekerjaan"].astype(str).str.strip()

                    df_ref_kontrak = df_ref[df_ref["Nomor Kontrak Clean"] == str(selected_kontrak).strip()]
                    if df_ref_kontrak.empty:
                        df_ref_kontrak = df_ref 

                    list_kat = sorted(df_ref_kontrak["Kategori Clean"].dropna().unique().tolist())
                    if "PROFESSIONAL SUM" not in list_kat and "PROVISIONAL SUM" not in list_kat:
                        list_kat.append("PROVISIONAL SUM")

                    if "num_rows" not in st.session_state:
                        st.session_state.num_rows = len(loaded_tx_items) if loaded_tx_items else 1

                    items_data_input = []
                    
                    for i in range(st.session_state.num_rows):
                        st.markdown(f"**Baris Item ke-{i+1}**")
                        
                        default_item_data = loaded_tx_items[i] if loaded_tx_items and i < len(loaded_tx_items) else {}
                        
                        c_k1, c_k2 = st.columns(2)
                        with c_k1:
                            def_kat_item = default_item_data.get("Kategori", list_kat[0] if list_kat else "-")
                            idx_kat = list_kat.index(def_kat_item) if def_kat_item in list_kat else 0
                            
                            kat_pilih = st.selectbox(
                                f"Kategori Pekerjaan {i+1}", 
                                list_kat if list_kat else ["-"], 
                                index=idx_kat,
                                key=f"kat_{i}"
                            )
                        
                        is_provisional = "provisional" in str(kat_pilih).lower() or "professional" in str(kat_pilih).lower()

                        with c_k2:
                            if is_provisional:
                                spek_pilih = st.text_input(f"Uraian Pekerjaan / Spesifikasi {i+1} (Manual)", value=default_item_data.get("Deskripsi Pekerjaan", "Provisional Sum (At Cost + 15% Fee)"), key=f"spek_manual_{i}")
                            else:
                                df_f_kat = df_ref_kontrak[df_ref_kontrak["Kategori Clean"] == str(kat_pilih).strip()]
                                list_spek = sorted(df_f_kat["Uraian Clean"].dropna().unique().tolist()) if not df_f_kat.empty else ["- (Tidak ada data uraian)"]
                                
                                def_spek_item = default_item_data.get("Deskripsi Pekerjaan", list_spek[0] if list_spek else "-")
                                idx_spek = list_spek.index(def_spek_item) if def_spek_item in list_spek else 0
                                
                                spek_pilih = st.selectbox(
                                    f"Uraian Pekerjaan / Spesifikasi {i+1}", 
                                    list_spek, 
                                    index=idx_spek,
                                    key=f"spek_{i}"
                                )

                        hs_otomatis = 0.0
                        unit_otomatis = "Month"
                        if is_provisional:
                            hs_otomatis = 0.0 
                            unit_otomatis = "Ls"
                        else:
                            if not df_f_kat.empty and spek_pilih != "- (Tidak ada data uraian)":
                                m_row = df_f_kat[df_f_kat["Uraian Clean"] == str(spek_pilih).strip()]
                                if not m_row.empty:
                                    row_m = m_row.iloc[0]
                                    try:
                                        hs_otomatis = float(row_m.get("Harga Satuan", 0.0))
                                    except:
                                        hs_otomatis = 0.0
                                    unit_otomatis = str(row_m.get("Unit", "Month"))

                        c_item1, c_item2, c_item3, c_item4 = st.columns([1, 1, 1, 1])
                        with c_item1:
                            def_qty = float(default_item_data.get("Qty", 1.0))
                            q_val = st.number_input(f"Qty {i+1}", value=def_qty, key=f"qty_{i}")
                        with c_item2:
                            default_u_opts = ["Month", "Day", "Ls", "Unit", "Trip", "Jam", "EA", "AU"]
                            existing_u_from_master = df_ref["Unit"].dropna().astype(str).unique().tolist() if "Unit" in df_ref.columns else []
                            u_opts = sorted(list(set(default_u_opts + existing_u_from_master)))
                            def_unit = default_item_data.get("Unit", unit_otomatis)
                            idx_u = u_opts.index(def_unit) if def_unit in u_opts else 0
                            u_val = st.selectbox(f"Unit {i+1}", u_opts, index=idx_u, key=f"unit_{i}")
                        with c_item3:
                            def_tm_str = default_item_data.get("Tanggal Mulai", "")
                            try:
                                def_tm = datetime.strptime(def_tm_str, "%d %b %Y").date()
                            except:
                                def_tm = date.today()
                            tm_val = st.date_input(f"Tanggal Mulai {i+1}", value=def_tm, key=f"tm_{i}")
                        with c_item4:
                            def_ts_str = default_item_data.get("Tanggal Selesai", "")
                            try:
                                def_ts = datetime.strptime(def_ts_str, "%d %b %Y").date()
                            except:
                                def_ts = date.today()
                            ts_val = st.date_input(f"Tanggal Selesai {i+1}", value=def_ts, key=f"ts_{i}")

                        if is_provisional:
                            def_harga_manual = float(default_item_data.get("Harga Satuan", 0.0))
                            hs_manual = st.number_input(f"Harga At Cost / Nilai Dasar {i+1} (Rp)", min_value=0.0, value=def_harga_manual, step=1000.0, format="%.2f", key=f"hs_prov_{i}")
                            hs_final = hs_manual
                            st.info("ℹ️ *Catatan Provisional Sum:* Total nilai baris ini akan diakumulasikan secara total keseluruhan sebelum ditambahkan 15% management fee.")
                        else:
                            st.markdown(f"**Harga Satuan Tetap:** Rp {hs_otomatis:,.2f}")
                            hs_final = hs_otomatis

                        def_ket = default_item_data.get("Keterangan", "")
                        ket_val = st.text_input(f"Keterangan / Deskripsi Tambahan {i+1}", value=def_ket, key=f"ket_{i}")
                        st.markdown("---")

                        items_data_input.append({
                            "kategori": kat_pilih,
                            "deskripsi": spek_pilih,
                            "qty": q_val,
                            "unit": u_val,
                            "tgl_mulai": tm_val.strftime("%d %b %Y"),
                            "tgl_selesai": ts_val.strftime("%d %b %Y"),
                            "harga_satuan": hs_final,
                            "keterangan": ket_val,
                            "is_provisional": is_provisional
                        })

                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        if st.button("➕ Tambah Baris Pekerjaan"):
                            st.session_state.num_rows += 1
                            st.rerun()
                    with col_m2:
                        if st.button("➖ Kurangi Baris Terakhir") and st.session_state.num_rows > 1:
                            st.session_state.num_rows -= 1
                            st.rerun()

                    st.markdown("---")

                    col_btn_save, col_btn_dist = st.columns(2)
                    with col_btn_save:
                        if st.button("💾 Simpan / Update Data Sementara", type="secondary"):
                            waktu_aksi = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
                            existing_tx = muat_data_transaksi()
                            pi_target_simpan = str(selected_pi).strip()
                            
                            existing_tx = [t for t in existing_tx if bersih_angka(t.get("PI No.")) != pi_target_simpan]

                            prov_items = [it for it in items_data_input if it.get("is_provisional")]
                            subtotal_prov = sum([it["qty"] * it["harga_satuan"] for it in prov_items])
                            total_prov_with_fee = subtotal_prov * 1.15 

                            for item in items_data_input:
                                if item.get("is_provisional"):
                                    if len(prov_items) > 0 and item == prov_items[0]:
                                        total_harga = total_prov_with_fee * (persen_val / 100.0)
                                    else:
                                        total_harga = 0.0 
                                else:
                                    total_harga = (item["qty"] * item["harga_satuan"]) * (persen_val / 100.0)

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
                                    "Kategori": item["kategori"],
                                    "Deskripsi Pekerjaan": item["deskripsi"],
                                    "Qty": item["qty"],
                                    "Unit": item["unit"],
                                    "Percent": persen_val,
                                    "Tanggal Mulai": item["tgl_mulai"],
                                    "Tanggal Selesai": item["tgl_selesai"],
                                    "Harga Satuan": item["harga_satuan"],
                                    "Total Harga": total_harga,
                                    "Bank Name": bank_name,
                                    "Bank Branch": bank_branch,
                                    "Account No": bank_acc_no,
                                    "Account Name": bank_acc_name,
                                    "Attn": attn_to,
                                    "Keterangan": item["keterangan"],
                                    "Update Terakhir": waktu_aksi
                                }
                                existing_tx.append(data_transaksi)

                            simpan_data_transaksi(existing_tx)
                            st.success(f"💾 Berhasil menyimpan data sementara untuk PI [{pi_target_simpan}] (Data lama ditimpa dengan sukses)!")

                    with col_btn_dist:
                        if st.button("🚀 Proses & Distribusikan Data ke Dokumen Turunan", type="primary"):
                            waktu_aksi = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
                            existing_tx = muat_data_transaksi()
                            pi_baru = str(selected_pi).strip()
                            
                            existing_tx = [t for t in existing_tx if bersih_angka(t.get("PI No.")) != pi_baru]

                            prov_items = [it for it in items_data_input if it.get("is_provisional")]
                            subtotal_prov = sum([it["qty"] * it["harga_satuan"] for it in prov_items])
                            total_prov_with_fee = subtotal_prov * 1.15

                            for item in items_data_input:
                                if item.get("is_provisional"):
                                    if len(prov_items) > 0 and item == prov_items[0]:
                                        total_harga = total_prov_with_fee * (persen_val / 100.0)
                                    else:
                                        total_harga = 0.0
                                else:
                                    total_harga = (item["qty"] * item["harga_satuan"]) * (persen_val / 100.0)

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
                                    "Kategori": item["kategori"],
                                    "Deskripsi Pekerjaan": item["deskripsi"],
                                    "Qty": item["qty"],
                                    "Unit": item["unit"],
                                    "Percent": persen_val,
                                    "Tanggal Mulai": item["tgl_mulai"],
                                    "Tanggal Selesai": item["tgl_selesai"],
                                    "Harga Satuan": item["harga_satuan"],
                                    "Total Harga": total_harga,
                                    "Bank Name": bank_name,
                                    "Bank Branch": bank_branch,
                                    "Account No": bank_acc_no,
                                    "Account Name": bank_acc_name,
                                    "Attn": attn_to,
                                    "Keterangan": item["keterangan"],
                                    "Update Terakhir": waktu_aksi
                                }
                                existing_tx.append(data_transaksi)

                            simpan_data_transaksi(existing_tx)
                            st.session_state.num_rows = 1
                            st.success(f"🎉 Berhasil mendistribusikan {len(items_data_input)} baris item secara resmi untuk Proforma Invoice [{pi_baru}] ke dokumen turunan!")

            elif menu == "Pratinjau, Cetak & Download PDF Dokumen":
                transaksi_list = muat_data_transaksi()
                if not transaksi_list:
                    st.warning("⚠️ Belum ada data transaksi rincian pekerjaan yang diproses di Modul 2.")
                else:
                    doc_type = st.selectbox("Pilih Jenis Dokumen Resmi:", [
                        "Rincian Pekerjaan",
                        "Proforma Invoice",
                        "Berita Acara Mulai Pekerjaan (BAMP)",
                        "Berita Acara Selesai Pekerjaan (BASP)",
                        "Work Completion Certificate (WCC)",
                        "Berita Acara Mulai & Selesai Pekerjaan (BASP)",
                        "Formulir tkdn",
                        "Timesheet Peralatan",
                        "Berita Acara Opname pekerjaan",
                        "📦 Master Paket Dokumen Lengkap (1-Click Batch)" 
                    ])

                    if doc_type == "Rincian Pekerjaan":
                        tampilkan_rincian_pekerjaan(transaksi_list)
                    elif doc_type == "Proforma Invoice":
                        tampilkan_proforma_invoice(transaksi_list)
                    elif doc_type == "Berita Acara Mulai Pekerjaan (BAMP)":
                         tampilkan_bamp(transaksi_list)
                    elif doc_type == "Berita Acara Mulai & Selesai Pekerjaan (BASP)" or doc_type == "Berita Acara Selesai Pekerjaan (BASP)":
                         tampilkan_basp(transaksi_list)
                    elif doc_type == "Work Completion Certificate (WCC)":
                         tampilkan_wcc(transaksi_list)
                    elif doc_type.lower() == "formulir tkdn":
                         tkdn.tampilkan_tkdn(transaksi_list)
                    elif doc_type == "Berita Acara Opname pekerjaan":
                         tampilkan_opname(transaksi_list)
                    elif doc_type.lower() == "timesheet peralatan" or doc_type.lower() == "timesheet":
                         tampilkan_timesheet(transaksi_list)
                    elif doc_type == "📦 Master Paket Dokumen Lengkap (1-Click Batch)":
                         tampilkan_paket_lengkap(transaksi_list)

            elif menu == "Lihat Akumulasi Riwayat Transaksi":
                st.markdown("""
                    <div class="dashboard-card">
                        <h3 style="margin-top:0; color:#065f46; font-size:18px;">📂 Akumulasi Riwayat Transaksi Rincian Pekerjaan</h3>
                    </div>
                """, unsafe_allow_html=True)
                
                tx_records = muat_data_transaksi()
                if tx_records:
                    cleaned_tx_records = [{k: bersih_angka(v) for k, v in rec.items()} for rec in tx_records]
                    st.dataframe(pd.DataFrame(cleaned_tx_records), use_container_width=True)
                    
                    st.markdown("---")
                    st.markdown("#### 🗑️ Hapus Riwayat Transaksi yang Salah / Duplikat")
                    
                    pilihan_hapus_tx = []
                    for idx, item in enumerate(tx_records):
                        pi_val = bersih_angka(item.get('PI No.', 'Tanpa PI'))
                        kontrak_val = bersih_angka(item.get('Nomor Kontrak', 'Tanpa Kontrak'))
                        total_val = float(item.get('Total Harga', 0.0))
                        pilihan_hapus_tx.append(f"Index {idx} | PI: {pi_val} | Kontrak: {kontrak_val} | Total: Rp {total_val:,.0f}")

                    col_ht1, col_ht2 = st.columns([2, 1])
                    with col_ht1:
                        target_hapus_tx_idx = st.selectbox(
                            "Pilih Riwayat Transaksi yang Ingin Dihapus:",
                            range(len(pilihan_hapus_tx)),
                            format_func=lambda x: pilihan_hapus_tx[x],
                            key="select_tx_row_to_delete"
                        )
                    with col_ht2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("❌ Hapus Transaksi Terpilih", use_container_width=True, type="primary"):
                            try:
                                deleted_tx = tx_records.pop(target_hapus_tx_idx)
                                simpan_data_transaksi(tx_records)
                                pi_terhapus = bersih_angka(deleted_tx.get('PI No.', 'Data'))
                                st.success(f"✅ Berhasil menghapus riwayat transaksi (PI: {pi_terhapus}) secara permanen!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"⚠️ Terjadi kesalahan saat menghapus transaksi: {e}")
                else:
                    st.info("Belum ada riwayat transaksi rincian pekerjaan tersimpan.")