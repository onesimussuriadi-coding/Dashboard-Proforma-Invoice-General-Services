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

# FUNGSI BANTUAN FORMAT TANGGAL KONSISTEN VERSI INDONESIA (DD MMM YYYY)
def format_tanggal_indo(tanggal_str):
    if not tanggal_str or str(tanggal_str).strip() in ["-", "nan", "None"]:
        return "-"
    clean_str = str(tanggal_str).strip().split()[0]
    for fmt in ("%Y-%m-%d", "%d %b %Y", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            dt_obj = datetime.strptime(clean_str, fmt)
            return dt_obj.strftime("%d %b %Y")
        except:
            continue
    return str(tanggal_str)

def tampilkan_rincian_pekerjaan(transaksi_list):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">🖨️ Pratinjau, Cetak & Download Dokumen Rincian Pekerjaan</h3>
        </div>
    """, unsafe_allow_html=True)

    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi rincian pekerjaan yang diproses.")
        return

    # --- DIREKTORI PENYIMPANAN EXCEL RINCIAN PEKERJAAN ---
    DIR_DATABASE_RINCIAN = os.path.join("database_penyimpanan_aman")
    if not os.path.exists(DIR_DATABASE_RINCIAN):
        os.makedirs(DIR_DATABASE_RINCIAN)
    EXCEL_FILE_RINCIAN = os.path.join(DIR_DATABASE_RINCIAN, "database_rincian_pekerjaan_tersimpan.xlsx")

    def muat_database_rincian_excel():
        if os.path.exists(EXCEL_FILE_RINCIAN):
            try:
                df = pd.read_excel(EXCEL_FILE_RINCIAN)
                if df is not None and not df.empty:
                    return df.to_dict(orient="records")
            except:
                pass
        return []

    def simpan_database_rincian_excel(list_data_rekaman):
        try:
            df_save = pd.DataFrame(list_data_rekaman)
            df_save.to_excel(EXCEL_FILE_RINCIAN, index=False)
            return True
        except Exception as e:
            st.error(f"Gagal menyimpan ke Excel: {e}")
            return False

    seen_pi_dd = set()
    unique_pi_list = []
    for t in transaksi_list:
        pi_key = str(t.get('PI No.', '')).strip()
        if pi_key and pi_key not in seen_pi_dd:
            seen_pi_dd.add(pi_key)
            unique_pi_list.append(t)

    pilihan_tx = [f"PI: {t.get('PI No.', '')} | Kontrak: {t.get('Nomor Kontrak', '')}" for t in unique_pi_list]
    
    if "rincian_saved_data" not in st.session_state:
        st.session_state.rincian_saved_data = {}

    selected_idx = st.selectbox("Pilih Dokumen Transaksi Tersimpan:", range(len(pilihan_tx)), format_func=lambda x: pilihan_tx[x], key="rincian_sel_idx")
    
    t_data_ref = unique_pi_list[selected_idx]
    current_pi_no = str(t_data_ref.get('PI No.', '')).strip()

    if current_pi_no not in st.session_state.rincian_saved_data:
        st.session_state.rincian_saved_data[current_pi_no] = {
            'sig_dibuat': None,
            'sig_diperiksa': None
        }

    saved_rincian_item = st.session_state.rincian_saved_data[current_pi_no]

    st.markdown("#### ✍️ Pengaturan Tanda Tangan Dokumen")
    col_sig1, col_sig2 = st.columns(2)
    
    with col_sig1:
        uploaded_sig_dibuat = st.file_uploader("Upload Gambar Tanda Tangan (DIBUAT OLEH)", type=["png", "jpg", "jpeg"], key=f"sig_dibuat_{current_pi_no}")
        if saved_rincian_item.get('sig_dibuat') is not None:
            if st.button("🗑️ Hapus Tanda Tangan Dibuat Oleh", key=f"btn_del_sig1_{current_pi_no}"):
                saved_rincian_item['sig_dibuat'] = None
                st.success("✅ Tanda Tangan Dibuat Oleh berhasil dihapus!")
                st.rerun()

    with col_sig2:
        uploaded_sig_diperiksa = st.file_uploader("Upload Gambar Tanda Tangan (DIPERIKSA)", type=["png", "jpg", "jpeg"], key=f"sig_diperiksa_{current_pi_no}")
        if saved_rincian_item.get('sig_diperiksa') is not None:
            if st.button("🗑️ Hapus Tanda Tangan Diperiksa", key=f"btn_del_sig2_{current_pi_no}"):
                saved_rincian_item['sig_diperiksa'] = None
                st.success("✅ Tanda Tangan Diperiksa berhasil dihapus!")
                st.rerun()

    with st.form(key=f"form_rincian_sig_{current_pi_no}"):
        st.markdown(f"**Konfirmasi Rincian Pekerjaan (PI: {current_pi_no}):** Klik tombol di bawah untuk mengunci konfigurasi dan menyimpan ke database Excel.")
        submit_save_rincian = st.form_submit_button("💾 Simpan & Kunci Dokumen Rincian Pekerjaan Ini", type="primary")
        
        if submit_save_rincian:
            sig1_final = uploaded_sig_dibuat.getvalue() if uploaded_sig_dibuat is not None else saved_rincian_item.get('sig_dibuat')
            sig2_final = uploaded_sig_diperiksa.getvalue() if uploaded_sig_diperiksa is not None else saved_rincian_item.get('sig_diperiksa')

            st.session_state.rincian_saved_data[current_pi_no] = {
                'sig_dibuat': sig1_final,
                'sig_diperiksa': sig2_final
            }

            # --- PROSES SIMPAN OTOMATIS KE FILE EXCEL HISTORI ---
            matching_mutasi_to_save = [item for item in transaksi_list if str(item.get('PI No.', '')).strip() == current_pi_no]
            existing_excel_records = muat_database_rincian_excel()
            
            # Hapus data lama dengan PI yang sama agar tidak duplikat
            filtered_existing = [r for r in existing_excel_records if str(r.get('PI No.', '')).strip() != current_pi_no]
            
            waktu_simpan_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for m in matching_mutasi_to_save:
                rekaman_baris = {
                    "Waktu Simpan": waktu_simpan_str,
                    "Nomor Kontrak": str(t_data_ref.get('Nomor Kontrak', '')),
                    "PI No.": current_pi_no,
                    "Nomor PO": str(t_data_ref.get('Nomor PO', '')),
                    "Kategori": m.get('Kategori', ''),
                    "Uraian Pekerjaan": m.get('Deskripsi Pekerjaan', ''),
                    "Qty": float(m.get('Qty', 0.0)),
                    "Satuan": m.get('Unit', ''),
                    "Tanggal Mulai": format_tanggal_indo(m.get('Tanggal Mulai', '')),
                    "Tanggal Selesai": format_tanggal_indo(m.get('Tanggal Selesai', '')),
                    "Harga Satuan (IDR)": float(m.get('Harga Satuan', 0.0)),
                    "Percent (%)": float(m.get('Percent', 100.0)),
                    "Keterangan": m.get('Keterangan', '-')
                }
                filtered_existing.append(rekaman_baris)

            if simpan_database_rincian_excel(filtered_existing):
                st.success(f"✅ Sukses! Data rincian pekerjaan untuk PI [{current_pi_no}] berhasil disimpan ke file Excel histori (`database_rincian_pekerjaan_tersimpan.xlsx`) dan dikunci secara permanen!")
            else:
                st.warning("⚠️ Konfigurasi terkunci di sesi, tetapi gagal menulis ke file Excel.")

    sig_dibuat_bytes = saved_rincian_item.get('sig_dibuat', None)
    sig_diperiksa_bytes = saved_rincian_item.get('sig_diperiksa', None)

    img_style = "max-height: 75px; max-width: 200px; object-fit: contain;"
    
    if sig_dibuat_bytes is not None:
        b64_sig = base64.b64encode(sig_dibuat_bytes).decode()
        sig_dibuat_html = f'<div style="margin: 4px auto; height: 75px; display: flex; align-items: center; justify-content: center;"><img src="data:image/png;base64,{b64_sig}" style="{img_style}"></div>'
    else:
        sig_dibuat_html = '<div style="height: 60px;"></div>'

    if sig_diperiksa_bytes is not None:
        b64_sig_2 = base64.b64encode(sig_diperiksa_bytes).decode()
        sig_diperiksa_html = f'<div style="margin: 4px auto; height: 75px; display: flex; align-items: center; justify-content: center;"><img src="data:image/png;base64,{b64_sig_2}" style="{img_style}"></div>'
    else:
        sig_diperiksa_html = '<div style="height: 60px;"></div>'

    matching_mutasi_list = [item for item in transaksi_list if str(item.get('PI No.', '')).strip() == current_pi_no]

    grand_total = 0.0
    for m in matching_mutasi_list:
        kategori_str = str(m.get('Kategori', '')).lower()
        qty_val = float(m.get('Qty', 0))
        harga_satuan_val = float(m.get('Harga Satuan', 0))
        percent_val = float(m.get('Percent', 100.0))

        if "provisional" in kategori_str or "professional" in kategori_str:
            tot_val = (qty_val * harga_satuan_val) * 1.15 * (percent_val / 100.0)
        elif "estimated" in kategori_str or "estimasi" in kategori_str:
            tot_val = (qty_val * harga_satuan_val * 0.9) * (percent_val / 100.0)
        else:
            tot_val = (qty_val * harga_satuan_val) * (percent_val / 100.0)
        grand_total += tot_val

    try:
        from __main__ import muat_data_invoice
        saved_db_induk = muat_data_invoice()
    except:
        try:
            import os
            df_induk = pd.read_excel(os.path.join("database_penyimpanan_aman", "database_proforma_invoice.xlsx"))
            saved_db_induk = df_induk.to_dict(orient="records")
        except:
            saved_db_induk = []

    matched_item = {}
    for item in saved_db_induk:
        if isinstance(item, dict):
            val_pi_0 = str(item.get(0, item.get('Proforma Invoice No.', ''))).strip().lower()
            if val_pi_0 == current_pi_no.lower():
                matched_item = item
                break

    def get_induk(idx_num, text_key, fallback="-"):
        if idx_num in matched_item:
            v = matched_item[idx_num]
            if v is not None and str(v).strip() != "" and str(v).strip().lower() != "nan":
                return str(v).strip()
        if text_key in matched_item:
            v = matched_item[text_key]
            if v is not None and str(v).strip() != "" and str(v).strip().lower() != "nan":
                return str(v).strip()
        return fallback

    nomor_wcc_full = get_induk(19, 'Nomor WCC', f"{t_data_ref.get('Nomor Kontrak', '')}-BSS-WCC-2026")
    terbilang_str = terbilang(grand_total).strip() + " Rupiah"

    rows_html = ""
    for idx, m in enumerate(matching_mutasi_list, start=1):
        kategori_str = str(m.get('Kategori', '')).lower()
        qty_val = float(m.get('Qty', 0))
        harga_satuan_val = float(m.get('Harga Satuan', 0))
        percent_val = float(m.get('Percent', 100.0))
        kategori_awal = str(m.get('Kategori', '-'))
        keterangan_murni = str(m.get('Keterangan', '-'))

        tgl_mulai_formatted = format_tanggal_indo(m.get('Tanggal Mulai', '-'))
        tgl_selesai_formatted = format_tanggal_indo(m.get('Tanggal Selesai', '-'))

        if "estimated" in kategori_str or "estimasi" in kategori_str:
            total_harga_val = (qty_val * harga_satuan_val * 0.9) * (percent_val / 100.0)
            harga_diskon_val = harga_satuan_val * 0.9
            kategori_display = f"{kategori_awal}<br><span style='font-size: 8px; font-weight: normal; color: #334155; line-height: 1.2; display: inline-block; margin-top: 3px;'>(Diskon 10% dari harga penawaran Rp {harga_satuan_val:,.2f} menjadi Rp {harga_diskon_val:,.2f})</span>"
        elif "provisional" in kategori_str or "professional" in kategori_str:
            total_harga_val = (qty_val * harga_satuan_val) * 1.15 * (percent_val / 100.0)
            kategori_display = kategori_awal
        else:
            total_harga_val = (qty_val * harga_satuan_val) * (percent_val / 100.0)
            kategori_display = kategori_awal

        rows_html += f"""
            <tr>
                <td style="text-align: center;">{idx}</td>
                <td>{kategori_display}</td>
                <td>{m.get('Deskripsi Pekerjaan', '-')}</td>
                <td style="text-align: center;">{qty_val:,.2f}</td>
                <td style="text-align: center;">{m.get('Unit', '-')}</td>
                <td style="text-align: center; white-space: nowrap;">{tgl_mulai_formatted}</td>
                <td style="text-align: center; white-space: nowrap;">{tgl_selesai_formatted}</td>
                <td style="text-align: right;">{harga_satuan_val:,.2f}</td>
                <td style="text-align: right;">{total_harga_val:,.2f}</td>
                <td>{keterangan_murni}</td>
            </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4 landscape;
                margin: 6mm;
            }}
            @media print {{
                html, body {{
                    width: 297mm;
                    height: 210mm;
                    margin: 0 !important;
                    padding: 6mm !important;
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
                padding: 6mm;
                margin: 0;
                font-size: 10px;
                line-height: 1.3;
            }}
            .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 6mm; margin-bottom: 10px; }}
            .title {{ text-align: center; font-weight: bold; font-size: 13px; margin-bottom: 12px; text-transform: uppercase; text-decoration: underline; }}
            table.info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; border: none; }}
            table.info-table td {{ border: none; padding: 3px 5px; font-size: 10px; vertical-align: top; }}
            .label-col {{ width: 140px; font-weight: bold; }}
            .colon-col {{ width: 10px; font-weight: bold; text-align: center; }}
            table.data-table {{ width: 100%; border-collapse: collapse; margin-top: 6mm; margin-bottom: 0px; }}
            table.data-table th, table.data-table td {{ border: 1px solid #333; padding: 6px 8px; font-size: 9.5px; text-align: left; }}
            table.data-table th {{ background-color: #f1f5f9; text-align: center; vertical-align: middle; }}
            
            .total-row td {{
                font-weight: bold;
                background-color: #f8fafc;
                font-size: 10.5px;
            }}
            
            .terbilang-box {{
                margin-top: 8px;
                margin-bottom: 15px;
                font-size: 10px;
            }}

            .sign-table {{ border: none; width: 100%; margin-top: 15px; page-break-inside: avoid; }}
            .sign-table td {{ border: none; text-align: center; width: 50%; font-size: 9.5px; vertical-align: top; }}
            .sign-title {{ font-weight: bold; font-size: 9.5px; text-transform: uppercase; margin-bottom: 8px; }}
            .sign-name {{ font-weight: bold; font-size: 9.5px; text-decoration: underline; margin-top: 4px; }}
            .sign-pos {{ font-size: 8.5px; margin-top: 2px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2 style="margin: 0; font-size: 14px;">PT. BANGGAI SENTRAL SULAWESI</h2>
            <p style="margin: 2px 0; font-size: 8px;">General Contractor and Suppliers | Jl. Urip Sumoharjo No. 53 Luwuk, Kabupaten Banggai, Propinsi Sulawesi Tengah</p>
        </div>
        <div class="title">Rincian Pekerjaan</div>
        
        <table class="info-table">
            <tr>
                <td class="label-col">Rincian Pekerjaan</td>
                <td class="colon-col">:</td>
                <td><b>{nomor_wcc_full}</b></td>
                <td class="label-col">Ditujukan Kepada</td>
                <td class="colon-col">:</td>
                <td>{t_data_ref.get('Ditujukan Kepada', '')}</td>
            </tr>
            <tr>
                <td class="label-col">Nomor Kontrak</td>
                <td class="colon-col">:</td>
                <td>{t_data_ref.get('Nomor Kontrak', '')}</td>
                <td class="label-col">Nomor Purchase Order</td>
                <td class="colon-col">:</td>
                <td>{t_data_ref.get('Nomor PO', '')}</td>
            </tr>
            <tr>
                <td class="label-col">Nama Kontrak</td>
                <td class="colon-col">:</td>
                <td>{t_data_ref.get('Nama Kontrak', '')}</td>
                <td class="label-col">Lingkup Pekerjaan</td>
                <td class="colon-col">:</td>
                <td>{t_data_ref.get('Deskripsi PO', '')}</td>
            </tr>
            <tr>
                <td class="label-col">Nomor Tender</td>
                <td class="colon-col">:</td>
                <td>{t_data_ref.get('Nomor Tender', '')}</td>
                <td class="label-col">Tanggal Purchase Order</td>
                <td class="colon-col">:</td>
                <td>{format_tanggal_indo(t_data_ref.get('Tanggal PO', ''))}</td>
            </tr>
            <tr>
                <td class="label-col">Tanggal Proforma</td>
                <td class="colon-col">:</td>
                <td>{format_tanggal_indo(t_data_ref.get('Tanggal PI', ''))}</td>
                <td class="label-col">Mata Uang</td>
                <td class="colon-col">:</td>
                <td>{t_data_ref.get('Mata Uang', 'IDR')}</td>
            </tr>
        </table>
        
        <table class="data-table">
            <tr>
                <th>No.</th>
                <th>Kategori</th>
                <th>Uraian Pekerjaan</th>
                <th>Qty</th>
                <th>Satuan</th>
                <th>Tanggal Mulai</th>
                <th>Tanggal Selesai</th>
                <th>Harga Satuan<br><span style="font-size: 8px; font-weight: normal;">(IDR)</span></th>
                <th>Total Harga<br><span style="font-size: 8px; font-weight: normal;">(IDR)</span></th>
                <th>Keterangan</th>
            </tr>
            {rows_html}
            <tr class="total-row">
                <td colspan="8" style="text-align: right; text-transform: uppercase;">TOTAL TAGIHAN :</td>
                <td style="text-align: right;">{grand_total:,.2f}</td>
                <td></td>
            </tr>
        </table>
        
        <div class="terbilang-box">
            <b>Terbilang :</b> <i>{terbilang_str}</i>
        </div>
        
        <table class="sign-table">
            <tr>
                <td>
                    <div class="sign-title">DIBUAT OLEH</div>
                    {sig_dibuat_html}
                    <div class="sign-name">Yanuar Wiranata / Ireine Langi</div>
                    <div class="sign-pos">Supervisor</div>
                </td>
                <td>
                    <div class="sign-title">DIPERIKSA</div>
                    {sig_diperiksa_html}
                    <div class="sign-name">Onesimus Suriadi</div>
                    <div class="sign-pos">Manager General Services</div>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    st.markdown('<div class="document-preview">', unsafe_allow_html=True)
    st.components.v1.html(html_content, height=580, scrolling=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        b64_html = base64.b64encode(html_content.encode()).decode()
        print_script = f"""
            <script>
                function printDoc() {{
                    var win = window.open('about:blank', '_blank');
                    win.document.open();
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
        download_link = f'<a href="data:text/html;base64,{b64_pdf}" download="Rincian_Pekerjaan_{current_pi_no.replace("/", "-")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download Dokumen</button></a>'
        st.markdown(download_link, unsafe_allow_html=True)