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

def tampilkan_opname(transaksi_list):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📋 Pratinjau, Cetak & Download Berita Acara Opname Pekerjaan (PI & PO Dual-Logic)</h3>
        </div>
    """, unsafe_allow_html=True)

    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi yang diproses.")
        return

    seen_pi_dd = set()
    unique_pi_list = []
    for t in transaksi_list:
        pi_key = str(t.get('PI No.', '')).strip()
        if pi_key and pi_key not in seen_pi_dd:
            seen_pi_dd.add(pi_key)
            unique_pi_list.append(pi_key)

    col_sel1, col_sel2 = st.columns([2, 2])
    with col_sel1:
        selected_pi = st.selectbox("Pilih Nomor Proforma Invoice (PI):", unique_pi_list, key="opname_sel_pi")
    
    transaksi_by_pi = [t for t in transaksi_list if str(t.get('PI No.')).strip() == str(selected_pi).strip()]

    unique_po_list = []
    for t in transaksi_by_pi:
        po_key = str(t.get('Nomor PO', t.get('No PO', ''))).strip()
        if po_key and po_key not in unique_po_list:
            unique_po_list.append(po_key)
    
    if not unique_po_list:
        unique_po_list = ["-"]

    with col_sel2:
        selected_po = st.selectbox("Pilih Nomor Purchase Order (PO):", unique_po_list, key="opname_sel_po")

    pi_sekarang = str(selected_pi).strip()
    po_sekarang = str(selected_po).strip()
    opname_storage_key = f"{pi_sekarang}_{po_sekarang}"

    # --- INISIALISASI SESSION STATE PERMANEN UNTUK OPNAME ---
    if "opname_saved_data" not in st.session_state:
        st.session_state.opname_saved_data = {}

    if opname_storage_key not in st.session_state.opname_saved_data:
        st.session_state.opname_saved_data[opname_storage_key] = {
            'lokasi_office': "Paisubololi",
            'tanggal_opname': date.today(),
            'items': {},
            'logo_1': None,
            'logo_2': None,
            'ttd_1': None,
            'ttd_2': None
        }

    saved_global = st.session_state.opname_saved_data[opname_storage_key]

    mutasi_terpilih = transaksi_by_pi
    if selected_po != "-":
        filtered_po = [t for t in transaksi_by_pi if str(t.get('Nomor PO', t.get('No PO', ''))).strip() == str(selected_po).strip()]
        if filtered_po:
            mutasi_terpilih = filtered_po

    if not mutasi_terpilih:
        st.warning("⚠️ Tidak ada item mutasi ditemukan.")
        return

    t_data_utama = mutasi_terpilih[0]

    db_invoice_path = os.path.join("database_penyimpanan_aman", "database_proforma_invoice.xlsx")
    matched_db_row = {}
    row_values = []
    
    if os.path.exists(db_invoice_path):
        try:
            df_inv = pd.read_excel(db_invoice_path)
            for idx, row in df_inv.iterrows():
                val_pi_0 = str(row.iloc[0]).strip().lower()
                if val_pi_0 == pi_sekarang.lower():
                    matched_db_row = row.to_dict()
                    row_values = row.values.tolist()
                    break
        except:
            pass

    db_ctr = str(row_values[23]) if len(row_values) > 23 and pd.notnull(row_values[23]) and str(row_values[23]).strip() != "" else str(matched_db_row.get('Nomor CTR', ''))
    db_wo = str(row_values[21]) if len(row_values) > 21 and pd.notnull(row_values[21]) and str(row_values[21]).strip() != "" else str(matched_db_row.get('Nomor WO', ''))
    db_po = po_sekarang if po_sekarang != "-" else str(t_data_utama.get('Nomor PO', ''))

    ref_list_bawah = [x for x in [db_ctr, db_wo, db_po] if x and x.strip() and x.strip().lower() != "nan" and x != "-"]
    ctr_wo_po_str = " / ".join(ref_list_bawah) if ref_list_bawah else "-"

    st.markdown("---")
    
    # Form interaktif untuk parameter utama dan rincian per baris opname
    with st.form(key=f"form_opname_params_{opname_storage_key}"):
        st.markdown("#### ⚙️ Pengaturan Parameter & Rincian Baris Opname (Terkunci & Persisten)")
        
        c_head1, c_head2 = st.columns(2)
        with c_head1:
            lokasi_office = st.text_input("📍 Lokasi Office:", value=str(saved_global.get('lokasi_office', 'Paisubololi')), key=f"opn_lok_{opname_storage_key}")
        with c_head2:
            selected_date_obj = st.date_input("📅 Tanggal Opname:", value=saved_global.get('tanggal_opname', date.today()), key=f"opn_date_{opname_storage_key}")

        st.markdown("<br>", unsafe_allow_html=True)
        
        temp_items_storage = {}
        for idx, m in enumerate(mutasi_terpilih, start=1):
            kategori_m = str(m.get('Kategori', '')).strip()
            deskripsi_m = str(m.get('Deskripsi Pekerjaan', '')).strip()
            ket_m = str(m.get('Keterangan', '')).strip()
            
            item_label = f"{kategori_m} - {deskripsi_m}"
            if ket_m:
                item_label += f" ({ket_m})"

            st.markdown(f"**Item {idx}: {item_label}**")
            c_p1, c_p2, c_p3, c_p4 = st.columns(4)
            
            default_qty = float(m.get('Qty', 1.0))
            is_prov_sum = "provisional" in kategori_m.lower() or "provisional" in deskripsi_m.lower()
            default_price = float(m.get('Total Harga', m.get('Harga Satuan', 0.0))) if is_prov_sum else float(m.get('Harga Satuan', 0.0))

            saved_item_opn = saved_global.get('items', {}).get(idx, {})

            with c_p1:
                po_vol = st.number_input(f"📦 Volume PO / Kontrak (Item {idx})", value=float(saved_item_opn.get('po_vol', 0.0)), step=0.1, format="%.2f", key=f"opn_po_vol_{opname_storage_key}_{idx}")
            with c_p2:
                unit_price = st.number_input(f"💵 Unit Price / Total Tagihan (Item {idx})", value=float(saved_item_opn.get('unit_price', default_price)), step=1000.0, format="%.2f", key=f"opn_unit_price_{opname_storage_key}_{idx}")
            with c_p3:
                prev_vol = st.number_input(f"📉 Volume Lalu / Previous (Item {idx})", value=float(saved_item_opn.get('prev_vol', 0.0)), step=0.1, format="%.2f", key=f"opn_prev_vol_{opname_storage_key}_{idx}")
            with c_p4:
                current_vol = st.number_input(f"📈 Volume Aktual Bulan Ini (Item {idx})", value=float(saved_item_opn.get('current_vol', default_qty)), step=0.1, format="%.2f", key=f"opn_curr_vol_{opname_storage_key}_{idx}")

            temp_items_storage[idx] = {
                'po_vol': po_vol,
                'unit_price': unit_price,
                'prev_vol': prev_vol,
                'current_vol': current_vol
            }
            st.markdown("<br>", unsafe_allow_html=True)

        submit_save_opname = st.form_submit_button("💾 Simpan / Kunci Parameter Opname Ini", type="primary")
        if submit_save_opname:
            st.session_state.opname_saved_data[opname_storage_key] = {
                'lokasi_office': lokasi_office,
                'tanggal_opname': selected_date_obj,
                'items': temp_items_storage,
                'logo_1': saved_global.get('logo_1'),
                'logo_2': saved_global.get('logo_2'),
                'ttd_1': saved_global.get('ttd_1'),
                'ttd_2': saved_global.get('ttd_2')
            }
            st.success("✅ Parameter opname berhasil disimpan dan dikunci secara permanen!")

    # --- PENGATURAN LOGO (DI LUAR FORM AGAR REAKTIF & ADA TOMBOL HAPUS) ---
    st.markdown("---")
    st.markdown("#### 🖼️ Pengaturan Logo Header Dokumen Opname")
    c_log1, c_log2 = st.columns(2)
    with c_log1:
        uploaded_logo_1 = st.file_uploader("Upload Logo Pihak Pertama (PT BSS)", type=["png", "jpg", "jpeg"], key=f"logo_opn_1_{opname_storage_key}")
        if uploaded_logo_1 is not None:
            saved_global['logo_1'] = uploaded_logo_1.getvalue()
        if saved_global.get('logo_1') is not None:
            if st.button("🗑️ Hapus Logo Pihak Pertama", key=f"btn_del_opn_l1_{opname_storage_key}"):
                saved_global['logo_1'] = None
                st.success("✅ Logo Pihak Pertama berhasil dihapus!")
                st.rerun()

    with c_log2:
        uploaded_logo_2 = st.file_uploader("Upload Logo Pihak Kedua (JOB Pertamina)", type=["png", "jpg", "jpeg"], key=f"logo_opn_2_{opname_storage_key}")
        if uploaded_logo_2 is not None:
            saved_global['logo_2'] = uploaded_logo_2.getvalue()
        if saved_global.get('logo_2') is not None:
            if st.button("🗑️ Hapus Logo Pihak Kedua", key=f"btn_del_opn_l2_{opname_storage_key}"):
                saved_global['logo_2'] = None
                st.success("✅ Logo Pihak Kedua berhasil dihapus!")
                st.rerun()

    # --- PENGATURAN TANDA TANGAN (DI LUAR FORM AGAR REAKTIF & ADA TOMBOL HAPUS) ---
    st.markdown("---")
    st.markdown("#### ✍️ Pengaturan Tanda Tangan Digital Opname")
    c_ttd1, c_ttd2 = st.columns(2)
    with c_ttd1:
        uploaded_ttd_1 = st.file_uploader("Upload Tanda Tangan Pihak Pertama (Prepared by)", type=["png", "jpg", "jpeg"], key=f"ttd_opn_1_{opname_storage_key}")
        if uploaded_ttd_1 is not None:
            saved_global['ttd_1'] = uploaded_ttd_1.getvalue()
        if saved_global.get('ttd_1') is not None:
            if st.button("🗑️ Hapus TTD Pihak Pertama", key=f"btn_del_opn_t1_{opname_storage_key}"):
                saved_global['ttd_1'] = None
                st.success("✅ TTD Pihak Pertama berhasil dihapus!")
                st.rerun()

    with c_ttd2:
        uploaded_ttd_2 = st.file_uploader("Upload Tanda Tangan Pihak Kedua (Approved by)", type=["png", "jpg", "jpeg"], key=f"ttd_opn_2_{opname_storage_key}")
        if uploaded_ttd_2 is not None:
            saved_global['ttd_2'] = uploaded_ttd_2.getvalue()
        if saved_global.get('ttd_2') is not None:
            if st.button("🗑️ Hapus TTD Pihak Kedua", key=f"btn_del_opn_t2_{opname_storage_key}"):
                saved_global['ttd_2'] = None
                st.success("✅ TTD Pihak Kedua berhasil dihapus!")
                st.rerun()

    # Ambil data aktif yang tersimpan
    active_lokasi = saved_global.get('lokasi_office', 'Paisubololi')
    active_date_obj = saved_global.get('tanggal_opname', date.today())
    opname_date = active_date_obj.strftime('%d %B %Y')

    # Kalkulasi nilai menggunakan data yang tersimpan/terkunci
    rows_html = ""
    sum_po_vol = 0.0
    sum_base_price = 0.0
    sum_prev_tot = 0.0
    sum_curr_tot = 0.0
    sum_cum_tot = 0.0
    sum_sisa_tot = 0.0
    sum_po_vol_tot = 0.0
    sum_prev_vol_tot = 0.0
    sum_curr_vol_tot = 0.0
    sum_cum_vol_tot = 0.0
    sum_sisa_vol_tot = 0.0

    for idx, m in enumerate(mutasi_terpilih, start=1):
        kategori_m = str(m.get('Kategori', '')).strip()
        deskripsi_m = str(m.get('Deskripsi Pekerjaan', '')).strip()
        ket_m = str(m.get('Keterangan', '')).strip()

        is_prov_sum = "provisional" in kategori_m.lower() or "provisional" in deskripsi_m.lower()
        default_price_calc = float(m.get('Total Harga', m.get('Harga Satuan', 0.0))) if is_prov_sum else float(m.get('Harga Satuan', 0.0))

        active_item_data = saved_global.get('items', {}).get(idx, {})
        po_vol = float(active_item_data.get('po_vol', 0.0))
        unit_price = float(active_item_data.get('unit_price', default_price_calc))
        prev_vol = float(active_item_data.get('prev_vol', 0.0))
        current_vol = float(active_item_data.get('current_vol', float(m.get('Qty', 1.0))))

        base_price = po_vol * unit_price
        prev_tot = prev_vol * unit_price
        curr_tot = current_vol * unit_price
        cum_vol = prev_vol + current_vol
        cum_tot = prev_tot + curr_tot
        sisa_vol = po_vol - cum_vol
        sisa_tot = base_price - cum_tot

        sum_po_vol += po_vol
        sum_base_price += base_price
        sum_prev_tot += prev_tot
        sum_curr_tot += curr_tot
        sum_cum_tot += cum_tot
        sum_sisa_tot += sisa_tot

        sum_po_vol_tot += po_vol
        sum_prev_vol_tot += prev_vol
        sum_curr_vol_tot += current_vol
        sum_cum_vol_tot += cum_vol
        sum_sisa_vol_tot += sisa_vol

        actual_unit = str(m.get('Unit', 'AU' if is_prov_sum else 'Day'))
        desc_full = f"<b>{kategori_m}</b><br>{deskripsi_m}"
        if ket_m:
            desc_full += f"<br><span style='font-size: 8.5px; color: #334155;'>{ket_m}</span>"

        rows_html += f"""
            <tr>
                <td>1.{idx}</td>
                <td class="text-left">{desc_full}</td>
                <td>{actual_unit}</td>
                <td>{po_vol:.2f}</td>
                <td class="text-right">{unit_price:,.2f}</td>
                <td class="text-right">{base_price:,.2f}</td>
                <td>{prev_vol:.2f}</td>
                <td class="text-right">{prev_tot:,.2f}</td>
                <td>{current_vol:.2f}</td>
                <td class="text-right">{curr_tot:,.2f}</td>
                <td>{cum_vol:.2f}</td>
                <td class="text-right">{cum_tot:,.2f}</td>
                <td>{sisa_vol:.2f}</td>
                <td class="text-right">{sisa_tot:,.2f}</td>
            </tr>
        """

    wo_title = str(matched_db_row.get('Keterangan WO', t_data_utama.get('Deskripsi PO', 'General Services')))

    def get_db_val(idx_num, key_name, fallback=""):
        if idx_num in matched_db_row and pd.notnull(matched_db_row[idx_num]):
            val = str(matched_db_row[idx_num]).strip()
            if val and val.lower() != "nan":
                return val
        if key_name in matched_db_row and pd.notnull(matched_db_row[key_name]):
            val = str(matched_db_row[key_name]).strip()
            if val and val.lower() != "nan":
                return val
        return fallback

    prepared_name = get_db_val(25, 'Prepared by Name', 'Onesimus Suryadi')
    prepared_title = get_db_val(26, 'Prepared by Title', 'General Service Manager')
    
    reviewed_name = get_db_val(12, 'Diwakili Oleh', '')
    reviewed_title = get_db_val(13, 'Selaku', '')

    app1_name = get_db_val(27, 'Approved by 1', 'Imron Maulana / Moh Bazarul Aqhsa')
    app1_title = get_db_val(28, 'Approved by Title 1', 'Maintenance Superintendent')
    
    app2_name = get_db_val(29, 'Approved by 2', '')
    app2_title = get_db_val(30, 'Approved by Title 2', 'Field Senior Manager')

    is_app2_valid = bool(app2_name and app2_name != "--- (Tidak Ada / Kosong) ---" and app2_name.lower() != "nan")
    if is_app2_valid:
        final_app_name = app2_name
        final_app_title = app2_title if app2_title else "Field Senior Manager"
    else:
        final_app_name = app1_name if app1_name and app1_name != "--- (Tidak Ada / Kosong) ---" else "Imron Maulana / Moh Bazarul Aqhsa"
        final_app_title = app1_title if app1_title else "Maintenance Superintendent"

    is_same_person = (
        str(reviewed_name).strip().lower() == str(final_app_name).strip().lower() and
        str(reviewed_title).strip().lower() == str(final_app_title).strip().lower()
    )

    l1_bytes = saved_global.get('logo_1')
    l2_bytes = saved_global.get('logo_2')
    t1_bytes = saved_global.get('ttd_1')
    t2_bytes = saved_global.get('ttd_2')

    logo1_html = f'<img src="data:image/png;base64,{base64.b64encode(l1_bytes).decode()}" style="max-height: 50px; max-width: 130px; object-fit: contain; display: block; margin: 0 auto;">' if l1_bytes is not None else ""
    logo2_html = f'<img src="data:image/png;base64,{base64.b64encode(l2_bytes).decode()}" style="max-height: 50px; max-width: 130px; object-fit: contain; display: block; margin: 0 auto;">' if l2_bytes is not None else ""

    img_style = "max-height: 75px; max-width: 180px; object-fit: contain;"
    ttd1_html = f'<div style="margin: 4px auto; height: 80px; display: flex; align-items: center; justify-content: flex-start;"><img src="data:image/png;base64,{base64.b64encode(t1_bytes).decode()}" style="{img_style}"></div>' if t1_bytes is not None else '<div style="height: 75px;"></div>'
    ttd2_html = f'<div style="margin: 4px auto; height: 80px; display: flex; align-items: center; justify-content: center;"><img src="data:image/png;base64,{base64.b64encode(t2_bytes).decode()}" style="{img_style}"></div>' if t2_bytes is not None else '<div style="height: 75px;"></div>'

    if is_same_person or not reviewed_name or str(reviewed_name).strip() == "" or str(reviewed_name).strip().lower() == "nan":
        sig_table_html = f"""
        <table class="sig-table">
            <tr>
                <td style="width: 50%; text-align: left; padding-left: 10px;">
                    {active_lokasi}, {opname_date}<br>
                    <b>PT Banggai Sentral Sulawesi</b><br>
                    Prepared by,
                    {ttd1_html}
                    <u><b>{prepared_name}</b></u><br>
                    {prepared_title}
                </td>
                <td style="width: 50%; text-align: center;">
                    <br>
                    <b>JOB Pertamina - Medco E&P Tomori Sulawesi</b><br>
                    Approved by,
                    {ttd2_html}
                    <u><b>{final_app_name}</b></u><br>
                    {final_app_title}
                </td>
            </tr>
        </table>
        """
    else:
        sig_table_html = f"""
        <table class="sig-table">
            <tr>
                <td style="width: 33.3%; text-align: left; padding-left: 10px;">
                    {active_lokasi}, {opname_date}<br>
                    <b>PT Banggai Sentral Sulawesi</b><br>
                    Prepared by,
                    {ttd1_html}
                    <u><b>{prepared_name}</b></u><br>
                    {prepared_title}
                </td>
                <td style="width: 33.3%; text-align: center;">
                    <br>
                    <b>JOB Pertamina - Medco E&P Tomori Sulawesi</b><br>
                    Reviewed by,<br><br><br><br>
                    <u><b>{reviewed_name}</b></u><br>
                    {reviewed_title}
                </td>
                <td style="width: 33.3%; text-align: center;">
                    <br>
                    <b>JOB Pertamina - Medco E&P Tomori Sulawesi</b><br>
                    Approved by,
                    {ttd2_html}
                    <u><b>{final_app_name}</b></u><br>
                    {final_app_title}
                </td>
            </tr>
        </table>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Berita Acara Pekerjaan / Opname - PT BSS</title>
        <style>
            @page {{ 
                size: A4 landscape; 
                margin: 6mm; 
            }}
            @media print {{
                body {{ 
                    -webkit-print-color-adjust: exact; 
                    margin: 0; 
                }}
                @page {{ 
                    size: A4 landscape; 
                    margin: 6mm; 
                }}
                header, footer, .no-print {{
                    display: none !important;
                }}
            }}
            body {{ 
                font-family: Arial, sans-serif; 
                background-color: #ffffff; 
                color: #000000; 
                padding: 0mm; 
                margin: 0; 
                font-size: 9.5px; 
                line-height: 1.25; 
            }}
            .header-table {{ width: 100%; border-collapse: collapse; border-bottom: 2px solid #000; padding-bottom: 5px; margin-bottom: 6px; }}
            .header-table td {{ border: none; vertical-align: middle; padding: 0 10px; }}
            .title-box {{ background-color: #dbeafe; border: 1px solid #000; text-align: center; font-weight: bold; font-size: 11px; padding: 4px; margin-bottom: 6px; text-transform: uppercase; }}
            .info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 6px; font-size: 9.5px; }}
            .info-table td {{ padding: 2px 4px; border: none; }}
            table.opname-grid {{ width: 100%; border-collapse: collapse; margin-bottom: 6px; }}
            table.opname-grid th, table.opname-grid td {{ border: 1px solid #000; padding: 4px 5px; font-size: 9px; vertical-align: middle; text-align: center; }}
            .th-header {{ background-color: #f1f5f9; font-weight: bold; text-transform: uppercase; }}
            .text-left {{ text-align: left !important; }}
            .text-right {{ text-align: right !important; }}
            .summary-box {{ margin-top: 4px; font-size: 10px; font-weight: bold; }}
            table.sig-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; border: none; page-break-inside: avoid; }}
            table.sig-table td {{ border: none; vertical-align: top; font-size: 9.5px; padding: 2px; }}
        </style>
    </head>
    <body>
        <table class="header-table">
            <tr>
                <td style="width: 22%; text-align: center;">{logo1_html}</td>
                <td style="width: 56%; text-align: center;"><h3 style="margin: 0; font-size: 11px; font-weight: bold; text-transform: uppercase;">BERITA ACARA PEKERJAAN / OPNAME</h3></td>
                <td style="width: 22%; text-align: center;">{logo2_html}</td>
            </tr>
        </table>

        <table class="info-table">
            <tr><td style="width: 18%; font-weight: bold;">JOB TITLE / WO / PO</td><td style="width: 2%;">:</td><td style="width: 80%;"><b>{wo_title}</b></td></tr>
            <tr><td style="font-weight: bold;">CTR / WO / PO No.</td><td>:</td><td>{ctr_wo_po_str}</td></tr>
            <tr><td style="font-weight: bold;">DATE</td><td>:</td><td>{opname_date}</td></tr>
            <tr><td style="font-weight: bold; color: #065f46;">PROFORMA INVOICE No.</td><td style="color: #065f46;">:</td><td><b>{pi_sekarang}</b></td></tr>
        </table>

        <table class="opname-grid">
            <tr>
                <th rowspan="2" class="th-header" style="width: 5%;">NO</th>
                <th rowspan="2" class="th-header" style="width: 25%;">ITEM - DESCRIPTION</th>
                <th rowspan="2" class="th-header" style="width: 7%;">UOM</th>
                <th colspan="3" class="th-header" style="width: 21%;">BASE ON CTR / PO</th>
                <th colspan="2" class="th-header" style="width: 12%;">PREVIOUS OPNAME (IDR)</th>
                <th colspan="2" class="th-header" style="width: 13%;">AKTUAL OPNAME (BULAN INI) (IDR)</th>
                <th colspan="2" class="th-header" style="width: 13%;">CUMMULATIVE OPNAME (IDR)</th>
                <th colspan="2" class="th-header" style="width: 14%;">SISA ANGGARAN (DEVIASI) (IDR)</th>
            </tr>
            <tr>
                <th class="th-header">VOLUME</th>
                <th class="th-header">UNIT PRICE (IDR)</th>
                <th class="th-header">TOTAL PRICE (IDR)</th>
                <th class="th-header">VOLUME</th>
                <th class="th-header">TOTAL PRICE</th>
                <th class="th-header">VOLUME</th>
                <th class="th-header">TOTAL PRICE</th>
                <th class="th-header">VOLUME</th>
                <th class="th-header">TOTAL PRICE</th>
                <th class="th-header">VOLUME</th>
                <th class="th-header">TOTAL PRICE</th>
            </tr>
            {rows_html}
            <tr style="background-color: #fafafa; font-weight: bold;">
                <td colspan="3" class="text-right">TOTAL :</td>
                <td>{sum_po_vol_tot:.2f}</td>
                <td class="text-right">-</td>
                <td class="text-right">{sum_base_price:,.2f}</td>
                <td>{sum_prev_vol_tot:.2f}</td>
                <td class="text-right">{sum_prev_tot:,.2f}</td>
                <td>{sum_curr_vol_tot:.2f}</td>
                <td class="text-right">{sum_curr_tot:,.2f}</td>
                <td>{sum_cum_vol_tot:.2f}</td>
                <td class="text-right">{sum_cum_tot:,.2f}</td>
                <td>{sum_sisa_vol_tot:.2f}</td>
                <td class="text-right">{sum_sisa_tot:,.2f}</td>
            </tr>
        </table>

        <div class="summary-box">
            Total Akumulasi Penyerapan (Cumulative Opname): Rp {sum_cum_tot:,.2f}<br>
            Sisa Nilai Anggaran PO (Deviasi): Rp {sum_sisa_tot:,.2f}
        </div>

        {sig_table_html}
    </body>
    </html>
    """

    st.markdown('<div class="document-preview">', unsafe_allow_html=True)
    st.components.v1.html(html_content, height=640, scrolling=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        b64_html = base64.b64encode(html_content.encode()).decode()
        st.components.v1.html(f'<script>function printDoc(){{var win=window.open("about:blank","_blank");win.document.write(atob("{b64_html}"));win.document.close();win.print();}}</script><button onclick="printDoc()" style="width: 100%; background-color: #10b981; color: white; padding: 10px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">🖨️ Cetak Dokumen Opname</button>', height=50)
    with col_btn2:
        b64_pdf = base64.b64encode(html_content.encode()).decode()
        st.markdown(f'<a href="data:text/html;base64,{b64_pdf}" download="Opname_{pi_sekarang.replace("/", "-")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download File Opname</button></a>', unsafe_allow_html=True)