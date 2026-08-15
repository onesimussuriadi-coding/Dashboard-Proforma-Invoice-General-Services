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
    .document-preview {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        border: 1px solid #94a3b8;
        color: #0f172a;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- SISTEM DATABASE EXCEL LOKAL ---
EXCEL_INVOICE = "database_proforma_invoice.xlsx"
EXCEL_TRANSAKSI = "database_transaksi_rincian.xlsx"

def muat_data_invoice():
    if os.path.exists(EXCEL_INVOICE):
        try: return pd.read_excel(EXCEL_INVOICE).to_dict(orient="records")
        except: return []
    return []

def simpan_data_invoice(data_list):
    pd.DataFrame(data_list).to_excel(EXCEL_INVOICE, index=False)

def muat_data_transaksi():
    if os.path.exists(EXCEL_TRANSAKSI):
        try: return pd.read_excel(EXCEL_TRANSAKSI).to_dict(orient="records")
        except: return []
    return []

def simpan_data_transaksi(data_list):
    pd.DataFrame(data_list).to_excel(EXCEL_TRANSAKSI, index=False)

if "edit_index" not in st.session_state: st.session_state["edit_index"] = None

# --- HEADER UTAMA ---
st.markdown('<div class="company-header-centered"><h2>PT. BANGGAI SENTRAL SULAWESI</h2></div>', unsafe_allow_html=True)

# --- SIDEBAR: NAVIGASI ---
modul_pilihan = st.sidebar.selectbox("Pilih Modul Utama:", ["📁 Modul 1: Database & Master Kontrak", "📄 Modul 2: Invoice & Dokumen Turunan"])
if modul_pilihan == "📁 Modul 1: Database & Master Kontrak":
    menu = st.sidebar.radio("Pilih Menu:", ["Input Database & Invoice (26 Kolom)", "Lihat Database Tersimpan", "Master Kontrak"])
else:
    menu = st.sidebar.radio("Pilih Menu:", ["Input & Proses Rincian Pekerjaan", "Pratinjau, Cetak & Download PDF Dokumen", "Lihat Akumulasi Riwayat Transaksi"])

# =========================================================================
# LOGIKA MODUL 2 (KOREKSI INPUT KOSONG)
# =========================================================================
if menu == "Input & Proses Rincian Pekerjaan":
    st.markdown('<div class="dashboard-card"><h3>📝 Input Rincian Pekerjaan</h3></div>', unsafe_allow_html=True)
    with st.form("form_proses_rincian"):
        col1, col2 = st.columns(2)
        with col1:
            nomor_kontrak = st.text_input("Nomor Kontrak", "")
            nama_kontrak = st.text_input("Nama Kontrak", "")
            nomor_tender = st.text_input("Nomor Tender", "")
            pi_no = st.text_input("Nomor Proforma Invoice (PI)", "")
            tanggal_pi = st.text_input("Tanggal Proforma Invoice", "")
        with col2:
            ditujukan_kepada = st.text_input("Ditujukan Kepada", "")
            nomor_po = st.text_input("Nomor PO", "")
            desc_po = st.text_area("Deskripsi PO", "")
            tanggal_po = st.text_input("Tanggal PO", "")
            mata_uang = st.text_input("Mata Uang", "")

        c_item1, c_item2, c_item3, c_item4 = st.columns([3, 1, 1, 1])
        with c_item1: deskripsi_pekerjaan = st.text_input("Spesifikasi / Deskripsi Pekerjaan", "")
        with c_item2: qty = st.number_input("Qty Out", value=0.0)
        with c_item3: unit = st.text_input("Unit", "")
        with c_item4: harga_satuan = st.number_input("Harga Satuan (Rp)", value=0.0, format="%.2f")

        keterangan_pekerjaan = st.text_input("Keterangan Pekerjaan", "")
        submit_proses = st.form_submit_button("🚀 Proses & Distribusikan Data")

        if submit_proses:
            total_harga = qty * harga_satuan
            data_transaksi = {
                "Nomor Kontrak": nomor_kontrak, "Nama Kontrak": nama_kontrak, "Nomor Tender": nomor_tender,
                "PI No.": pi_no, "Tanggal PI": tanggal_pi, "Ditujukan Kepada": ditujukan_kepada,
                "Nomor PO": nomor_po, "Deskripsi PO": desc_po, "Tanggal PO": tanggal_po,
                "Mata Uang": mata_uang, "Deskripsi Pekerjaan": deskripsi_pekerjaan,
                "Qty": qty, "Unit": unit, "Harga Satuan": harga_satuan,
                "Total Harga": total_harga, "Keterangan": keterangan_pekerjaan
            }
            existing_tx = muat_data_transaksi()
            existing_tx.append(data_transaksi)
            simpan_data_transaksi(existing_tx)
            st.success("🎉 Data berhasil diproses!")

elif menu == "Pratinjau, Cetak & Download PDF Dokumen":
    transaksi_list = muat_data_transaksi()
    if transaksi_list:
        selected_idx = st.selectbox("Pilih Dokumen:", range(len(transaksi_list)), format_func=lambda x: f"Kontrak: {transaksi_list[x]['Nomor Kontrak']}")
        t_data = transaksi_list[selected_idx]
        doc_type = st.selectbox("Pilih Jenis Dokumen:", ["Rincian Pekerjaan (Sheet Rincian Pek)", "Proforma Invoice"])
        
        # HTML Content
        html_content = f"<html><body><h2>{doc_type}</h2><p>Kontrak: {t_data['Nomor Kontrak']}</p></body></html>"
        
        st.markdown('<div class="document-preview">', unsafe_allow_html=True)
        st.components.v1.html(html_content, height=400)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Tombol Klik Murni
        col1, col2 = st.columns(2)
        if col1.button("🖨️ Cetak Dokumen"):
            st.write('<script>window.print();</script>', unsafe_allow_html=True)
        b64 = base64.b64encode(html_content.encode()).decode()
        col2.markdown(f'<a href="data:text/html;base64,{b64}" download="Doc.html"><button>📥 Download</button></a>', unsafe_allow_html=True)

# [Sisa kode lainnya (Input 26 Kolom, dll) dapat Anda tempel di sini kembali...]