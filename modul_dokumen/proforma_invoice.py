import streamlit as st
import pandas as pd
import base64
import os
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

# FUNGSI FORMAT TANGGAL INDONESIA (DD MMM YYYY)
def format_tanggal_indo_konsisten(tanggal_val):
    if not tanggal_val or str(tanggal_val).strip() in ["-", "nan", "None", ""]:
        return "-"
    clean_str = str(tanggal_val).strip().split()[0]
    bulan_indo_map = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
        7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }
    for fmt in ("%Y-%m-%d", "%d %b %Y", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            dt_obj = datetime.strptime(clean_str, fmt)
            return f"{dt_obj.day:02d} {bulan_indo_map[dt_obj.month]} {dt_obj.year}"
        except:
            continue
    return str(tanggal_val)

def tampilkan_proforma_invoice(transaksi_list):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">🖨️ Pratinjau, Cetak & Download Proforma Invoice (Multi-Item Ready)</h3>
        </div>
    """, unsafe_allow_html=True)

    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi rincian pekerjaan yang diproses.")
        return

    # --- DIREKTORI PENYIMPANAN EXCEL PROFORMA INVOICE ---
    DIR_DATABASE_PI = os.path.join("database_penyimpanan_aman")
    if not os.path.exists(DIR_DATABASE_PI):
        os.makedirs(DIR_DATABASE_PI)
    EXCEL_FILE_PI = os.path.join(DIR_DATABASE_PI, "database_proforma_invoice_tersimpan.xlsx")

    def muat_database_pi_excel():
        if os.path.exists(EXCEL_FILE_PI):
            try:
                df = pd.read_excel(EXCEL_FILE_PI)
                if df is not None and not df.empty:
                    return df.to_dict(orient="records")
            except:
                pass
        return []

    def simpan_database_pi_excel(list_data_rekaman):
        try:
            df_save = pd.DataFrame(list_data_rekaman)
            df_save.to_excel(EXCEL_FILE_PI, index=False)
            return True
        except Exception as e:
            st.error(f"Gagal menyimpan ke Excel: {e}")
            return False

    seen_pi_dd = set()
    unique_pi_list = []
    for t in transaksi_list:
        pi_key = str(t.get('PI No.', ''))
        if pi_key and pi_key not in seen_pi_dd:
            seen_pi_dd.add(pi_key)
            unique_pi_list.append(pi_key)

    if "proforma_saved_data" not in st.session_state:
        st.session_state.proforma_saved_data = {}

    selected_pi = st.selectbox("Pilih Nomor Proforma Invoice (PI):", unique_pi_list, key="proforma_sel_pi")
    
    pi_storage_key = str(selected_pi).strip()
    if pi_storage_key not in st.session_state.proforma_saved_data:
        st.session_state.proforma_saved_data[pi_storage_key] = {
            'locked_at': False,
            'ttd_bytes': None
        }

    saved_pi_global = st.session_state.proforma_saved_data[pi_storage_key]

    mutasi_terpilih = [t for t in transaksi_list if str(t.get('PI No.')) == str(selected_pi)]
    
    if not mutasi_terpilih:
        st.warning("⚠️ Tidak ada item mutasi ditemukan untuk PI ini.")
        return

    t_data_utama = mutasi_terpilih[0]

    st.markdown("---")
    uploaded_signature = st.file_uploader(
        "✍️ **Upload Tanda Tangan Digital (Format PNG / JPG - Transparan disarankan):**",
        type=["png", "jpg", "jpeg"],
        key=f"ttd_uploader_{pi_storage_key}"
    )

    if saved_pi_global.get('ttd_bytes') is not None:
        if st.button("🗑️ Hapus Tanda Tangan Digital Proforma Invoice", key=f"btn_del_pi_ttd_{pi_storage_key}"):
            saved_pi_global['ttd_bytes'] = None
            st.success("✅ Tanda Tangan Digital berhasil dihapus!")
            st.rerun()

    with st.form(key=f"form_proforma_save_{pi_storage_key}"):
        st.markdown(f"**Status Dokumen PI:** `{selected_pi}` siap dikunci dan disimpan ke database Excel.")
        submit_save_proforma = st.form_submit_button("💾 Simpan & Kunci Proforma Invoice Ini", type="primary")
        if submit_save_proforma:
            ttd_final = uploaded_signature.getvalue() if uploaded_signature is not None else saved_pi_global.get('ttd_bytes')

            st.session_state.proforma_saved_data[pi_storage_key] = {
                'locked_at': True,
                'ttd_bytes': ttd_final
            }

            # --- PROSES SIMPAN OTOMATIS KE FILE EXCEL HISTORI ---
            existing_excel_records = muat_database_pi_excel()
            filtered_existing = [r for r in existing_excel_records if str(r.get('PI No.', '')).strip() != pi_storage_key]
            
            waktu_simpan_str = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            for m in mutasi_terpilih:
                rekaman_baris = {
                    "Waktu Simpan": waktu_simpan_str,
                    "Nomor Kontrak": str(t_data_utama.get('Nomor Kontrak', '')),
                    "PI No.": pi_storage_key,
                    "Tanggal PI": str(t_data_utama.get('Tanggal PI', '')),
                    "Nomor PO": str(t_data_utama.get('Nomor PO', '')),
                    "Ditujukan Kepada": str(t_data_utama.get('Ditujukan Kepada', '')),
                    "Kategori": m.get('Kategori', ''),
                    "Uraian Pekerjaan": m.get('Deskripsi Pekerjaan', ''),
                    "Qty": float(m.get('Qty', 0.0)),
                    "Satuan": m.get('Unit', ''),
                    "Harga Satuan (IDR)": float(m.get('Harga Satuan', 0.0)),
                    "Percent (%)": float(m.get('Percent', 100.0)),
                    "Keterangan": m.get('Keterangan', '-')
                }
                filtered_existing.append(rekaman_baris)

            if simpan_database_pi_excel(filtered_existing):
                st.success(f"✅ Proforma Invoice untuk nomor PI [{selected_pi}] berhasil disimpan permanen ke file Excel (`database_proforma_invoice_tersimpan.xlsx`)!")
            else:
                st.warning("⚠️ Dokumen terkunci di sesi, tetapi gagal menulis ke file Excel.")

    ttd_bytes_active = saved_pi_global.get('ttd_bytes')
    if ttd_bytes_active:
        img_b64 = base64.b64encode(ttd_bytes_active).decode("utf-8")
        ttd_html_element = f"""
            <div style="height: 70px; display: flex; align-items: center; justify-content: center; margin: 4px 0;">
                <img src="data:image/png;base64,{img_b64}" style="max-height: 70px; max-width: 180px; object-fit: contain;">
            </div>
        """
    else:
        ttd_html_element = "<br><br><br><br>"

    # --- FORMAT TANGGAL PI KONSISTEN URUTAN TANGGAL, BULAN, TAHUN ---
    raw_tgl_pi = str(t_data_utama.get('Tanggal PI', ''))
    tanggal_pi_bersih = format_tanggal_indo_konsisten(raw_tgl_pi)

    # Hitung Grand Total secara mandiri per baris dengan mendukung Provisional Sum & Estimated Sum (Diskon 10%)
    grand_total_pi = 0.0
    for m in mutasi_terpilih:
        kategori_str = str(m.get('Kategori', '')).lower()
        qty_val = float(m.get('Qty', 0.0))
        unit_price = float(m.get('Harga Satuan', 0.0))
        percent_val = float(m.get('Percent', 100.0))

        if "provisional" in kategori_str or "professional" in kategori_str:
            tot_item = (qty_val * unit_price) * 1.15 * (percent_val / 100.0)
        elif "estimated" in kategori_str or "estimasi" in kategori_str:
            tot_item = (qty_val * unit_price * 0.9) * (percent_val / 100.0)
        else:
            tot_item = (qty_val * unit_price) * (percent_val / 100.0)
        grand_total_pi += tot_item

    terbilang_str = terbilang(grand_total_pi).strip() + " Rupiah"

    nama_pt_sign = t_data_utama.get('Nama PT Sign', 'PT. BANGGAI SENTRAL SULAWESI')
    nama_pejabat = t_data_utama.get('Penandatangan Nama', 'Onesimus Suriadi')
    jabatan_pejabat = t_data_utama.get('Penandatangan Jabatan', 'Manager General Services')

    rows_html = ""
    for idx, m in enumerate(mutasi_terpilih, start=1):
        kategori_str = str(m.get('Kategori', '')).lower()
        qty_val = float(m.get('Qty', 0.0))
        unit_price = float(m.get('Harga Satuan', 0.0))
        percent_val = float(m.get('Percent', 100.0))
        kategori_awal = str(m.get('Kategori', 'MONTHLY BASIS'))

        if "provisional" in kategori_str or "professional" in kategori_str:
            base_at_cost = qty_val * unit_price * (percent_val / 100.0)
            fee_15 = base_at_cost * 0.15
            total_item = base_at_cost * 1.15
            # Breakdown gabungan di kolom Unit Price
            unit_price_display = f"Rp {base_at_cost:,.2f}<br><span style='font-size: 8px; font-weight: normal; color: #334155;'>+ 15% Fee (Rp {fee_15:,.2f})</span>"
            kategori_display = kategori_awal
        elif "estimated" in kategori_str or "estimasi" in kategori_str:
            total_item = (qty_val * unit_price * 0.9) * (percent_val / 100.0)
            harga_diskon_val = unit_price * 0.9
            kategori_display = f"{kategori_awal}<br><span style='font-size: 8.5px; font-weight: normal; color: #334155; line-height: 1.2; display: inline-block; margin-top: 3px;'>(Diskon 10% dari harga penawaran Rp {unit_price:,.2f} menjadi Rp {harga_diskon_val:,.2f})</span>"
            unit_price_display = f"{unit_price:,.2f}"
        else:
            total_item = (qty_val * unit_price) * (percent_val / 100.0)
            unit_price_display = f"{unit_price:,.2f}"
            kategori_display = kategori_awal

        desc_text = f"<b>{kategori_display}</b><br>{m.get('Deskripsi Pekerjaan', '-')}"
        if m.get('Keterangan'):
            desc_text += f"<br><span style='font-size: 10px; color: #334155;'>{m.get('Keterangan')}</span>"
        
        unit_val = str(m.get('Unit', 'Unit'))

        rows_html += f"""
            <tr>
                <td style="text-align: center;">{idx}</td>
                <td>{desc_text}</td>
                <td style="text-align: center;">{qty_val:,.2f}</td>
                <td style="text-align: center;">{unit_val}</td>
                <td style="text-align: right;">{unit_price_display}</td>
                <td style="text-align: right;">{total_item:,.2f}</td>
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
                    size: A4;
                    margin: 5mm 10mm 5mm 10mm;
                }}
            }}
            body {{ font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; padding: 15px; margin: 0; font-size: 11px; }}
            .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 8px; margin-bottom: 15px; }}
            .header-title {{ font-size: 15px; font-weight: bold; margin-bottom: 15px; text-transform: uppercase; text-align: center; }}
            table.two-col {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; border: none; }}
            table.two-col td {{ border: none; padding: 2px 0; vertical-align: top; font-size: 11px; }}
            table.data-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 0px; }}
            table.data-table th, table.data-table td {{ border: 1px solid #333; padding: 6px 8px; font-size: 11px; text-align: left; }}
            table.data-table th {{ background-color: #f1f5f9; text-align: center; vertical-align: middle; }}
            
            .total-row td {{
                font-weight: bold;
                background-color: #f8fafc;
                font-size: 11.5px;
            }}
            
            .terbilang-box {{
                margin-top: 8px;
                margin-bottom: 15px;
                font-size: 11px;
            }}

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
                            <td style="border: none;">{tanggal_pi_bersih}</td>
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
                <th style="width: 6%;">Item</th>
                <th style="width: 42%;">Description</th>
                <th style="width: 10%;">Qty</th>
                <th style="width: 10%;">Satuan</th>
                <th style="width: 16%;">Unit Price<br><span style="font-size: 8.5px; font-weight: normal;">(IDR)</span></th>
                <th style="width: 16%;">TOTAL<br><span style="font-size: 8.5px; font-weight: normal;">(IDR)</span></th>
            </tr>
            {rows_html}
            <tr class="total-row">
                <td colspan="5" style="text-align: right; text-transform: uppercase;">GRAND TOTAL :</td>
                <td style="text-align: right;">{grand_total_pi:,.2f}</td>
            </tr>
        </table>

        <div class="terbilang-box">
            <b>Terbilang :</b> <i>{terbilang_str}</i>
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
                    <div class="bank-section" style="margin-top: 20px; text-align: center; display: inline-block; min-width: 220px;">
                        <b>{nama_pt_sign}</b><br>
                        {ttd_html_element}
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
                    win.document.open();
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