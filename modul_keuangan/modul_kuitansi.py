import streamlit as st
import pandas as pd
import base64
from datetime import datetime

def terbilang(n):
    try:
        n = int(n)
    except:
        return ""
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

def tampilkan_kuitansi(transaksi_list, menu_pilihan=None):
    st.markdown("#### 🧾 Pratinjau Resmi Kuitansi Pembayaran Korporat")
    
    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi rincian untuk dirender ke dalam kuitansi.")
        return

    t_data = transaksi_list[0] if isinstance(transaksi_list, list) and len(transaksi_list) > 0 else {}
    
    # Ambil data secara dinamis dari database/transaksi aktif (Tanpa hardcoded salah)
    customer_name = t_data.get("Ditujukan Kepada", "JOB Pertamina - Medco E&P Tomori Sulawesi")
    pi_no = t_data.get("PI No.", "")
    if not pi_no:
        pi_no = t_data.get("Proforma Invoice No.", "010/BSS-JOB/IX/2026")
        
    nomor_po = t_data.get("Nomor PO", "-")
    
    # Ambil tanggal dari data transaksi/invoice jika tersedia, jika tidak gunakan hari ini
    tanggal_pi_raw = t_data.get("Tanggal PI", "")
    if not tanggal_pi_raw:
        tanggal_pi_raw = datetime.today().strftime('%d %B %Y')

    # Hitung total tagihan murni dari akumulasi Total Harga transaksi tanpa angka pengganti hardcoded
    total_tagihan = sum([float(item.get("Total Harga", 0.0)) for item in transaksi_list]) if isinstance(transaksi_list, list) else 0.0

    terbilang_str = terbilang(total_tagihan).strip() + " Rupiah" if total_tagihan > 0 else "Nol Rupiah"

    html_kuitansi = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Kuitansi Pembayaran - PT Banggai Sentral Sulawesi</title>
        <style>
            @page {{ 
                size: A4 portrait; 
                margin: 0mm; 
            }}
            @media print {{
                html, body {{
                    width: 210mm;
                    height: 297mm;
                    margin: 0 !important;
                    padding: 10mm !important;
                    background: #fff !important;
                    -webkit-print-color-adjust: exact;
                }}
                @page {{
                    margin: 0;
                }}
            }}
            body {{ 
                font-family: Arial, sans-serif; 
                background-color: #ffffff; 
                color: #000000; 
                padding: 12mm; 
                margin: 0; 
                font-size: 12px; 
            }}
            .receipt-box {{
                border: 2px solid #0f172a;
                padding: 25px;
                border-radius: 8px;
                max-width: 720px;
                margin: auto;
                background: #ffffff;
            }}
            .header-table {{
                width: 100%;
                border-bottom: 2px solid #0f172a;
                padding-bottom: 12px;
                margin-bottom: 20px;
            }}
            .receipt-title {{
                font-size: 20px;
                font-weight: bold;
                text-align: right;
                color: #0f172a;
                letter-spacing: 0.5px;
                margin-bottom: 4px;
            }}
            .content-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 12.5px;
                margin-bottom: 20px;
            }}
            .content-table td {{
                padding: 8px 4px;
                vertical-align: top;
            }}
            .nominal-box {{
                background-color: #f1f5f9;
                border: 1px solid #0f172a;
                padding: 8px 12px;
                font-size: 15px;
                font-weight: bold;
                display: inline-block;
                margin-top: 5px;
            }}
            .terbilang-cell {{
                background-color: #f8fafc;
                border: 1px dashed #64748b;
                padding: 8px 12px;
                font-style: italic;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="receipt-box">
            <table class="header-table">
                <tr>
                    <td style="width: 55%; vertical-align: middle;">
                        <h2 style="margin:0; font-size:16px; color:#0f172a; text-transform:uppercase;">PT. BANGGAI SENTRAL SULAWESI</h2>
                        <p style="margin:2px 0; font-size:10px; color:#334155;">General Contractor and Supplier</p>
                        <p style="margin:2px 0 0 0; font-size:9px; color:#475569;">Jl. Urip Sumoharjo No. 53, Luwuk, Kab. Banggai, Sulawesi Tengah</p>
                    </td>
                    <td style="width: 45%; text-align: right; vertical-align: middle;">
                        <div class="receipt-title">KUITANSI PEMBAYARAN</div>
                        <p style="margin: 0; font-size: 10.5px; color: #475569;">No. Ref: <b>KT-{pi_no.replace('/IX/', '/').replace('/VIII/', '/')}</b></p>
                    </td>
                </tr>
            </table>

            <table class="content-table">
                <tr>
                    <td style="width: 150px; font-weight: bold;">Sudah Terima Dari</td>
                    <td style="width: 15px;">:</td>
                    <td style="font-weight: bold; font-size: 13.5px; color: #0f172a;">{customer_name}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold;">Uang Sejumlah</td>
                    <td>:</td>
                    <td>
                        <div class="terbilang-cell"># {terbilang_str} #</div>
                    </td>
                </tr>
                <tr>
                    <td style="font-weight: bold;">Untuk Pembayaran</td>
                    <td>:</td>
                    <td>
                        Pelunasan biaya pekerjaan berdasarkan Proforma Invoice <b>{pi_no}</b> dan Nomor PO <b>{nomor_po}</b>.
                    </td>
                </tr>
            </table>

            <table style="width: 100%; margin-top: 10px; border-collapse: collapse;">
                <tr>
                    <td style="width: 50%; vertical-align: top;">
                        <div style="font-size: 11px; color: #475569; margin-bottom: 4px;">Jumlah Nominal Pembayaran:</div>
                        <div class="nominal-box">Rp {total_tagihan:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")</div>
                    </td>
                    <td style="width: 50%; text-align: center; vertical-align: top;">
                        <p style="margin: 0 0 10px 0;">Luwuk, {tanggal_pi_raw}</p>
                        <div style="height: 65px;"></div>
                        <p style="margin: 0; font-weight: bold; text-decoration: underline; font-size: 12.5px;">Ferry Tatimu</p>
                        <p style="margin: 2px 0 0 0; font-size: 11px;">Direktur</p>
                    </td>
                </tr>
            </table>
        </div>
    </body>
    </html>
    """

    st.markdown('<div class="document-preview">', unsafe_allow_html=True)
    st.components.v1.html(html_kuitansi, height=520, scrolling=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col_k1, col_k2 = st.columns(2)
    with col_k1:
        b64_html = base64.b64encode(html_kuitansi.encode()).decode()
        print_script = f"""
            <script>
                function printReceipt() {{
                    var win = window.open('about:blank', '_blank');
                    win.document.open();
                    win.document.write(atob("{b64_html}"));
                    win.document.close();
                    win.focus();
                    setTimeout(function(){{ win.print(); }}, 500);
                }}
            </script>
            <button onclick="printReceipt()" style="width: 100%; background-color: #10b981; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
                🖨️ Cetak / Print Kuitansi
            </button>
        """
        st.components.v1.html(print_script, height=50)

    with col_k2:
        download_link = f'<a href="data:text/html;base64,{b64_html}" download="Kuitansi_{pi_no.replace("/", "-")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download Kuitansi</button></a>'
        st.markdown(download_link, unsafe_allow_html=True)