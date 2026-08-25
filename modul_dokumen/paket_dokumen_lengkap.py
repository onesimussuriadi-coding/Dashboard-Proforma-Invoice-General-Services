import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime, date

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
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📦 Master Bundle: Fotokopi Digital Dokumen (Exact Duplication & Batch Export)</h3>
            <p style="margin-bottom:0; font-size:12px; color:#4b5563;">Modul ini menduplikasi secara utuh dan identik 100% seluruh dokumen asli yang telah divalidasi dan disimpan di setiap modul (Rincian Pekerjaan, Proforma Invoice, BAMP, BASP, WCC, Opname, dan TKDN).</p>
        </div>
    """, unsafe_allow_html=True)

    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi rincian pekerjaan yang diproses.")
        return

    DIR_PAKET_SAVED = os.path.join("database_penyimpanan_aman", "paket_dokumen_tersimpan")
    if not os.path.exists(DIR_PAKET_SAVED):
        os.makedirs(DIR_PAKET_SAVED)

    seen_pi_dd = set()
    unique_pi_list = []
    for t in transaksi_list:
        pi_key = str(t.get('PI No.', '')).strip()
        if pi_key and pi_key not in seen_pi_dd:
            seen_pi_dd.add(pi_key)
            unique_pi_list.append(pi_key)

    selected_pi = st.selectbox("Pilih Nomor Proforma Invoice (PI) untuk Paket Dokumen:", unique_pi_list, key="bundle_pi_select")
    current_pi_no = str(selected_pi).strip()

    file_saved_path = os.path.join(DIR_PAKET_SAVED, f"paket_{current_pi_no.replace('/', '_')}.html")
    
    is_loaded_from_save = False
    saved_html_content = ""
    if os.path.exists(file_saved_path):
        st.success("✅ Dokumen Paket Lengkap (Fotokopi Identik) untuk PI ini sudah pernah disimpan secara final.")
        col_load1, col_load2 = st.columns([2, 2])
        with col_load1:
            if st.button("📂 Muat Dokumen Tersimpan (Load Final)", use_container_width=True):
                try:
                    with open(file_saved_path, "r", encoding="utf-8") as f:
                        saved_html_content = f.read()
                    is_loaded_from_save = True
                    st.session_state[f"loaded_saved_{current_pi_no}"] = True
                except:
                    pass
        with col_load2:
            if st.button("🔄 Perbarui / Buat Ulang Duplikat", use_container_width=True):
                if f"loaded_saved_{current_pi_no}" in st.session_state:
                    del st.session_state[f"loaded_saved_{current_pi_no}"]
                st.rerun()

    if st.session_state.get(f"loaded_saved_{current_pi_no}", False) and os.path.exists(file_saved_path):
        with open(file_saved_path, "r", encoding="utf-8") as f:
            master_html = f.read()
        
        st.info("📌 Menampilkan dokumen dalam mode **Final Tersimpan (Fotokopi Identik)**.")
        st.markdown('<div class="document-preview">', unsafe_allow_html=True)
        st.components.v1.html(master_html, height=750, scrolling=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            b64_html = base64.b64encode(master_html.encode("utf-8")).decode()
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
                    🖨️ Cetak Seluruh Paket Dokumen (1-Click Print)
                </button>
            """
            st.components.v1.html(print_script, height=60)

        with col_b2:
            download_link = f'<a href="data:text/html;base64,{b64_html}" download="Master_Paket_Dokumen_{current_pi_no.replace("/", "-")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 12px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 14px;">📥 Download File HTML</button></a>'
            st.markdown(download_link, unsafe_allow_html=True)
        return

    with st.expander("⚙️ Pengaturan Tambahan: Upload Logo & Tanda Tangan", expanded=False):
        col_up1, col_up2 = st.columns(2)
        with col_up1:
            logo_p1_file = st.file_uploader("Upload Logo Pihak Pertama", type=["png", "jpg", "jpeg"], key="up_logo_p1")
            logo_p2_file = st.file_uploader("Upload Logo Pihak Kedua (BSS)", type=["png", "jpg", "jpeg"], key="up_logo_p2")
        with col_up2:
            ttd_supervisor_file = st.file_uploader("Upload Tanda Tangan Supervisor", type=["png", "jpg", "jpeg"], key="up_ttd_supervisor")
            ttd_onesimus_file = st.file_uploader("Upload Tanda Tangan Onesimus Suriadi", type=["png", "jpg", "jpeg"], key="up_ttd_onesimus")
            ttd_ferry_file = st.file_uploader("Upload Tanda Tangan Ir. Ferry Tatimu", type=["png", "jpg", "jpeg"], key="up_ttd_ferry")

    def img_to_base64_str(uploaded_file):
        if uploaded_file is not None:
            bytes_data = uploaded_file.getvalue()
            b64_str = base64.b64encode(bytes_data).decode()
            mime = uploaded_file.type
            return f"data:{mime};base64,{b64_str}"
        return None

    custom_logo_p1 = img_to_base64_str(logo_p1_file) or "https://i.ibb.co.com/7t1g2y6/skkmigas-pertamina-medco.png"
    custom_logo_p2 = img_to_base64_str(logo_p2_file) or "https://i.ibb.co.com/84N3q5P/bss-logo.png"
    custom_ttd_supervisor = img_to_base64_str(ttd_supervisor_file)
    custom_ttd_onesimus = img_to_base64_str(ttd_onesimus_file)
    custom_ttd_ferry = img_to_base64_str(ttd_ferry_file)

    mutasi_terpilih = [t for t in transaksi_list if str(t.get('PI No.')).strip() == current_pi_no]
    if not mutasi_terpilih:
        st.warning("⚠️ Tidak ada item ditemukan untuk PI ini.")
        return

    t_data_utama = mutasi_terpilih[0]

    bamp_saved = st.session_state.get("bamp_saved_data", {}).get(current_pi_no, {})
    basp_saved = st.session_state.get("basp_saved_data", {}).get(current_pi_no, {})
    wcc_saved = st.session_state.get("wcc_saved_data", {}).get(current_pi_no, {})
    tkdn_saved = st.session_state.get("tkdn_saved_data", {}).get(current_pi_no, {})

    bamp_date_obj = bamp_saved.get('main_date', t_data_utama.get('Tanggal Mulai', t_data_utama.get('Tanggal PI', datetime.now())))
    basp_date_obj = basp_saved.get('main_date', t_data_utama.get('Tanggal Selesai', t_data_utama.get('Tanggal PI', datetime.now())))
    
    opname_date_obj = basp_saved.get('main_date', t_data_utama.get('Tanggal Selesai', basp_date_obj))
    tkdn_date_obj = tkdn_saved.get('tanggal_dokumen', datetime.now())
    
    lokasi_bamp = bamp_saved.get('lokasi', 'Luwuk')
    lokasi_tkdn = tkdn_saved.get('lokasi_office', 'Luwuk')

    bulan_indo = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
        7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }
    
    def format_tgl_indo(dt_val):
        try:
            if isinstance(dt_val, str):
                dt_val = pd.to_datetime(dt_val)
            return f"{dt_val.day} {bulan_indo[dt_val.month]} {dt_val.year}"
        except:
            return str(dt_val)

    bamp_date_str = format_tgl_indo(bamp_date_obj)
    basp_date_str = format_tgl_indo(basp_date_obj)
    opname_date_str = format_tgl_indo(opname_date_obj)
    tkdn_date_str = format_tgl_indo(tkdn_date_obj)

    db_invoice_path = os.path.join("database_penyimpanan_aman", "database_proforma_invoice.xlsx")
    matched_db_row = {}
    if os.path.exists(db_invoice_path):
        try:
            df_inv = pd.read_excel(db_invoice_path)
            for idx, row in df_inv.iterrows():
                val_pi_0 = str(row.iloc[0]).strip().lower()
                if val_pi_0 == current_pi_no.lower():
                    matched_db_row = row.to_dict()
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
    nama_kontrak = get_induk(7, 'Nama Kontrak', t_data_utama.get('Nama Kontrak', '-'))
    nomor_tender = get_induk(2, 'Nomor Tender', '-')
    tgl_kontrak = get_induk(4, 'Tanggal Kontrak', '-')
    jangka_waktu = get_induk(5, 'Jangka Waktu Kontrak', '2 tahun')
    tgl_pi = get_induk(6, 'Tanggal Performa Invoice', format_tgl_indo(datetime.now()))
    lingkup_pekerjaan = get_induk(3, 'Lingkup Pekerjaan', t_data_utama.get('Deskripsi PO', t_data_utama.get('Kategori', '-')))
    
    raw_po = str(get_induk(8, 'Nomor Purchase Order', t_data_utama.get('Nomor PO', current_pi_no)))
    if not raw_po or raw_po.lower() == 'nan' or raw_po == '-':
        raw_po = current_pi_no
    if raw_po.endswith('.0'):
        no_po = raw_po[:-2]
    else:
        no_po = raw_po

    tgl_po = get_induk(9, 'Tanggal Purchase Order', t_data_utama.get('Tanggal PO', '-'))

    p1_nama = get_induk(10, 'Pihak Pertama', 'JOB Pertamina - Medco E&P Tomori Sulawesi')
    p1_alamat = get_induk(11, 'Alamat Pihak Pertama', 'Bidakara Office Tower I 4Th Floor, Jl. Gatot Subroto Kav. 71 - 73, Jakarta 12870, Indonesia')
    p1_wakil = get_induk(12, 'Diwakili Oleh', 'Aldito Fauzi Roe / Aryanto Yoga')
    p1_jabatan = get_induk(13, 'Selaku', 'Contract Engineer')

    p2_nama = get_induk(14, 'Pihak Kedua', 'PT Banggai Sentral Sulawesi')
    p2_alamat = get_induk(15, 'Alamat Pihak Kedua', 'Jl. Urip Sumoharjo No. 53, Luwuk, Kabupaten Banggai, Provinsi Sulawesi Tengah (94715), Indonesia')
    
    wcc_lokasi = wcc_saved.get('lokasi', 'Luwuk')
    wcc_date_val = wcc_saved.get('main_date', basp_date_obj)
    try:
        if isinstance(wcc_date_val, str):
            wcc_date_val = pd.to_datetime(wcc_date_val)
        months_en = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        wcc_date_str = f"{wcc_date_val.day} {months_en[wcc_date_val.month]} {wcc_date_val.year}"
    except:
        wcc_date_str = basp_date_str

    wcc_header_title = wcc_saved.get('header_title', nama_kontrak)
    wcc_header_contract = wcc_saved.get('header_contract', f"Contract No. {nomor_kontrak}")
    wcc_cert_no = wcc_saved.get('wcc_no', current_pi_no)
    wcc_wo_no = wcc_saved.get('wo_no', no_po)
    wcc_wo_title = wcc_saved.get('wo_title', lingkup_pekerjaan)
    wcc_ctr_no = wcc_saved.get('ctr_no', current_pi_no)
    
    progress_desc = "100% - Penyelesaian Pekerjaan"

    wcc_signers_list = wcc_saved.get('signers_list', [])
    if not wcc_signers_list:
        if str(nomor_kontrak).strip() == "7207250142":
            wcc_signers_list = [
                {"role": "Prepared by,", "company": p2_nama, "name": "Onesimus Suriadi", "title": "Manager General Services", "show_loc": True},
                {"role": "Reviewed by,", "company": p1_nama, "name": "Rafik Hidayat / Ronny Dwi Purnomo", "title": "Maintenance Support Supervisor", "show_loc": False},
                {"role": "Approved by,", "company": p1_nama, "name": "Imron Maulana / Moh Bazarul Aqhsa", "title": "Maintenance Superintendent", "show_loc": False}
            ]
        else:
            wcc_signers_list = [
                {"role": "Prepared by,", "company": p2_nama, "name": "Onesimus Suriadi", "title": "Manager General Services", "show_loc": True},
                {"role": "Approved by,", "company": p1_nama, "name": p1_wakil, "title": p1_jabatan, "show_loc": False}
            ]

    bank_name = t_data_utama.get('Bank Name', 'BANK RAKYAT INDONESIA (PERSERO) Tbk.')
    bank_branch = t_data_utama.get('Bank Branch', 'Cabang Luwuk')
    bank_acc_no = t_data_utama.get('Account No', '0167 0167 8888 303')
    bank_acc_name = t_data_utama.get('Account Name', 'PT. BANGGAI SENTRAL SULAWESI')
    attn_to = t_data_utama.get('Attn', 'Accounts Payable - Finance Department')

    grand_total = 0.0
    rincian_rows_html = ""
    pi_rows_html = ""
    bamp_rows_html = ""
    basp_rows_html = ""
    opname_rows_html = ""

    bamp_items_saved = bamp_saved.get('items', [])

    for idx, m in enumerate(mutasi_terpilih, start=1):
        kat = str(m.get('Kategori', '')).strip()
        desc = str(m.get('Deskripsi Pekerjaan', '')).strip()
        ket = str(m.get('Keterangan', '')).strip()
        qty = float(m.get('Qty', 1.0))
        unit = str(m.get('Unit', 'AU'))
        price = float(m.get('Harga Satuan', 0.0))
        tot = float(m.get('Total Harga', qty * price))
        grand_total += tot

        tgl_mulai_item = str(m.get('Tanggal Mulai', tgl_pi))
        tgl_selesai_item = str(m.get('Tanggal Selesai', tgl_pi))

        # --- LOGIKA PENYEMPURNAAN PEMBACAAN QTY BAMP ---
        # Prioritas mutlak membaca langsung dari bamp_saved_data aktual secara dinamis (mendukung nilai 0.0)
        qty_bamp = float(m.get('Qty', 1.0))
        if bamp_items_saved and len(bamp_items_saved) >= idx:
            try:
                val_saved = bamp_items_saved[idx-1].get('qty')
                if val_saved is not None and str(val_saved).strip() != "":
                    qty_bamp = float(val_saved)
            except:
                pass
        elif m.get('Qty BAMP') is not None:
            try:
                qty_bamp = float(m.get('Qty BAMP'))
            except:
                pass

        rincian_rows_html += f"""
            <tr>
                <td>{idx}</td>
                <td>{kat}</td>
                <td style="text-align: left;">{desc}</td>
                <td>{qty:.2f}</td>
                <td>{unit}</td>
                <td>{tgl_mulai_item}</td>
                <td>{tgl_selesai_item}</td>
                <td style="text-align: right;">{price:,.2f}</td>
                <td style="text-align: right;">{tot:,.2f}</td>
                <td style="text-align: left;">{ket}</td>
            </tr>
        """

        desc_full_pi = f"<b>{kat}</b><br>{desc}"
        if ket:
            desc_full_pi += f"<br>{ket}"
        pi_rows_html += f"""
            <tr>
                <td>{idx}</td>
                <td style="text-align: left;">{desc_full_pi}</td>
                <td>{qty:.2f}</td>
                <td>{unit}</td>
                <td style="text-align: right;">{price:,.2f}</td>
                <td style="text-align: right;">{tot:,.2f}</td>
            </tr>
        """

        catatan_bamp = f"Mulai Berlaku Tanggal {bamp_date_str}"
        if ket:
            catatan_bamp = f"{catatan_bamp}<br>{ket}"
        bamp_rows_html += f"""
            <tr>
                <td>{idx}</td>
                <td style='text-align:left;'><b>{kat}</b><br>{desc}</td>
                <td>{qty_bamp:.2f}</td>
                <td>{unit}</td>
                <td style='text-align:left;'>{catatan_bamp}</td>
            </tr>
        """

        catatan_basp = f"Selesai Pelaksanaan Pekerjaan Tanggal {basp_date_str}"
        if ket:
            catatan_basp = f"{catatan_basp}<br>{ket}"
        basp_rows_html += f"""
            <tr>
                <td>{idx}</td>
                <td style='text-align:left;'><b>{kat}</b><br>{desc}</td>
                <td>{qty:.2f}</td>
                <td>{unit}</td>
                <td style='text-align:left;'>{catatan_basp}</td>
            </tr>
        """

        desc_full_opname = f"<b>{kat}</b><br>{desc}"
        if ket:
            desc_full_opname += f"<br>{ket}"
        opname_rows_html += f"""
            <tr>
                <td>1.{idx}</td>
                <td style="text-align: left;">{desc_full_opname}</td>
                <td>{unit}</td>
                <td>{qty:.2f}</td>
                <td style="text-align: right;">{price:,.2f}</td>
                <td style="text-align: right;">{tot:,.2f}</td>
                <td>0.00</td>
                <td style="text-align: right;">0.00</td>
                <td>{qty:.2f}</td>
                <td style="text-align: right;">{tot:,.2f}</td>
                <td>{qty:.2f}</td>
                <td style="text-align: right;">{tot:,.2f}</td>
                <td>0.00</td>
                <td style="text-align: right;">0.00</td>
            </tr>
        """

    terbilang_str = terbilang(grand_total)

    ttd_supervisor_html = f'<div style="height: 55px; display: flex; align-items: center; justify-content: center;"><img src="{custom_ttd_supervisor}" style="max-height: 52px; max-width: 140px; object-fit: contain;" alt="TTD Supervisor"></div>' if custom_ttd_supervisor else '<div style="height: 55px;"></div>'
    ttd_onesimus_html = f'<div style="height: 55px; display: flex; align-items: center; justify-content: center;"><img src="{custom_ttd_onesimus}" style="max-height: 52px; max-width: 140px; object-fit: contain;" alt="TTD Onesimus"></div>' if custom_ttd_onesimus else '<div style="height: 55px;"></div>'
    ttd_ferry_html = f'<div style="height: 55px; display: flex; align-items: center; justify-content: center;"><img src="{custom_ttd_ferry}" style="max-height: 52px; max-width: 140px; object-fit: contain;" alt="TTD Ferry"></div>' if custom_ttd_ferry else '<div style="height: 55px;"></div>'

    # ==========================================
    # 1. HALAMAN RINCIAN PEKERJAAN
    # ==========================================
    rincian_html = f"""
    <div class="page-break">
        <div style="text-align: center; font-weight: bold; font-size: 11px; margin-bottom: 2px;">PT. BANGGAI SENTRAL SULAWESI</div>
        <div style="text-align: center; font-size: 8.5px; color: #4b5563; margin-bottom: 10px;">General Contractor and Suppliers | Jl. Urip Sumoharjo No. 53 Luwuk, Kabupaten Banggai, Propinsi Sulawesi Tengah</div>
        <h2 style="text-align: center; font-size: 13px; text-transform: uppercase; border-bottom: 2px solid #000; padding-bottom: 4px; margin-bottom: 15px;">RINCIAN PEKERJAAN</h2>
        
        <table style="width: 100%; font-size: 9.5px; margin-bottom: 15px; border-collapse: collapse;">
            <tr>
                <td style="width: 18%; font-weight: bold;">Rincian Pekerjaan</td><td style="width: 2%;">:</td><td style="width: 35%;"><b>{current_pi_no}</b></td>
                <td style="width: 18%; font-weight: bold;">Ditujukan Kepada</td><td style="width: 2%;">:</td><td style="width: 25%;"><b>{p1_nama}</b></td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Nomor Kontrak</td><td>:</td><td>{nomor_kontrak}</td>
                <td style="font-weight: bold;">Nomor Purchase Order</td><td>:</td><td><b>{no_po}</b></td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Nama Kontrak</td><td>:</td><td>{nama_kontrak}</td>
                <td style="font-weight: bold;">Lingkup Pekerjaan</td><td>:</td><td>{lingkup_pekerjaan}</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Nomor Tender</td><td>:</td><td>{nomor_tender}</td>
                <td style="font-weight: bold;">Tanggal Purchase Order</td><td>:</td><td>{tgl_po}</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Tanggal Proforma</td><td>:</td><td>{tgl_pi}</td>
                <td style="font-weight: bold;">Mata Uang</td><td>:</td><td>IDR</td>
            </tr>
        </table>

        <table class="doc-table" style="width:100%; border-collapse:collapse; margin-bottom: 10px; font-size: 8px;">
            <tr>
                <th>No.</th><th>Kategori</th><th>Uraian Pekerjaan</th><th>Qty</th><th>Satuan</th>
                <th>Tanggal Mulai</th><th>Tanggal Selesai</th><th>Harga Satuan (IDR)</th><th>Total Harga (IDR)</th><th>Keterangan</th>
            </tr>
            {rincian_rows_html}
            <tr style="font-weight: bold; background: #f9fafb;">
                <td colspan="8" style="text-align: right;">TOTAL TAGIHAN :</td>
                <td style="text-align: right;">{grand_total:,.2f}</td>
                <td></td>
            </tr>
        </table>

        <div style="font-size: 9.5px; margin-bottom: 20px;">
            <b>Terbilang :</b> <i>{terbilang_str}</i>
        </div>

        <table style="width: 100%; table-layout: fixed; margin-top: 30px; border-collapse: collapse; page-break-inside: avoid;">
            <tr>
                <td style="width: 50%; text-align: center; vertical-align: top;">
                    <b>DIBUAT OLEH</b>
                    {ttd_supervisor_html}
                    <u><b>Yanuar Wiranata / Ireine Langi</b></u><br>Supervisor
                </td>
                <td style="width: 50%; text-align: center; vertical-align: top;">
                    <b>DIPERIKSA</b>
                    {ttd_onesimus_html}
                    <u><b>Onesimus Suriadi</b></u><br>Manager General Services
                </td>
            </tr>
        </table>
    </div>
    """

    # ==========================================
    # 2. HALAMAN PROFORMA INVOICE
    # ==========================================
    pi_html = f"""
    <div class="page-break">
        <div style="text-align: center; font-weight: bold; font-size: 10px; margin-bottom: 2px;">PT. BANGGAI SENTRAL SULAWESI</div>
        <div style="text-align: center; font-size: 8.5px; color: #4b5563; margin-bottom: 10px;">General Contractor and Suppliers | Jl. Urip Sumoharjo No. 53 Luwuk, Kabupaten Banggai, Propinsi Sulawesi Tengah</div>
        <h2 style="text-align: center; font-size: 13px; text-transform: uppercase; border-bottom: 2px solid #000; padding-bottom: 4px; margin-bottom: 10px;">PROFORMA INVOICE</h2>
        
        <table style="width: 100%; font-size: 9.5px; margin-bottom: 15px; border-collapse: collapse;">
            <tr>
                <td style="width: 55%; vertical-align: top;">
                    <b>TO:</b><br>
                    <b>{p1_nama}</b><br>
                    {p1_alamat}<br><br>
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

        <table style="width: 100%; table-layout: fixed; margin-top: 20px; border-collapse: collapse; page-break-inside: avoid;">
            <tr>
                <td style="width: 50%; text-align: center; vertical-align: top;"></td>
                <td style="width: 50%; text-align: center; vertical-align: top;">
                    <b>{p2_nama}</b>
                    {ttd_onesimus_html}
                    <u><b>Onesimus Suriadi</b></u><br>
                    Manager General Services
                </td>
            </tr>
        </table>
    </div>
    """

    # ==========================================
    # 3. HALAMAN BAMP
    # ==========================================
    bamp_html = f"""
    <div class="page-break">
        <table style="width: 100%; margin-top: 5px; margin-bottom: 12px; border-collapse: collapse;">
            <tr>
                <td style="width: 25%; text-align: left; vertical-align: middle; padding-left: 15px;">
                    <img src="{custom_logo_p1}" style="height: 35px;" alt="Logo Pihak Pertama">
                </td>
                <td style="width: 50%; text-align: center; vertical-align: middle;">
                    <h2 style="font-size: 14px; font-weight: bold; text-transform: uppercase; margin: 0; padding: 0;">BERITA ACARA MULAI PEKERJAAN (BAMP)</h2>
                </td>
                <td style="width: 25%; text-align: right; vertical-align: middle; padding-right: 15px;">
                    <img src="{custom_logo_p2}" style="height: 35px;" alt="Logo Pihak Kedua">
                </td>
            </tr>
        </table>
        <div style="border-bottom: 2px solid #000; margin-bottom: 15px;"></div>

        <p style="font-size: 9.5px;">Pada hari ini, tanggal <b>{bamp_date_str}</b>, yang bertanda tangan di bawah ini:</p>
        
        <table style="width: 100%; font-size: 9.5px; margin-bottom: 10px; border-collapse: collapse;">
            <tr><td style="width: 25%; font-weight: bold;">01. PIHAK PERTAMA</td><td></td></tr>
            <tr><td>Nama Perusahaan</td><td>: {p1_nama}</td></tr>
            <tr><td>Alamat</td><td>: {p1_alamat}</td></tr>
            <tr><td>Diwakili oleh</td><td>: {p1_wakil}</td></tr>
            <tr><td>Jabatan</td><td>: {p1_jabatan}</td></tr>
            <tr><td style="font-weight: bold; padding-top: 5px;">02. PIHAK KEDUA</td><td></td></tr>
            <tr><td>Nama Perusahaan</td><td>: {p2_nama}</td></tr>
            <tr><td>Alamat</td><td>: {p2_alamat}</td></tr>
            <tr><td>Diwakili oleh</td><td>: Ir. Ferry Tatimu</td></tr>
            <tr><td>Jabatan</td><td>: Direktur</td></tr>
        </table>

        <div style="font-size: 9.5px; font-weight: bold; margin-top: 10px; margin-bottom: 5px;">DASAR PELAKSANAAN PEKERJAAN</div>
        <table style="width: 100%; font-size: 9.5px; margin-bottom: 10px; border-collapse: collapse;">
            <tr><td style="width: 25%;">Nomor Kontrak</td><td style="width: 75%;">: {nomor_kontrak}</td></tr>
            <tr><td>Tanggal Kontrak</td><td>: {tgl_kontrak}</td></tr>
            <tr><td>Nomor Purchase Order</td><td>: {no_po}</td></tr>
            <tr><td>Tanggal Purchase Order</td><td>: {tgl_po}</td></tr>
            <tr><td>Lingkup Pekerjaan</td><td>: {lingkup_pekerjaan}</td></tr>
        </table>

        <p style="font-size: 9.5px;">Dengan ini PIHAK KEDUA menyatakan mulai melaksanakan seluruh pekerjaan secara baik dan siap terhitung mulai tanggal <b>{bamp_date_str}</b> dengan rincian sebagai berikut:</p>

        <table class="doc-table" style="width:100%; border-collapse:collapse; margin-top:10px; margin-bottom: 20px;">
            <tr><th style="width: 8%;">NO</th><th style="width: 42%;">KETERANGAN PEKERJAAN</th><th style="width: 10%;">JUMLAH</th><th style="width: 10%;">SATUAN</th><th style="width: 30%;">CATATAN</th></tr>
            {bamp_rows_html}
        </table>

        <p style="font-size: 9.5px;">Demikian Berita Acara Mulai Pekerjaan ini dibuat dan ditandatangani oleh kedua belah pihak untuk dipergunakan sebagaimana mestinya.</p>

        <table style="width: 100%; table-layout: fixed; margin-top: 30px; border-collapse: collapse; page-break-inside: avoid;">
            <tr>
                <td style="width: 50%; text-align: center; vertical-align: top;">
                    <b>{p1_nama}</b><br>PIHAK PERTAMA
                    <div style="height: 55px;"></div>
                    <u><b>{p1_wakil}</b></u><br>{p1_jabatan}
                </td>
                <td style="width: 50%; text-align: center; vertical-align: top;">
                    <b>{p2_nama}</b><br>PIHAK KEDUA
                    {ttd_ferry_html}
                    <u><b>Ir. Ferry Tatimu</b></u><br>Direktur
                </td>
            </tr>
        </table>
    </div>
    """

    # ==========================================
    # 4. HALAMAN BASP
    # ==========================================
    basp_html = f"""
    <div class="page-break">
        <table style="width: 100%; margin-top: 5px; margin-bottom: 12px; border-collapse: collapse;">
            <tr>
                <td style="width: 25%; text-align: left; vertical-align: middle; padding-left: 15px;">
                    <img src="{custom_logo_p1}" style="height: 35px;" alt="Logo Pihak Pertama">
                </td>
                <td style="width: 50%; text-align: center; vertical-align: middle;">
                    <h2 style="font-size: 14px; font-weight: bold; text-transform: uppercase; margin: 0; padding: 0;">BERITA ACARA SELESAI PEKERJAAN (BASP)</h2>
                </td>
                <td style="width: 25%; text-align: right; vertical-align: middle; padding-right: 15px;">
                    <img src="{custom_logo_p2}" style="height: 35px;" alt="Logo Pihak Kedua">
                </td>
            </tr>
        </table>
        <div style="border-bottom: 2px solid #000; margin-bottom: 15px;"></div>

        <p style="font-size: 9.5px;">Pada hari ini, tanggal <b>{basp_date_str}</b>, yang bertanda tangan di bawah ini:</p>
        
        <table style="width: 100%; font-size: 9.5px; margin-bottom: 10px; border-collapse: collapse;">
            <tr><td style="width: 25%; font-weight: bold;">01. PIHAK PERTAMA</td><td></td></tr>
            <tr><td>Nama Perusahaan</td><td>: {p1_nama}</td></tr>
            <tr><td>Alamat</td><td>: {p1_alamat}</td></tr>
            <tr><td>Diwakili oleh</td><td>: {p1_wakil}</td></tr>
            <tr><td>Jabatan</td><td>: {p1_jabatan}</td></tr>
            <tr><td style="font-weight: bold; padding-top: 5px;">02. PIHAK KEDUA</td><td></td></tr>
            <tr><td>Nama Perusahaan</td><td>: {p2_nama}</td></tr>
            <tr><td>Alamat</td><td>: {p2_alamat}</td></tr>
            <tr><td>Diwakili oleh</td><td>: Ir. Ferry Tatimu</td></tr>
            <tr><td>Jabatan</td><td>: Direktur</td></tr>
        </table>

        <div style="font-size: 9.5px; font-weight: bold; margin-top: 10px; margin-bottom: 5px;">DASAR PELAKSANAAN PEKERJAAN</div>
        <table style="width: 100%; font-size: 9.5px; margin-bottom: 10px; border-collapse: collapse;">
            <tr><td style="width: 25%;">Nomor Kontrak</td><td style="width: 75%;">: {nomor_kontrak}</td></tr>
            <tr><td>Tanggal Kontrak</td><td>: {tgl_kontrak}</td></tr>
            <tr><td>Nomor Purchase Order</td><td>: {no_po}</td></tr>
            <tr><td>Tanggal Purchase Order</td><td>: {tgl_po}</td></tr>
            <tr><td>Lingkup Pekerjaan</td><td>: {lingkup_pekerjaan}</td></tr>
        </table>

        <p style="font-size: 9.5px;">Dengan ini PIHAK KEDUA menyatakan telah menyelesaikan seluruh pekerjaan secara baik dan lengkap terhitung sampai dengan tanggal <b>{basp_date_str}</b> dengan rincian sebagai berikut:</p>

        <table class="doc-table" style="width:100%; border-collapse:collapse; margin-top:10px; margin-bottom: 20px;">
            <tr><th style="width: 8%;">NO</th><th style="width: 42%;">KETERANGAN PEKERJAAN</th><th style="width: 10%;">JUMLAH</th><th style="width: 10%;">SATUAN</th><th style="width: 30%;">CATATAN</th></tr>
            {basp_rows_html}
        </table>

        <p style="font-size: 9.5px;">Demikian Berita Acara Selesai Pekerjaan ini dibuat dan ditandatangani oleh kedua belah pihak untuk dipergunakan sebagaimana mestinya.</p>

        <table style="width: 100%; table-layout: fixed; margin-top: 30px; border-collapse: collapse; page-break-inside: avoid;">
            <tr>
                <td style="width: 50%; text-align: center; vertical-align: top;">
                    <b>{p1_nama}</b><br>PIHAK PERTAMA
                    <div style="height: 55px;"></div>
                    <u><b>{p1_wakil}</b></u><br>{p1_jabatan}
                </td>
                <td style="width: 50%; text-align: center; vertical-align: top;">
                    <b>{p2_nama}</b><br>PIHAK KEDUA
                    {ttd_ferry_html}
                    <u><b>Ir. Ferry Tatimu</b></u><br>Direktur
                </td>
            </tr>
        </table>
    </div>
    """

    # ==========================================
    # 5. HALAMAN WORK COMPLETION CERTIFICATE (WCC)
    # ==========================================
    num_signers_wcc = len(wcc_signers_list)
    col_width_pct_wcc = round(100.0 / num_signers_wcc, 2) if num_signers_wcc > 0 else 50.0
    
    wcc_signers_cells_html = ""
    for idx, sig in enumerate(wcc_signers_list):
        s_role = sig.get('role', '')
        s_comp = sig.get('company', '')
        s_name = sig.get('name', '')
        s_title = sig.get('title', '')
        s_show_loc = sig.get('show_loc', idx == 0)
        
        loc_date_text = f"{wcc_lokasi}, {wcc_date_str}<br>" if s_show_loc else "<br>"
        
        img_box = '<div style="height: 55px;"></div>'
        if idx == 0 and custom_ttd_onesimus:
            img_box = f'<div style="height: 55px; display: flex; align-items: center; justify-content: center;"><img src="{custom_ttd_onesimus}" style="max-height: 52px; max-width: 140px; object-fit: contain;"></div>'

        wcc_signers_cells_html += f"""
            <td style="width: {col_width_pct_wcc}%; text-align: center; vertical-align: top; font-size: 9px; padding: 0 10px;">
                {loc_date_text}
                <b>{s_comp}</b><br>
                {s_role}
                {img_box}
                <u><b>{s_name}</b></u><br>
                {s_title}
            </td>
        """

    wcc_sig_table_html = f"""
    <table style="width: 100%; table-layout: fixed; margin-top: 30px; border-collapse: collapse; page-break-inside: avoid;">
        <tr>
            {wcc_signers_cells_html}
        </tr>
    </table>
    """

    wcc_html = f"""
    <div class="page-break">
        <div style="text-align: center; font-weight: bold; font-size: 13px; text-transform: uppercase; margin-bottom: 2px;">{wcc_header_title}</div>
        <div style="text-align: center; font-weight: bold; font-size: 11px; margin-bottom: 15px;">{wcc_header_contract}</div>
        
        <div style="border: 1px solid #000; background-color: #dbeafe; text-align: center; font-weight: bold; font-size: 12px; padding: 6px; margin-bottom: 2px;">
            WORK COMPLETION CERTIFICATE
        </div>
        <div style="border: 1px solid #000; background-color: #f8fafc; text-align: center; font-weight: bold; font-size: 11px; padding: 6px; margin-bottom: 20px;">
            CERTIFICATE NO : {wcc_cert_no}
        </div>

        <div style="font-size: 10px; margin-bottom: 15px;">
            On the date of <b>{wcc_date_str}</b> we on behalf of <b>{p2_nama}</b> have completed the following job:
        </div>

        <table style="width: 100%; border-collapse: collapse; font-size: 9.5px; margin-bottom: 25px;">
            <tr style="border: 1px solid #000;">
                <td style="width: 25%; font-weight: bold; padding: 8px; border: 1px solid #000; background-color: #f8fafc;">WORK ORDER NUMBER</td>
                <td style="width: 3%; padding: 8px; border: 1px solid #000; text-align: center;">:</td>
                <td style="width: 72%; padding: 8px; border: 1px solid #000;">{wcc_wo_no}</td>
            </tr>
            <tr style="border: 1px solid #000;">
                <td style="font-weight: bold; padding: 8px; border: 1px solid #000; background-color: #f8fafc;">WORK ORDER TITLE</td>
                <td style="padding: 8px; border: 1px solid #000; text-align: center;">:</td>
                <td style="padding: 8px; border: 1px solid #000;">{wcc_wo_title}</td>
            </tr>
            <tr style="border: 1px solid #000;">
                <td style="font-weight: bold; padding: 8px; border: 1px solid #000; background-color: #f8fafc;">CTR NUMBER</td>
                <td style="padding: 8px; border: 1px solid #000; text-align: center;">:</td>
                <td style="padding: 8px; border: 1px solid #000;">{wcc_ctr_no}</td>
            </tr>
            <tr style="border: 1px solid #000;">
                <td style="font-weight: bold; padding: 8px; border: 1px solid #000; background-color: #f8fafc; vertical-align: top;">DESCRIPTION</td>
                <td style="padding: 8px; border: 1px solid #000; text-align: center; vertical-align: top;">:</td>
                <td style="padding: 8px; border: 1px solid #000;">
                    <table style="width:100%; border:none;"><tr><td style="border:none; padding:0; width:65%;">{progress_desc}</td><td style="border:none; padding:0; width:35%; text-align:right; font-weight:bold;">Rp {grand_total:,.2f}</td></tr></table>
                </td>
            </tr>
            <tr style="border: 1px solid #000;">
                <td style="font-weight: bold; padding: 8px; border: 1px solid #000; background-color: #f8fafc;">AMOUNT TOTAL</td>
                <td style="padding: 8px; border: 1px solid #000; text-align: center;">:</td>
                <td style="padding: 8px; border: 1px solid #000; font-weight: bold;">{terbilang_str}</td>
            </tr>
        </table>

        <div style="font-size: 10px; margin-bottom: 30px;">
            The work has been properly completed as per requirement, witnessed and accepted by <b>{p1_nama}</b>.
        </div>

        {wcc_sig_table_html}
    </div>
    """

    # ==========================================
    # 6. HALAMAN OPNAME PEKERJAAN (BERBASIS TANGGAL SELESAI / BASP)
    # ==========================================
    if str(nomor_kontrak).strip() == "7207250142":
        opname_sig_table_html = f"""
        <table style="width: 100%; table-layout: fixed; margin-top: 20px; border-collapse: collapse; page-break-inside: avoid;">
            <tr>
                <td style="width: 33.3%; text-align: center; vertical-align: top; font-size: 9px; padding: 0 10px;">
                    {lokasi_bamp}, {opname_date_str}<br><b>{p2_nama}</b><br>Prepared by,
                    {ttd_onesimus_html}
                    <u><b>Onesimus Suriadi</b></u><br>Manager General Services
                </td>
                <td style="width: 33.3%; text-align: center; vertical-align: top; font-size: 9px; padding: 0 10px;">
                    <br><b>{p1_nama}</b><br>Reviewed by,
                    <div style="height: 55px;"></div>
                    <u><b>Rafik Hidayat / Ronny Dwi Purnomo</b></u><br>Maintenance Support Supervisor
                </td>
                <td style="width: 33.3%; text-align: center; vertical-align: top; font-size: 9px; padding: 0 10px;">
                    <br><b>{p1_nama}</b><br>Approved by,
                    <div style="height: 55px;"></div>
                    <u><b>{p1_wakil}</b></u><br>{p1_jabatan}
                </td>
            </tr>
        </table>
        """
    else:
        opname_sig_table_html = f"""
        <table style="width: 100%; table-layout: fixed; margin-top: 20px; border-collapse: collapse; page-break-inside: avoid;">
            <tr>
                <td style="width: 50%; text-align: center; vertical-align: top; font-size: 9px; padding: 0 10px;">
                    {lokasi_bamp}, {opname_date_str}<br><b>{p2_nama}</b><br>Prepared by,
                    {ttd_onesimus_html}
                    <u><b>Onesimus Suriadi</b></u><br>Manager General Services
                </td>
                <td style="width: 50%; text-align: center; vertical-align: top; font-size: 9px; padding: 0 10px;">
                    <br><b>{p1_nama}</b><br>Approved by,
                    <div style="height: 55px;"></div>
                    <u><b>{p1_wakil}</b></u><br>{p1_jabatan}
                </td>
            </tr>
        </table>
        """

    opname_html = f"""
    <div class="page-break">
        <table style="width: 100%; margin-top: 5px; margin-bottom: 12px; border-collapse: collapse;">
            <tr>
                <td style="width: 25%; text-align: left; vertical-align: middle; padding-left: 15px;">
                    <img src="{custom_logo_p1}" style="height: 35px;" alt="Logo Pihak Pertama">
                </td>
                <td style="width: 50%; text-align: center; vertical-align: middle;">
                    <h2 style="font-size: 14px; font-weight: bold; text-transform: uppercase; margin: 0; padding: 0;">BERITA ACARA PEKERJAAN / OPNAME</h2>
                </td>
                <td style="width: 25%; text-align: right; vertical-align: middle; padding-right: 15px;">
                    <img src="{custom_logo_p2}" style="height: 35px;" alt="Logo Pihak Kedua">
                </td>
            </tr>
        </table>
        <div style="border-bottom: 2px solid #000; margin-bottom: 15px;"></div>
        
        <table style="width: 100%; font-size: 9.5px; margin-bottom: 10px; border-collapse: collapse;">
            <tr><td style="width: 25%; font-weight: bold;">JOB TITLE / WO / PO</td><td>: {lingkup_pekerjaan}</td></tr>
            <tr><td style="font-weight: bold;">CTR / WO / PO No.</td><td>: <b>{no_po}</b></td></tr>
            <tr><td style="font-weight: bold;">DATE</td><td>: <b>{opname_date_str}</b></td></tr>
            <tr><td style="font-weight: bold; color: #065f46;">PROFORMA INVOICE No.</td><td>: <b>{current_pi_no}</b></td></tr>
        </table>

        <table class="doc-table" style="width:100%; border-collapse:collapse; margin-bottom: 10px; font-size: 8px;">
            <tr>
                <th rowspan="2">NO</th><th rowspan="2">ITEM - DESCRIPTION</th><th rowspan="2">UOM</th>
                <th colspan="3">BASE ON CTR / PO</th>
                <th colspan="2">PREVIOUS OPNAME (IDR)</th>
                <th colspan="2">AKTUAL OPNAME (BULAN INI) (IDR)</th>
                <th colspan="2">CUMMULATIVE OPNAME (IDR)</th>
                <th colspan="2">SISA ANGGARAN (DEVIASI) (IDR)</th>
            </tr>
            <tr>
                <th>VOLUME</th><th>UNIT PRICE (IDR)</th><th>TOTAL PRICE (IDR)</th>
                <th>VOLUME</th><th>TOTAL PRICE</th>
                <th>VOLUME</th><th>TOTAL PRICE</th>
                <th>VOLUME</th><th>TOTAL PRICE</th>
                <th>VOLUME</th><th>TOTAL PRICE</th>
            </tr>
            {opname_rows_html}
            <tr style="font-weight: bold; background: #f9fafb;">
                <td colspan="3" style="text-align: right;">TOTAL :</td>
                <td>{float(t_data_utama.get('Qty', 1.0)):.2f}</td><td>-</td><td style="text-align: right;">{grand_total:,.2f}</td>
                <td>0.00</td><td style="text-align: right;">0.00</td>
                <td>{float(t_data_utama.get('Qty', 1.0)):.2f}</td><td style="text-align: right;">{grand_total:,.2f}</td>
                <td>{float(t_data_utama.get('Qty', 1.0)):.2f}</td><td style="text-align: right;">{grand_total:,.2f}</td>
                <td>0.00</td><td style="text-align: right;">0.00</td>
            </tr>
        </table>

        <div style="font-size: 9.5px; font-weight: bold; margin-bottom: 20px;">
            Total Akumulasi Penyerapan (Cumulative Opname): Rp {grand_total:,.2f}<br>
            Sisa Nilai Anggaran PO (Deviasi): Rp 0.00
        </div>

        {opname_sig_table_html}
    </div>
    """

    # ==========================================
    # 7. HALAMAN TKDN
    # ==========================================
    total_jasa = grand_total * (95.0 / 100.0)
    non_cost = grand_total * 0.05

    tkdn_html = f"""
    <div class="page-break">
        <div style="text-align: center; font-weight: bold; font-size: 11px; margin-bottom: 2px;">TABEL PERHITUNGAN TINGKAT KOMPONEN DALAM NEGERI - JASA</div>
        <div style="text-align: center; font-size: 10px; font-weight: bold; margin-bottom: 15px;">SELF - ASSESSMENT (PERMEN ESDM NO. 15 TAHUN 2013)</div>
        
        <table style="width: 100%; font-size: 9.5px; margin-bottom: 12px; border-collapse: collapse;">
            <tr>
                <td style="width: 18%; font-weight: bold;">Nama Penyedia Jasa</td><td style="width: 2%;">:</td><td style="width: 50%;"><b>{p2_nama}</b></td>
                <td style="width: 13%; font-weight: bold;">Nomor Kontrak</td><td style="width: 2%;">:</td><td style="width: 15%;"><b>{nomor_kontrak}</b></td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Judul Kontrak</td><td>:</td><td>{nama_kontrak}</td>
                <td style="font-weight: bold;">Nomor PO</td><td>:</td><td><b>{no_po}</b></td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Mata Uang</td><td>:</td><td>IDR</td>
                <td style="font-weight: bold;">Tanggal</td><td>:</td><td>{tkdn_date_str}</td>
            </tr>
        </table>

        <table class="doc-table" style="width:100%; border-collapse:collapse; margin-bottom: 10px; font-size: 8.5px;">
            <tr>
                <th style="width: 28%;">A. KOMPONEN BIAYA<br>(COST COMPONENT)</th>
                <th style="width: 8%;">MATA UANG</th>
                <th style="width: 13%;">KDN (A)</th>
                <th style="width: 13%;">KLN (B)</th>
                <th style="width: 14%;">TOTAL (C = A + B)</th>
                <th style="width: 12%;">% NILAI TKDN<br>(D = A / C)</th>
                <th style="width: 12%;">NILAI TKDN<br>(E = C X D)</th>
            </tr>
            <tr>
                <td style="text-align: left;">I. Biaya Bahan (Material) Terpakai<br><span style="font-size:7px; color:#555;">(material used cost)</span></td>
                <td>Rp</td><td style="background-color: #fef08a;">Rp 0.00</td><td style="background-color: #fef08a;">Rp 0.00</td><td>Rp 0.00</td><td>0.00%</td><td>Rp 0.00</td>
            </tr>
            <tr>
                <td style="text-align: left;"></td>
                <td>US$</td><td style="background-color: #fef08a;">0.00</td><td style="background-color: #fef08a;">0.00</td><td>0.00</td><td>0.00%</td><td>0.00</td>
            </tr>
            <tr>
                <td style="text-align: left;">II. Biaya Tenaga Kerja & Konsultan<br><span style="font-size:7px; color:#555;">(personnel & consultant cost)</span></td>
                <td>Rp</td><td style="background-color: #fef08a;">Rp 0.00</td><td style="background-color: #fef08a;">Rp 0.00</td><td>Rp 0.00</td><td>0.00%</td><td>Rp 0.00</td>
            </tr>
            <tr>
                <td style="text-align: left;"></td>
                <td>US$</td><td style="background-color: #fef08a;">0.00</td><td style="background-color: #fef08a;">0.00</td><td>0.00</td><td>0.00%</td><td>0.00</td>
            </tr>
            <tr>
                <td style="text-align: left;">III. Biaya Alat Kerja / Fasilitas Kerja<br><span style="font-size:7px; color:#555;">(equipment & work facility cost)</span></td>
                <td>Rp</td><td style="background-color: #fef08a;">Rp 0.00</td><td style="background-color: #fef08a;">Rp 0.00</td><td>Rp 0.00</td><td>0.00%</td><td>Rp 0.00</td>
            </tr>
            <tr>
                <td style="text-align: left;"></td>
                <td>US$</td><td style="background-color: #fef08a;">0.00</td><td style="background-color: #fef08a;">0.00</td><td>0.00</td><td>0.00%</td><td>0.00</td>
            </tr>
            <tr>
                <td style="text-align: left;">IV. Biaya Jasa Umum<br><span style="font-size:7px; color:#555;">(other services cost)</span></td>
                <td>Rp</td><td style="background-color: #fef08a;">Rp {total_jasa:,.2f}</td><td style="background-color: #fef08a;">Rp 0.00</td><td>Rp {total_jasa:,.2f}</td><td>100.00%</td><td>Rp {total_jasa:,.2f}</td>
            </tr>
            <tr>
                <td style="text-align: left;"></td>
                <td>US$</td><td style="background-color: #fef08a;">0.00</td><td style="background-color: #fef08a;">0.00</td><td>0.00</td><td>0.00%</td><td>0.00</td>
            </tr>
            <tr style="font-weight: bold; background: #f8fafc;">
                <td style="text-align: left;">V. JUMLAH BIAYA (&Sigma; I s/d IV)<br><span style="font-size:7px; color:#555;">(Total Cost)</span></td>
                <td>Rp</td><td>Rp {total_jasa:,.2f}</td><td>Rp 0.00</td><td>Rp {total_jasa:,.2f}</td><td>100.00%</td><td>Rp {total_jasa:,.2f}</td>
            </tr>
            <tr style="font-weight: bold; background: #f8fafc;">
                <td style="text-align: left;"></td>
                <td>US$</td><td>0.00</td><td>0.00</td><td>0.00</td><td>0.00%</td><td>0.00</td>
            </tr>
            <tr>
                <td style="text-align: left; font-weight: bold;">B. KOMPONEN BUKAN BIAYA<br><span style="font-size:7px; color:#555;">(Non-cost Component)</span></td>
                <td>Rp</td><td colspan="2" style="background-color: #fef08a;"></td><td>Rp {non_cost:,.2f}</td><td colspan="2"></td>
            </tr>
            <tr>
                <td style="text-align: left;"></td>
                <td>US$</td><td colspan="2" style="background-color: #fef08a;"></td><td>0.00</td><td colspan="2"></td>
            </tr>
            <tr style="font-weight: bold; background: #f1f5f9;">
                <td style="text-align: left;">C. JUMLAH NILAI TOTAL (A + B)</td>
                <td>Rp</td><td colspan="2"></td><td>Rp {grand_total:,.2f}</td><td colspan="2"></td>
            </tr>
            <tr style="font-weight: bold; background: #f1f5f9;">
                <td style="text-align: left;"></td>
                <td>US$</td><td colspan="2"></td><td>0.00</td><td colspan="2"></td>
            </tr>
            <tr style="font-weight: bold; background: #e2e8f0; font-size: 10.5px; color: #065f46;">
                <td colspan="6" style="text-align: right;">CAPAIAN PERSENTASE TKDN AKHIR (%):</td>
                <td style="text-align: right;">95.00 %</td>
            </tr>
        </table>

        <div style="font-size: 8.5px; margin-bottom: 15px;">
            <b>Catatan:</b><br>
            &bull; Isi hanya pada kolom yang berwarna kuning pastel.<br>
            &bull; Formulasi perhitungan mengacu pada Permen ESDM No. 15 Tahun 2013.
        </div>

        <table style="width: 100%; table-layout: fixed; margin-top: 25px; border-collapse: collapse; page-break-inside: avoid;">
            <tr>
                <td style="width: 50%; text-align: center; vertical-align: top;"></td>
                <td style="width: 50%; text-align: center; vertical-align: top;">
                    {lokasi_tkdn}, {tkdn_date_str}<br>
                    <b>{p2_nama}</b>
                    {ttd_ferry_html}
                    <u><b>Ir. Ferry Tatimu</b></u><br>
                    Direktur
                </td>
            </tr>
        </table>
    </div>
    """

    # --- MASTER CONTAINER HTML ---
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
        {rincian_html}
        {pi_html}
        {bamp_html}
        {basp_html}
        {wcc_html}
        {opname_html}
        {tkdn_html}
    </body>
    </html>
    """

    st.markdown('<div class="document-preview">', unsafe_allow_html=True)
    st.components.v1.html(master_html, height=750, scrolling=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_b1, col_b2, col_b3 = st.columns(3)
    
    with col_b1:
        if st.button("💾 Simpan Paket Dokumen Final (Save)", use_container_width=True, type="primary"):
            try:
                with open(file_saved_path, "w", encoding="utf-8") as f:
                    f.write(master_html)
                st.success(f"✅ Paket dokumen untuk PI [{current_pi_no}] berhasil disimpan secara permanen!")
                st.rerun()
            except Exception as e:
                st.error(f"Gagal menyimpan dokumen: {e}")

    with col_b2:
        b64_html = base64.b64encode(master_html.encode("utf-8")).decode()
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
            <button onclick="printAllDocs()" style="width: 100%; background-color: #10b981; color: white; padding: 10px 15px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 13px;">
                🖨️ Cetak (1-Click Print)
            </button>
        """
        st.components.v1.html(print_script, height=50)

    with col_b3:
        download_link = f'<a href="data:text/html;base64,{b64_html}" download="Master_Paket_Dokumen_{current_pi_no.replace("/", "-")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px 15px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 13px;">📥 Download File (.HTML)</button></a>'
        st.markdown(download_link, unsafe_allow_html=True)