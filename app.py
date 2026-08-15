import streamlit as st
import pandas as pd
import os
import glob

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Terintegrasi - PT. Banggai Sentral Sulawesi", layout="wide")

# CSS Styling Profesional (Tampilan Terang & Ramah Mata untuk Pratinjau Dokumen)
st.markdown("""
    <style>
    .main { background-color: #f1f5f9; }
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
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 15px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }
    /* Kotak Pratinjau Dokumen dengan Warna Terang/Abu-abu Lembut */
    .document-preview {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #cbd5e1;
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
    /* Sembunyikan elemen sidebar saat dicetak */
    @media print {
        [data-testid="stSidebar"] { display: none; }
        .stButton { display: none; }
        .document-preview { border: none; box-shadow: none; padding: 0; }
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

# --- SIDEBAR: NAVIGASI 2 TINGKAT (2 MODUL UTAMA) ---
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
            <p style="color:#047857; font-size:13px; margin:0; color:#334155;">Pilih dokumen untuk melihat preview terang/jelas, lalu gunakan tombol cetak untuk mencetak atau menyimpan sebagai PDF.</p>
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

        # AREA PRATINJAU DOKUMEN (LATAR PUTIH BERSIH & KONTRAS TINGGI)
        st.markdown('<div class="document-preview">', unsafe_allow_html=True)
        
        # Kop Surat Terang & Jelas
        st.markdown("""
            <div style="text-align: center; border-bottom: 2px solid #0f172a; padding-bottom: 12px; margin-bottom: 25px;">
                <h3 style="margin: 0; color: #0f172a; font-size: 20px; font-weight: 700;">PT. BANGGAI SENTRAL SULAWESI</h3>
                <p style="margin: 4px 0 0 0; font-size: 13px; color: #475569; font-weight: 500;">Jl. Urip Sumoharjo No. 53 Luwuk, Kabupaten Banggai, Propinsi Sulawesi Tengah</p>
            </div>
        """, unsafe_allow_html=True)

        if doc_type == "Rincian Pekerjaan (Sheet Rincian Pek)":
            st.markdown("<h4 style='text-align: center; margin-bottom: 20px; color: #0f172a;'>RINCIAN PEKERJAAN</h4>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Nomor Kontrak &nbsp;&nbsp;&nbsp;:** {t_data['Nomor Kontrak']}")
                st.markdown(f"**Nama Kontrak &nbsp;&nbsp;&nbsp;&nbsp;:** {t_data['Nama Kontrak']}")
                st.markdown(f"**Nomor Tender &nbsp;&nbsp;&nbsp;&nbsp;:** {t_data['Nomor Tender']}")
                st.markdown(f"**Tanggal Proforma :** {t_data['Tanggal PI']}")
            with c2:
                st.markdown(f"**Ditujukan Kepada :** {t_data['Ditujukan Kepada']}")
                st.markdown(f"**Nomor PO &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:** {t_data['Nomor PO']}")
                st.markdown(f"**Tanggal PO &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:** {t_data['Tanggal PO']}")
                st.markdown(f"**Mata Uang &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:** {t_data['Mata Uang']}")

            st.markdown("<br>", unsafe_allow_html=True)
            
            df_table = pd.DataFrame([{
                "No": 1,
                "Kategori": "MONTHLY BASIS",
                "Spesifikasi / Deskripsi": t_data['Deskripsi Pekerjaan'],
                "Out Qty": t_data['Qty'],
                "Unit": t_data['Unit'],
                "Harga Satuan (Rp)": f"Rp {t_data['Harga Satuan']:,.2f}",
                "Total Harga (Rp)": f"Rp {t_data['Total Harga']:,.2f}",
                "Keterangan": t_data['Keterangan']
            }])
            st.table(df_table)

            st.markdown(f"<h5 style='color: #0f172a;'>TOTAL TAGIHAN: Rp {t_data['Total Harga']:,.2f}</h5>", unsafe_allow_html=True)
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            col_sign1, col_sign2 = st.columns(2)
            with col_sign1:
                st.markdown("<div style='text-align: center; color: #0f172a;'><b>DIBUAT OLEH</b><br><br><br><br><u>Yanuar Wiranata / Ireine Langi</u><br>Supervisor</div>", unsafe_allow_html=True)
            with col_sign2:
                st.markdown("<div style='text-align: center; color: #0f172a;'><b>DIPERIKSA</b><br><br><br><br><u>Onesimus Suriadi</u><br>Manager General Services</div>", unsafe_allow_html=True)

        elif doc_type == "Proforma Invoice":
            st.markdown(f"""
                <div style="display: flex; justify-content: space-between; color: #0f172a;">
                    <div>
                        <b>TO:</b><br>{t_data['Ditujukan Kepada']}<br>Indonesia
                    </div>
                    <div>
                        <b>PI No. :</b> {t_data['PI No.']}<br>
                        <b>Date :</b> {t_data['Tanggal PI']}<br>
                        <b>Contract No. :</b> {t_data['Nomor Kontrak']}
                    </div>
                </div>
                <h3 style="text-align: center; margin: 30px 0 20px 0; color: #0f172a;">PROFORMA INVOICE</h3>
            """, unsafe_allow_html=True)

            df_pi = pd.DataFrame([{
                "Item": "1",
                "Description": t_data['Deskripsi Pekerjaan'],
                "Qty": t_data['Qty'],
                "Unit": t_data['Unit'],
                "Unit Price (IDR)": f"Rp {t_data['Harga Satuan']:,.2f}",
                "TOTAL (IDR)": f"Rp {t_data['Total Harga']:,.2f}"
            }])
            st.table(df_pi)
            st.markdown(f"<h4 style='color: #0f172a;'>GRAND TOTAL: Rp {t_data['Total Harga']:,.2f}</h4>", unsafe_allow_html=True)

        elif doc_type == "WCC (Work Completion Certificate)":
            st.markdown("<h4 style='text-align: center; color: #0f172a;'>WORK COMPLETION CERTIFICATE (WCC)</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: #0f172a;'><b>CERTIFICATE NO :</b> {t_data['Nomor Kontrak']}-BSS-WCC-2026-019</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: #0f172a;'>On the date of {t_data['Tanggal PI']}, we on behalf of PT Banggai Sentral Sulawesi have completed the following job for <b>{t_data['Ditujukan Kepada']}</b>.</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: #0f172a;'><b>WORK ORDER TITLE :</b> {t_data['Deskripsi PO']}</p>", unsafe_allow_html=True)
            st.markdown(f"<h5 style='color: #0f172a;'>AMOUNT TOTAL: Rp {t_data['Total Harga']:,.2f}</h5>", unsafe_allow_html=True)

        elif doc_type == "Opname Pekerjaan":
            st.markdown("<h4 style='text-align: center; color: #0f172a;'>BERITA ACARA PEKERJAAN / OPNAME</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: #0f172a;'><b>Contract No :</b> {t_data['Nomor Kontrak']}</p>", unsafe_allow_html=True)
            df_opname = pd.DataFrame([{
                "No": "1.1",
                "Item - Description": t_data['Deskripsi Pekerjaan'],
                "Volume Aktual": t_data['Qty'],
                "Unit": t_data['Unit'],
                "Unit Price": f"Rp {t_data['Harga Satuan']:,.2f}",
                "Total Price": f"Rp {t_data['Total Harga']:,.2f}"
            }])
            st.table(df_opname)

        elif doc_type == "Berita Acara Mulai Pekerjaan (BAMP)":
            st.markdown("<h4 style='text-align: center; color: #0f172a;'>BERITA ACARA MULAI PEKERJAAN (BAMP)</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: #0f172a;'>Pada hari ini tanggal {t_data['Tanggal PO']}, bertempat di Area Kerja Senoro dan Tiaka, telah disepakati mulai pelaksanaan pekerjaan untuk kontrak nomor: <b>{t_data['Nomor Kontrak']}</b>.</p>", unsafe_allow_html=True)

        elif doc_type == "Berita Acara Selesai Pekerjaan (BASP)":
            st.markdown("<h4 style='text-align: center; color: #0f172a;'>BERITA ACARA SELESAI PEKERJAAN (BASP)</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: #0f172a;'>Pada hari ini tanggal {t_data['Tanggal PI']}, pekerjaan berdasarkan kontrak nomor <b>{t_data['Nomor Kontrak']}</b> telah diselesaikan dengan baik.</p>", unsafe_allow_html=True)

        elif doc_type == "Formulir TKDN":
            st.markdown("<h4 style='text-align: center; color: #0f172a;'>FORMULIR TINGKAT KOMPONEN DALAM NEGERI (TKDN)</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: #0f172a;'><b>Kontrak No:</b> {t_data['Nomor Kontrak']}</p>", unsafe_allow_html=True)
            st.markdown("<p style='color: #0f172a;'>Rekapitulasi komponen barang, jasa, dan tenaga kerja dalam negeri memenuhi ketentuan TKDN PT. Banggai Sentral Sulawesi.</p>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Tombol Cetak / Download PDF Profesional
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if st.button("🖨️ Cetak Dokumen (Print Preview)"):
                st.markdown("""
                    <script>
                        window.print();
                    </script>
                """, unsafe_allow_html=True)
                st.success("✨ Jendela Print / Cetak telah dipanggil! (Atau tekan Ctrl+P untuk mencetak dan pilih 'Save as PDF').")
        with col_p2:
            st.info("💡 **Tips Download PDF:** Klik tombol cetak di atas, lalu pada jendela *printer*, ubah tujuan (*Destination*) menjadi **'Save as PDF'**.")

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