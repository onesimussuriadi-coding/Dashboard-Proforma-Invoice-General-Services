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

def tampilkan_rincian_pekerjaan(transaksi_list):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">🖨️ Pratinjau, Cetak & Download Dokumen Rincian Pekerjaan</h3>
        </div>
    """, unsafe_allow_html=True)

    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi rincian pekerjaan yang diproses.")
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

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Rincian Pekerjaan - PT BSS</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; padding: 30px; margin: 0; }}
            .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px; }}
            .title {{ text-align: center; font-weight: bold; font-size: 15px; margin-bottom: 20px; text-transform: uppercase; text-decoration: underline; }}
            table.info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; border: none; }}
            table.info-table td {{ border: none; padding: 4px 6px; font-size: 11px; vertical-align: top; }}
            .label-col {{ width: 160px; font-weight: bold; }}
            .colon-col {{ width: 10px; font-weight: bold; text-align: center; }}
            table.data-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 10px; }}
            table.data-table th, table.data-table td {{ border: 1px solid #333; padding: 6px 10px; font-size: 11px; text-align: left; }}
            table.data-table th {{ background-color: #f1f5f9; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2 style="margin: 0; font-size: 16px;">PT. BANGGAI SENTRAL SULAWESI</h2>
            <p style="margin: 2px 0; font-size: 10px;">General Contractor and Suppliers | Jl. Urip Sumoharjo No. 53 Luwuk, Kabupaten Banggai, Propinsi Sulawesi Tengah</p>
        </div>
        <div class="title">Rincian Pekerjaan</div>
        
        <table class="info-table">
            <tr>
                <td class="label-col">Rincian Pekerjaan</td>
                <td class="colon-col">:</td>
                <td>{t_data['Nomor Kontrak']}-BSS-WCC-2026</td>
                <td class="label-col">Ditujukan Kepada</td>
                <td class="colon-col">:</td>
                <td>{t_data['Ditujukan Kepada']}</td>
            </tr>
            <tr>
                <td class="label-col">Nomor Kontrak</td>
                <td class="colon-col">:</td>
                <td>{t_data['Nomor Kontrak']}</td>
                <td class="label-col">Nomor Purchase Order</td>
                <td class="colon-col">:</td>
                <td>{t_data['Nomor PO']}</td>
            </tr>
            <tr>
                <td class="label-col">Nama Kontrak</td>
                <td class="colon-col">:</td>
                <td>{t_data['Nama Kontrak']}</td>
                <td class="label-col">Lingkup Pekerjaan</td>
                <td class="colon-col">:</td>
                <td>{t_data['Deskripsi PO']}</td>
            </tr>
            <tr>
                <td class="label-col">Nomor Tender</td>
                <td class="colon-col">:</td>
                <td>{t_data['Nomor Tender']}</td>
                <td class="label-col">Tanggal Purchase Order</td>
                <td class="colon-col">:</td>
                <td>{t_data['Tanggal PO']}</td>
            </tr>
            <tr>
                <td class="label-col">Tanggal Proforma</td>
                <td class="colon-col">:</td>
                <td>{t_data['Tanggal PI']}</td>
                <td class="label-col">Mata Uang</td>
                <td class="colon-col">:</td>
                <td>{t_data['Mata Uang']}</td>
            </tr>
        </table>
        
        <table class="data-table">
            <tr>
                <th>No.</th>
                <th>Kategori</th>
                <th>Uraian Pekerjaan</th>
                <th>Qty Out</th>
                <th>Unit</th>
                <th>Tanggal Mulai</th>
                <th>Tanggal Selesai</th>
                <th>Harga Satuan</th>
                <th>Total Harga</th>
                <th>Keterangan</th>
            </tr>
            <tr>
                <td style="text-align: center;">1</td>
                <td>{t_data.get('Kategori', '-')}</td>
                <td>{t_data['Deskripsi Pekerjaan']}</td>
                <td style="text-align: center;">{t_data['Qty']:,.2f}</td>
                <td style="text-align: center;">{t_data['Unit']}</td>
                <td style="text-align: center; white-space: nowrap;">{t_data.get('Tanggal Mulai', '-')}</td>
                <td style="text-align: center; white-space: nowrap;">{t_data.get('Tanggal Selesai', '-')}</td>
                <td style="text-align: right;">{t_data['Harga Satuan']:,.2f}</td>
                <td style="text-align: right;">{t_data['Total Harga']:,.2f}</td>
                <td>{t_data['Keterangan']}</td>
            </tr>
        </table>
        
        <table style="width: 100%; border: none; margin-top: 15px;">
            <tr>
                <td style="border: none; text-align: left; font-size: 11px; vertical-align: top; width: 55%;">
                    <b>Terbilang :</b> <i>{terbilang_str}</i>
                </td>
                <td style="border: none; text-align: right; font-weight: bold; font-size: 13px; width: 45%; vertical-align: top;">
                    TOTAL TAGIHAN: Rp {t_data['Total Harga']:,.2f}
                </td>
            </tr>
        </table>
        <br>
        
        <table style="border: none; width: 100%; margin-top: 20px;">
            <tr>
                <td style="border: none; text-align: center; width: 50%;">
                    <b>DIBUAT OLEH</b><br><br><br><br>
                    <u>Yanuar Wiranata / Ireine Langi</u><br>Supervisor
                </td>
                <td style="border: none; text-align: center; width: 50%;">
                    <b>DIPERIKSA</b><br><br><br><br>
                    <u>Onesimus Suriadi</u><br>Manager General Services
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    st.markdown('<div class="document-preview">', unsafe_allow_html=True)
    st.components.v1.html(html_content, height=550, scrolling=True)
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
                🖨️ Cetak / Print Dokumen (Klik Disini)
            </button>
        """
        st.components.v1.html(print_script, height=50)

    with col_btn2:
        b64_pdf = base64.b64encode(html_content.encode()).decode()
        download_link = f'<a href="data:text/html;base64,{b64_pdf}" download="Rincian_Pekerjaan_{t_data["PI No."].replace("/", "-")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download Dokumen</button></a>'
        st.markdown(download_link, unsafe_allow_html=True)