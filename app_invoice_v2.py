import streamlit as st
import pandas as pd
import os

# Konfigurasi Halaman Khusus Modul Proforma Invoice & Dokumen Turunan
st.set_page_config(page_title="Modul Proforma Invoice & Dokumen - PT. Banggai Sentral Sulawesi", layout="wide")

# Pastikan folder database ada
DIR_DATABASE = "database_penyimpanan_aman"
if not os.path.exists(DIR_DATABASE):
    os.makedirs(DIR_DATABASE)

# CSS Styling Profesional (Sama Persis Asli)
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

EXCEL_TRANSAKSI = os.path.join(DIR_DATABASE, "database_transaksi_rincian.xlsx")
TS_DB_PATH = os.path.join(DIR_DATABASE, "database_timesheet_history.xlsx")
EXCEL_MASTER_REF = os.path.join(DIR_DATABASE, "database_master_referensi.xlsx")

def muat_data_transaksi():
    if os.path.exists(EXCEL_TRANSAKSI):
        try:
            df = pd.read_excel(EXCEL_TRANSAKSI)
            if df is not None and not df.empty:
                return df.dropna(how='all').to_dict(orient="records")
        except:
            return []
    return []

def simpan_data_transaksi(data_list):
    df = pd.DataFrame(data_list)
    df.to_excel(EXCEL_TRANSAKSI, index=False)
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

if "db_transaksi" not in st.session_state:
    st.session_state["db_transaksi"] = muat_data_transaksi()
if "sync" not in st.session_state:
    st.session_state["sync"] = None

# Inisialisasi Keranjang Mutasi Sementara di Session State
if "list_mutasi_sementara" not in st.session_state:
    st.session_state["list_mutasi_sementara"] = []

# --- HEADER UTAMA ---
st.markdown("""
    <div class="company-header-centered">
        <h2 style="margin:0; font-size: 24px; font-weight: 700;">PT. BANGGAI SENTRAL SULAWESI</h2>
        <p style="margin:4px 0 0 0; font-size: 13px; color: #34d399; font-weight: 500;">General Contractor and Suppliers | Modul Khusus Proforma Invoice & Dokumen Turunan (Multi-Mutasi)</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar Navigasi Asli Bersih (Tanpa Teks Tersisip)
st.sidebar.markdown("### 🗂️ Menu Modul Invoice")
menu_inv = st.sidebar.selectbox("Pilih Aktivitas:", [
    "Input & Proses Rincian Pekerjaan",
    "Pratinjau & Cetak Dokumen Turunan (Hardcopy)",
    "Lihat Akumulasi Riwayat Transaksi"
])
st.sidebar.markdown("---")
st.sidebar.success("📂 **Status File:** Terhubung ke Database Aman")

# --- 1. INPUT & PROSES RINCIAN PEKERJAAN (MULTI-MUTASI) ---
if menu_inv == "Input & Proses Rincian Pekerjaan":
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📝 Lembar Kerja Multi-Mutasi Rincian Pekerjaan</h3>
            <p style="color:#047857; font-size:13px; margin:0;">Tambahkan beberapa baris mutasi/item pekerjaan, lalu simpan sekaligus untuk satu Nomor Proforma Invoice (PI).</p>
        </div>
    """, unsafe_allow_html=True)

    master_ref_data = muat_master_referensi()

    # Bagian Data Induk (Header Dokumen)
    with st.form("form_data_induk"):
        col1, col2 = st.columns(2)
        with col1:
            nomor_kontrak = st.text_input("Nomor Kontrak", value="7207250142")
            nama_kontrak = st.text_input("Nama Kontrak", value="Jasa Sewa Alat Berat Pendukung Operasional Senoro dan Tiaka")
            nomor_tender = st.text_input("Nomor Tender", value="S250551FLD-R1")
            pi_no = st.text_input("Nomor Proforma Invoice (PI)", value="042/BSS-JOB/AB/VII/2026")
            tanggal_pi = st.text_input("Tanggal Proforma Invoice", value="31 Jul 2026")
        with col2:
            ditujukan_kepada = st.text_input("Ditujukan Kepada", value="JOB Pertamina - Medco E&P Tomori Sulawesi")
            nomor_po = st.text_input("Nomor PO", value="4500011424")
            desc_po = st.text_area("Deskripsi / Lingkup PO", value="Jasa Sewa Alat Berat Untuk support Kegiatan Operation & Maintenance")
            tanggal_po = st.text_input("Tanggal PO", value="1 Jul 2026")
            mata_uang = st.text_input("Mata Uang", value="IDR")

        submitted_induk = st.form_submit_button("💾 Kunci Data Induk (Lanjut Input Item Mutasi)")
        if submitted_induk:
            st.success("Data induk berhasil dikunci! Silakan tambahkan baris mutasi di bawah.")

    st.markdown("---")
    st.markdown("#### ⚙️ Tambah Baris Mutasi / Item Pekerjaan")

    # Form untuk Menambahkan Item ke Keranjang Sementara
    with st.form("form_tambah_item"):
        list_kat = list(set([str(m.get("Kategori", "")).strip() for m in master_ref_data if m.get("Kategori")])) if master_ref_data else ["MONTHLY BASIS", "DAILY BASIS", "JASA MOBILISASI", "ON-CALL BASIS"]
        kategori_pilih = st.selectbox("Kategori Pekerjaan", list_kat)

        list_spek = [str(m.get("Uraian Pekerjaan", "")).strip() for m in master_ref_data if str(m.get("Kategori", "")).strip() == str(kategori_pilih).strip()] if master_ref_data else ["Jasa Sewa Alat Berat"]
        if not list_spek:
            list_spek = ["Jasa Sewa Alat Berat"]

        deskripsi_pekerjaan = st.selectbox("Spesifikasi / Uraian Pekerjaan", list_spek)

        harga_satuan_otomatis = 0.0
        unit_otomatis = "Month"
        if master_ref_data:
            for m in master_ref_data:
                if str(m.get("Uraian Pekerjaan", "")).strip() == str(deskripsi_pekerjaan).strip():
                    try:
                        harga_satuan_otomatis = float(m.get("Harga Satuan", 0.0))
                    except:
                        pass
                    unit_otomatis = str(m.get("Unit", "Month"))
                    break

        c_it1, c_it2 = st.columns(2)
        with c_it1:
            qty = st.number_input("Qty / Volume", value=1.0, format="%.2f")
        with c_it2:
            satuan_options = ["Month", "Day", "Ls", "Unit", "Trip", "Jam", "AU", "Kwh"]
            idx_sat = satuan_options.index(unit_otomatis) if unit_otomatis in satuan_options else 0
            unit = st.selectbox("Unit Satuan", satuan_options, index=idx_sat)

        c_d1, c_d2 = st.columns(2)
        with c_d1:
            tgl_mulai = st.date_input("Tanggal Mulai (Start)")
        with c_d2:
            tgl_selesai = st.date_input("Tanggal Selesai (Finish)")

        harga_satuan = st.number_input("Harga Satuan (Rp) - Otomatis / Bisa Disesuaikan", value=harga_satuan_otomatis, format="%.2f")
        keterangan_pekerjaan = st.text_input("Keterangan Pekerjaan", value="Alat Beroperasi Periode Juli 2026")

        submitted_item = st.form_submit_button("➕ Masukkan ke Daftar Mutasi")
        if submitted_item:
            total_harga_item = qty * harga_satuan
            item_mutasi = {
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
                "Kategori": kategori_pilih,
                "Deskripsi Pekerjaan": deskripsi_pekerjaan,
                "Qty": qty,
                "Unit": unit,
                "Tanggal Mulai": tgl_mulai.strftime("%d %b %Y"),
                "Tanggal Selesai": tgl_selesai.strftime("%d %b %Y"),
                "Harga Satuan": harga_satuan,
                "Total Harga": total_harga_item,
                "Keterangan": keterangan_pekerjaan
            }
            st.session_state["list_mutasi_sementara"].append(item_mutasi)
            st.success("Baris mutasi berhasil ditambahkan ke daftar sementara!")
            st.rerun()

    # Tampilkan Tabel Daftar Mutasi dengan Tombol Hapus per Baris di Sudut Kanan
    if st.session_state["list_mutasi_sementara"]:
        st.markdown("#### 📋 Daftar Mutasi yang Akan Diproses:")
        
        for idx_m, item_m in enumerate(st.session_state["list_mutasi_sementara"]):
            with st.container(border=True):
                col_row_info, col_row_del = st.columns([6, 1])
                with col_row_info:
                    st.markdown(f"**Baris {idx_m + 1} | {item_m['Kategori']}** - {item_m['Deskripsi Pekerjaan']}")
                    st.text(f"Periode: {item_m.get('Tanggal Mulai', '-')} s/d {item_m.get('Tanggal Selesai', '-')} | Qty: {item_m['Qty']} {item_m['Unit']}")
                    st.text(f"Harga Satuan: Rp {item_m['Harga Satuan']:,.2f} | Total: Rp {item_m['Total Harga']:,.2f} | Ket: {item_m['Keterangan']}")
                with col_row_del:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑️ Hapus", key=f"del_mutasi_{idx_m}"):
                        st.session_state["list_mutasi_sementara"].pop(idx_m)
                        st.rerun()

        st.markdown("---")
        if st.button("🚀 Simpan Semua Mutasi ke Database Utama"):
            existing_tx = muat_data_transaksi()
            existing_tx = [t for t in existing_tx if str(t.get("PI No.")) != str(pi_no)]
            existing_tx.extend(st.session_state["list_mutasi_sementara"])
            simpan_data_transaksi(existing_tx)
            
            st.session_state["list_mutasi_sementara"] = []
            st.success("🎉 Seluruh mutasi berhasil disimpan dan didistribusikan ke dokumen turunan!")
            st.rerun()

# --- 2. PRATINJAU & CETAK DOKUMEN TURUNAN ---
elif menu_inv == "Pratinjau & Cetak Dokumen Turunan (Hardcopy)":
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">🖨️ Pratinjau & Cetak Dokumen Resmi (Multi-Mutasi Ready)</h3>
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

            if doc_type == "Rincian Pekerjaan":
                st.markdown("<h4 style='text-align: center; margin-bottom: 20px;'>RINCIAN PEKERJAAN</h4>", unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.text(f"Nomor Kontrak    : {t_data_utama.get('Nomor Kontrak', '-')}")
                    st.text(f"Nama Kontrak     : {t_data_utama.get('Nama Kontrak', '-')}")
                    st.text(f"Nomor Tender     : {t_data_utama.get('Nomor Tender', '-')}")
                    st.text(f"Tanggal Proforma : {t_data_utama.get('Tanggal PI', '-')}")
                with c2:
                    st.text(f"Ditujukan Kepada : {t_data_utama.get('Ditujukan Kepada', '-')}")
                    st.text(f"Nomor PO         : {t_data_utama.get('Nomor PO', '-')}")
                    st.text(f"Tanggal PO       : {t_data_utama.get('Tanggal PO', '-')}")
                    st.text(f"Mata Uang        : {t_data_utama.get('Mata Uang', '-')}")

                st.markdown("<br>", unsafe_allow_html=True)

                tabel_data = []
                grand_total = 0.0
                for idx, m in enumerate(mutasi_terpilih, start=1):
                    tot = float(m.get('Total Harga', 0.0))
                    grand_total += tot
                    periode_str = f"{m.get('Tanggal Mulai', '-')}" if m.get('Tanggal Mulai') else "-"
                    if m.get('Tanggal Selesai'):
                        periode_str += f" s/d {m.get('Tanggal Selesai')}"

                    tabel_data.append({
                        "No": idx,
                        "Kategori": m.get('Kategori', '-'),
                        "Spesifikasi / Deskripsi": m.get('Deskripsi Pekerjaan', '-'),
                        "Periode": periode_str,
                        "Qty": m.get('Qty', 0),
                        "Unit": m.get('Unit', '-'),
                        "Harga Satuan (Rp)": f"Rp {float(m.get('Harga Satuan', 0)):,.2f}",
                        "Total Harga (Rp)": f"Rp {tot:,.2f}",
                        "Keterangan": m.get('Keterangan', '-')
                    })

                st.table(pd.DataFrame(tabel_data))
                st.markdown(f"**TOTAL TAGIHAN KESELURUHAN:** Rp {grand_total:,.2f}")

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
                            <b>TO:</b><br>{t_data_utama.get('Ditujukan Kepada', '-')}<br>Indonesia
                        </div>
                        <div>
                            <b>PI No. :</b> {t_data_utama.get('PI No.', '-')}<br>
                            <b>Date :</b> {t_data_utama.get('Tanggal PI', '-')}<br>
                            <b>Contract No. :</b> {t_data_utama.get('Nomor Kontrak', '-')}
                        </div>
                    </div>
                    <h3 style="text-align: center; margin: 30px 0 20px 0;">PROFORMA INVOICE</h3>
                """, unsafe_allow_html=True)

                tabel_pi = []
                grand_total_pi = 0.0
                for idx, m in enumerate(mutasi_terpilih, start=1):
                    tot = float(m.get('Total Harga', 0.0))
                    grand_total_pi += tot
                    desc_text = m.get('Deskripsi Pekerjaan', '-')
                    if m.get('Tanggal Mulai') and m.get('Tanggal Selesai'):
                        desc_text += f" ({m.get('Tanggal Mulai')} s/d {m.get('Tanggal Selesai')})"

                    tabel_pi.append({
                        "Item": idx,
                        "Description": desc_text,
                        "Qty": m.get('Qty', 0),
                        "Unit": m.get('Unit', '-'),
                        "Unit Price (IDR)": f"Rp {float(m.get('Harga Satuan', 0)):,.2f}",
                        "TOTAL (IDR)": f"Rp {tot:,.2f}"
                    })
                st.table(pd.DataFrame(tabel_pi))
                st.markdown(f"<b>GRAND TOTAL: Rp {grand_total_pi:,.2f}</b>", unsafe_allow_html=True)

            else:
                st.info(f"Pratinjau untuk dokumen **{doc_type}** siap disesuaikan menggunakan data multi-mutasi.")

            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🖨️ Cetak / Print Dokumen Ini (Gunakan Ctrl+P)"):
                st.success("💡 Tekan **Ctrl + P** pada keyboard Anda untuk mencetak dokumen ini.")

# --- 3. LIHAT AKUMULASI RIWAYAT TRANSAKSI ---
elif menu_inv == "Lihat Akumulasi Riwayat Transaksi":
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📂 Akumulasi Riwayat Transaksi (Multi-Mutasi)</h3>
        </div>
    """, unsafe_allow_html=True)
    
    tx_records = muat_data_transaksi()
    if tx_records:
        st.dataframe(pd.DataFrame(tx_records), use_container_width=True)
    else:
        st.info("Belum ada riwayat transaksi tersimpan.")