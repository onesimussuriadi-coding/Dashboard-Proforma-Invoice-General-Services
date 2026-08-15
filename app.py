import streamlit as st
import pandas as pd
import os
import glob
import base64

# Konfigurasi Halaman (Memaksa Tampilan Bersih Terang)
st.set_page_config(page_title="Dashboard Terintegrasi - PT. Banggai Sentral Sulawesi", layout="wide", initial_sidebar_state="expanded")

# CSS Styling Profesional (Tema Terang / Light Mode, Bersih, Ramah Cetak Tanpa Boros Tinta)
st.markdown("""
    <style>
    /* Paksa Tema Latar Belakang Terang / Abu-abu Muda */
    .stApp { background-color: #f8fafc; color: #0f172a; }
    
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
    /* Kotak Pratinjau Dokumen dengan Warna Putih Bersih Anti Boros Tinta */
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
    /* Sembunyikan elemen sidebar & tombol saat mode cetak browser */
    @media print {
        [data-testid="stSidebar"] { display: none; }
        .stButton { display: none; }
        .dashboard-card { display: none; }
        .company-header-centered { display: none; }
        .document-preview { border: none; box-shadow: none; padding: 0; width: 100%; }
    }
    </style>
""", unsafe_allow_html=True)

# --- SISTEM DATABASE EXCEL LOKAL ---
EXCEL_INVOICE = "database_proforma_invoice.xlsx"
EXCEL_TRANSAKSI = "database_transaksi_rincian.xlsx"

def muat_data_invoice():
    if os.path.exists(EXCEL_INVOICE):
        try:
            return pd.read_excel(EXCEL_INVOICE).to_dict(orient="records")
        except:
            return []
    return []

def simpan_data_invoice(data_list):
    df = pd.DataFrame(data_list)
    cols_prioritas = ["Proforma Invoice No.", "Contract No.", "Tender No", "Keterangan PO"]
    sisa_cols = [c for c in df.columns if c not in cols_prioritas]
    df = df[cols_prioritas + sisa_cols]
    df.to_excel(EXCEL_INVOICE, index=False)

def muat_data_transaksi():
    if os.path.exists(EXCEL_TRANSAKSI):
        try:
            return pd.read_excel(EXCEL_TRANSAKSI).to_dict(orient="records")
        except:
            return []
    return []

def simpan_data_transaksi(data_list):
    df = pd.DataFrame(data_list)
    df.to_excel(EXCEL_TRANSAKSI, index=False)

if "db_tersimpan" not in st.session_state:
    st.session_state["db_tersimpan"] = muat_data_invoice()
if "db_transaksi" not in st.session_state:
    st.session_state["db_transaksi"] = muat_data_transaksi()
if "edit_index" not in st.session_state:
    st.session_state["edit_index"] = None

# --- HEADER UTAMA ---
st.markdown("""
    <div class="company-header-centered">
        <h2 style="margin:0; font-size: 24px; font-weight: 700; color: #ffffff;">PT. BANGGAI SENTRAL SULAWESI</h2>
        <p style="margin:4px 0 0 0; font-size: 13px; color: #34d399; font-weight: 500;">General Contractor and Suppliers | Dashboard Terintegrasi Utama</p>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR: NAVIGASI 2 TINGKAT ---
st.sidebar.markdown("### 🗂️ Navigasi Dashboard Utama")

modul_pilihan = st.sidebar.selectbox("Pilih Modul Utama:", [
    "📁 Modul 1: Database & Master Kontrak",
    "📄 Modul 2: Invoice & Dokumen Turunan"
])

st.sidebar.markdown("---")

if modul_pilihan == "📁 Modul 1: Database & Master Kontrak":
    menu = st.sidebar.radio("Pilih Menu:", [
        "Input Database & Invoice (26 Kolom)",
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
st.sidebar.success("📂 **Status Sistem:** Terhubung ke Database Lokal")


# =========================================================================
# LOGIKA MODUL 1: DATABASE & MASTER KONTRAK
# =========================================================================
if menu == "Input Database & Invoice (26 Kolom)":
    st.markdown("""
        <div class="dashboard-card">
            <h4 style="margin-top:0; color:#065f46; font-size:15px;">🔍 Panggil Ulang atau Buat Database Identifikasi Kontrak & PI</h4>
        </div>
    """, unsafe_allow_html=True)

    st.session_state["db_tersimpan"] = muat_data_invoice()

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
        st.info("📌 Belum ada data database tersimpan di Excel.")

    if st.session_state["edit_index"] is not None and st.session_state["edit_index"] < len(st.session_state["db_tersimpan"]):
        st.info(f"📋 **DATA DIPANGGIL:** Silakan ubah isian, lalu gunakan tombol **'Save As (Buat PI Baru)'** atau **'Update Data Ini'**.")

    def_data = {}
    if st.session_state["edit_index"] is not None and st.session_state["edit_index"] < len(st.session_state["db_tersimpan"]):
        def_data = st.session_state["db_tersimpan"][st.session_state["edit_index"]]
    
    def get_val(key):
        return def_data.get(key, "")

    st.markdown("""
        <div class="dashboard-card" style="margin-top: 10px;">
            <h4 style="margin:0; color:#065f46; font-size:16px;">📝 Lembar Kerja 26 Kolom Identifikasi Kontrak & PI</h4>
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
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📂 Daftar Database Identifikasi Tersimpan (Excel)</h3>
        </div>
    """, unsafe_allow_html=True)
    
    saved_records = muat_data_invoice()
    if len(saved_records) > 0:
        df_saved = pd.DataFrame(saved_records)
        cols_prioritas = ["Proforma Invoice No.", "Contract No.", "Tender No", "Keterangan PO"]
        sisa_cols = [c for c in df_saved.columns if c not in cols_prioritas]
        df_saved = df_saved[cols_prioritas + sisa_cols]
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
            st.dataframe(pd.read_excel(pilih_file, sheet_name=sheet_pilih), use_container_width=True)
    else:
        st.warning("Belum ada file Master Kontrak di folder.")


# =========================================================================
# LOGIKA MODUL 2: INVOICE & DOKUMEN TURUNAN
# =========================================================================
elif menu == "Input & Proses Rincian Pekerjaan":
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📝 Lembar Kerja & Pemrosesan Rincian Pekerjaan</h3>
            <p style="color:#047857; font-size:13px; margin:0;">Isi form rincian pekerjaan di bawah ini. Tombol proses akan mendistribusikan data secara otomatis ke Proforma Invoice, WCC, Opname, BAMP, BASP, dan TKDN.</p>
        </div>
    """, unsafe_allow_html=True)

    with st.form("form_proses_rincian"):
        col1, col2 = st.columns(2)
        with col1:
            nomor_kontrak = st.text_input("Nomor Kontrak", "7207250142")
            nama_kontrak = st.text_input("Nama Kontrak", "Jasa Sewa Alat Berat Pendukung Operasional Senoro dan Tiaka")
            nomor_tender = st.text_input("Nomor Tender", "S250551FLD-R1")
            pi_no = st.text_input("Nomor Proforma Invoice (PI)", "042/BSS-JOB/AB/VII/2026")
            tanggal_pi = st.text_input("Tanggal Proforma Invoice", "31 Jul 2026")
        with col2:
            ditujukan_kepada = st.text_input("Ditujukan Kepada", "JOB Pertamina - Medco E&P Tomori Sulawesi")
            nomor_po = st.text_input("Nomor PO", "4500011424")
            desc_po = st.text_area("Deskripsi PO", "Jasa Sewa Backhoe Loader Untuk support Kegiatan Operation & Maintenance di Area Senoro dan Tiaka Periode Juli - September 2026")
            tanggal_po = st.text_input("Tanggal PO", "1 Jul 2026")
            mata_uang = st.text_input("Mata Uang", "IDR")

        st.markdown("---")
        st.markdown("#### ⚙️ Rincian Item Pekerjaan & Tarif")
        
        c_item1, c_item2, c_item3, c_item4 = st.columns([3, 1, 1, 1])
        with c_item1:
            deskripsi_pekerjaan = st.text_input("Spesifikasi / Deskripsi Pekerjaan", "Jasa Sewa Alat Berat Monthly Basis (Include Operator, Rigger, Helper, BBM & Sertifikasi), Backhoe Loader 70 - 100 HP")
        with c_item2:
            qty = st.number_input("Qty Out", value=1.0)
        with c_item3:
            unit = st.text_input("Unit", "Month")
        with c_item4:
            harga_satuan = st.number_input("Harga Satuan (Rp)", value=75538000.0, format="%.2f")

        keterangan_pekerjaan = st.text_input("Keterangan Pekerjaan", "Alat Beroperasi Periode 01 sd 31 Juli 2026")

        st.markdown("---")
        submit_proses = st.form_submit_button("🚀 Proses & Distribusikan Data ke Semua Dokumen Turunan")

        if submit_proses:
            total_harga = qty * harga_satuan
            data_transaksi = {
                "Nomor Kontrak": nomor_kontrak,
                "Nama Kontrak": nama_kontrak,
                "Nomor Tender": nomor_tender,
                "PI No.": pi_no,
                "Tanggal PI": tanggal_pi,
                "Ditujukan Kepada": ditujukan_kepada,
                "Nomor PO": nomor_po,
                "Deskripsi PO": desc_po,
                "Tanggal PO": tanggal_po,
                "Mata Uang": mata_uang,
                "Deskripsi Pekerjaan": deskripsi_pekerjaan,
                "Qty": qty,
                "Unit": unit,
                "Harga Satuan": harga_satuan,
                "Total Harga": total_harga,
                "Keterangan": keterangan_pekerjaan
            }
            
            existing_tx = muat_data_transaksi()
            existing_tx.append(data_transaksi)
            simpan_data_transaksi(existing_tx)
            
            st.success("🎉 Data Rincian Pekerjaan Berhasil Diproses dan Didistribusikan ke Seluruh Sheet Dokumen Turunan secara Otomatis!")

elif menu == "Pratinjau, Cetak & Download PDF Dokumen":
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">🖨️ Pratinjau, Cetak & Download PDF Dokumen Resmi</h3>
            <p style="color:#047857; font-size:13px; margin:0; color:#334155;">Pilih dokumen untuk melihat preview terang/jelas, lalu gunakan tombol klik mouse di bawah untuk mencetak atau mendownload PDF.</p>
        </div>
    """, unsafe_allow_html=True)

    transaksi_list = muat_data_transaksi()
    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi rincian pekerjaan yang diproses. Silakan lakukan input pada menu **Input & Proses Rincian Pekerjaan**.")
    else:
        pilihan_tx = [f"PI: {t['PI No.']} | Kontrak: {t['Nomor Kontrak']} | Total: Rp {t['Total Harga']:,.0f}" for t in transaksi_list]
        selected_idx = st.selectbox("Pilih Dokumen Transaksi Tersimpan:", range(len(pilihan_tx)), format_func=lambda x: pilihan_tx[x])
        
        t_data = transaksi_list[selected_idx]
        
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

        # GENERATE KONTEN DOKUMEN DALAM FORMAT HTML BERSIH (PUTIH / ANTI BOROS TINTA)
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{doc_type} - PT BSS</title>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; padding: 30px; margin: 0; }}
                .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px; }}
                .title {{ text-align: center; font-weight: bold; font-size: 16px; margin-bottom: 20px; text-transform: uppercase; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 15px; }}
                th, td {{ border: 1px solid #333; padding: 8px 12px; font-size: 12px; text-align: left; }}
                th {{ background-color: #f1f5f9; }}
                .footer-sign {{ margin-top: 40px; width: 100%; display: flex; justify-content: space-between; }}
                .sign-box {{ text-align: center; width: 45%; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2 style="margin: 0; font-size: 18px;">PT. BANGGAI SENTRAL SULAWESI</h2>
                <p style="margin: 2px 0; font-size: 11px;">Jl. Urip Sumoharjo No. 53 Luwuk, Kabupaten Banggai, Propinsi Sulawesi Tengah</p>
            </div>
            <div class="title">{doc_type}</div>
        """

        if doc_type == "Rincian Pekerjaan (Sheet Rincian Pek)":
            html_content += f"""
            <table style="border: none; margin-bottom: 20px;">
                <tr>
                    <td style="border: none; width: 50%;"><b>Nomor Kontrak:</b> {t_data['Nomor Kontrak']}</td>
                    <td style="border: none; width: 50%;"><b>Ditujukan Kepada:</b> {t_data['Ditujukan Kepada']}</td>
                </tr>
                <tr>
                    <td style="border: none;"><b>Nama Kontrak:</b> {t_data['Nama Kontrak']}</td>
                    <td style="border: none;"><b>Nomor PO:</b> {t_data['Nomor PO']}</td>
                </tr>
                <tr>
                    <td style="border: none;"><b>Nomor Tender:</b> {t_data['Nomor Tender']}</td>
                    <td style="border: none;"><b>Tanggal PO:</b> {t_data['Tanggal PO']}</td>
                </tr>
                <tr>
                    <td style="border: none;"><b>Tanggal Proforma:</b> {t_data['Tanggal PI']}</td>
                    <td style="border: none;"><b>Mata Uang:</b> {t_data['Mata Uang']}</td>
                </tr>
            </table>
            <table>
                <tr>
                    <th>No.</th>
                    <th>Kategori</th>
                    <th>Spesifikasi / Deskripsi</th>
                    <th>Qty Out</th>
                    <th>Unit</th>
                    <th>Harga Satuan (Rp)</th>
                    <th>Total Harga (Rp)</th>
                    <th>Keterangan</th>
                </tr>
                <tr>
                    <td>1</td>
                    <td>MONTHLY BASIS</td>
                    <td>{t_data['Deskripsi Pekerjaan']}</td>
                    <td>{t_data['Qty']}</td>
                    <td>{t_data['Unit']}</td>
                    <td>Rp {t_data['Harga Satuan']:,.2f}</td>
                    <td>Rp {t_data['Total Harga']:,.2f}</td>
                    <td>{t_data['Keterangan']}</td>
                </tr>
            </table>
            <p><b>TOTAL TAGIHAN: Rp {t_data['Total Harga']:,.2f}</b></p>
            <br><br>
            <table style="border: none; width: 100%;">
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
        elif doc_type == "Proforma Invoice":
            html_content += f"""
            <table style="border: none; margin-bottom: 20px;">
                <tr>
                    <td style="border: none;"><b>TO:</b><br>{t_data['Ditujukan Kepada']}<br>Indonesia</td>
                    <td style="border: none; text-align: right;"><b>PI No. :</b> {t_data['PI No.']}<br><b>Date :</b> {t_data['Tanggal PI']}<br><b>Contract No. :</b> {t_data['Nomor Kontrak']}</td>
                </tr>
            </table>
            <table>
                <tr>
                    <th>Item</th>
                    <th>Description</th>
                    <th>Qty</th>
                    <th>Unit</th>
                    <th>Unit Price (IDR)</th>
                    <th>TOTAL (IDR)</th>
                </tr>
                <tr>
                    <td>1</td>
                    <td>{t_data['Deskripsi Pekerjaan']}</td>
                    <td>{t_data['Qty']}</td>
                    <td>{t_data['Unit']}</td>
                    <td>Rp {t_data['Harga Satuan']:,.2f}</td>
                    <td>Rp {t_data['Total Harga']:,.2f}</td>
                </tr>
            </table>
            <h3>GRAND TOTAL: Rp {t_data['Total Harga']:,.2f}</h3>
            """
        else:
            html_content += f"""
            <p><b>Nomor Kontrak:</b> {t_data['Nomor Kontrak']}</p>
            <p><b>Nama Kontrak:</b> {t_data['Nama Kontrak']}</p>
            <p><b>Nilai Transaksi:</b> Rp {t_data['Total Harga']:,.2f}</p>
            <p>Dokumen resmi untuk <b>{doc_type}</b> telah terbit berdasarkan data transaksi sistem PT. Banggai Sentral Sulawesi.</p>
            """

        html_content += "</body></html>"

        # TAMPILAN PRATINJAU DI LAYAR (PUTIH BERSIH)
        st.markdown('<div class="document-preview">', unsafe_allow_html=True)
        st.components.v1.html(html_content, height=500, scrolling=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # TOMBOL KLIK MOUSE INTERAKTIF (PRINT & DOWNLOAD PDF OTOMATIS)
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            # Tombol Print Langsung dengan Klik Mouse
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
            # Tombol Download PDF Otomatis via Klik Mouse
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