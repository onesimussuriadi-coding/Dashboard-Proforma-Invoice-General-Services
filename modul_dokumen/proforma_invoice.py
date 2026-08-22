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

def tampilkan_proforma_invoice(transaksi_list):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">🖨️ Pratinjau, Cetak & Download Proforma Invoice (Multi-Item Ready)</h3>
        </div>
    """, unsafe_allow_html=True)

    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi rincian pekerjaan yang diproses.")
        return

    # Ambil daftar PI unik untuk dropdown pilihan
    seen_pi_dd = set()
    unique_pi_list = []
    for t in transaksi_list:
        pi_key = str(t.get('PI No.', ''))
        if pi_key and pi_key not in seen_pi_dd:
            seen_pi_dd.add(pi_key)
            unique_pi_list.append(pi_key)

    selected_pi = st.selectbox("Pilih Nomor Proforma Invoice (PI):", unique_pi_list)
    
    # Saring semua baris mutasi yang memiliki PI No. yang sama
    mutasi_terpilih = [t for t in transaksi_list if str(t.get('PI No.')) == str(selected_pi)]
    
    if not mutasi_terpilih:
        st.warning("⚠️ Tidak ada item mutasi ditemukan untuk PI ini.")
        return

    t_data_utama = mutasi_terpilih[0]

    # Hitung Grand Total dari seluruh baris mutasi terpilih
    grand_total_pi = sum([float(m.get('Total Harga', 0.0)) for m in mutasi_terpilih])
    terbilang_str = terbilang(grand_total_pi).strip() + " Rupiah"

    # Pengambilan data penandatangan
    nama_pt_sign = t_data_utama.get('Nama PT Sign', 'PT. BANGGAI SENTRAL SULAWESI')
    nama_pejabat = t_data_utama.get('Penandatangan Nama', 'Onesimus Suriadi')
    jabatan_pejabat = t_data_utama.get('Penandatangan Jabatan', 'Manager General Services')

    # Buat baris tabel HTML secara dinamis untuk semua item mutasi
    rows_html = ""
    for idx, m in enumerate(mutasi_terpilih, start=1):
        desc_text = f"<b>{m.get('Kategori', 'MONTHLY BASIS')}</b><br>{m.get('Deskripsi Pekerjaan', '-')}"
        if m.get('Keterangan'):
            desc_text += f"<br><span style='font-size: 10px; color: #334155;'>{m.get('Keterangan')}</span>"
        
        qty_val = float(m.get('Qty', 0.0))
        unit_val = str(m.get('Unit', 'Unit'))
        duration_val = f"{qty_val:,.1f} {unit_val}"
        percent_val = f"{float(m.get('Percent', 100.0))}%"
        unit_price = float(m.get('Harga Satuan', 0.0))
        total_item = float(m.get('Total Harga', 0.0))

        rows_html += f"""
            <tr>
                <td style="text-align: center;">{idx}</td>
                <td>{desc_text}</td>
                <td style="text-align: center;">{qty_val:,.2f}</td>
                <td style="text-align: center;">{unit_val}</td>
                <td style="text-align: center; white-space: nowrap;">{duration_val}</td>
                <td style="text-align: center;">{percent_val}</td>
                <td style="text-align: right;">Rp {unit_price:,.2f}</td>
                <td style="text-align: right;">Rp {total_item:,.2f}</td>
            </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Proforma Invoice - PT BSS</title>
        <style>
            @page {{
                size: A4;
                margin: 5mm 10mm 5mm 10mm;
            }}
            @media print {{
                body {{
                    -webkit-print-color-adjust: exact;
                }}
                @page {{
                    margin: 5mm 10mm 5mm 10mm;
                }}
            }}
            body {{ font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; padding: 15px; margin: 0; font-size: 11px; }}
            .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 8px; margin-bottom: 15px; }}
            .header-title {{ font-size: 15px; font-weight: bold; margin-bottom: 15px; text-transform: uppercase; text-align: center; }}
            table.two-col {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; border: none; }}
            table.two-col td {{ border: none; padding: 2px 0; vertical-align: top; font-size: 11px; }}
            table.data-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 10px; }}
            table.data-table th, table.data-table td {{ border: 1px solid #333; padding: 6px 8px; font-size: 11px; text-align: left; }}
            table.data-table th {{ background-color: #f1f5f9; text-align: center; }}
            .bank-section {{ font-size: 11px; line-height: 1.4; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2 style="margin: 0; font-size: 15px;">PT. BANGGAI SENTRAL SULAWESI</h2>
            <p style="margin: 2px 0; font-size: 9px;">General Contractor and Suppliers | Jl. Urip Sumoharjo No. 53 Luwuk, Kabupaten Banggai, Propinsi Sulawesi Tengah</p>
        </div>

        <div class="header-title">PROFORMA INVOICE</div>
        
        <table class="two-col">
            <tr>
                <td style="width: 52%;">
                    <b>TO :</b><br>
                    <b>{t_data_utama.get('Ditujukan Kepada', 'JOB Pertamina - Medco E&P Tomori Sulawesi')}</b><br>
                    {t_data_utama.get('Alamat Pihak Pertama', 'Bidakara Office Tower I 4Th Floor, Jl. Gatot Subroto Kav. 71 - 73, Jakarta 12870, Indonesia')}<br><br>
                    <b>Attn. :</b> {t_data_utama.get('Attn', 'Accounts Payable - Finance Department')}
                </td>
                <td style="width: 48%;">
                    <table style="width: 100%; border-collapse: collapse; border: none;">
                        <tr>
                            <td style="border: none; width: 45%; font-weight: bold;">Proforma Invoice No.</td>
                            <td style="border: none; width: 5%; text-align: center;">:</td>
                            <td style="border: none; width: 50%;">{t_data_utama['PI No.']}</td>
                        </tr>
                        <tr>
                            <td style="border: none; font-weight: bold;">Tanggal Performa Invoice</td>
                            <td style="border: none; text-align: center;">:</td>
                            <td style="border: none;">{t_data_utama['Tanggal PI']}</td>
                        </tr>
                        <tr>
                            <td style="border: none; font-weight: bold;">Nomor Kontrak</td>
                            <td style="border: none; text-align: center;">:</td>
                            <td style="border: none;">{t_data_utama['Nomor Kontrak']}</td>
                        </tr>
                        <tr>
                            <td style="border: none; font-weight: bold;">Jangka Waktu Kontrak</td>
                            <td style="border: none; text-align: center;">:</td>
                            <td style="border: none;">{t_data_utama.get('Jangka Waktu Kontrak', '24 Month')}</td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>

        <table class="data-table">
            <tr>
                <th>Item</th>
                <th>Description</th>
                <th>Qty</th>
                <th>Unit</th>
                <th>Duration</th>
                <th>Percent</th>
                <th>Unit Price<br>(IDR)</th>
                <th>TOTAL (IDR)</th>
            </tr>
            {rows_html}
        </table>

        <div style="margin-bottom: 15px; font-size: 11px; display: flex; justify-content: space-between;">
            <div><b>Terbilang :</b> <i>{terbilang_str}</i></div>
            <div style="font-size: 12px; font-weight: bold;">GRAND TOTAL: Rp {grand_total_pi:,.2f}</div>
        </div>

        <table style="width: 100%; border: none; margin-top: 10px;">
            <tr>
                <td style="border: none; width: 55%; vertical-align: top;">
                    <div class="bank-section">
                        <b>PAYMENT INSTRUCTION</b><br>
                        Please remit to our bank:<br>
                        <b>Bank Name :</b> {t_data_utama.get('Bank Name', 'BANK RAKYAT INDONESIA (PERSERO) Tbk.')}<br>
                        <b>Branch :</b> {t_data_utama.get('Bank Branch', 'Cabang Luwuk')}<br>
                        <b>Account No :</b> {t_data_utama.get('Account No', '0167 0167 8888 303')}<br>
                        <b>Account Name :</b> {t_data_utama.get('Account Name', 'PT. BANGGAI SENTRAL SULAWESI')}
                    </div>
                </td>
                <td style="border: none; width: 45%; text-align: right; vertical-align: top;">
                    <div class="bank-section" style="margin-top: 75px; text-align: center; display: inline-block; min-width: 220px;">
                        <b>{nama_pt_sign}</b><br><br><br><br>
                        <u>{nama_pejabat}</u><br>
                        {jabatan_pejabat}
                    </div>
                </td>
            </tr>
        </table>
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
        download_link = f'<a href="data:text/html;base64,{b64_pdf}" download="Proforma_Invoice_{t_data_utama["PI No."].replace("/", "-")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download File HTML/PDF</button></a>'
        st.markdown(download_link, unsafe_allow_html=True)