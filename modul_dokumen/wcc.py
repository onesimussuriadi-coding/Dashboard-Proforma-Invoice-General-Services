import streamlit as st
import pandas as pd
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
    selected_idx = st.selectbox("Pilih Dokumen Transaksi Tersimpan:", range(len(pilihan_tx)), format_func=lambda x: pilihan_tx[x])
    
    t_data = unique_tx_list[selected_idx]
    terbilang_str = terbilang(t_data['Total Harga']).strip() + " Rupiah"
    
    # Ambil data spesifik dari database tanpa terpotong
    wcc_no = t_data.get('Nomor WCC', f"{t_data['Nomor Kontrak']}-BSS-WCC-2026-019")
    wcc_date = t_data.get('Tanggal WCC', t_data['Tanggal PI'])
    wo_no = t_data.get('Nomor WO', f"{t_data['Nomor Kontrak']}-BSS-WO-2026-019")
    ctr_no = t_data.get('Nomor CTR', f"{t_data['Nomor Kontrak']}-BSS-CTR-2026-019")
    
    wo_title = t_data.get('Keterangan WO', '')
    if not wo_title:
        wo_title = t_data.get('Deskripsi PO', t_data.get('Nama Kontrak', ''))

    progress_desc = t_data.get('Progress Pekerjaan', '☑ Penyelesaian Pekerjaan')
    lokasi_proyek = t_data.get('Lokasi Proyek', 'Paisubololi')

    # Nama penandatangan murni dari database
    prepared_name = t_data.get('Prepared by Name', 'Onesimus Suriadi')
    prepared_title = t_data.get('Prepared by Title', 'General Service Manager')
    reviewed_name = t_data.get('Diwakili Oleh', 'Ronny Dwi Purnomo / Rafik Hidayat')
    approved_name = t_data.get('Pejabat berwenang', 'Imron Maulana / Moh Bazarul Aqhsa')
    field_mgr_title = t_data.get('Jabatan Field Manager', 'Field Senior Manager')

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Work Completion Certificate - PT BSS</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; padding: 25px; margin: 0; font-size: 11px; line-height: 1.4; }}
            .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 8px; margin-bottom: 15px; }}
            .title-box {{ background-color: #dbeafe; border: 1px solid #000; text-align: center; font-weight: bold; font-size: 13px; padding: 6px; margin-bottom: 4px; text-transform: uppercase; }}
            .cert-box {{ background-color: #f1f5f9; border: 1px solid #000; text-align: center; font-weight: bold; font-size: 12px; padding: 6px; margin-bottom: 20px; }}
            
            table.grid-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
            table.grid-table th, table.grid-table td {{ border: 1px solid #000; padding: 8px 10px; font-size: 11px; vertical-align: middle; }}
            .col-label {{ width: 25%; font-weight: bold; background-color: #fafafa; }}
            .col-colon {{ width: 3%; text-align: center; font-weight: bold; }}
            .col-val {{ width: 72%; }}
            
            .content-text {{ margin-bottom: 15px; font-size: 11px; }}
            table.sig-table {{ width: 100%; border-collapse: collapse; margin-top: 30px; border: none; }}
            table.sig-table td {{ border: none; text-align: center; vertical-align: top; font-size: 11px; padding: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2 style="margin: 0; font-size: 15px;">PT. BANGGAI SENTRAL SULAWESI</h2>
            <p style="margin: 2px 0; font-size: 9px;">General Contractor and Suppliers | Jl. Urip Sumoharjo No. 53 Luwuk, Kabupaten Banggai, Propinsi Sulawesi Tengah</p>
        </div>

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
                    {lokasi_proyek}, {wcc_date}<br>
                    <b>PT Banggai Sentral Sulawesi</b><br>
                    Prepared by,<br><br><br><br>
                    <u><b>{prepared_name}</b></u><br>
                    {prepared_title}
                </td>
                <td style="width: 34%; text-align: center;">
                    <br><br>
                    <b>JOB Pertamina - Medco E&P Tomori Sulawesi</b><br>
                    Reviewed by,<br><br><br><br>
                    <u><b>{reviewed_name}</b></u><br>
                    Maintenance Support Supervisor
                </td>
                <td style="width: 33%; text-align: center;">
                    <br><br>
                    <br>
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
    st.components.v1.html(html_content, height=620, scrolling=True)
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