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
    
    # Penomoran WCC dinamis berdasarkan nomor kontrak / PI
    wcc_no = f"{t_data['Nomor Kontrak']}-BSS-WCC-2026"
    wo_no = f"{t_data['Nomor Kontrak']}-BSS-WO-2026"
    ctr_no = f"{t_data['Nomor Kontrak']}-BSS-CTR-2026"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Work Completion Certificate - PT BSS</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; padding: 30px; margin: 0; font-size: 11px; line-height: 1.5; }}
            .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px; }}
            .title {{ text-align: center; font-weight: bold; font-size: 14px; margin-bottom: 15px; text-transform: uppercase; }}
            .cert-no {{ text-align: center; font-weight: bold; font-size: 12px; margin-bottom: 20px; }}
            table.info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; border: none; }}
            table.info-table td {{ border: none; padding: 5px 0; vertical-align: top; font-size: 11px; }}
            .label-col {{ width: 180px; font-weight: bold; }}
            .colon-col {{ width: 15px; font-weight: bold; text-align: center; }}
            .content-text {{ margin-bottom: 15px; text-align: justify; font-size: 11px; }}
            table.sig-table {{ width: 100%; border-collapse: collapse; margin-top: 25px; border: none; }}
            table.sig-table td {{ border: none; text-align: center; vertical-align: top; font-size: 11px; padding: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2 style="margin: 0; font-size: 16px;">PT. BANGGAI SENTRAL SULAWESI</h2>
            <p style="margin: 2px 0; font-size: 10px;">General Contractor and Suppliers | Jl. Urip Sumoharjo No. 53 Luwuk, Kabupaten Banggai, Propinsi Sulawesi Tengah</p>
        </div>

        <div class="title">WORK COMPLETION CERTIFICATE</div>
        <div class="cert-no">CERTIFICATE NO : {wcc_no}</div>

        <div class="content-text">
            On the date of <b>{t_data['Tanggal PI']}</b> we on behalf of <b>PT Banggai Sentral Sulawesi</b> have completed the following job:
        </div>

        <table class="info-table">
            <tr>
                <td class="label-col">WORK ORDER NUMBER</td>
                <td class="colon-col">:</td>
                <td>{wo_no}</td>
            </tr>
            <tr>
                <td class="label-col">WORK ORDER TITLE</td>
                <td class="colon-col">:</td>
                <td>{t_data['Nama Kontrak']}</td>
            </tr>
            <tr>
                <td class="label-col">CTR NUMBER</td>
                <td class="colon-col">:</td>
                <td>{ctr_no}</td>
            </tr>
            <tr>
                <td class="label-col">CONTRACT NO.</td>
                <td class="colon-col">:</td>
                <td>{t_data['Nomor Kontrak']}</td>
            </tr>
            <tr>
                <td class="label-col">DESCRIPTION</td>
                <td class="colon-col">:</td>
                <td>{t_data['Deskripsi Pekerjaan']}</td>
            </tr>
            <tr>
                <td class="label-col">AMOUNT TOTAL</td>
                <td class="colon-col">:</td>
                <td><b>Rp {t_data['Total Harga']:,.2f}</b> <i>({terbilang_str})</i></td>
            </tr>
        </table>

        <div class="content-text">
            The work has been properly completed as per requirement, witnessed and accepted by <b>JOB Pertamina - Medco E&P Tomori Sulawesi</b>.
        </div>

        <div style="margin-top: 15px; margin-bottom: 25px;">
            Paisubololi, {t_data['Tanggal PI']}
        </div>

        <table class="sig-table">
            <tr>
                <td style="width: 33%;">
                    <b>Prepared by,</b><br><br><br><br>
                    <u>Ronny Dwi Purnomo</u><br>Maintenance Support Supervisor
                </td>
                <td style="width: 34%;">
                    <b>Reviewed by,</b><br><br><br><br>
                    <u>Rafik Hidayat</u><br>Field Senior Manager
                </td>
                <td style="width: 33%;">
                    <b>Approved by,</b><br><br><br><br>
                    <u>Imron Maulana / Moh Bazarul</u><br>JOB Pertamina - Medco E&P
                </td>
            </tr>
        </table>
        
        <br>
        <table class="sig-table" style="margin-top: 10px;">
            <tr>
                <td style="width: 100%; text-align: center;">
                    <b>PT BANGGAI SENTRAL SULAWESI</b><br><br><br><br>
                    <u>Onesimus Suriadi</u><br>General Service Manager
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    st.markdown('<div class="document-preview">', unsafe_allow_html=True)
    st.components.v1.html(html_content, height=600, scrolling=True)
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