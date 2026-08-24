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

    # Inisialisasi penyimpanan session state khusus WCC
    if "wcc_saved_data" not in st.session_state:
        st.session_state.wcc_saved_data = {}

    col_sel1 = st.columns([1])[0]
    with col_sel1:
        selected_pi = st.selectbox("Pilih Nomor Proforma Invoice (PI):", unique_pi_list, key="wcc_sel_pi")

    pi_storage_key = str(selected_pi).strip()

    # Inisialisasi default session state untuk PI terpilih jika belum ada
    if pi_storage_key not in st.session_state.wcc_saved_data:
        st.session_state.wcc_saved_data[pi_storage_key] = {
            'lokasi': "Paisubololi"
        }

    saved_wcc = st.session_state.wcc_saved_data[pi_storage_key]

    # Form khusus tombol save / simpan dokumen WCC beserta input lokasi yang terkunci
    with st.form(key=f"form_wcc_save_{pi_storage_key}"):
        lokasi_office = st.text_input("📍 Lokasi Office (Tempat WCC):", value=str(saved_wcc.get('lokasi', 'Paisubololi')), key=f"wcc_lok_office_{pi_storage_key}")
        
        st.markdown(f"**Konfirmasi Dokumen WCC (PI: {selected_pi}):** Klik tombol di bawah untuk mengunci konfigurasi.")
        submit_save_wcc = st.form_submit_button("💾 Simpan & Kunci Dokumen WCC Ini", type="primary")
        
        if submit_save_wcc:
            st.session_state.wcc_saved_data[pi_storage_key] = {
                'lokasi': lokasi_office
            }
            st.success(f"✅ Dokumen WCC untuk PI [{selected_pi}] berhasil disimpan dan dikunci!")

    # Ambil nilai lokasi aktif yang sudah tersimpan/terkunci
    active_lokasi = st.session_state.wcc_saved_data[pi_storage_key].get('lokasi', 'Paisubololi')

    mutasi_terpilih = [t for t in transaksi_list if str(t.get('PI No.')).strip() == str(selected_pi).strip()]
    
    if not mutasi_terpilih:
        st.warning("⚠️ Tidak ada item mutasi ditemukan untuk PI ini.")
        return

    t_data_utama = mutasi_terpilih[0]
    grand_total_wcc = sum([float(m.get('Total Harga', 0.0)) for m in mutasi_terpilih])
    terbilang_str = terbilang(grand_total_wcc).strip() + " Rupiah"

    if 'persisted_logo_1' not in st.session_state:
        st.session_state.persisted_logo_1 = None
    if 'persisted_logo_2' not in st.session_state:
        st.session_state.persisted_logo_2 = None

    st.markdown("#### 🖼️ Pengaturan Logo Header Dokumen WCC (Tersimpan Otomatis)")
    c_log1, c_log2 = st.columns(2)
    with c_log1:
        uploaded_logo_1 = st.file_uploader("Upload Logo Pihak Pertama (PT BSS)", type=["png", "jpg", "jpeg"], key="logo_wcc_1_u")
        if uploaded_logo_1 is not None:
            st.session_state.persisted_logo_1 = uploaded_logo_1.getvalue()
    with c_log2:
        uploaded_logo_2 = st.file_uploader("Upload Logo Pihak Kedua / Instansi (JOB Pertamina)", type=["png", "jpg", "jpeg"], key="logo_wcc_2_u")
        if uploaded_logo_2 is not None:
            st.session_state.persisted_logo_2 = uploaded_logo_2.getvalue()

    db_invoice_path = os.path.join("database_penyimpanan_aman", "database_proforma_invoice.xlsx")
    matched_db_row = {}
    wcc_no = "DATA WCC BELUM DIINPUT"
    wo_no = "DATA WO BELUM DIINPUT"
    ctr_no = "DATA CTR BELUM DIINPUT"
    
    if os.path.exists(db_invoice_path):
        try:
            df_inv = pd.read_excel(db_invoice_path)
            pi_sekarang = str(selected_pi).strip().lower()
            
            for idx, row in df_inv.iterrows():
                val_pi_0 = str(row.iloc[0]).strip().lower()
                if val_pi_0 == pi_sekarang:
                    matched_db_row = row.to_dict()
                    wcc_no = str(row.iloc[19]) if len(row) > 19 and pd.notnull(row.iloc[19]) else "DATA WCC BELUM DIINPUT"
                    wo_no = str(row.iloc[21]) if len(row) > 21 and pd.notnull(row.iloc[21]) else "DATA WO BELUM DIINPUT"
                    ctr_no = str(row.iloc[23]) if len(row) > 23 and pd.notnull(row.iloc[23]) else "DATA CTR BELUM DIINPUT"
                    break
        except:
            pass

    nomor_kontrak_str = str(t_data_utama.get('Nomor Kontrak', '7201250141'))
    
    raw_date = matched_db_row.get('Tanggal WCC', t_data_utama.get('Tanggal PI', datetime.now().strftime('%d %B %Y')))
    try:
        if isinstance(raw_date, str) and len(raw_date) >= 10:
            parsed_date = pd.to_datetime(raw_date)
            wcc_date = parsed_date.strftime('%d %B %Y')
        else:
            wcc_date = datetime.now().strftime('%d %B %Y')
    except:
        wcc_date = str(raw_date)

    wo_title = str(matched_db_row.get('Keterangan WO', ''))
    if not wo_title:
        wo_title = str(t_data_utama.get('Deskripsi PO', t_data_utama.get('Nama Kontrak', 'General Services Supporting Well Workover and Maintenance')))

    progress_val = str(matched_db_row.get('Progress Pekerjaan', '100%'))
    progress_desc = f"[&#10003;] {progress_val} - Penyelesaian Pekerjaan"

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

    logo1_html = f'<img src="data:image/png;base64,{base64.b64encode(st.session_state.persisted_logo_1).decode()}" style="max-height: 50px; max-width: 130px; object-fit: contain; display: block; margin: 0 auto;">' if st.session_state.persisted_logo_1 is not None else ""
    logo2_html = f'<img src="data:image/png;base64,{base64.b64encode(st.session_state.persisted_logo_2).decode()}" style="max-height: 50px; max-width: 130px; object-fit: contain; display: block; margin: 0 auto;">' if st.session_state.persisted_logo_2 is not None else ""

    if is_same_person or not reviewed_name or str(reviewed_name).strip() == "" or str(reviewed_name).strip().lower() == "nan":
        sig_table_html = f"""
        <table class="sig-table">
            <tr>
                <td style="width: 50%; text-align: left; padding-left: 10px;">
                    {active_lokasi}, {wcc_date}<br>
                    <b>PT Banggai Sentral Sulawesi</b><br>
                    Prepared by,<br><br><br><br>
                    <u><b>{prepared_name}</b></u><br>
                    {prepared_title}
                </td>
                <td style="width: 50%; text-align: center;">
                    <br>
                    <b>JOB Pertamina - Medco E&P Tomori Sulawesi</b><br>
                    Approved by,<br><br><br><br>
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
                    {active_lokasi}, {wcc_date}<br>
                    <b>PT Banggai Sentral Sulawesi</b><br>
                    Prepared by,<br><br><br><br>
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
                    Approved by,<br><br><br><br>
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
            table.sig-table {{ width: 100%; border-collapse: collapse; margin-top: 30px; border: none; }}
            table.sig-table td {{ border: none; vertical-align: top; font-size: 11px; padding: 5px; }}
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