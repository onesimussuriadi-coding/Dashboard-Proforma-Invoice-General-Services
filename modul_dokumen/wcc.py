import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime

def terbilang(n):
    n = int(n)
    if n < 0:
        return "minus " + terbilang(-n)
    satuan = ["", "Satu", "Dua", "Tiga", "Empat", "Lima", "Enam", "Tujuh", "Delapan", "Sembilan", "Sepuluh", "Sebelas"]
    if n < 12:
        return " " + satuan[n]
    elif n < 20:
        return terbilang(n - 10) + " Belas"
    elif n < 100:
        return terbilang(n // 10) + " Puluh" + terbilang(n % 10)
    elif n < 200:
        return " Seratus" + terbilang(n - 100)
    elif n < 1000:
        return terbilang(n // 100) + " Ratus" + terbilang(n % 100)
    elif n < 2000:
        return " Seribu" + terbilang(n - 1000)
    elif n < 1000000:
        return terbilang(n // 1000) + " Ribu" + terbilang(n % 1000)
    elif n < 1000000000:
        return terbilang(n // 1000000) + " Juta" + terbilang(n % 1000000)
    elif n < 1000000000000:
        return terbilang(n // 1000000000) + " Miliar" + terbilang(n % 1000000000)
    else:
        return " Angka terlalu besar"

def tampilkan_wcc(transaksi_list):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">🖨️ Pratinjau, Cetak & Download Work Completion Certificate (WCC - Multi-Item Ready)</h3>
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

    if "wcc_saved_data" not in st.session_state:
        st.session_state.wcc_saved_data = {}

    col_sel1 = st.columns([1])[0]
    with col_sel1:
        selected_pi = st.selectbox("Pilih Nomor Proforma Invoice (PI):", unique_pi_list, key="wcc_sel_pi")

    pi_storage_key = str(selected_pi).strip()

    if pi_storage_key not in st.session_state.wcc_saved_data:
        st.session_state.wcc_saved_data[pi_storage_key] = {
            'lokasi': "Paisubololi",
            'logo_1': None,
            'logo_2': None,
            'ttd_1': None,
            'ttd_2': None,
            'ttd_3': None
        }

    saved_wcc = st.session_state.wcc_saved_data[pi_storage_key]

    # --- PENGATURAN UPLOAD & HAPUS FILE (DI LUAR FORM AGAR REAKTIF) ---
    st.markdown("---")
    st.markdown("#### 🖼️ Pengaturan Logo Header Dokumen WCC")
    c_log1, c_log2 = st.columns(2)
    with c_log1:
        uploaded_logo_1 = st.file_uploader("Upload Logo Pihak Pertama (PT BSS)", type=["png", "jpg", "jpeg"], key=f"logo_wcc_1_{pi_storage_key}")
        if saved_wcc.get('logo_1') is not None:
            if st.button("🗑️ Hapus Logo Pihak Pertama", key=f"btn_del_logo_1_{pi_storage_key}"):
                saved_wcc['logo_1'] = None
                st.success("✅ Logo Pihak Pertama berhasil dihapus!")
                st.rerun()
    with c_log2:
        uploaded_logo_2 = st.file_uploader("Upload Logo Pihak Kedua / Instansi (JOB Pertamina)", type=["png", "jpg", "jpeg"], key=f"logo_wcc_2_{pi_storage_key}")
        if saved_wcc.get('logo_2') is not None:
            if st.button("🗑️ Hapus Logo Pihak Kedua", key=f"btn_del_logo_2_{pi_storage_key}"):
                saved_wcc['logo_2'] = None
                st.success("✅ Logo Pihak Kedua berhasil dihapus!")
                st.rerun()

    st.markdown("---")
    st.markdown("#### ✍️ Pengaturan Tanda Tangan Digital WCC")
    c_t1, c_t2, c_t3 = st.columns(3)
    with c_t1:
        uploaded_ttd_1 = st.file_uploader("TTD Pihak 1 (Prepared by)", type=["png", "jpg", "jpeg"], key=f"wcc_t1_{pi_storage_key}")
        if saved_wcc.get('ttd_1') is not None:
            if st.button("🗑️ Hapus TTD Pihak 1", key=f"btn_del_t1_{pi_storage_key}"):
                saved_wcc['ttd_1'] = None
                st.success("✅ TTD Pihak 1 berhasil dihapus!")
                st.rerun()
    with c_t2:
        uploaded_ttd_2 = st.file_uploader("TTD Pihak 2 (Reviewed by)", type=["png", "jpg", "jpeg"], key=f"wcc_t2_{pi_storage_key}")
        if saved_wcc.get('ttd_2') is not None:
            if st.button("🗑️ Hapus TTD Pihak 2", key=f"btn_del_t2_{pi_storage_key}"):
                saved_wcc['ttd_2'] = None
                st.success("✅ TTD Pihak 2 berhasil dihapus!")
                st.rerun()
    with c_t3:
        uploaded_ttd_3 = st.file_uploader("TTD Pihak 3 (Approved by)", type=["png", "jpg", "jpeg"], key=f"wcc_t3_{pi_storage_key}")
        if saved_wcc.get('ttd_3') is not None:
            if st.button("🗑️ Hapus TTD Pihak 3", key=f"btn_del_t3_{pi_storage_key}"):
                saved_wcc['ttd_3'] = None
                st.success("✅ TTD Pihak 3 berhasil dihapus!")
                st.rerun()

    # Form khusus untuk tombol Simpan & Kunci Dokumen
    with st.form(key=f"form_wcc_save_{pi_storage_key}"):
        st.markdown("---")
        lokasi_office = st.text_input("📍 Lokasi Office (Tempat WCC):", value=str(saved_wcc.get('lokasi', 'Paisubololi')), key=f"wcc_lok_office_{pi_storage_key}")
        st.markdown(f"**Konfirmasi Dokumen WCC (PI: {selected_pi}):** Klik tombol di bawah untuk mengunci konfigurasi.")
        submit_save_wcc = st.form_submit_button("💾 Simpan & Kunci Dokumen WCC Ini", type="primary")
        
        if submit_save_wcc:
            # Pertahankan data lama jika tidak ada file baru yang di-upload
            l1_final = uploaded_logo_1.getvalue() if uploaded_logo_1 is not None else saved_wcc.get('logo_1')
            l2_final = uploaded_logo_2.getvalue() if uploaded_logo_2 is not None else saved_wcc.get('logo_2')
            t1_final = uploaded_ttd_1.getvalue() if uploaded_ttd_1 is not None else saved_wcc.get('ttd_1')
            t2_final = uploaded_ttd_2.getvalue() if uploaded_ttd_2 is not None else saved_wcc.get('ttd_2')
            t3_final = uploaded_ttd_3.getvalue() if uploaded_ttd_3 is not None else saved_wcc.get('ttd_3')

            st.session_state.wcc_saved_data[pi_storage_key] = {
                'lokasi': lokasi_office,
                'logo_1': l1_final,
                'logo_2': l2_final,
                'ttd_1': t1_final,
                'ttd_2': t2_final,
                'ttd_3': t3_final
            }
            st.success(f"✅ Sukses! Dokumen WCC untuk nomor PI [{selected_pi}] berhasil disimpan dan dikunci secara permanen.")

    # Ambil nilai data aktif yang sudah tersimpan di session state
    active_lokasi = st.session_state.wcc_saved_data[pi_storage_key].get('lokasi', 'Paisubololi')
    l1_bytes = st.session_state.wcc_saved_data[pi_storage_key].get('logo_1')
    l2_bytes = st.session_state.wcc_saved_data[pi_storage_key].get('logo_2')
    t1_bytes = st.session_state.wcc_saved_data[pi_storage_key].get('ttd_1')
    t2_bytes = st.session_state.wcc_saved_data[pi_storage_key].get('ttd_2')
    t3_bytes = st.session_state.wcc_saved_data[pi_storage_key].get('ttd_3')

    mutasi_terpilih = [t for t in transaksi_list if str(t.get('PI No.')).strip() == str(selected_pi).strip()]
    if not mutasi_terpilih:
        st.warning("⚠️ Tidak ada item mutasi ditemukan untuk PI ini.")
        return

    t_data_utama = mutasi_terpilih[0]
    grand_total_wcc = sum([float(m.get('Total Harga', 0.0)) for m in mutasi_terpilih])
    terbilang_str = terbilang(grand_total_wcc).strip() + " Rupiah"

    db_invoice_path = os.path.join("database_penyimpanan_aman", "database_proforma_invoice.xlsx")
    matched_db_row = {}
    wcc_no, wo_no, ctr_no = "DATA WCC BELUM DIINPUT", "DATA WO BELUM DIINPUT", "DATA CTR BELUM DIINPUT"
    
    if os.path.exists(db_invoice_path):
        try:
            df_inv = pd.read_excel(db_invoice_path)
            pi_sekarang = str(selected_pi).strip().lower()
            for idx, row in df_inv.iterrows():
                if str(row.iloc[0]).strip().lower() == pi_sekarang:
                    matched_db_row = row.to_dict()
                    wcc_no = str(row.iloc[19]) if len(row) > 19 and pd.notnull(row.iloc[19]) else wcc_no
                    wo_no = str(row.iloc[21]) if len(row) > 21 and pd.notnull(row.iloc[21]) else wo_no
                    ctr_no = str(row.iloc[23]) if len(row) > 23 and pd.notnull(row.iloc[23]) else ctr_no
                    break
        except:
            pass

    nomor_kontrak_str = str(t_data_utama.get('Nomor Kontrak', '7201250141'))
    raw_date = matched_db_row.get('Tanggal WCC', t_data_utama.get('Tanggal PI', datetime.now().strftime('%d %B %Y')))
    try:
        wcc_date = pd.to_datetime(raw_date).strftime('%d %B %Y') if len(str(raw_date)) >= 10 else datetime.now().strftime('%d %B %Y')
    except:
        wcc_date = str(raw_date)

    wo_title = str(matched_db_row.get('Keterangan WO', '')) or str(t_data_utama.get('Deskripsi PO', 'General Services'))
    progress_val = str(matched_db_row.get('Progress Pekerjaan', '100%'))
    progress_desc = f"[&#10003;] {progress_val} - Penyelesaian Pekerjaan"

    def get_db_val(idx_num, key_name, fallback=""):
        if idx_num in matched_db_row and pd.notnull(matched_db_row[idx_num]) and str(matched_db_row[idx_num]).strip().lower() != "nan":
            return str(matched_db_row[idx_num]).strip()
        if key_name in matched_db_row and pd.notnull(matched_db_row[key_name]) and str(matched_db_row[key_name]).strip().lower() != "nan":
            return str(matched_db_row[key_name]).strip()
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
    final_app_name = app2_name if is_app2_valid else (app1_name if app1_name and app1_name != "--- (Tidak Ada / Kosong) ---" else "Imron Maulana / Moh Bazarul Aqhsa")
    final_app_title = app2_title if (is_app2_valid and app2_title) else (app1_title if app1_title else "Maintenance Superintendent")

    is_same_person = (
        str(reviewed_name).strip().lower() == str(final_app_name).strip().lower() and
        str(reviewed_title).strip().lower() == str(final_app_title).strip().lower()
    )

    logo1_html = f'<img src="data:image/png;base64,{base64.b64encode(l1_bytes).decode()}" style="max-height: 50px; max-width: 130px; object-fit: contain; display: block; margin: 0 auto;">' if l1_bytes is not None else ""
    logo2_html = f'<img src="data:image/png;base64,{base64.b64encode(l2_bytes).decode()}" style="max-height: 50px; max-width: 130px; object-fit: contain; display: block; margin: 0 auto;">' if l2_bytes is not None else ""

    img_style = "max-height: 85px; max-width: 200px; object-fit: contain;"
    ttd1_html = f'<div style="margin: 6px auto; height: 90px; display: flex; align-items: center; justify-content: center;"><img src="data:image/png;base64,{base64.b64encode(t1_bytes).decode()}" style="{img_style}"></div>' if t1_bytes is not None else '<div style="height: 90px;"></div>'
    ttd2_html = f'<div style="margin: 6px auto; height: 90px; display: flex; align-items: center; justify-content: center;"><img src="data:image/png;base64,{base64.b64encode(t2_bytes).decode()}" style="{img_style}"></div>' if t2_bytes is not None else '<div style="height: 90px;"></div>'
    ttd3_html = f'<div style="margin: 6px auto; height: 90px; display: flex; align-items: center; justify-content: center;"><img src="data:image/png;base64,{base64.b64encode(t3_bytes).decode()}" style="{img_style}"></div>' if t3_bytes is not None else '<div style="height: 90px;"></div>'

    if is_same_person or not reviewed_name or str(reviewed_name).strip() == "" or str(reviewed_name).strip().lower() == "nan":
        sig_table_html = f"""
        <table class="sig-table">
            <tr>
                <td style="width: 50%; vertical-align: top; text-align: center; padding: 0 20px;">
                    {active_lokasi}, {wcc_date}<br>
                    <b>PT Banggai Sentral Sulawesi</b><br>
                    Prepared by,
                    {ttd1_html}
                    <u><b>{prepared_name}</b></u><br>
                    {prepared_title}
                </td>
                <td style="width: 50%; vertical-align: top; text-align: center; padding: 0 20px;">
                    <br>
                    <b>JOB Pertamina - Medco E&P Tomori Sulawesi</b><br>
                    Approved by,
                    {ttd3_html}
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
                <td style="width: 33.3%; vertical-align: top; text-align: center; padding: 0 10px;">
                    {active_lokasi}, {wcc_date}<br>
                    <b>PT Banggai Sentral Sulawesi</b><br>
                    Prepared by,
                    {ttd1_html}
                    <u><b>{prepared_name}</b></u><br>
                    {prepared_title}
                </td>
                <td style="width: 33.3%; vertical-align: top; text-align: center; padding: 0 10px;">
                    <br>
                    <b>JOB Pertamina - Medco E&P Tomori Sulawesi</b><br>
                    Reviewed by,
                    {ttd2_html}
                    <u><b>{reviewed_name}</b></u><br>
                    {reviewed_title}
                </td>
                <td style="width: 33.3%; vertical-align: top; text-align: center; padding: 0 10px;">
                    <br>
                    <b>JOB Pertamina - Medco E&P Tomori Sulawesi</b><br>
                    Approved by,
                    {ttd3_html}
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
        <title>Work Completion Certificate - PT BSS</title>
        <style>
            @page {{ size: A4; margin: 10mm; }}
            @media print {{
                body {{ -webkit-print-color-adjust: exact; }}
                @page {{ margin: 0; }}
                body {{ margin: 10mm; }}
                header, footer, .no-print {{ display: none !important; }}
            }}
            body {{ font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; padding: 25px; margin: 0; font-size: 11px; line-height: 1.4; }}
            .header-table {{ width: 100%; border-collapse: collapse; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 15px; }}
            .header-table td {{ border: none; vertical-align: middle; padding: 0 10px; }}
            .title-box {{ background-color: #dbeafe; border: 1px solid #000; text-align: center; font-weight: bold; font-size: 13px; padding: 6px; margin-bottom: 4px; text-transform: uppercase; }}
            .cert-box {{ background-color: #f1f5f9; border: 1px solid #000; text-align: center; font-weight: bold; font-size: 12px; padding: 6px; margin-bottom: 20px; }}
            table.grid-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
            table.grid-table th, table.grid-table td {{ border: 1px solid #000; padding: 8px 10px; font-size: 11px; vertical-align: middle; }}
            .col-label {{ width: 25%; font-weight: bold; background-color: #fafafa; }}
            .col-colon {{ width: 3%; text-align: center; font-weight: bold; }}
            .col-val {{ width: 72%; }}
            .content-text {{ margin-bottom: 15px; font-size: 11px; }}
            table.sig-table {{ width: 100%; border-collapse: collapse; margin-top: 25px; border: none; table-layout: fixed; }}
            table.sig-table td {{ border: none; font-size: 11px; word-wrap: break-word; }}
        </style>
    </head>
    <body>
        <table class="header-table">
            <tr>
                <td style="width: 22%; text-align: center;">{logo1_html}</td>
                <td style="width: 56%; text-align: center;">
                    <h3 style="margin: 0; font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;">JASA SEWA ALAT BERAT PENDUKUNG OPERASIONAL SENORO & TIAKA</h3>
                    <p style="margin: 4px 0 0 0; font-size: 11px; font-weight: bold;">Contract No. {nomor_kontrak_str}</p>
                </td>
                <td style="width: 22%; text-align: center;">{logo2_html}</td>
            </tr>
        </table>
        <div class="title-box">WORK COMPLETION CERTIFICATE</div>
        <div class="cert-box">CERTIFICATE NO : {wcc_no}</div>
        <div class="content-text">On the date of <b>{wcc_date}</b> we on behalf of <b>PT Banggai Sentral Sulawesi</b> have completed the following job:</div>
        <table class="grid-table">
            <tr><td class="col-label">WORK ORDER NUMBER</td><td class="col-colon">:</td><td class="col-val"><b>{wo_no}</b></td></tr>
            <tr><td class="col-label">WORK ORDER TITLE</td><td class="col-colon">:</td><td class="col-val">{wo_title}</td></tr>
            <tr><td class="col-label">CTR NUMBER</td><td class="col-colon">:</td><td class="col-val"><b>{ctr_no}</b></td></tr>
            <tr><td class="col-label">DESCRIPTION</td><td class="col-colon">:</td><td class="col-val"><table style="width:100%; border:none;"><tr><td style="border:none; padding:0; width:65%;">{progress_desc}</td><td style="border:none; padding:0; width:35%; text-align:right; font-weight:bold;">Rp {grand_total_wcc:,.2f}</td></tr></table></td></tr>
            <tr><td class="col-label">AMOUNT TOTAL</td><td class="col-colon">:</td><td class="col-val"><b>{terbilang_str}</b></td></tr>
        </table>
        <div class="content-text">The work has been properly completed as per requirement, witnessed and accepted by <b>JOB Pertamina - Medco E&P Tomori Sulawesi</b>.</div>
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
        st.components.v1.html(f'<script>function printDoc(){{var win=window.open("about:blank","_blank");win.document.write(atob("{b64_html}"));win.document.close();win.print();}}</script><button onclick="printDoc()" style="width: 100%; background-color: #10b981; color: white; padding: 10px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">🖨️ Cetak Dokumen WCC</button>', height=50)
    with col_btn2:
        b64_pdf = base64.b64encode(html_content.encode()).decode()
        st.markdown(f'<a href="data:text/html;base64,{b64_pdf}" download="WCC_{str(selected_pi).replace("/", "-")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download File WCC</button></a>', unsafe_allow_html=True)