import streamlit as st
import pandas as pd
import base64
from datetime import datetime, date

def tampilkan_basp(transaksi_list):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📋 Pratinjau, Cetak & Download Berita Acara Selesai Pekerjaan (BASP - Multi-Item Ready)</h3>
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

    # Inisialisasi penyimpanan session state khusus BASP
    if "basp_saved_data" not in st.session_state:
        st.session_state.basp_saved_data = {}

    selected_pi = st.selectbox("Pilih Nomor Proforma Invoice (PI):", unique_pi_list, key="basp_pi_select")
    
    pi_storage_key = str(selected_pi).strip()
    if pi_storage_key not in st.session_state.basp_saved_data:
        st.session_state.basp_saved_data[pi_storage_key] = {
            'lokasi': "Luwuk",
            'main_date': date.today(),
            'items': {}
        }

    saved_global = st.session_state.basp_saved_data[pi_storage_key]

    mutasi_terpilih = [t for t in transaksi_list if str(t.get('PI No.')).strip() == pi_storage_key]
    
    if not mutasi_terpilih:
        st.warning("⚠️ Tidak ada item mutasi ditemukan untuk PI ini.")
        return

    t_data_utama = mutasi_terpilih[0]
    current_pi_no = pi_storage_key.lower()

    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel2:
        lokasi_office = st.text_input("📍 Lokasi Office (Tempat BASP):", value=str(saved_global.get('lokasi', 'Luwuk')), key=f"basp_lokasi_{pi_storage_key}")

    selected_date = st.date_input("📅 Tanggal Utama Berita Acara (BASP):", value=saved_global.get('main_date', date.today()), key=f"basp_main_date_{pi_storage_key}")
    
    bulan_indo = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
        7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }
    basp_date = f"{selected_date.day:02d} {bulan_indo[selected_date.month]} {selected_date.year}"

    st.markdown("---")
    st.markdown("#### ⚙️ Pengaturan Parameter Detail & Catatan Fleksibel per Baris Pekerjaan BASP")
    
    rows_html = ""
    uom_options = ["Month", "Day", "AU", "Ls", "Unit", "Trip", "Jam", "Orang", "Set", "Pallet", "man-days"]
    temp_items_storage = {}

    for idx, m in enumerate(mutasi_terpilih, start=1):
        st.markdown(f"**Item {idx}: {m.get('Kategori')} - {m.get('Deskripsi Pekerjaan')}**")
        c_b1, c_b2, c_b3, c_b4 = st.columns(4)
        
        raw_tgl_selesai = m.get('Tanggal Selesai', str(date.today()))
        try:
            default_row_date = pd.to_datetime(raw_tgl_selesai).date()
        except:
            default_row_date = date.today()

        keterangan_m1 = str(m.get('Keterangan', '')).strip()
        saved_item_data = saved_global.get('items', {}).get(idx, {})

        with c_b1:
            row_date = st.date_input(f"Tanggal Selesai (Item {idx})", value=saved_item_data.get('date', default_row_date), key=f"basp_date_{pi_storage_key}_{idx}")
        with c_b2:
            row_qty = st.number_input(f"Jumlah / Qty (Item {idx})", min_value=0.0, value=float(saved_item_data.get('qty', m.get('Qty', 1.0))), step=1.0, format="%.2f", key=f"basp_qty_{pi_storage_key}_{idx}")
        with c_b3:
            default_uom = str(saved_item_data.get('uom', m.get('Unit', 'Day'))).strip()
            if default_uom not in uom_options:
                uom_options.append(default_uom)
            default_idx = uom_options.index(default_uom) if default_uom in uom_options else 0
            row_uom = st.selectbox(f"Satuan (Item {idx})", uom_options, index=default_idx, key=f"basp_uom_{pi_storage_key}_{idx}")
        with c_b4:
            row_catatan = st.text_input(f"Catatan Bebas / Fleksibel (Item {idx})", value=saved_item_data.get('catatan', keterangan_m1), placeholder="Contoh: Selesai Pelaksanaan", key=f"basp_cat_{pi_storage_key}_{idx}")

        temp_items_storage[idx] = {
            'date': row_date,
            'qty': row_qty,
            'uom': row_uom,
            'catatan': row_catatan
        }

        row_date_str = f"{row_date.day:02d} {bulan_indo[row_date.month]} {row_date.year}"
        
        catatan_row_final = f"Selesai Pelaksanaan Pekerjaan Tanggal {row_date_str}"
        text_keterangan_aktif = row_catatan.strip() if row_catatan.strip() else keterangan_m1
        if text_keterangan_aktif:
            catatan_row_final += f"<br><span style='font-size: 8.5px; color: #334155;'>{text_keterangan_aktif}</span>"

        kategori_m = str(m.get('Kategori', '')).strip()
        deskripsi_m = str(m.get('Deskripsi Pekerjaan', '')).strip()
        desc_final_m = f"<b>{kategori_m}</b><br>{deskripsi_m}" if kategori_m else deskripsi_m

        rows_html += f"""
            <tr>
                <td style="text-align: center;">{idx}</td>
                <td style="text-align: left;">{desc_final_m}</td>
                <td style="text-align: center;">{row_qty:.2f}</td>
                <td style="text-align: center;">{row_uom}</td>
                <td style="text-align: left;"><b>{catatan_row_final}</b></td>
            </tr>
        """
        st.markdown("<br>", unsafe_allow_html=True)

    # Form khusus tombol save / simpan dokumen BASP
    with st.form(key=f"form_basp_save_{pi_storage_key}"):
        st.markdown(f"**Konfirmasi Dokumen BASP (PI: {selected_pi}):** Klik tombol di bawah untuk mengunci konfigurasi.")
        submit_save_basp = st.form_submit_button("💾 Simpan & Kunci Dokumen BASP Ini", type="primary")
        if submit_save_basp:
            st.session_state.basp_saved_data[pi_storage_key] = {
                'lokasi': lokasi_office,
                'main_date': selected_date,
                'items': temp_items_storage
            }
            st.success(f"✅ Dokumen BASP untuk PI [{selected_pi}] berhasil disimpan dan dikunci!")

    if 'persisted_logo_1' not in st.session_state: st.session_state.persisted_logo_1 = None
    if 'persisted_logo_2' not in st.session_state: st.session_state.persisted_logo_2 = None

    st.markdown("---")
    st.markdown("#### 🖼️ Pengaturan Logo Header Dokumen BASP")
    c_log1, c_log2 = st.columns(2)
    with c_log1:
        uploaded_logo_1 = st.file_uploader("Upload Logo Pihak Pertama", type=["png", "jpg", "jpeg"], key="logo_basp_1")
        if uploaded_logo_1 is not None: st.session_state.persisted_logo_1 = uploaded_logo_1.getvalue()
    with c_log2:
        uploaded_logo_2 = st.file_uploader("Upload Logo Pihak Kedua", type=["png", "jpg", "jpeg"], key="logo_basp_2")
        if uploaded_logo_2 is not None: st.session_state.persisted_logo_2 = uploaded_logo_2.getvalue()

    logo1_html = f'<img src="data:image/png;base64,{base64.b64encode(st.session_state.persisted_logo_1).decode()}" style="max-height: 42px; max-width: 110px; object-fit: contain; display: block; margin: 0 auto;">' if st.session_state.persisted_logo_1 is not None else ""
    logo2_html = f'<img src="data:image/png;base64,{base64.b64encode(st.session_state.persisted_logo_2).decode()}" style="max-height: 42px; max-width: 110px; object-fit: contain; display: block; margin: 0 auto;">' if st.session_state.persisted_logo_2 is not None else ""

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

    nomor_kontrak_str = get_induk(1, 'Nomor Kontrak', t_data_utama.get('Nomor Kontrak', '-'))
    tgl_kontrak = get_induk(4, 'Tanggal Kontrak', '-')
    lingkup_pekerjaan = get_induk(3, 'Lingkup Pekerjaan', t_data_utama.get('Deskripsi PO', '-'))
    no_po_auto = get_induk(8, 'Nomor Purchase Order', t_data_utama.get('Nomor PO', '-'))
    tgl_po_auto = get_induk(9, 'Tanggal Purchase Order', t_data_utama.get('Tanggal PO', '-'))

    p1_nama = get_induk(10, 'Pihak Pertama', 'JOB Pertamina - Medco E&P Tomori Sulawesi')
    p1_alamat = get_induk(11, 'Alamat Pihak Pertama', 'Bidakara Office Tower I 4Th Floor, Jl. Gatot Subroto Kav. 71 - 73, Jakarta 12870, Indonesia')
    p1_wakil_lengkap = get_induk(12, 'Diwakili Oleh', 'Ronny Dwi Purnomo / Rafik Hidayat')
    p1_jabatan = get_induk(13, 'Selaku', 'Maintenance Support Supervisor')
    p1_wakil_sign = p1_wakil_lengkap

    p2_nama = get_induk(14, 'Pihak Kedua', 'PT Banggai Sentral Sulawesi')
    p2_alamat = get_induk(15, 'Alamat Pihak Kedua', 'Jl. Urip Sumoharjo No. 53, Luwuk, Kabupaten Banggai, Provinsi Sulawesi Tengah (94715), Indonesia')
    p2_wakil = get_induk(16, 'Diwakili Oleh (P2)', 'Ir. Ferry Tatimu')
    p2_jabatan = get_induk(17, 'Selaku (P2)', 'Direktur Utama')

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Berita Acara Selesai Pekerjaan</title>
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
            .header-table {{ width: 100%; border-collapse: collapse; border-bottom: 2px solid #000; padding-bottom: 6px; margin-bottom: 10mm; }}
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
                    <div class="main-doc-title">BERITA ACARA SELESAI PEKERJAAN (BASP)</div>
                </td>
                <td style="width: 25%; text-align: right;">{logo2_html}</td>
            </tr>
        </table>

        <div class="content-text">
            Pada hari ini, tanggal <b>{basp_date}</b>, yang bertanda tangan di bawah ini:
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
            Dengan ini <b>PIHAK KEDUA</b> menyatakan telah menyelesaikan seluruh pekerjaan secara baik dan lengkap terhitung sampai dengan tanggal <b>{basp_date}</b> dengan rincian sebagai berikut:
        </div>

        <table class="item-grid">
            <tr>
                <th class="th-header" style="width: 8%;">NO</th>
                <th class="th-header" style="width: 42%;">KETERANGAN PEKERJAAN</th>
                <th class="th-header" style="width: 12%;">JUMLAH</th>
                <th class="th-header" style="width: 12%;">SATUAN</th>
                <th class="th-header" style="width: 26%;">CATATAN</th>
            </tr>
            {rows_html}
        </table>

        <div class="content-text">
            Demikian Berita Acara Selesai Pekerjaan ini dibuat dan ditandatangani oleh kedua belah pihak untuk dipergunakan sebagaimana mestinya.
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

        <div class="iso-footer-left">Dokumen No: FM-GS-15 Rev:03</div>
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
        download_link = f'<a href="data:text/html;base64,{b64_pdf}" download="BASP_{nomor_kontrak_str.replace("/", "-")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download File HTML/PDF</button></a>'
        st.markdown(download_link, unsafe_allow_html=True)