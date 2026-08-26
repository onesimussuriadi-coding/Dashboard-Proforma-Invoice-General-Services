import streamlit as st
import pandas as pd
import base64
from datetime import datetime, date

def tampilkan_bastb(transaksi_list):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📦 Pratinjau, Cetak & Download Berita Acara Serah Terima Barang (BASTB - FM-GS-04 Rev:03)</h3>
        </div>
    """, unsafe_allow_html=True)

    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi rincian pekerjaan yang diproses.")
        return

    # --- FILTER CERDAS BASTB ---
    # BASTB hanya merekam/menampilkan item Barang / Material atau Gabungan (mengabaikan murni Jasa)
    transaksi_list = [
        t for t in transaksi_list 
        if "jasa" not in str(t.get('Jenis BASTP', 'Barang')).lower() 
        or "barang" in str(t.get('Jenis BASTP', 'Barang')).lower() 
        or "gabungan" in str(t.get('Jenis BASTP', 'Barang')).lower()
    ]

    if not transaksi_list:
        st.warning("ℹ️ Tidak ada item kategori Barang / Material untuk ditampilkan pada BASTB di PI ini (Item murni Jasa disaring otomatis ke BAMP & BASP).")
        return

    seen_pi_dd = set()
    unique_pi_list = []
    for t in transaksi_list:
        pi_key = str(t.get('PI No.', '')).strip()
        if pi_key and pi_key not in seen_pi_dd:
            seen_pi_dd.add(pi_key)
            unique_pi_list.append(pi_key)

    # Inisialisasi penyimpanan session state khusus BASTB secara komprehensif
    if "bastb_saved_data" not in st.session_state:
        st.session_state.bastb_saved_data = {}

    selected_pi = st.selectbox("Pilih Nomor Proforma Invoice (PI):", unique_pi_list, key="bastb_pi_select")
    
    pi_storage_key = str(selected_pi).strip()
    if pi_storage_key not in st.session_state.bastb_saved_data:
        st.session_state.bastb_saved_data[pi_storage_key] = {
            'lokasi': "Luwuk",
            'main_date': date.today(),
            'items': {},
            'logo_1': None,
            'logo_2': None,
            'ttd_1': None,
            'ttd_2': None
        }

    saved_global = st.session_state.bastb_saved_data[pi_storage_key]

    mutasi_terpilih = [t for t in transaksi_list if str(t.get('PI No.')).strip() == pi_storage_key]
    
    if not mutasi_terpilih:
        st.warning("⚠️ Tidak ada item mutasi ditemukan untuk PI ini.")
        return

    t_data_utama = mutasi_terpilih[0]
    current_pi_no = pi_storage_key.lower()

    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel2:
        lokasi_office = st.text_input("📍 Lokasi Office (Tempat BASTB):", value=str(saved_global.get('lokasi', 'Luwuk')), key=f"bastb_lokasi_{pi_storage_key}")

    selected_date = st.date_input("📅 Tanggal Utama Berita Acara (BASTB):", value=saved_global.get('main_date', date.today()), key=f"bastb_main_date_{pi_storage_key}")
    
    bulan_indo = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
        7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }
    bastb_date = f"{selected_date.day:02d} {bulan_indo[selected_date.month]} {selected_date.year}"

    st.markdown("---")
    st.markdown("#### ⚙️ Pengaturan Parameter Detail & Catatan Fleksibel per Baris Barang / Material BASTB")
    
    rows_html = ""
    uom_options = ["Month", "Day", "AU", "Ls", "Unit", "Trip", "Jam", "Orang", "Set", "Pallet", "Pcs"]
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
            row_date = st.date_input(f"Tanggal Terima (Item {idx})", value=saved_item_data.get('date', default_row_date), key=f"bastb_date_{pi_storage_key}_{idx}")
        with c_b2:
            row_qty = st.number_input(f"Jumlah / Qty (Item {idx})", min_value=0.0, value=float(saved_item_data.get('qty', m.get('Qty', 1.0))), step=1.0, format="%.2f", key=f"bastb_qty_{pi_storage_key}_{idx}")
        with c_b3:
            default_uom = str(saved_item_data.get('uom', m.get('Unit', 'Unit'))).strip()
            if default_uom not in uom_options:
                uom_options.append(default_uom)
            default_idx = uom_options.index(default_uom) if default_uom in uom_options else 0
            row_uom = st.selectbox(f"Satuan (Item {idx})", uom_options, index=default_idx, key=f"bastb_uom_{pi_storage_key}_{idx}")
        with c_b4:
            row_catatan = st.text_input(f"Kondisi / Keterangan (Item {idx})", value=saved_item_data.get('catatan', keterangan_m1 if keterangan_m1 else "Sesuai dan lengkap diterima."), placeholder="Sesuai dan lengkap diterima.", key=f"bastb_cat_{pi_storage_key}_{idx}")

        temp_items_storage[idx] = {
            'date': row_date,
            'qty': row_qty,
            'uom': row_uom,
            'catatan': row_catatan
        }

        row_date_str = f"{row_date.day:02d} {bulan_indo[row_date.month]} {row_date.year}"
        
        catatan_row_final = row_catatan.strip() if row_catatan.strip() else "Sesuai dan lengkap diterima."

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

    # --- PENGATURAN LOGO (DI LUAR FORM AGAR REAKTIF & ADA TOMBOL HAPUS) ---
    st.markdown("---")
    st.markdown("#### 🖼️ Pengaturan Logo Header Dokumen BASTB")
    c_log1, c_log2 = st.columns(2)
    with c_log1:
        uploaded_logo_1 = st.file_uploader("Upload Logo Pihak Pertama (Kiri)", type=["png", "jpg", "jpeg"], key=f"logo_bastb_1_{pi_storage_key}")
        if saved_global.get('logo_1') is not None:
            if st.button("🗑️ Hapus Logo Pihak Pertama", key=f"btn_del_bastb_l1_{pi_storage_key}"):
                saved_global['logo_1'] = None
                st.success("✅ Logo Pihak Pertama berhasil dihapus!")
                st.rerun()

    with c_log2:
        uploaded_logo_2 = st.file_uploader("Upload Logo Pihak Kedua (Kanan)", type=["png", "jpg", "jpeg"], key=f"logo_bastb_2_{pi_storage_key}")
        if saved_global.get('logo_2') is not None:
            if st.button("🗑️ Hapus Logo Pihak Kedua", key=f"btn_del_bastb_l2_{pi_storage_key}"):
                saved_global['logo_2'] = None
                st.success("✅ Logo Pihak Kedua berhasil dihapus!")
                st.rerun()

    # --- PENGATURAN TANDA TANGAN (DI LUAR FORM AGAR REAKTIF & ADA TOMBOL HAPUS) ---
    st.markdown("---")
    st.markdown("#### ✍️ Pengaturan Tanda Tangan Digital BASTB")
    c_ttd1, c_ttd2 = st.columns(2)
    with c_ttd1:
        uploaded_ttd_1 = st.file_uploader("Upload Tanda Tangan Pihak Pertama", type=["png", "jpg", "jpeg"], key=f"ttd_bastb_1_{pi_storage_key}")
        if saved_global.get('ttd_1') is not None:
            if st.button("🗑️ Hapus TTD Pihak Pertama", key=f"btn_del_bastb_t1_{pi_storage_key}"):
                saved_global['ttd_1'] = None
                st.success("✅ TTD Pihak Pertama berhasil dihapus!")
                st.rerun()

    with c_ttd2:
        uploaded_ttd_2 = st.file_uploader("Upload Tanda Tangan Pihak Kedua", type=["png", "jpg", "jpeg"], key=f"ttd_bastb_2_{pi_storage_key}")
        if saved_global.get('ttd_2') is not None:
            if st.button("🗑️ Hapus TTD Pihak Kedua", key=f"btn_del_bastb_t2_{pi_storage_key}"):
                saved_global['ttd_2'] = None
                st.success("✅ TTD Pihak Kedua berhasil dihapus!")
                st.rerun()

    # --- FORM TOMBOL SIMPAN & KUNCI ---
    with st.form(key=f"form_bastb_save_{pi_storage_key}"):
        st.markdown(f"**Konfirmasi Dokumen BASTB (PI: {selected_pi}):** Klik tombol di bawah untuk mengunci konfigurasi.")
        submit_save_bastb = st.form_submit_button("💾 Simpan & Kunci Dokumen BASTB Ini", type="primary")
        
        if submit_save_bastb:
            l1_final = uploaded_logo_1.getvalue() if uploaded_logo_1 is not None else saved_global.get('logo_1')
            l2_final = uploaded_logo_2.getvalue() if uploaded_logo_2 is not None else saved_global.get('logo_2')
            t1_final = uploaded_ttd_1.getvalue() if uploaded_ttd_1 is not None else saved_global.get('ttd_1')
            t2_final = uploaded_ttd_2.getvalue() if uploaded_ttd_2 is not None else saved_global.get('ttd_2')

            st.session_state.bastb_saved_data[pi_storage_key] = {
                'lokasi': lokasi_office,
                'main_date': selected_date,
                'items': temp_items_storage,
                'logo_1': l1_final,
                'logo_2': l2_final,
                'ttd_1': t1_final,
                'ttd_2': t2_final
            }
            st.success(f"✅ Dokumen BASTB untuk PI [{selected_pi}] beserta logo dan tanda tangan berhasil disimpan permanen!")

    # Render HTML Logo & Tanda Tangan dari Data yang Tersimpan di Session State
    l1_bytes = saved_global.get('logo_1')
    l2_bytes = saved_global.get('logo_2')
    t1_bytes = saved_global.get('ttd_1')
    t2_bytes = saved_global.get('ttd_2')

    logo1_html = f'<img src="data:image/png;base64,{base64.b64encode(l1_bytes).decode()}" style="max-height: 45px; max-width: 140px; object-fit: contain; display: block; margin: 0 0 0 55px;" />' if l1_bytes else '<span style="font-size: 8.5px; color: #64748b; margin-left: 55px;">(Logo Pihak Pertama Belum Diunggah)</span>'
    logo2_html = f'<img src="data:image/png;base64,{base64.b64encode(l2_bytes).decode()}" style="max-height: 45px; max-width: 140px; object-fit: contain; display: block; margin: 0 55px 0 auto;" />' if l2_bytes else '<span style="font-size: 8.5px; color: #64748b; margin-right: 55px; display: block; text-align: right;">(Logo Pihak Kedua Belum Diunggah)</span>'

    ttd1_html = f'<div style="height: 60px; display: flex; align-items: center; justify-content: flex-start; margin: 2px 0;"><img src="data:image/png;base64,{base64.b64encode(t1_bytes).decode()}" style="max-height: 60px; max-width: 160px; object-fit: contain;"></div>' if t1_bytes else '<div style="height: 50px;"></div>'
    ttd2_html = f'<div style="height: 60px; display: flex; align-items: center; justify-content: flex-start; margin: 2px 0 2px -15px;"><img src="data:image/png;base64,{base64.b64encode(t2_bytes).decode()}" style="max-height: 60px; max-width: 160px; object-fit: contain;"></div>' if t2_bytes else '<div style="height: 50px;"></div>'

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
        <title>Berita Acara Serah Terima Barang</title>
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
            .header-table {{ width: 100%; border-collapse: collapse; border-bottom: 2px solid #000; padding-bottom: 6px; margin-bottom: 8mm; }}
            .header-table td {{ border: none; vertical-align: middle; padding: 0 4px; }}
            
            .main-doc-title {{ font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; margin: 0; text-align: center; }}
            .sub-doc-title {{ font-size: 9px; font-weight: bold; margin-top: 3px; text-align: center; text-transform: uppercase; }}
            
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
            
            table.sig-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 15px; border: none; }}
            table.sig-table td {{ border: none; vertical-align: top; font-size: 9.5px; padding: 6px; }}
            
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
                <td style="width: 20%; text-align: left;">{logo1_html}</td>
                <td style="width: 60%; text-align: center;">
                    <div class="main-doc-title">BERITA ACARA SERAH TERIMA BARANG (BASTB)</div>
                    <div class="sub-doc-title">PENYERAHAN BARANG / MATERIAL</div>
                </td>
                <td style="width: 20%; text-align: right;">{logo2_html}</td>
            </tr>
        </table>

        <div class="content-text">
            Pada hari ini, tanggal <b>{bastb_date}</b>, yang bertanda tangan di bawah ini:
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

        <div class="section-title" style="margin-top: 10px;">DASAR PENYERAHAN BARANG / MATERIAL</div>
        <table class="info-table">
            <tr><td class="col-label" style="font-weight: bold;">Nomor Kontrak</td><td class="col-colon">:</td><td class="col-value"><b>{nomor_kontrak_str}</b></td></tr>
            <tr><td class="col-label" style="font-weight: bold;">Tanggal Kontrak</td><td class="col-colon">:</td><td class="col-value">{tgl_kontrak}</td></tr>
            <tr><td class="col-label" style="font-weight: bold;">Nomor Purchase Order</td><td class="col-colon">:</td><td class="col-value"><b>{no_po_auto}</b></td></tr>
            <tr><td class="col-label" style="font-weight: bold;">Tanggal Purchase Order</td><td class="col-colon">:</td><td class="col-value">{tgl_po_auto}</td></tr>
            <tr><td class="col-label" style="font-weight: bold; vertical-align: top;">Lingkup Pengadaan</td><td class="col-colon" style="vertical-align: top;">:</td><td class="col-value"><b>{lingkup_pekerjaan}</b></td></tr>
        </table>

        <div class="content-text" style="margin-top: 8px;">
            Dengan ini <b>PIHAK KEDUA</b> menyerahkan dan <b>PIHAK PERTAMA</b> menyatakan telah menerima pengadaan barang/material dengan baik, lengkap, dan sesuai spesifikasi terhitung sampai dengan tanggal <b>{bastb_date}</b>:
        </div>

        <table class="item-grid">
            <tr>
                <th class="th-header" style="width: 8%;">NO</th>
                <th class="th-header" style="width: 42%;">SPESIFIKASI BARANG / MATERIAL</th>
                <th class="th-header" style="width: 10%;">QTY</th>
                <th class="th-header" style="width: 10%;">SATUAN</th>
                <th class="th-header" style="width: 30%;">KONDISI / KETERANGAN</th>
            </tr>
            {rows_html}
        </table>

        <div class="content-text">
            Demikian Berita Acara Serah Terima Barang (BASTB) ini dibuat dengan sebenarnya dan ditandatangani oleh kedua belah pihak untuk dipergunakan sebagaimana mestinya.
        </div>

        <table class="sig-table">
            <tr>
                <td style="width: 50%; text-align: left; padding-left: 15px;">
                    <b>{p1_nama}</b><br><b>PIHAK PERTAMA</b>
                    {ttd1_html}
                    <u><b>{p1_wakil_sign}</b></u><br>{p1_jabatan}
                </td>
                <td style="width: 50%; text-align: left; padding-left: 15px;">
                    <b>{p2_nama}</b><br><b>PIHAK KEDUA</b>
                    {ttd2_html}
                    <u><b>{p2_wakil}</b></u><br>{p2_jabatan}
                </td>
            </tr>
        </table>

        <div class="iso-footer-left">Dokumen No: FM-GS-04 Rev:03</div>
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
        download_link = f'<a href="data:text/html;base64,{b64_pdf}" download="BASTB_{nomor_kontrak_str.replace("/", "-")}.html" style="text-style: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download File HTML/PDF</button></a>'
        st.markdown(download_link, unsafe_allow_html=True)