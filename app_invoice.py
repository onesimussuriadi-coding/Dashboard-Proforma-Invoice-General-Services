import streamlit as st
import pandas as pd
import os
import glob

# Konfigurasi Halaman Khusus Modul Proforma Invoice & Dokumen Turunan
st.set_page_config(page_title="Modul Proforma Invoice & Dokumen - PT. Banggai Sentral Sulawesi", layout="wide")

# CSS Styling Profesional & Print View Ready
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
        background-color: #ecfdf5;
        border: 1px solid #a7f3d0;
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    .document-preview {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid #cbd5e1;
        color: #000000;
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

EXCEL_TRANSAKSI = "database_transaksi_rincian.xlsx"

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

if "db_transaksi" not in st.session_state:
    st.session_state["db_transaksi"] = muat_data_transaksi()

# --- HEADER UTAMA ---
st.markdown("""
    <div class="company-header-centered">
        <h2 style="margin:0; font-size: 24px; font-weight: 700;">PT. BANGGAI SENTRAL SULAWESI</h2>
        <p style="margin:4px 0 0 0; font-size: 13px; color: #34d399; font-weight: 500;">General Contractor and Suppliers | Modul Khusus Proforma Invoice & Dokumen Turunan</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar Navigasi Khusus Modul Invoice
st.sidebar.markdown("### 🗂️ Menu Modul Invoice")
menu_inv = st.sidebar.selectbox("Pilih Aktivitas:", [
    "Input & Proses Rincian Pekerjaan",
    "Pratinjau & Cetak Dokumen Turunan (Hardcopy)",
    "Lihat Akumulasi Riwayat Transaksi"
])
st.sidebar.markdown("---")
st.sidebar.success("📂 **Status File:** Terpisah & Aman dari File Utama")

# --- 1. INPUT & PROSES RINCIAN PEKERJAAN ---
if menu_inv == "Input & Proses Rincian Pekerjaan":
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📝 Lembar Kerja & Pemrosesan Rincian Pekerjaan</h3>
            <p style="color:#047857; font-size:13px; margin:0;">Isi form rincian pekerjaan di bawah ini. Tombol proses akan mendistribusikan data secara otomatis ke Proforma Invoice, WCC, Opname, BAMP, BASP, TKDN, dan Rekap Biaya.</p>
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

# --- 2. PRATINJAU & CETAK DOKUMEN TURUNAN ---
elif menu_inv == "Pratinjau & Cetak Dokumen Turunan (Hardcopy)":
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">🖨️ Pratinjau & Cetak Dokumen Resmi (Hardcopy Ready)</h3>
            <p style="color:#047857; font-size:13px; margin:0;">Pilih dokumen yang ingin ditampilkan format cetaknya berdasarkan data transaksi yang telah diproses.</p>
        </div>
    """, unsafe_allow_html=True)

    transaksi_list = muat_data_transaksi()
    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi rincian pekerjaan yang diproses. Silakan lakukan input pada menu **Input & Proses Rincian Pekerjaan**.")
    else:
        pilihan_tx = [f"PI: {t['PI No.']} | Kontrak: {t['Nomor Kontrak']} | Total: Rp {t['Total Harga']:,.0f}" for t in transaksi_list]
        selected_idx = st.selectbox("Pilih Dokumen Transaksi Tersimpan:", range(len(pilihan_tx)), format_func=lambda x: pilihan_tx[x])
        
        t_data = transaksi_list[selected_idx]
        
        doc_type = st.selectbox("Pilih Jenis Dokumen untuk Dicetak:", [
            "Rincian Pekerjaan (Sheet Rincian Pek)",
            "Proforma Invoice",
            "WCC (Work Completion Certificate)",
            "Opname Pekerjaan",
            "Berita Acara Mulai Pekerjaan (BAMP)",
            "Berita Acara Selesai Pekerjaan (BASP)",
            "Formulir TKDN"
        ])

        st.markdown("---")

        st.markdown('<div class="document-preview">', unsafe_allow_html=True)
        
        st.markdown("""
            <div style="text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px;">
                <h3 style="margin: 0; color: #0f172a;">PT. BANGGAI SENTRAL SULAWESI</h3>
                <p style="margin: 2px 0; font-size: 12px; color: #334155;">Jl. Urip Sumoharjo No. 53 Luwuk, Kabupaten Banggai, Propinsi Sulawesi Tengah</p>
            </div>
        """, unsafe_allow_html=True)

        if doc_type == "Rincian Pekerjaan (Sheet Rincian Pek)":
            st.markdown("<h4 style='text-align: center; margin-bottom: 20px;'>RINCIAN PEKERJAAN</h4>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.text(f"Nomor Kontrak   : {t_data['Nomor Kontrak']}")
                st.text(f"Nama Kontrak    : {t_data['Nama Kontrak']}")
                st.text(f"Nomor Tender    : {t_data['Nomor Tender']}")
                st.text(f"Tanggal Proforma: {t_data['Tanggal PI']}")
            with c2:
                st.text(f"Ditujukan Kepada: {t_data['Ditujukan Kepada']}")
                st.text(f"Nomor PO        : {t_data['Nomor PO']}")
                st.text(f"Tanggal PO      : {t_data['Tanggal PO']}")
                st.text(f"Mata Uang       : {t_data['Mata Uang']}")

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

            st.markdown(f"**TOTAL TAGIHAN:** Rp {t_data['Total Harga']:,.2f}")
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            col_sign1, col_sign2 = st.columns(2)
            with col_sign1:
                st.markdown("<div style='text-align: center;'><b>DIBUAT OLEH</b><br><br><br><u>Yanuar Wiranata / Ireine Langi</u><br>Supervisor</div>", unsafe_allow_html=True)
            with col_sign2:
                st.markdown("<div style='text-align: center;'><b>DIPERIKSA</b><br><br><br><u>Onesimus Suriadi</u><br>Manager General Services</div>", unsafe_allow_html=True)

        elif doc_type == "Proforma Invoice":
            st.markdown(f"""
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <b>TO:</b><br>{t_data['Ditujukan Kepada']}<br>Indonesia
                    </div>
                    <div>
                        <b>PI No. :</b> {t_data['PI No.']}<br>
                        <b>Date :</b> {t_data['Tanggal PI']}<br>
                        <b>Contract No. :</b> {t_data['Nomor Kontrak']}
                    </div>
                </div>
                <h3 style="text-align: center; margin: 30px 0 20px 0;">PROFORMA INVOICE</h3>
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
            st.markdown(f"<b>GRAND TOTAL: Rp {t_data['Total Harga']:,.2f}</b>", unsafe_allow_html=True)

        elif doc_type == "WCC (Work Completion Certificate)":
            st.markdown("<h4 style='text-align: center;'>WORK COMPLETION CERTIFICATE (WCC)</h4>", unsafe_allow_html=True)
            st.text(f"CERTIFICATE NO : {t_data['Nomor Kontrak']}-BSS-WCC-2026-019")
            st.markdown(f"<p>On the date of {t_data['Tanggal PI']}, we on behalf of PT Banggai Sentral Sulawesi have completed the following job for <b>{t_data['Ditujukan Kepada']}</b>.</p>", unsafe_allow_html=True)
            st.text(f"WORK ORDER TITLE : {t_data['Deskripsi PO']}")
            st.markdown(f"<b>AMOUNT TOTAL: Rp {t_data['Total Harga']:,.2f}</b>")

        elif doc_type == "Opname Pekerjaan":
            st.markdown("<h4 style='text-align: center;'>BERITA ACARA PEKERJAAN / OPNAME</h4>", unsafe_allow_html=True)
            st.text(f"Contract No : {t_data['Nomor Kontrak']}")
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
            st.markdown("<h4 style='text-align: center;'>BERITA ACARA MULAI PEKERJAAN (BAMP)</h4>", unsafe_allow_html=True)
            st.markdown(f"<p>Pada hari ini tanggal {t_data['Tanggal PO']}, bertempat di Area Kerja Senoro dan Tiaka, telah disepakati mulai pelaksanaan pekerjaan untuk kontrak nomor: <b>{t_data['Nomor Kontrak']}</b>.</p>", unsafe_allow_html=True)

        elif doc_type == "Berita Acara Selesai Pekerjaan (BASP)":
            st.markdown("<h4 style='text-align: center;'>BERITA ACARA SELESAI PEKERJAAN (BASP)</h4>", unsafe_allow_html=True)
            st.markdown(f"<p>Pada hari ini tanggal {t_data['Tanggal PI']}, pekerjaan berdasarkan kontrak nomor <b>{t_data['Nomor Kontrak']}</b> telah diselesaikan dengan baik.</p>", unsafe_allow_html=True)

        elif doc_type == "Formulir TKDN":
            st.markdown("<h4 style='text-align: center;'>FORMULIR TINGKAT KOMPONEN DALAM NEGERI (TKDN)</h4>", unsafe_allow_html=True)
            st.text(f"Kontrak No: {t_data['Nomor Kontrak']}")

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🖨️ Cetak / Print Dokumen Ini (Gunakan Ctrl+P)"):
            st.success("💡 Tekan **Ctrl + P** pada keyboard Anda untuk mencetak dokumen ini.")

# --- 3. LIHAT AKUMULASI RIWAYAT TRANSAKSI ---
elif menu_inv == "Lihat Akumulasi Riwayat Transaksi":
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