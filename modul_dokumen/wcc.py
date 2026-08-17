import streamlit as st
import pandas as pd
import os
import base64

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
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">🖨️ Pratinjau, Cetak & Download Work Completion Certificate (WCC)</h3>
        </div>
    """, unsafe_allow_html=True)

    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi yang diproses.")
        return

    seen_pi_dd = set()
    unique_tx_list = []
    for t in transaksi_list:
        pi_key = str(t.get('PI No.', ''))
        if pi_key not in seen_pi_dd:
            seen_pi_dd.add(pi_key)
            unique_tx_list.append(t)

    pilihan_tx = [f"PI: {t['PI No.']} | Kontrak: {t['Nomor Kontrak']} | Total: Rp {t['Total Harga']:,.0f}" for t in unique_tx_list]
    
    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        selected_idx = st.selectbox("Pilih Dokumen Transaksi Tersimpan:", range(len(pilihan_tx)), format_func=lambda x: pilihan_tx[x])
    with col_sel2:
        lokasi_office = st.text_input("📍 Lokasi Office (Tempat WCC):", value="Paisubololi")

    if 'persisted_logo_1' not in st.session_state:
        st.session_state.persisted_logo_1 = None
    if 'persisted_logo_2' not in st.session_state:
        st.session_state.persisted_logo_2 = None

    st.markdown("#### 🖼️ Pengaturan Logo Header Dokumen WCC (Tersimpan Otomatis)")
    c_log1, c_log2 = st.columns(2)
    with c_log1:
        uploaded_logo_1 = st.file_uploader("Upload Logo Pihak Pertama (PT BSS)", type=["png", "jpg", "jpeg"], key="logo_wcc_1")
        if uploaded_logo_1 is not None:
            st.session_state.persisted_logo_1 = uploaded_logo_1.getvalue()
    with c_log2:
        uploaded_logo_2 = st.file_uploader("Upload Logo Pihak Kedua / Instansi (JOB Pertamina)", type=["png", "jpg", "jpeg"], key="logo_wcc_2")
        if uploaded_logo_2 is not None:
            st.session_state.persisted_logo_2 = uploaded_logo_2.getvalue()

    t_data = unique_tx_list[selected_idx]
    terbilang_str = terbilang(t_data['Total Harga']).strip() + " Rupiah"
    
    db_invoice_path = os.path.join("database_penyimpanan_aman", "database_proforma_invoice.xlsx")
    matched_db_row = {}
    if os.path.exists(db_invoice_path):
        try:
            df_inv = pd.read_excel(db_invoice_path)
            pi_sekarang = str(t_data.get('PI No.', '')).strip()
            row_match = df_inv[df_inv['Proforma Invoice No.'].astype(str).str.strip() == pi_sekarang]
            if not row_match.empty:
                matched_db_row = row_match.iloc[0].to_dict()
        except:
            pass

    nomor_kontrak_str = str(t_data.get('Nomor Kontrak', ''))
    wcc_no = str(matched_db_row.get('Nomor WCC', nomor_kontrak_str + '-BSS-WCC-2026'))
    wcc_date = str(matched_db_row.get('Tanggal WCC', t_data.get('Tanggal PI', '')))
    wo_no = str(matched_db_row.get('Nomor WO', nomor_kontrak_str + '-BSS-WO-2026'))
    ctr_no = str(matched_db_row.get('Nomor CTR', nomor_kontrak_str + '-BSS-CTR-2026'))
    
    wo_title = str(matched_db_row.get('Keterangan WO', ''))
    if not wo_title:
        wo_title = str(t_data.get('Deskripsi PO', t_data.get('Nama Kontrak', '')))

    progress_val = str(matched_db_row.get('Progress Pekerjaan', '100%'))
    
    # PERBAIKAN: Menggunakan simbol HTML universal aman-PDF pengganti kotak-kotak
    progress_desc = f"[&#10003;] {progress_val} - Penyelesaian Pekerjaan"

    prepared_name = str(matched_db_row.get('Prepared by Name', 'Onesimus Suriadi'))
    prepared_title = str(matched_db_row.get('Prepared by Title', 'General Service Manager'))
    reviewed_name = str(matched_db_row.get('Diwakili Oleh', 'Ronny Dwi Purnomo / Rafik Hidayat'))
    approved_name = str(matched_db_row.get('Pejabat berwenang', 'Imron Maulana / Moh Bazarul Aqhsa'))
    field_mgr_title = str(matched_db_row.get('Jabatan Field Manager', 'Field Senior Manager'))

    logo1_html = ""
    if st.session_state.persisted_logo_1 is not None:
        b64_l1 = base64.b64encode(st.session_state.persisted_logo_1).decode()
        logo1_html = f'<img src="data:image/png;base64,{b64_l1}" style="max-height: 50px; max-width: 130px; object-fit: contain; display: block; margin: 0 auto;">'

    logo2_html = ""
    if st.session_state.persisted_logo_2 is not None:
        b64_l2 = base64.b64encode(st.session_state.persisted_logo_2).decode()
        logo2_html = f'<img src="data:image/png;base64,{b64_l2}" style="max-height: 50px; max-width: 130px; object-fit: contain; display: block; margin: 0 auto;">'

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Work Completion Certificate - PT BSS</title>
        <style>
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

        <div class="content-text">
            On the date of <b>{wcc_date}</b> we on behalf of <b>PT Banggai Sentral Sulawesi</b> have completed the following job:
        </div>

        <table class="grid-table">
            <tr>
                <td class="col-label">WORK ORDER NUMBER</td>
                <td class="col-colon">:</td>
                <td class="col-val"><b>{wo_no}</b></td>
            </tr>
            <tr>
                <td class="col-label">WORK ORDER TITLE</td>
                <td class="col-colon">:</td>
                <td class="col-val">{wo_title}</td>
            </tr>
            <tr>
                <td class="col-label">CTR NUMBER</td>
                <td class="col-colon">:</td>
                <td class="col-val">{ctr_no}</td>
            </tr>
            <tr>
                <td class="col-label">DESCRIPTION</td>
                <td class="col-colon">:</td>
                <td class="col-val">
                    <table style="width:100%; border:none;">
                        <tr>
                            <td style="border:none; padding:0; width:65%;">{progress_desc}</td>
                            <td style="border:none; padding:0; width:35%; text-align:right; font-weight:bold;">Rp {t_data['Total Harga']:,.2f}</td>
                        </tr>
                    </table>
                </td>
            </tr>
            <tr>
                <td class="col-label">AMOUNT TOTAL</td>
                <td class="col-colon">:</td>
                <td class="col-val"><b>{terbilang_str}</b></td>
            </tr>
        </table>

        <div class="content-text">
            The work has been properly completed as per requirement, witnessed and accepted by <b>JOB Pertamina - Medco E&P Tomori Sulawesi</b>.
        </div>

        <table class="sig-table">
            <tr>
                <td style="width: 33%; text-align: left; padding-left: 10px;">
                    {lokasi_office}, {wcc_date}<br>
                    <b>PT Banggai Sentral Sulawesi</b><br>
                    Prepared by,<br><br><br><br>
                    <u><b>{prepared_name}</b></u><br>
                    {prepared_title}
                </td>
                <td style="width: 34%; text-align: center;">
                    <br>
                    <b>JOB Pertamina - Medco E&P Tomori Sulawesi</b><br>
                    Reviewed by,<br><br><br><br>
                    <u><b>{reviewed_name}</b></u><br>
                    Maintenance Support Supervisor
                </td>
                <td style="width: 33%; text-align: center;">
                    <br>
                    <b>JOB Pertamina - Medco E&P Tomori Sulawesi</b><br>
                    Approved by,<br><br><br><br>
                    <u><b>{approved_name}</b></u><br>
                    {field_mgr_title}
                </td>
            </tr>
        </table>
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
                🖨️ Cetak / Print Dokumen WCC (Klik Disini)
            </button>
        """
        st.components.v1.html(print_script, height=50)

    with col_btn2:
        b64_pdf = base64.b64encode(html_content.encode()).decode()
        download_link = f'<a href="data:text/html;base64,{b64_pdf}" download="WCC_{t_data["PI No."].replace("/", "-")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download File WCC</button></a>'
        st.markdown(download_link, unsafe_allow_html=True)