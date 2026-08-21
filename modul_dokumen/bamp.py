import streamlit as st
import pandas as pd
import base64
from datetime import datetime

def tampilkan_bamp(transaksi_list):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📋 Pratinjau, Cetak & Download Berita Acara Mulai Pekerjaan (BAMP)</h3>
        </div>
    """, unsafe_allow_html=True)

    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi rincian pekerjaan yang diproses.")
        return

    seen_pi_dd = set()
    unique_tx_list = []
    for t in transaksi_list:
        pi_key = str(t.get('PI No.', '')).strip()
        if pi_key not in seen_pi_dd:
            seen_pi_dd.add(pi_key)
            unique_tx_list.append(t)

    pilihan_tx = [f"PI: {t['PI No.']} | Kontrak: {t['Nomor Kontrak']} | Total: Rp {t['Total Harga']:,.0f}" for t in unique_tx_list]
    
    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        selected_idx = st.selectbox("Pilih Dokumen Transaksi Berdasarkan PI:", range(len(pilihan_tx)), format_func=lambda x: pilihan_tx[x])
    with col_sel2:
        lokasi_office = st.text_input("📍 Lokasi Office (Tempat BAMP):", value="Luwuk", key="bamp_lokasi")

    t_data = unique_tx_list[selected_idx]
    current_pi_no = str(t_data.get('PI No.', '')).strip().lower()

    # --- PENGAMBILAN DATABASE INDUK MODUL 1 ---
    try:
        from __main__ import muat_data_invoice
        saved_db_induk = muat_data_invoice()
    except:
        try:
            import os
            df_induk = pd.read_excel(os.path.join("database_penyimpanan_aman", "database_proforma_invoice.xlsx"))
            saved_db_induk = df_induk.to_dict(orient="records")
        except:
            saved_db_induk = []

    matched_item = {}
    for item in saved_db_induk:
        if isinstance(item, dict):
            val_pi_0 = str(item.get(0, item.get('Proforma Invoice No.', ''))).strip().lower()
            if val_pi_0 == current_pi_no:
                matched_item = item
                break

    def get_induk(idx_num, text_key, fallback="-"):
        if idx_num in matched_item:
            v = matched_item[idx_num]
            if v is not None and str(v).strip() != "" and str(v).strip().lower() != "nan":
                return str(v).strip()
        if text_key in matched_item:
            v = matched_item[text_key]
            if v is not None and str(v).strip() != "" and str(v).strip().lower() != "nan":
                return str(v).strip()
        return fallback

    nomor_kontrak_str = get_induk(1, 'Nomor Kontrak', t_data.get('Nomor Kontrak', '-'))
    tgl_kontrak = get_induk(4, 'Tanggal Kontrak', '-')
    lingkup_pekerjaan = get_induk(3, 'Lingkup Pekerjaan', t_data.get('Deskripsi PO', '-'))
    no_po_auto = get_induk(8, 'Nomor Purchase Order', t_data.get('Nomor PO', '-'))
    tgl_po_auto = get_induk(9, 'Tanggal Purchase Order', t_data.get('Tanggal PO', '-'))

    p1_nama = get_induk(10, 'Pihak Pertama', 'JOB Pertamina - Medco E&P Tomori Sulawesi')
    p1_alamat = get_induk(11, 'Alamat Pihak Pertama', 'Bidakara Office Tower I 4Th Floor, Jl. Gatot Subroto Kav. 71 - 73, Jakarta 12870, Indonesia')
    p1_wakil_lengkap = get_induk(12, 'Diwakili Oleh', 'Ronny Dwi Purnomo / Rafik Hidayat')
    p1_jabatan = get_induk(13, 'Selaku', 'Maintenance Support Supervisor')
    p1_wakil_sign = p1_wakil_lengkap

    p2_nama = get_induk(14, 'Pihak Kedua', 'PT Banggai Sentral Sulawesi')
    p2_alamat = get_induk(15, 'Alamat Pihak Kedua', 'Jl. Urip Sumoharjo No. 53, Luwuk, Kabupaten Banggai, Provinsi Sulawesi Tengah (94715), Indonesia')
    p2_wakil = get_induk(16, 'Diwakili Oleh (P2)', 'Ir. Ferry Tatimu')
    p2_jabatan = get_induk(17, 'Selaku (P2)', 'Direktur Utama')

    kategori_item = str(t_data.get('Kategori', '')).strip()
    deskripsi_item = str(t_data.get('Deskripsi Pekerjaan', '')).strip()
    item_desc_final = f"<b>{kategori_item}</b><br>{deskripsi_item}" if kategori_item else deskripsi_item
    
    default_uom = str(t_data.get('Unit', 'Day')).strip()

    st.markdown("#### ⚙️ Pengaturan Parameter Detail Berita Acara Mulai Pekerjaan (BAMP)")
    
    c_b1, c_b2, c_b3, c_b4 = st.columns(4)
    with c_b1:
        selected_date = st.date_input("📅 Mulai Operasi Tanggal:", value=datetime(2026, 7, 1), key="bamp_date_picker")
        bulan_indo = {
            1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
            7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
        }
        bamp_date = f"{selected_date.day:02d} {bulan_indo[selected_date.month]} {selected_date.year}"

    with c_b2:
        qty_val = st.number_input(
            "🔢 Jumlah / Qty BAMP:", 
            min_value=0.0, 
            value=1.0, 
            step=1.0, 
            format="%.2f"
        )

    with c_b3:
        # Ditambahkan pilihan satuan "AU" di dalam daftar dropdown
        uom_options = ["Month", "Day", "AU", "Ls", "Unit", "Trip", "Jam", "Orang", "Set"]
        default_idx = uom_options.index(default_uom) if default_uom in uom_options else 1
        uom_str = st.selectbox("🏷️ Satuan Unit:", uom_options, index=default_idx)

    with c_b4:
        tambahan_opsional = st.text_input("Catatan BAMP:", value="", placeholder="Opsional", key="bamp_catatan")

    catatan_final = f"Mulai Operasi Tanggal {bamp_date}"
    if tambahan_opsional.strip():
        catatan_final += f" - {tambahan_opsional.strip()}"

    if 'persisted_logo_1' not in st.session_state: st.session_state.persisted_logo_1 = None
    if 'persisted_logo_2' not in st.session_state: st.session_state.persisted_logo_2 = None

    st.markdown("#### 🖼️ Pengaturan Logo Header Dokumen BAMP")
    c_log1, c_log2 = st.columns(2)
    with c_log1:
        uploaded_logo_1 = st.file_uploader("Upload Logo Pihak Pertama", type=["png", "jpg", "jpeg"], key="logo_bamp_1")
        if uploaded_logo_1 is not None: st.session_state.persisted_logo_1 = uploaded_logo_1.getvalue()
    with c_log2:
        uploaded_logo_2 = st.file_uploader("Upload Logo Pihak Kedua", type=["png", "jpg", "jpeg"], key="logo_bamp_2")
        if uploaded_logo_2 is not None: st.session_state.persisted_logo_2 = uploaded_logo_2.getvalue()

    logo1_html = f'<img src="data:image/png;base64,{base64.b64encode(st.session_state.persisted_logo_1).decode()}" style="max-height: 42px; max-width: 110px; object-fit: contain; display: block; margin: 0 auto;">' if st.session_state.persisted_logo_1 is not None else ""
    logo2_html = f'<img src="data:image/png;base64,{base64.b64encode(st.session_state.persisted_logo_2).decode()}" style="max-height: 42px; max-width: 110px; object-fit: contain; display: block; margin: 0 auto;">' if st.session_state.persisted_logo_2 is not None else ""

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Berita Acara Mulai Pekerjaan</title>
        <style>
            @page {{ 
                size: A4; 
                margin: 8mm; 
            }}
            @media print {{
                body {{ -webkit-print-color-adjust: exact; margin: 0; }}
                @page {{ size: A4; margin: 8mm; }}
                .iso-footer-left {{
                    position: fixed;
                    bottom: 0;
                    left: 0;
                }}
            }}
            body {{ font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; padding: 10px; margin: 0; font-size: 9.5px; line-height: 1.35; }}
            .header-table {{ width: 100%; border-collapse: collapse; border-bottom: 2px solid #000; padding-bottom: 6px; margin-bottom: 10px; }}
            .header-table td {{ border: none; vertical-align: middle; padding: 0 4px; }}
            
            .main-doc-title {{ font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; margin: 0; text-align: center; }}
            
            .section-title {{ font-weight: bold; font-size: 9.5px; text-transform: uppercase; margin-top: 8px; margin-bottom: 3px; text-decoration: underline; }}
            .info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 8px; font-size: 9.5px; }}
            .info-table td {{ padding: 1.5px 3px; border: none; vertical-align: top; }}
            .col-label {{ width: 22%; }}
            .col-colon {{ width: 2%; text-align: center; }}
            .col-value {{ width: 76%; }}
            table.item-grid {{ width: 100%; border-collapse: collapse; margin-bottom: 12px; }}
            table.item-grid th, table.item-grid td {{ border: 1px solid #000; padding: 5px 6px; font-size: 9px; vertical-align: middle; }}
            .th-header {{ background-color: #f1f5f9; font-weight: bold; text-transform: uppercase; text-align: center; }}
            .content-text {{ margin-bottom: 10px; font-size: 9.5px; text-align: justify; }}
            
            table.sig-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; margin-bottom: 15px; border: none; }}
            table.sig-table td {{ border: none; vertical-align: top; font-size: 9.5px; padding: 6px; }}
            .sig-space {{ height: 50px; }}
            
            .iso-footer-left {{ 
                font-size: 8px; 
                font-weight: bold; 
                text-align: left; 
                margin-top: 15px; 
                padding-top: 4px; 
            }}
        </style>
    </head>
    <body>
        <table class="header-table">
            <tr>
                <td style="width: 25%; text-align: left;">{logo1_html}</td>
                <td style="width: 50%; text-align: center;">
                    <div class="main-doc-title">BERITA ACARA MULAI PEKERJAAN (BAMP)</div>
                </td>
                <td style="width: 25%; text-align: right;">{logo2_html}</td>
            </tr>
        </table>

        <div class="content-text">
            Pada hari ini, tanggal <b>{bamp_date}</b>, yang bertanda tangan di bawah ini:
        </div>

        <div class="section-title">01. PIHAK PERTAMA</div>
        <table class="info-table">
            <tr><td class="col-label">Nama Perusahaan</td><td class="col-colon">:</td><td class="col-value"><b>{p1_nama}</b></td></tr>
            <tr><td class="col-label">Alamat</td><td class="col-colon">:</td><td class="col-value">{p1_alamat}</td></tr>
            <tr><td class="col-label">Diwakili oleh</td><td class="col-colon">:</td><td class="col-value"><b>{p1_wakil_lengkap}</b></td></tr>
            <tr><td class="col-label">Jabatan</td><td class="col-colon">:</td><td class="col-value"><b>{p1_jabatan}</b></td></tr>
        </table>

        <div class="section-title" style="margin-top: 8px;">02. PIHAK KEDUA</div>
        <table class="info-table">
            <tr><td class="col-label">Nama Perusahaan</td><td class="col-colon">:</td><td class="col-value"><b>{p2_nama}</b></td></tr>
            <tr><td class="col-label">Alamat</td><td class="col-colon">:</td><td class="col-value">{p2_alamat}</td></tr>
            <tr><td class="col-label">Diwakili oleh</td><td class="col-colon">:</td><td class="col-value"><b>{p2_wakil}</b></td></tr>
            <tr><td class="col-label">Jabatan</td><td class="col-colon">:</td><td class="col-value"><b>{p2_jabatan}</b></td></tr>
        </table>

        <div class="section-title" style="margin-top: 10px;">DASAR PELAKSANAAN PEKERJAAN</div>
        <table class="info-table">
            <tr><td class="col-label" style="font-weight: bold;">Nomor Kontrak</td><td class="col-colon">:</td><td class="col-value"><b>{nomor_kontrak_str}</b></td></tr>
            <tr><td class="col-label" style="font-weight: bold;">Tanggal Kontrak</td><td class="col-colon">:</td><td class="col-value">{tgl_kontrak}</td></tr>
            <tr><td class="col-label" style="font-weight: bold;">Nomor Purchase Order</td><td class="col-colon">:</td><td class="col-value"><b>{no_po_auto}</b></td></tr>
            <tr><td class="col-label" style="font-weight: bold;">Tanggal Purchase Order</td><td class="col-colon">:</td><td class="col-value">{tgl_po_auto}</td></tr>
            <tr><td class="col-label" style="font-weight: bold; vertical-align: top;">Lingkup Pekerjaan</td><td class="col-colon" style="vertical-align: top;">:</td><td class="col-value"><b>{lingkup_pekerjaan}</b></td></tr>
        </table>

        <div class="content-text" style="margin-top: 8px;">
            Dengan ini <b>PIHAK KEDUA</b> menyatakan mulai melaksanakan seluruh pekerjaan secara baik dan siap terhitung mulai tanggal <b>{bamp_date}</b> dengan rincian sebagai berikut:
        </div>

        <table class="item-grid">
            <tr>
                <th class="th-header" style="width: 8%;">NO</th>
                <th class="th-header" style="width: 45%;">KETERANGAN PEKERJAAN</th>
                <th class="th-header" style="width: 12%;">JUMLAH</th>
                <th class="th-header" style="width: 12%;">SATUAN</th>
                <th class="th-header" style="width: 23%;">CATATAN</th>
            </tr>
            <tr>
                <td style="text-align: center;">1</td>
                <td style="text-align: left;">{item_desc_final}</td>
                <td style="text-align: center;">{qty_val:.2f}</td>
                <td style="text-align: center;">{uom_str}</td>
                <td style="text-align: center;"><b>{catatan_final}</b></td>
            </tr>
        </table>

        <div class="content-text">
            Demikian Berita Acara Mulai Pekerjaan ini dibuat dan ditandatangani oleh kedua belah pihak untuk dipergunakan sebagaimana mestinya.
        </div>

        <table class="sig-table">
            <tr>
                <td style="width: 50%; text-align: left; padding-left: 15px;">
                    <b>{p1_nama}</b><br><b>PIHAK PERTAMA</b>
                    <div class="sig-space"></div>
                    <u><b>{p1_wakil_sign}</b></u><br>{p1_jabatan}
                </td>
                <td style="width: 50%; text-align: left; padding-left: 15px;">
                    <b>{p2_nama}</b><br><b>PIHAK KEDUA</b>
                    <div class="sig-space"></div>
                    <u><b>{p2_wakil}</b></u><br>{p2_jabatan}
                </td>
            </tr>
        </table>

        <div class="iso-footer-left">Dokumen No: FM-GS-14 Rev:03</div>
    </body>
    </html>
    """

    st.markdown('<div class="document-preview">', unsafe_allow_html=True)
    st.components.v1.html(html_content, height=650, scrolling=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
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
                🖨️ Cetak / Print Dokumen ke PDF (Klik Disini)
            </button>
        """
        st.components.v1.html(print_script, height=50)
        
    with col_btn2:
        b64_pdf = base64.b64encode(html_content.encode()).decode()
        download_link = f'<a href="data:text/html;base64,{b64_pdf}" download="BAMP_{nomor_kontrak_str.replace("/", "-")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download File HTML/PDF</button></a>'
        st.markdown(download_link, unsafe_allow_html=True)