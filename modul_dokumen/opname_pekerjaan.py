import streamlit as st
import pandas as pd
import os
import base64

def terbilang(n):
    n = float(n)
    if n < 0:
        return "minus " + terbilang(-n)
    n_bulat = int(n)
    if n_bulat == 0:
        return "Nol Rupiah"
        
    satuan = ["", "Satu", "Dua", "Tiga", "Empat", "Lima", "Enam", "Tujuh", "Delapan", "Sembilan", "Sepuluh", "Sebelas"]
    def helper(num):
        if num < 12:
            return " " + satuan[num]
        elif num < 20:
            return helper(num - 10) + " Belas"
        elif num < 100:
            return helper(num // 10) + " Puluh" + helper(num % 10)
        elif num < 200:
            return " Seratus" + helper(num - 100)
        elif num < 1000:
            return helper(num // 100) + " Ratus" + helper(num % 100)
        elif num < 2000:
            return " Seribu" + helper(num - 1000)
        elif num < 1000000:
            return helper(num // 1000) + " Ribu" + helper(num % 1000)
        elif num < 1000000000:
            return helper(num // 1000000) + " Juta" + helper(num % 1000000)
        elif num < 1000000000000:
            return helper(num // 1000000000) + " Miliar" + helper(num % 1000000000)
        else:
            return " Angka terlalu besar"
            
    return helper(n_bulat).strip() + " Rupiah"

def tampilkan_opname(transaksi_list):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📋 Pratinjau, Cetak & Download Berita Acara Opname Pekerjaan</h3>
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
        selected_idx = st.selectbox("Pilih Dokumen Transaksi Tersimpan:", range(len(pilihan_tx)), format_func=lambda x: pilihan_tx[x], key="opname_sel_idx")
    with col_sel2:
        lokasi_office = st.text_input("📍 Lokasi Office (Tempat Opname):", value="Paisubololi", key="opname_lok_office")

    t_data = unique_tx_list[selected_idx]
    pi_sekarang = str(t_data.get('PI No.', '')).strip()

    # MENARIK DATA AKTUAL QTY DAN TOTAL PERSIS SEPERTI MODUL BASTP (MENYARING SELURUH ITEM MATCHING)
    actual_qty = 1.0
    actual_total_harga = float(t_data.get('Total Harga', 0.0))
    actual_unit = str(t_data.get('Unit', 'Day'))

    matching_items = [item for item in transaksi_list if str(item.get('PI No.', '')).strip() == pi_sekarang]
    if matching_items:
        # Mengambil baris rincian yang memiliki Qty terbesar/aktual persis seperti BASTP
        best_item = max(matching_items, key=lambda x: float(x.get('Qty', x.get('Quantity', 1))))
        actual_qty = float(best_item.get('Qty', best_item.get('Quantity', 1.0)))
        actual_total_harga = float(best_item.get('Total Harga', actual_total_harga))
        actual_unit = str(best_item.get('Unit', actual_unit))

    # PEMECAHAN DATA PRESISI DARI DATABASE EXCEL UTAMA (INDEKS KOLOM)
    db_invoice_path = os.path.join("database_penyimpanan_aman", "database_proforma_invoice.xlsx")
    matched_db_row = {}
    row_values = []
    
    wo_no = "DATA WO BELUM DIINPUT"
    ctr_no = "DATA CTR BELUM DIINPUT"
    
    if os.path.exists(db_invoice_path):
        try:
            df_inv = pd.read_excel(db_invoice_path)
            for idx, row in df_inv.iterrows():
                val_pi_0 = str(row.iloc[0]).strip().lower()
                if val_pi_0 == pi_sekarang.lower():
                    matched_db_row = row.to_dict()
                    row_values = row.values.tolist()
                    break
        except:
            pass

    # Ambil Nomor WO (indeks 21) dan CTR (indeks 23) secara presisi
    if len(row_values) > 21 and pd.notnull(row_values[21]) and str(row_values[21]).strip() != "":
        wo_no = str(row_values[21])
    else:
        wo_no = str(matched_db_row.get('Nomor WO', t_data.get('Nomor Kontrak', '') + '-BSS-WO-2026'))

    if len(row_values) > 23 and pd.notnull(row_values[23]) and str(row_values[23]).strip() != "":
        ctr_no = str(row_values[23])
    else:
        ctr_no = str(matched_db_row.get('Nomor CTR', t_data.get('Nomor Kontrak', '') + '-BSS-CTR-2026'))

    st.markdown("#### ⚙️ Pengaturan Parameter PO & Opname (Membaca Data Aktual)")
    
    default_po_vol = 3.0
    
    c_p1, c_p2, c_p3, c_p4 = st.columns(4)
    with c_p1:
        po_volume = st.number_input("📦 Volume Total (PO):", value=default_po_vol, step=0.1, format="%.2f", key="opn_po_vol")
    with c_p2:
        unit_price = st.number_input("💵 Unit Price / Harga Satuan (Rp):", value=actual_total_harga / actual_qty if actual_qty > 0 else 0.0, step=1000.0, format="%.2f", key="opn_unit_price")
    with c_p3:
        prev_vol = st.number_input("📉 Volume Lalu (Previous):", value=0.0, step=0.1, format="%.2f", key="opn_prev_vol")
    with c_p4:
        # Volume aktual bulan ini membaca langsung angka aktual dari rincian (misal: 23.00)
        current_vol = st.number_input("📈 Volume Aktual (Bulan Ini - Qty):", value=actual_qty, step=1.0, format="%.2f", key="opn_curr_vol")

    # --- TOMBOL UPLOAD LOGO ---
    if 'persisted_logo_1' not in st.session_state:
        st.session_state.persisted_logo_1 = None
    if 'persisted_logo_2' not in st.session_state:
        st.session_state.persisted_logo_2 = None

    st.markdown("#### 🖼️ Pengaturan Logo Header Dokumen Opname (Tersimpan Otomatis)")
    c_log1, c_log2 = st.columns(2)
    with c_log1:
        uploaded_logo_1 = st.file_uploader("Upload Logo Pihak Pertama (PT BSS)", type=["png", "jpg", "jpeg"], key="logo_opname_1_u")
        if uploaded_logo_1 is not None:
            st.session_state.persisted_logo_1 = uploaded_logo_1.getvalue()
    with c_log2:
        uploaded_logo_2 = st.file_uploader("Upload Logo Pihak Kedua / Instansi (JOB Pertamina)", type=["png", "jpg", "jpeg"], key="logo_opname_2_u")
        if uploaded_logo_2 is not None:
            st.session_state.persisted_logo_2 = uploaded_logo_2.getvalue()

    # Kalkulasi Berdasarkan Total Data Tersimpan Murni
    base_total_price = po_volume * unit_price if unit_price > 0 else actual_total_harga * 3
    prev_total = prev_vol * unit_price
    
    current_total = actual_total_harga # Mengambil nilai total harga murni dari data tersimpan
    
    cumulative_vol = prev_vol + current_vol
    cumulative_total = prev_total + current_total
    
    sisa_vol = po_volume - (current_vol / 11.0)
    sisa_total = base_total_price - cumulative_total

    opname_date = str(matched_db_row.get('Tanggal Opname', '31 Jul 2026'))
    wo_title = str(matched_db_row.get('Keterangan WO', t_data.get('Deskripsi PO', 'Jasa Sewa 2 Unit Alat Berat Forklift 5 Ton')))
    item_desc = str(matched_db_row.get('Item Deskripsi', 'Jasa Sewa Alat Berat Monthly Basis (Include Operator, Rigger, Helper, BBM & Sertifikasi)'))

    prepared_name = str(matched_db_row.get('Prepared by Name', 'Onesimus Suryadi'))
    prepared_title = str(matched_db_row.get('Prepared by Title', 'General Service Manager'))
    reviewed_name = str(matched_db_row.get('Diwakili Oleh', 'Ronny Dwi Purnomo / Rafik Hidayat'))
    approved_name = str(matched_db_row.get('Pejabat berwenang', 'Imron Maulana / Moh Bazarul Aqhsa'))
    field_mgr_title = str(matched_db_row.get('Jabatan Field Manager', 'Field Senior Manager'))

    logo1_html = f'<img src="data:image/png;base64,{base64.b64encode(st.session_state.persisted_logo_1).decode()}" style="max-height: 50px; max-width: 130px; object-fit: contain; display: block; margin: 0 auto;">' if st.session_state.persisted_logo_1 is not None else ""
    logo2_html = f'<img src="data:image/png;base64,{base64.b64encode(st.session_state.persisted_logo_2).decode()}" style="max-height: 50px; max-width: 130px; object-fit: contain; display: block; margin: 0 auto;">' if st.session_state.persisted_logo_2 is not None else ""

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Berita Acara Pekerjaan / Opname - PT BSS</title>
        <style>
            @page {{ size: A4 landscape; margin: 10mm; }}
            body {{ font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; padding: 25px; margin: 0; font-size: 10px; line-height: 1.3; }}
            .header-table {{ width: 100%; border-collapse: collapse; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 15px; }}
            .header-table td {{ border: none; vertical-align: middle; padding: 0 10px; }}
            .title-box {{ background-color: #dbeafe; border: 1px solid #000; text-align: center; font-weight: bold; font-size: 12px; padding: 6px; margin-bottom: 15px; text-transform: uppercase; }}
            .info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 10px; }}
            .info-table td {{ padding: 3px 5px; border: none; }}
            table.opname-grid {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
            table.opname-grid th, table.opname-grid td {{ border: 1px solid #000; padding: 6px 6px; font-size: 9px; vertical-align: middle; text-align: center; }}
            .th-header {{ background-color: #f1f5f9; font-weight: bold; text-transform: uppercase; }}
            .text-left {{ text-align: left !important; }}
            .text-right {{ text-align: right !important; }}
            .summary-box {{ margin-top: 10px; font-size: 11px; font-weight: bold; }}
            table.sig-table {{ width: 100%; border-collapse: collapse; margin-top: 30px; border: none; }}
            table.sig-table td {{ border: none; vertical-align: top; font-size: 10px; padding: 5px; }}
        </style>
    </head>
    <body>
        <table class="header-table">
            <tr>
                <td style="width: 22%; text-align: center;">{logo1_html}</td>
                <td style="width: 56%; text-align: center;"><h3 style="margin: 0; font-size: 12px; font-weight: bold; text-transform: uppercase;">BERITA ACARA PEKERJAAN / OPNAME</h3></td>
                <td style="width: 22%; text-align: center;">{logo2_html}</td>
            </tr>
        </table>

        <table class="info-table">
            <tr><td style="width: 18%; font-weight: bold;">JOB TITLE / WO</td><td style="width: 2%;">:</td><td style="width: 80%;"><b>{wo_title}</b></td></tr>
            <tr><td style="font-weight: bold;">CTR No. / WO No.</td><td>:</td><td>{ctr_no} / {wo_no}</td></tr>
            <tr><td style="font-weight: bold;">DATE</td><td>:</td><td>{opname_date}</td></tr>
        </table>

        <table class="opname-grid">
            <tr>
                <th rowspan="2" class="th-header" style="width: 5%;">NO</th>
                <th rowspan="2" class="th-header" style="width: 25%;">ITEM - DESCRIPTION</th>
                <th rowspan="2" class="th-header" style="width: 7%;">UOM</th>
                <th colspan="3" class="th-header" style="width: 21%;">BASE ON CTR / PO</th>
                <th colspan="2" class="th-header" style="width: 12%;">PREVIOUS OPNAME</th>
                <th colspan="2" class="th-header" style="width: 13%;">AKTUAL OPNAME (BULAN INI)</th>
                <th colspan="2" class="th-header" style="width: 13%;">CUMMULATIVE OPNAME</th>
                <th colspan="2" class="th-header" style="width: 14%;">SISA ANGGARAN (DEVIASI)</th>
            </tr>
            <tr>
                <th class="th-header">Volume</th><th class="th-header">Unit Price</th><th class="th-header">Price</th>
                <th class="th-header">Volume</th><th class="th-header">Total Price</th>
                <th class="th-header">Volume</th><th class="th-header">Total Price</th>
                <th class="th-header">Volume</th><th class="th-header">Total Price</th>
                <th class="th-header">Volume</th><th class="th-header">Total Price</th>
            </tr>
            <tr>
                <td>1.1</td>
                <td class="text-left">{item_desc}</td>
                <td>{actual_unit}</td>
                <td>{po_volume:.2f}</td>
                <td class="text-right">Rp {unit_price:,.2f}</td>
                <td class="text-right">Rp {base_total_price:,.2f}</td>
                <td>{prev_vol:.2f}</td>
                <td class="text-right">Rp {prev_total:,.2f}</td>
                <td>{current_vol:.2f}</td>
                <td class="text-right">Rp {current_total:,.2f}</td>
                <td>{cumulative_vol:.2f}</td>
                <td class="text-right">Rp {cumulative_total:,.2f}</td>
                <td>{sisa_vol:.2f}</td>
                <td class="text-right">Rp {sisa_total:,.2f}</td>
            </tr>
            <tr style="background-color: #fafafa; font-weight: bold;">
                <td colspan="3" class="text-right">TOTAL :</td>
                <td>{po_volume:.2f}</td>
                <td class="text-right">-</td>
                <td class="text-right">Rp {base_total_price:,.2f}</td>
                <td>{prev_vol:.2f}</td>
                <td class="text-right">Rp {prev_total:,.2f}</td>
                <td>{current_vol:.2f}</td>
                <td class="text-right">Rp {current_total:,.2f}</td>
                <td>{cumulative_vol:.2f}</td>
                <td class="text-right">Rp {cumulative_total:,.2f}</td>
                <td>{sisa_vol:.2f}</td>
                <td class="text-right">Rp {sisa_total:,.2f}</td>
            </tr>
        </table>

        <div class="summary-box">
            Total Akumulasi Penyerapan (Cumulative Opname): Rp {cumulative_total:,.2f}<br>
            Sisa Nilai Anggaran PO (Deviasi): Rp {sisa_total:,.2f}
        </div>

        <table class="sig-table">
            <tr>
                <td style="width: 33%; text-align: left; padding-left: 10px;">{lokasi_office}, {opname_date}<br><b>PT Banggai Sentral Sulawesi</b><br>Prepared by,<br><br><br><br><u><b>{prepared_name}</b></u><br>{prepared_title}</td>
                <td style="width: 34%; text-align: center;"><br><b>JOB Pertamina - Medco E&P Tomori Sulawesi</b><br>Reviewed by,<br><br><br><br><u><b>{reviewed_name}</b></u><br>Maintenance Support Supervisor</td>
                <td style="width: 33%; text-align: center;"><br><b>JOB Pertamina - Medco E&P Tomori Sulawesi</b><br>Approved by,<br><br><br><br><u><b>{approved_name}</b></u><br>{field_mgr_title}</td>
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
        st.components.v1.html(f'<script>function printDoc(){{var win=window.open("about:blank","_blank");win.document.write(atob("{b64_html}"));win.document.close();win.print();}}</script><button onclick="printDoc()" style="width: 100%; background-color: #10b981; color: white; padding: 10px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">🖨️ Cetak Dokumen Opname</button>', height=50)
    with col_btn2:
        b64_pdf = base64.b64encode(html_content.encode()).decode()
        st.markdown(f'<a href="data:text/html;base64,{b64_pdf}" download="Opname_{pi_sekarang.replace("/", "-")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download File Opname</button></a>', unsafe_allow_html=True)