import streamlit as st
import pandas as pd
import os

# Konfigurasi Halaman Khusus Modul Proforma Invoice & Dokumen Turunan
st.set_page_config(page_title="Modul Proforma Invoice & Dokumen - PT. Banggai Sentral Sulawesi", layout="wide")

# Pastikan folder database ada
DIR_DATABASE = "database_penyimpanan_aman"
if not os.path.exists(DIR_DATABASE):
    os.makedirs(DIR_DATABASE)

# CSS Styling Profesional
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
    .dashboard-card { background-color: #ecfdf5; border: 1px solid #a7f3d0; padding: 15px 20px; border-radius: 8px; margin-bottom: 15px; }
    .document-preview { background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #cbd5e1; color: #000000; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: 600; background-color: #10b981; color: white; }
    </style>
""", unsafe_allow_html=True)

EXCEL_TRANSAKSI = os.path.join(DIR_DATABASE, "database_transaksi_rincian.xlsx")
EXCEL_MASTER_REF = os.path.join(DIR_DATABASE, "database_master_referensi.xlsx")

def muat_data_transaksi():
    if os.path.exists(EXCEL_TRANSAKSI):
        try:
            df = pd.read_excel(EXCEL_TRANSAKSI)
            if df is not None and not df.empty: return df.dropna(how='all').to_dict(orient="records")
        except: return []
    return []

def simpan_data_transaksi(data_list):
    pd.DataFrame(data_list).to_excel(EXCEL_TRANSAKSI, index=False)
    st.session_state["db_transaksi"] = data_list

def muat_master_referensi():
    if os.path.exists(EXCEL_MASTER_REF):
        try:
            df = pd.read_excel(EXCEL_MASTER_REF)
            if df is not None and not df.empty: return df.to_dict(orient="records")
        except: pass
    return []

if "db_transaksi" not in st.session_state: st.session_state["db_transaksi"] = muat_data_transaksi()
if "list_mutasi_sementara" not in st.session_state: st.session_state["list_mutasi_sementara"] = []

st.markdown("""<div class="company-header-centered"><h2>PT. BANGGAI SENTRAL SULAWESI</h2><p>General Contractor and Suppliers | Modul Invoice & Dokumen Turunan</p></div>""", unsafe_allow_html=True)

menu_inv = st.sidebar.selectbox("Pilih Aktivitas:", ["Input & Proses Rincian Pekerjaan", "Pratinjau & Cetak Dokumen Turunan (Hardcopy)", "Lihat Akumulasi Riwayat Transaksi"])

# --- MODUL INPUT (MULTI-MUTASI) ---
if menu_inv == "Input & Proses Rincian Pekerjaan":
    st.markdown('<div class="dashboard-card"><h3>📝 Input Multi-Mutasi</h3></div>', unsafe_allow_html=True)
    master_ref = muat_master_referensi()
    
    with st.form("form_induk"):
        col1, col2 = st.columns(2)
        pi_no = col1.text_input("Nomor PI", value="042/BSS-JOB/AB/VII/2026")
        nomor_kontrak = col2.text_input("Nomor Kontrak", value="7207250142")
        submitted_induk = st.form_submit_button("💾 Kunci Data Induk")

    with st.form("form_item"):
        kat = st.selectbox("Kategori", list(set([m.get("Kategori", "MONTHLY") for m in master_ref])) if master_ref else ["MONTHLY"])
        desk = st.selectbox("Spesifikasi", [m.get("Uraian Pekerjaan", "-") for m in master_ref if m.get("Kategori") == kat])
        c1, c2 = st.columns(2)
        qty = c1.number_input("Qty", value=1.0)
        unit = c2.text_input("Unit", value="Month")
        c3, c4 = st.columns(2)
        tm = c3.date_input("Tanggal Mulai")
        ts = c4.date_input("Tanggal Selesai")
        hs = st.number_input("Harga Satuan", value=0.0)
        if st.form_submit_button("➕ Tambah ke Daftar"):
            st.session_state["list_mutasi_sementara"].append({
                "PI No.": pi_no, "Nomor Kontrak": nomor_kontrak, "Kategori": kat,
                "Deskripsi Pekerjaan": desk, "Qty": qty, "Unit": unit,
                "Tanggal Mulai": tm.strftime("%d %b %Y"), "Tanggal Selesai": ts.strftime("%d %b %Y"),
                "Harga Satuan": hs, "Total Harga": qty * hs
            })
            st.rerun()

    if st.session_state["list_mutasi_sementara"]:
        for i, it in enumerate(st.session_state["list_mutasi_sementara"]):
            if st.button(f"🗑️ Hapus {i+1}", key=f"d_{i}"):
                st.session_state["list_mutasi_sementara"].pop(i); st.rerun()
            st.write(f"{it['Deskripsi Pekerjaan']} | {it['Qty']} {it['Unit']} | {it['Tanggal Mulai']} s/d {it['Tanggal Selesai']}")
        if st.button("🚀 Simpan Semua ke Database"):
            data = muat_data_transaksi()
            data.extend(st.session_state["list_mutasi_sementara"])
            simpan_data_transaksi(data)
            st.session_state["list_mutasi_sementara"] = []
            st.rerun()# --- 2. PRATINJAU & CETAK DOKUMEN TURUNAN ---
elif menu_inv == "Pratinjau & Cetak Dokumen Turunan (Hardcopy)":
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">🖨️ Pratinjau & Cetak Dokumen Resmi</h3>
            <p style="color:#047857; font-size:13px; margin:0;">Dokumen akan otomatis membaca seluruh baris mutasi berdasarkan Nomor PI yang dipilih.</p>
        </div>
    """, unsafe_allow_html=True)

    transaksi_list = muat_data_transaksi()
    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi tersimpan.")
    else:
        unique_pi = list(set([str(t.get('PI No.', '')) for t in transaksi_list if t.get('PI No.')]))
        selected_pi = st.selectbox("Pilih Nomor Proforma Invoice (PI):", unique_pi)

        mutasi_terpilih = [t for t in transaksi_list if str(t.get('PI No.')) == str(selected_pi)]
        
        if mutasi_terpilih:
            t_data_utama = mutasi_terpilih[0]

            doc_type = st.selectbox("Pilih Jenis Dokumen untuk Dicetak:", [
                "Rincian Pekerjaan",
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

            # --- LOGIKA PRATINJAU DOKUMEN (ASLI BAPAK) ---
            if doc_type == "Rincian Pekerjaan":
                st.markdown("<h4 style='text-align: center; margin-bottom: 20px;'>RINCIAN PEKERJAAN</h4>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    st.text(f"Nomor Kontrak    : {t_data_utama.get('Nomor Kontrak', '-')}")
                    st.text(f"Nama Kontrak     : {t_data_utama.get('Nama Kontrak', '-')}")
                with c2:
                    st.text(f"Ditujukan Kepada : {t_data_utama.get('Ditujukan Kepada', '-')}")
                    st.text(f"Nomor PO         : {t_data_utama.get('Nomor PO', '-')}")
                
                tabel_data = []
                for idx, m in enumerate(mutasi_terpilih, start=1):
                    tabel_data.append({"No": idx, "Deskripsi": m.get('Deskripsi Pekerjaan', '-'), "Qty": m.get('Qty', 0), "Unit": m.get('Unit', '-'), "Total": f"Rp {float(m.get('Total Harga', 0)):,.2f}"})
                st.table(pd.DataFrame(tabel_data))

            elif doc_type == "Proforma Invoice":
                st.markdown("<h3 style='text-align: center;'>PROFORMA INVOICE</h3>", unsafe_allow_html=True)
                # ... (Silakan pastikan seluruh blok kode pratinjau asli Bapak untuk WCC, BASP, dll tetap berada di sini) ...
                st.write("Pratinjau dokumen siap ditampilkan.")

            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("🖨️ Cetak / Print Dokumen Ini"):
                st.success("💡 Tekan Ctrl + P untuk mencetak.")

# --- 3. LIHAT AKUMULASI RIWAYAT TRANSAKSI ---
elif menu_inv == "Lihat Akumulasi Riwayat Transaksi":
    st.markdown("### 📂 Akumulasi Riwayat Transaksi")
    tx_records = muat_data_transaksi()
    if tx_records:
        st.dataframe(pd.DataFrame(tx_records), use_container_width=True)