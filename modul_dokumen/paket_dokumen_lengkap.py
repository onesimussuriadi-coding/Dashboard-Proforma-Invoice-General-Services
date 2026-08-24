import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime

def terbilang(n):
    n = float(n)
    if n < 0:
        return "minus " + terbilang(-n)
    n_bulat = int(n)
    if n_bulat == 0:
        return "Nol Rupiah"
        
    satuan = ["", "Satu", "Dua", "Tiga", "Empat", "Lima", "Enam", "Tujuh", "Delapan", "Sembilan", "Sepuluh", "Sebelas"]
    def helper(num):
        if num < 12:
            return " " + satuan[num]
        elif num < 20:
            return helper(num - 10) + " Belas"
        elif num < 100:
            return helper(num // 10) + " Puluh" + helper(num % 10)
        elif num < 200:
            return " Seratus" + helper(num - 100)
        elif num < 1000:
            return helper(num // 100) + " Ratus" + helper(num % 100)
        elif num < 2000:
            return " Seribu" + helper(num - 1000)
        elif num < 1000000:
            return helper(num // 1000) + " Ribu" + helper(num % 1000)
        elif num < 1000000000:
            return helper(num // 1000000) + " Juta" + helper(num % 1000000)
        elif num < 1000000000000:
            return helper(num // 1000000000) + " Miliar" + helper(num % 1000000000)
        else:
            return " Angka terlalu besar"
            
    return helper(n_bulat).strip() + " Rupiah"

def tampilkan_paket_lengkap(transaksi_list):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📦 Master Bundle: Cetak & Download Seluruh Paket Dokumen Penagihan (1-Click Batch Export)</h3>
            <p style="margin-bottom:0; font-size:12px; color:#4b5563;">Modul ini menggabungkan Proforma Invoice, BAMP, BASP, Opname Pekerjaan, dan TKDN secara utuh dan lengkap sesuai standar dokumen perusahaan.</p>
        </div>
    """, unsafe_allow_html=True)

    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi rincian pekerjaan yang diproses.")
        return

    seen_pi_dd = set()
    unique_pi_list = []
    for t in transaksi_list:
        pi_key = str(t.get('PI No.', '')).strip()
        if pi_key and pi_key not in seen_pi_dd:
            seen_pi_dd.add(pi_key)
            unique_pi_list.append(pi_key)

    col_opt1, col_opt2, col_opt3 = st.columns([2, 1, 1])
    with col_opt1:
        selected_pi = st.selectbox("Pilih Nomor Proforma Invoice (PI) untuk Paket Dokumen:", unique_pi_list, key="bundle_pi_select")
    with col_opt2:
        lokasi_office = st.text_input("📍 Lokasi Dokumen:", value="Paisubololi", key="bundle_lokasi")
    with col_opt3:
        selected_date_obj = st.date_input("📅 Tanggal Dokumen Bersama:", value=datetime.now(), key="bundle_tanggal")

    tanggal_str = selected_date_obj.strftime('%d %B %Y')

    mutasi_terpilih = [t for t in transaksi_list if str(t.get('PI No.')).strip() == str(selected_pi).strip()]
    if not mutasi_terpilih:
        st.warning("⚠️ Tidak ada item ditemukan untuk PI ini.")
        return

    t_data_utama = mutasi_terpilih[0]
    current_pi_no = str(selected_pi).strip()

    # --- PENGAMBILAN DATABASE INDUK ---
    db_invoice_path = os.path.join("database_penyimpanan_aman", "database_proforma_invoice.xlsx")
    matched_db_row = {}
    row_values = []
    if os.path.exists(db_invoice_path):
        try:
            df_inv = pd.read_excel(db_invoice_path)
            for idx, row in df_inv.iterrows():
                val_pi_0 = str(row.iloc[0]).strip().lower()
                if val_pi_0 == current_pi_no.lower():
                    matched_db_row = row.to_dict()
                    row_values = row.values.tolist()
                    break
        except:
            pass

    def get_induk(idx_num, text_key, fallback="-"):
        if idx_num in matched_db_row:
            v = matched_db_row[idx_num]
            if v is not None and str(v).strip() != "" and str(v).strip().lower() != "nan":
                return str(v).strip()
        if text_key in matched_db_row:
            v = matched_db_row[text_key]
            if v is not None and str(v).strip() != "" and str(v).strip().lower() != "nan":
                return str(v).strip()
        return fallback

    nomor_kontrak = get_induk(1, 'Nomor Kontrak', t_data_utama.get('Nomor Kontrak', '-'))
    tgl_kontrak = get_induk(4, 'Tanggal Kontrak', '-')
    jangka_waktu = get_induk(5, 'Jangka Waktu Kontrak', '2 tahun')
    tgl_pi = get_induk(6, 'Tanggal Performa Invoice', tanggal_str)
    lingkup_pekerjaan = get_induk(3, 'Lingkup Pekerjaan', t_data_utama.get('Deskripsi PO', '-'))
    no_po = get_induk(8, 'Nomor Purchase Order', t_data_utama.get('Nomor PO', '-'))
    tgl_po = get_induk(9, 'Tanggal Purchase Order', t_data_utama.get('Tanggal PO', '-'))
    nomor_tender = get_induk(2, 'Nomor Tender', '-')

    p1_nama = get_induk(10, 'Pihak Pertama', 'JOB Pertamina - Medco E&P Tomori Sulawesi')
    p1_alamat = get_induk(11, 'Alamat Pihak Pertama', 'Bidakara Office Tower I 4Th Floor, Jl. Gatot Subroto Kav. 71 - 73, Jakarta 12870, Indonesia')
    p1_wakil = get_induk(12, 'Diwakili Oleh', 'Aldito Fauzi Roe / Aryanto Yoga')
    p1_jabatan = get_induk(13, 'Selaku', 'Contract Engineer')

    p2_nama = get_induk(14, 'Pihak Kedua', 'PT Banggai Sentral Sulawesi')
    p2_alamat = get_induk(15, 'Alamat Pihak Kedua', 'Jl. Urip Sumoharjo No. 53, Luwuk, Kabupaten Banggai, Provinsi Sulawesi Tengah (94715), Indonesia')
    p2_wakil = get_induk(16, 'Diwakili Oleh (P2)', 'Ir. Ferry Tatimu')
    p2_jabatan = get_induk(17, 'Selaku (P2)', 'Direktur Utama')

    bank_name = t_data_utama.get('Bank Name', 'BANK RAKYAT INDONESIA (PERSERO) Tbk.')
    bank_branch = t_data_utama.get('Bank Branch', 'Cabang Luwuk')
    bank_acc_no = t_data_utama.get('Account No', '0167 0167 8888 303')
    bank_acc_name = t_data_utama.get('Account Name', 'PT. BANGGAI SENTRAL SULAWESI')
    attn_to = t_data_utama.get('Attn', 'Accounts Payable - Finance Department')

    # --- HITUNG TOTAL ---
    grand_total = 0.0
    pi_rows_html = ""
    for idx, m in enumerate(mutasi_terpilih, start=1):
        kat = str(m.get('Kategori', '')).strip()
        desc = str(m.get('Deskripsi Pekerjaan', '')).strip()
        ket = str(m.get('Keterangan', '')).strip()
        qty = float(m.get('Qty', 1.0))
        unit = str(m.get('Unit', 'AU'))
        price = float(m.get('Harga Satuan', 0.0))
        tot = float(m.get('Total Harga', qty * price))
        grand_total += tot

        desc_full = f"<b>{kat}</b><br>{desc}"
        if ket:
            desc_full += f"<br>{ket}"

        pi_rows_html += f"""
            <tr>
                <td>{idx}</td>
                <td style="text-align: left;">{desc_full}</td>
                <td>{qty:.2f}</td>
                <td>{unit}</td>
                <td style="text-align: right;">{price:,.2f}</td>
                <td style="text-align: right;">{tot:,.2f}</td>
            </tr>
        """

    terbilang_str = terbilang(grand_total)

    # ==========================================
    # 1. HALAMAN PROFORMA INVOICE
    # ==========================================
    pi_html = f"""
    <div class="page-break">
        <div style="font-weight: bold; font-size: 10px; margin-bottom: 5px;">PT. BANGGAI SENTRAL SULAWESI</div>
        <div style="font-size: 8.5px; color: #4b5563; margin-bottom: 10px;">General Contractor and Suppliers | Jl. Urip Sumoharjo No. 53 Luwuk, Kabupaten Banggai, Propinsi Sulawesi Tengah</div>
        <h2 style="text-align: center; font-size: 13px; text-transform: uppercase; border-bottom: 2px solid #000; padding-bottom: 4px; margin-bottom: 10px;">PROFORMA INVOICE</h2>
        
        <table style="width: 100%; font-size: 9.5px; margin-bottom: 15px; border-collapse: collapse;">
            <tr>
                <td style="width: 55%; vertical-align: top;">
                    <b>TO:</b><br>
                    <b>{p1_nama}</b><br>
                    {p1_alamat}<br>
                    <b>Attn.:</b> {attn_to}
                </td>
                <td style="width: 45%; vertical-align: top;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td><b>Proforma Invoice No.</b></td><td>:</td><td><b>{current_pi_no}</b></td></tr>
                        <tr><td><b>Tanggal Performa Invoice</b></td><td>:</td><td>{tgl_pi}</td></tr>
                        <tr><td><b>Nomor Kontrak</b></td><td>:</td><td>{nomor_kontrak}</td></tr>
                        <tr><td><b>Jangka Waktu Kontrak</b></td><td>:</td><td>{jangka_waktu}</td></tr>
                        <tr><td><b>Nomor Purchase Order</b></td><td>:</td><td>{no_po}</td></tr>
                    </table>
                </td>
            </tr>
        </table>

        <table class="doc-table" style="width:100%; border-collapse:collapse; margin-bottom: 10px;">
            <tr>
                <th style="width: 6%;">Item</th>
                <th style="width: 44%;">Description</th>
                <th style="width: 8%;">Qty</th>
                <th style="width: 8%;">Satuan</th>
                <th style="width: 17%;">Unit Price (IDR)</th>
                <th style="width: 17%;">TOTAL (IDR)</th>
            </tr>
            {pi_rows_html}
            <tr>
                <td colspan="5" style="text-align: right; font-weight: bold;">GRAND TOTAL:</td>
                <td style="text-align: right; font-weight: bold;">{grand_total:,.2f}</td>
            </tr>
        </table>

        <div style="font-size: 9.5px; margin-bottom: 15px;">
            <b>Terbilang:</b> <i>{terbilang_str}</i>
        </div>

        <div style="font-size: 9.5px; margin-bottom: 20px; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; padding: 6px 0;">
            <b>PAYMENT INSTRUCTION:</b><br>
            Please remit to our bank:<br>
            <b>Bank Name:</b> {bank_name}<br>
            <b>Branch:</b> {bank_branch}<br>
            <b>Account No:</b> {bank_acc_no}<br>
            <b>Account Name:</b> {bank_acc_name}
        </div>

        <table style="width: 100%; margin-top: 20px; border-collapse: collapse;">
            <tr>
                <td style="width: 50%;"></td>
                <td style="width: 50%; text-align: center;">
                    <b>PT. BANGGAI SENTRAL SULAWESI</b><br><br><br><br>
                    <u><b>{p2_wakil}</b></u><br>
                    {p2_jabatan}
                </td>
            </tr>
        </table>
    </div>
    """

    # ==========================================
    # 2. HALAMAN BAMP (Berita Acara Mulai Pekerjaan)
    # ==========================================
    bamp_rows = ""
    for idx, m in enumerate(mutasi_terpilih, start=1):
        kat = str(m.get('Kategori', '')).strip()
        desc = str(m.get('Deskripsi Pekerjaan', '')).strip()
        qty = float(m.get('Qty', 1.0))
        unit = str(m.get('Unit', 'AU'))
        bamp_rows += f"<tr><td>{idx}</td><td style='text-align:left;'><b>{kat}</b><br>{desc}</td><td>{qty:.2f}</td><td>{unit}</td><td>Mulai Berlaku Tanggal {tanggal_str}</td></tr>"

    bamp_html = f"""
    <div class="page-break">
        <h2 style="text-align: center; font-size: 13px; text-transform: uppercase; border-bottom: 2px solid #000; padding-bottom: 4px; margin-bottom: 10px;">BERITA ACARA MULAI PEKERJAAN (BAMP)</h2>
        <p style="font-size: 9.5px;">Pada hari ini, tanggal <b>{tanggal_str}</b>, yang bertanda tangan di bawah ini:</p>
        
        <table style="width: 100%; font-size: 9.5px; margin-bottom: 10px; border-collapse: collapse;">
            <tr><td style="width: 25%; font-weight: bold;">01. PIHAK PERTAMA</td><td></td></tr>
            <tr><td>Nama Perusahaan</td><td>: {p1_nama}</td></tr>
            <tr><td>Alamat</td><td>: {p1_alamat}</td></tr>
            <tr><td>Diwakili oleh</td><td>: {p1_wakil}</td></tr>
            <tr><td>Jabatan</td><td>: {p1_jabatan}</td></tr>
            <tr><td style="font-weight: bold; padding-top: 5px;">02. PIHAK KEDUA</td><td></td></tr>
            <tr><td>Nama Perusahaan</td><td>: {p2_nama}</td></tr>
            <tr><td>Alamat</td><td>: {p2_alamat}</td></tr>
            <tr><td>Diwakili oleh</td><td>: {p2_wakil}</td></tr>
            <tr><td>Jabatan</td><td>: {p2_jabatan}</td></tr>
        </table>

        <div style="font-size: 9.5px; font-weight: bold; margin-top: 10px; margin-bottom: 5px;">DASAR PELAKSANAAN PEKERJAAN</div>
        <table style="width: 100%; font-size: 9.5px; margin-bottom: 10px; border-collapse: collapse;">
            <tr><td style="width: 25%;">Nomor Kontrak</td><td style="width: 75%;">: {nomor_kontrak}</td></tr>
            <tr><td>Tanggal Kontrak</td><td>: {tgl_kontrak}</td></tr>
            <tr><td>Nomor Purchase Order</td><td>: {no_po}</td></tr>
            <tr><td>Tanggal Purchase Order</td><td>: {tgl_po}</td></tr>
            <tr><td>Lingkup Pekerjaan</td><td>: {lingkup_pekerjaan}</td></tr>
        </table>

        <p style="font-size: 9.5px;">Dengan ini PIHAK KEDUA menyatakan mulai melaksanakan seluruh pekerjaan secara baik dan siap terhitung mulai tanggal <b>{tanggal_str}</b> dengan rincian sebagai berikut:</p>

        <table class="doc-table" style="width:100%; border-collapse:collapse; margin-top:10px; margin-bottom: 20px;">
            <tr><th style="width: 8%;">NO</th><th style="width: 42%;">KETERANGAN PEKERJAAN</th><th style="width: 10%;">JUMLAH</th><th style="width: 10%;">SATUAN</th><th style="width: 30%;">CATATAN</th></tr>
            {bamp_rows}
        </table>

        <p style="font-size: 9.5px;">Demikian Berita Acara Mulai Pekerjaan ini dibuat dan ditandatangani oleh kedua belah pihak untuk dipergunakan sebagaimana mestinya.</p>

        <table style="width: 100%; margin-top: 30px; border-collapse: collapse; page-break-inside: avoid;">
            <tr>
                <td style="width: 50%; text-align: center;">
                    <b>{p1_nama}</b><br>
                    PIHAK PERTAMA<br><br><br><br>
                    <u><b>{p1_wakil}</b></u><br>
                    {p1_jabatan}
                </td>
                <td style="width: 50%; text-align: center;">
                    <b>{p2_nama}</b><br>
                    PIHAK KEDUA<br><br><br><br>
                    <u><b>{p2_wakil}</b></u><br>
                    {p2_jabatan}
                </td>
            </tr>
        </table>
    </div>
    """

    # ==========================================
    # 3. HALAMAN BASP (Berita Acara Selesai Pekerjaan)
    # ==========================================
    basp_rows = ""
    for idx, m in enumerate(mutasi_terpilih, start=1):
        kat = str(m.get('Kategori', '')).strip()
        desc = str(m.get('Deskripsi Pekerjaan', '')).strip()
        qty = float(m.get('Qty', 1.0))
        unit = str(m.get('Unit', 'AU'))
        basp_rows += f"<tr><td>{idx}</td><td style='text-align:left;'><b>{kat}</b><br>{desc}</td><td>{qty:.2f}</td><td>{unit}</td><td>Selesai Pelaksanaan Pekerjaan Tanggal {tanggal_str}</td></tr>"

    basp_html = f"""
    <div class="page-break">
        <h2 style="text-align: center; font-size: 13px; text-transform: uppercase; border-bottom: 2px solid #000; padding-bottom: 4px; margin-bottom: 10px;">BERITA ACARA SELESAI PEKERJAAN (BASP)</h2>
        <p style="font-size: 9.5px;">Pada hari ini, tanggal <b>{tanggal_str}</b>, yang bertanda tangan di bawah ini:</p>
        
        <table style="width: 100%; font-size: 9.5px; margin-bottom: 10px; border-collapse: collapse;">
            <tr><td style="width: 25%; font-weight: bold;">01. PIHAK PERTAMA</td><td></td></tr>
            <tr><td>Nama Perusahaan</td><td>: {p1_nama}</td></tr>
            <tr><td>Alamat</td><td>: {p1_alamat}</td></tr>
            <tr><td>Diwakili oleh</td><td>: {p1_wakil}</td></tr>
            <tr><td>Jabatan</td><td>: {p1_jabatan}</td></tr>
            <tr><td style="font-weight: bold; padding-top: 5px;">02. PIHAK KEDUA</td><td></td></tr>
            <tr><td>Nama Perusahaan</td><td>: {p2_nama}</td></tr>
            <tr><td>Alamat</td><td>: {p2_alamat}</td></tr>
            <tr><td>Diwakili oleh</td><td>: {p2_wakil}</td></tr>
            <tr><td>Jabatan</td><td>: {p2_jabatan}</td></tr>
        </table>

        <div style="font-size: 9.5px; font-weight: bold; margin-top: 10px; margin-bottom: 5px;">DASAR PELAKSANAAN PEKERJAAN</div>
        <table style="width: 100%; font-size: 9.5px; margin-bottom: 10px; border-collapse: collapse;">
            <tr><td style="width: 25%;">Nomor Kontrak</td><td style="width: 75%;">: {nomor_kontrak}</td></tr>
            <tr><td>Tanggal Kontrak</td><td>: {tgl_kontrak}</td></tr>
            <tr><td>Nomor Purchase Order</td><td>: {no_po}</td></tr>
            <tr><td>Tanggal Purchase Order</td><td>: {tgl_po}</td></tr>
            <tr><td>Lingkup Pekerjaan</td><td>: {lingkup_pekerjaan}</td></tr>
        </table>

        <p style="font-size: 9.5px;">Dengan ini PIHAK KEDUA menyatakan telah menyelesaikan seluruh pekerjaan secara baik dan lengkap terhitung sampai dengan tanggal <b>{tanggal_str}</b> dengan rincian sebagai berikut:</p>

        <table class="doc-table" style="width:100%; border-collapse:collapse; margin-top:10px; margin-bottom: 20px;">
            <tr><th style="width: 8%;">NO</th><th style="width: 42%;">KETERANGAN PEKERJAAN</th><th style="width: 10%;">JUMLAH</th><th style="width: 10%;">SATUAN</th><th style="width: 30%;">CATATAN</th></tr>
            {basp_rows}
        </table>

        <p style="font-size: 9.5px;">Demikian Berita Acara Selesai Pekerjaan ini dibuat dan ditandatangani oleh kedua belah pihak untuk dipergunakan sebagaimana mestinya.</p>

        <table style="width: 100%; margin-top: 30px; border-collapse: collapse; page-break-inside: avoid;">
            <tr>
                <td style="width: 50%; text-align: center;">
                    <b>{p1_nama}</b><br>
                    PIHAK PERTAMA<br><br><br><br>
                    <u><b>{p1_wakil}</b></u><br>
                    {p1_jabatan}
                </td>
                <td style="width: 50%; text-align: center;">
                    <b>{p2_nama}</b><br>
                    PIHAK KEDUA<br><br><br><br>
                    <u><b>{p2_wakil}</b></u><br>
                    {p2_jabatan}
                </td>
            </tr>
        </table>
    </div>
    """

    # ==========================================
    # 4. HALAMAN OPNAME PEKERJAAN
    # ==========================================
    opname_rows = ""
    for idx, m in enumerate(mutasi_terpilih, start=1):
        kat = str(m.get('Kategori', '')).strip()
        desc = str(m.get('Deskripsi Pekerjaan', '')).strip()
        qty = float(m.get('Qty', 1.0))
        unit = str(m.get('Unit', 'AU'))
        price = float(m.get('Harga Satuan', 0.0))
        tot = float(m.get('Total Harga', qty * price))
        
        desc_full = f"<b>{kat}</b><br>{desc}"
        opname_rows += f"""
            <tr>
                <td>1.{idx}</td>
                <td style="text-align: left;">{desc_full}</td>
                <td>{unit}</td>
                <td>0.00</td>
                <td style="text-align: right;">{price:,.2f}</td>
                <td>0.00</td>
                <td>0.00</td>
                <td>0.00</td>
                <td>{qty:.2f}</td>
                <td style="text-align: right;">{tot:,.2f}</td>
                <td>{qty:.2f}</td>
                <td style="text-align: right;">{tot:,.2f}</td>
                <td>-1.00</td>
                <td style="text-align: right;">-{{tot:,.2f}}</td>
            </tr>
        """

    opname_html = f"""
    <div class="page-break">
        <h2 style="text-align: center; font-size: 13px; text-transform: uppercase; border-bottom: 2px solid #000; padding-bottom: 4px; margin-bottom: 10px;">BERITA ACARA PEKERJAAN / OPNAME</h2>
        
        <table style="width: 100%; font-size: 9.5px; margin-bottom: 10px; border-collapse: collapse;">
            <tr><td style="width: 25%; font-weight: bold;">JOB TITLE / WO / PO</td><td>: {lingkup_pekerjaan}</td></tr>
            <tr><td style="font-weight: bold;">CTR / WO / PO No.</td><td>: {no_po}</td></tr>
            <tr><td style="font-weight: bold;">DATE</td><td>: {tanggal_str}</td></tr>
            <tr><td style="font-weight: bold; color: #065f46;">PROFORMA INVOICE No.</td><td>: <b>{current_pi_no}</b></td></tr>
        </table>

        <table class="doc-table" style="width:100%; border-collapse:collapse; margin-bottom: 10px; font-size: 8px;">
            <tr>
                <th rowspan="2">NO</th>
                <th rowspan="2">ITEM - DESCRIPTION</th>
                <th rowspan="2">UOM</th>
                <th colspan="3">BASE ON CTR / PO</th>
                <th colspan="2">PREVIOUS OPNAME</th>
                <th colspan="2">AKTUAL OPNAME (BULAN INI)</th>
                <th colspan="2">CUMMULATIVE OPNAME</th>
                <th colspan="2">SISA ANGGARAN (DEVIASI)</th>
            </tr>
            <tr>
                <th>VOLUME</th><th>UNIT PRICE</th><th>TOTAL PRICE</th>
                <th>VOLUME</th><th>TOTAL PRICE</th>
                <th>VOLUME</th><th>TOTAL PRICE</th>
                <th>VOLUME</th><th>TOTAL PRICE</th>
                <th>VOLUME</th><th>TOTAL PRICE</th>
            </tr>
            {opname_rows}
            <tr style="font-weight: bold; background: #f9fafb;">
                <td colspan="3" style="text-align: right;">TOTAL:</td>
                <td>0.00</td><td>-</td><td style="text-align: right;">0.00</td>
                <td>0.00</td><td style="text-align: right;">0.00</td>
                <td>{float(t_data_utama.get('Qty', 1.0)):.2f}</td><td style="text-align: right;">{grand_total:,.2f}</td>
                <td>{float(t_data_utama.get('Qty', 1.0)):.2f}</td><td style="text-align: right;">{grand_total:,.2f}</td>
                <td>-1.00</td><td style="text-align: right;">-{{grand_total:,.2f}}</td>
            </tr>
        </table>

        <div style="font-size: 9.5px; font-weight: bold; margin-bottom: 20px;">
            Total Akumulasi Penyerapan (Cumulative Opname): Rp {grand_total:,.2f}<br>
            Sisa Nilai Anggaran PO (Deviasi): Rp -{{grand_total:,.2f}}
        </div>

        <table style="width: 100%; margin-top: 20px; border-collapse: collapse; page-break-inside: avoid;">
            <tr>
                <td style="width: 50%; text-align: left;">
                    {lokasi_office}, {tanggal_str}<br>
                    <b>{p2_nama}</b><br>
                    Prepared by,<br><br><br><br>
                    <u><b>Onesimus Suriadi</b></u><br>
                    Manager General Services
                </td>
                <td style="width: 50%; text-align: center;">
                    <br>
                    <b>{p1_nama}</b><br>
                    Approved by,<br><br><br><br>
                    <u><b>{p1_wakil}</b></u><br>
                    {p1_jabatan}
                </td>
            </tr>
        </table>
    </div>
    """

    # ==========================================
    # 5. HALAMAN TKDN (Format Resmi Permen ESDM No. 15 / 2013)
    # ==========================================
    # Hitung estimasi komponen jasa umum (asumsi 95% TKDN sesuai contoh scan)
    total_jasa = grand_total * (95.0 / 100.0)
    non_cost = grand_total * 0.05

    tkdn_html = f"""
    <div class="page-break">
        <div style="text-align: center; font-weight: bold; font-size: 10px; margin-bottom: 2px;">TABEL PERHITUNGAN TINGKAT KOMPONEN DALAM NEGERI - JASA</div>
        <div style="text-align: center; font-size: 9px; font-weight: bold; margin-bottom: 10px;">SELF-ASSESSMENT (PERMEN ESDM NO. 15 TAHUN 2013)</div>
        
        <table style="width: 100%; font-size: 9px; margin-bottom: 10px; border-collapse: collapse;">
            <tr><td style="width: 20%; font-weight: bold;">Nama Penyedia Jasa</td><td style="width: 80%;">: {p2_nama}</td></tr>
            <tr><td style="font-weight: bold;">Judul Kontrak</td><td>: {lingkup_pekerjaan}</td></tr>
            <tr><td style="font-weight: bold;">Nomor Kontrak</td><td>: {nomor_kontrak}</td></tr>
            <tr><td style="font-weight: bold;">Nomor PO</td><td>: {no_po}</td></tr>
            <tr><td style="font-weight: bold;">Tanggal</td><td>: {tanggal_str}</td></tr>
            <tr><td style="font-weight: bold;">Mata Uang</td><td>: IDR</td></tr>
        </table>

        <table class="doc-table" style="width:100%; border-collapse:collapse; margin-bottom: 10px; font-size: 8.5px;">
            <tr>
                <th>A. KOMPONEN BIAYA (COST COMPONENT)</th>
                <th>MATA UANG</th>
                <th>KDN (A)</th>
                <th>KLN (B)</th>
                <th>TOTAL ($C=A+B$)</th>
                <th>% NILAI TKDN</th>
                <th>NILAI TKDN</th>
            </tr>
            <tr>
                <td style="text-align: left;">I. Biaya Bahan (Material) Terpakai</td>
                <td>Rp</td><td>0.00</td><td>0.00</td><td>0.00</td><td>0.00%</td><td>0.00</td>
            </tr>
            <tr>
                <td style="text-align: left;">II. Biaya Tenaga Kerja & Konsultan</td>
                <td>Rp</td><td>0.00</td><td>0.00</td><td>0.00</td><td>0.00%</td><td>0.00</td>
            </tr>
            <tr>
                <td style="text-align: left;">III. Biaya Alat Kerja / Fasilitas Kerja</td>
                <td>Rp</td><td>0.00</td><td>0.00</td><td>0.00</td><td>0.00%</td><td>0.00</td>
            </tr>
            <tr>
                <td style="text-align: left;">IV. Biaya Jasa Umum</td>
                <td>Rp</td><td>{total_jasa:,.2f}</td><td>0.00</td><td>{total_jasa:,.2f}</td><td>100.00%</td><td>{total_jasa:,.2f}</td>
            </tr>
            <tr style="font-weight: bold;">
                <td style="text-align: left;">V. JUMLAH BIAYA (I s/d IV)</td>
                <td>Rp</td><td>{total_jasa:,.2f}</td><td>0.00</td><td>{total_jasa:,.2f}</td><td>100.00%</td><td>{total_jasa:,.2f}</td>
            </tr>
            <tr>
                <td style="text-align: left; font-weight: bold;">B. KOMPONEN BUKAN BIAYA (Non-cost Component)</td>
                <td>Rp</td><td colspan="2"></td><td>{non_cost:,.2f}</td><td colspan="2"></td>
            </tr>
            <tr style="font-weight: bold; background: #f3f4f6;">
                <td style="text-align: left;">C. JUMLAH NILAI TOTAL (A + B)</td>
                <td>Rp</td><td colspan="2"></td><td>{grand_total:,.2f}</td><td colspan="2"></td>
            </tr>
            <tr style="font-weight: bold; background: #e5e7eb; font-size: 10px;">
                <td colspan="6" style="text-align: right;">CAPAIAN PERSENTASE TKDN AKHIR (%):</td>
                <td style="color: #065f46;">95.00%</td>
            </tr>
        </table>

        <div style="font-size: 8px; margin-bottom: 15px;">
            <b>Catatan:</b><br>
            • Isi hanya pada kolom yang berwarna kuning pastel.<br>
            • Formulasi perhitungan mengacu pada Permen ESDM No. 15 Tahun 2013.
        </div>

        <table style="width: 100%; margin-top: 20px; border-collapse: collapse; page-break-inside: avoid;">
            <tr>
                <td style="width: 50%;"></td>
                <td style="width: 50%; text-align: center;">
                    {lokasi_office}, {tanggal_str}<br>
                    <b>{p2_nama}</b><br><br><br><br>
                    <u><b>{p2_wakil}</b></u><br>
                    {p2_jabatan}
                </td>
            </tr>
        </table>
    </div>
    """

    # ==========================================
    # MASTER CONTAINER HTML
    # ==========================================
    master_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Master Bundle Dokumen - {current_pi_no}</title>
        <style>
            @page {{ size: A4 portrait; margin: 8mm; }}
            @media print {{
                body {{ -webkit-print-color-adjust: exact; margin: 0; }}
                .page-break {{ page-break-after: always; break-after: page; }}
            }}
            body {{ font-family: Arial, sans-serif; font-size: 9.5px; color: #000; line-height: 1.3; }}
            .page-break {{ page-break-after: always; break-after: page; padding-bottom: 10px; }}
            .doc-table th, .doc-table td {{ border: 1px solid #000; padding: 4px; font-size: 8.5px; text-align: center; vertical-align: middle; }}
            .doc-table th {{ background-color: #f1f5f9; font-weight: bold; }}
        </style>
    </head>
    <body>
        {pi_html}
        {bamp_html}
        {basp_html}
        {opname_html}
        {tkdn_html}
    </body>
    </html>
    """

    # --- PRATINJAU DI STREAMLIT ---
    st.markdown('<div class="document-preview">', unsafe_allow_html=True)
    st.components.v1.html(master_html, height=750, scrolling=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- TOMBOL AKSI 1-CLICK PRINT & DOWNLOAD ---
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        b64_html = base64.b64encode(master_html.encode()).decode()
        print_script = f"""
            <script>
                function printAllDocs() {{
                    var win = window.open('', '_blank');
                    win.document.write(atob("{b64_html}"));
                    win.document.close();
                    win.focus();
                    setTimeout(function(){{ win.print(); }}, 600);
                }}
            </script>
            <button onclick="printAllDocs()" style="width: 100%; background-color: #10b981; color: white; padding: 12px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 14px;">
                🖨️ Cetak Seluruh Paket Dokumen Sekaligus (1-Click Print)
            </button>
        """
        st.components.v1.html(print_script, height=60)

    with col_b2:
        download_link = f'<a href="data:text/html;base64,{b64_html}" download="Master_Paket_Dokumen_{current_pi_no.replace("/", "-")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 12px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 14px;">📥 Download Master File Paket (.HTML/PDF)</button></a>'
        st.markdown(download_link, unsafe_allow_html=True)