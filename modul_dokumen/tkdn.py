import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime, date
import json

def tampilkan_tkdn(transaksi_list):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📋 Pratinjau, Cetak & Download Formulir TKDN (Permen ESDM No. 15 Tahun 2013)</h3>
        </div>
    """, unsafe_allow_html=True)

    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi rincian pekerjaan yang diproses.")
        return

    # Inisialisasi direktori penyimpanan permanen
    DIR_TKDN_SAVED = os.path.join("database_penyimpanan_aman", "tkdn_tersimpan")
    if not os.path.exists(DIR_TKDN_SAVED):
        os.makedirs(DIR_TKDN_SAVED)

    # Saring transaksi berdasarkan PI No. yang unik agar grand total per PI akurat
    pi_dict_map = {}
    for t in transaksi_list:
        pi_key = str(t.get('PI No.', '')).strip()
        if pi_key:
            if pi_key not in pi_dict_map:
                pi_dict_map[pi_key] = {
                    'pi_no': pi_key,
                    'nomor_kontrak': t.get('Nomor Kontrak', ''),
                    'total_harga': 0.0,
                    'first_tx': t
                }
            pi_dict_map[pi_key]['total_harga'] += float(t.get('Total Harga', 0.0))

    unique_pi_list = list(pi_dict_map.keys())
    if not unique_pi_list:
        st.warning("⚠️ Tidak ada nomor Proforma Invoice (PI) yang valid ditemukan.")
        return

    pilihan_dropdown = []
    for pi_k in unique_pi_list:
        info = pi_dict_map[pi_k]
        pilihan_dropdown.append(f"PI: {pi_k} | Kontrak: {info['nomor_kontrak']} | Total: Rp {info['total_harga']:,.0f}")

    selected_idx = st.selectbox("Pilih Dokumen Transaksi Berdasarkan PI:", range(len(pilihan_dropdown)), format_func=lambda x: pilihan_dropdown[x], key="tkdn_select_pi_dropdown")

    selected_pi_key = unique_pi_list[selected_idx]
    pi_data_group = pi_dict_map[selected_pi_key]
    t_data = pi_data_group['first_tx']
    aktual_total_tagihan = pi_data_group['total_harga']

    db_invoice_path = os.path.join("database_penyimpanan_aman", "database_proforma_invoice.xlsx")
    matched_db_row = {}
    if os.path.exists(db_invoice_path):
        try:
            df_inv = pd.read_excel(db_invoice_path)
            row_match = df_inv[df_inv.iloc[:, 0].astype(str).str.strip() == selected_pi_key]
            if not row_match.empty:
                matched_db_row = row_match.iloc[0].to_dict()
        except:
            pass

    # --- INISIALISASI & MUAT DATA PERMANEN DARI DISK (JSON) ---
    tkdn_file_path = os.path.join(DIR_TKDN_SAVED, f"tkdn_{selected_pi_key.replace('/', '_')}.json")
    
    if 'tkdn_saved_data' not in st.session_state:
        st.session_state.tkdn_saved_data = {}

    # Jika file json permanen ada di disk, muat ke session_state jika belum ada
    if selected_pi_key not in st.session_state.tkdn_saved_data:
        if os.path.exists(tkdn_file_path):
            try:
                with open(tkdn_file_path, "r", encoding="utf-8") as f:
                    loaded_json = json.load(f)
                    # Konversi string tanggal kembali ke date object jika ada
                    if 'tanggal_dokumen' in loaded_json:
                        try:
                            loaded_json['tanggal_dokumen'] = datetime.strptime(loaded_json['tanggal_dokumen'], "%Y-%m-%d").date()
                        except:
                            loaded_json['tanggal_dokumen'] = date.today()
                    st.session_state.tkdn_saved_data[selected_pi_key] = loaded_json
            except:
                pass

    # Jika masih belum ada juga, gunakan default awal
    if selected_pi_key not in st.session_state.tkdn_saved_data:
        st.session_state.tkdn_saved_data[selected_pi_key] = {
            'lokasi_office': "Luwuk",
            'tanggal_dokumen': date.today(),
            'nama_direktur': "Ir. Ferry Tatimu",
            'total_tagihan': aktual_total_tagihan,
            'p_kdn_1': 15.09, 'p_kln_1': 1.51,
            'p_kdn_2': 28.26, 'p_kln_2': 0.0,
            'p_kdn_3': 47.18, 'p_kln_3': 1.51,
            'p_kdn_4': 1.55, 'p_kln_4': 0.0,
            'p_non_cost': 4.89,
            'ttd_direktur': None
        }
    else:
        saved_tagihan = st.session_state.tkdn_saved_data[selected_pi_key].get('total_tagihan', 0.0)
        if saved_tagihan <= 3200000.0 or abs(saved_tagihan - aktual_total_tagihan) > 1.0:
            st.session_state.tkdn_saved_data[selected_pi_key]['total_tagihan'] = aktual_total_tagihan

    saved_tkdn = st.session_state.tkdn_saved_data[selected_pi_key]
    
    default_rujukan_tagihan = float(saved_tkdn.get('total_tagihan', aktual_total_tagihan))
    if default_rujukan_tagihan <= 3200000.0:
        default_rujukan_tagihan = aktual_total_tagihan

    # Form khusus untuk menyimpan dan mengunci parameter
    with st.form(key=f"form_tkdn_save_{selected_pi_key}"):
        st.markdown("#### ⚙️ Pengaturan Parameter & Rujukan Perhitungan TKDN")
        
        c_master1, c_master2, c_master3, c_master4 = st.columns(4)
        with c_master1:
            lokasi_office = st.text_input("📍 Lokasi Office:", value=str(saved_tkdn.get('lokasi_office', 'Luwuk')), key=f"tkdn_lok_{selected_pi_key}")
        with c_master2:
            selected_date_tkdn = st.date_input("📅 Tanggal Dokumen:", value=saved_tkdn.get('tanggal_dokumen', date.today()), key=f"tkdn_date_{selected_pi_key}")
        with c_master3:
            total_tagihan_rujukan = st.number_input("💰 Rujukan Total Tagihan (Rp):", value=default_rujukan_tagihan, step=100000.0, key=f"master_tagihan_{selected_pi_key}")
        with c_master4:
            nama_direktur = st.text_input("Nama Direktur:", value=str(saved_tkdn.get('nama_direktur', 'Ir. Ferry Tatimu')), key=f"tkdn_dir_{selected_pi_key}")

        st.markdown("---")
        st.markdown("#### 🧮 Rincian Komponen Biaya & Non-Biaya (Berbasis Persentase)")
        st.info("💡 Masukkan persentase (%) untuk setiap komponen. Nilai nominal dihitung otomatis dari Rujukan Total Tagihan.")

        # --- I. BIAYA BAHAN ---
        st.markdown("**I. Biaya Bahan (Material)**")
        c_b1, c_b2 = st.columns(2)
        with c_b1:
            p_kdn_1 = st.number_input("Persentase KDN Bahan (%):", value=float(saved_tkdn.get('p_kdn_1', 15.09)), step=0.01, format="%.2f", key=f"input_p_kdn_1_{selected_pi_key}")
            temp_kdn_1 = (p_kdn_1 / 100.0) * total_tagihan_rujukan
            st.caption(f"-> Nilai KDN: Rp {temp_kdn_1:,.2f}")
        with c_b2:
            p_kln_1 = st.number_input("Persentase KLN Bahan (%):", value=float(saved_tkdn.get('p_kln_1', 1.51)), step=0.01, format="%.2f", key=f"input_p_kln_1_{selected_pi_key}")
            temp_kln_1 = (p_kln_1 / 100.0) * total_tagihan_rujukan
            st.caption(f"-> Nilai KLN: Rp {temp_kln_1:,.2f}")

        st.markdown("---")

        # --- II. BIAYA TENAGA KERJA ---
        st.markdown("**II. Biaya Tenaga Kerja & Konsultan**")
        c_t1, c_t2 = st.columns(2)
        with c_t1:
            p_kdn_2 = st.number_input("Persentase KDN Tenaga Kerja (%):", value=float(saved_tkdn.get('p_kdn_2', 28.26)), step=0.01, format="%.2f", key=f"input_p_kdn_2_{selected_pi_key}")
            temp_kdn_2 = (p_kdn_2 / 100.0) * total_tagihan_rujukan
            st.caption(f"-> Nilai KDN: Rp {temp_kdn_2:,.2f}")
        with c_t2:
            p_kln_2 = st.number_input("Persentase KLN Tenaga Kerja (%):", value=float(saved_tkdn.get('p_kln_2', 0.0)), step=0.01, format="%.2f", key=f"input_p_kln_2_{selected_pi_key}")
            temp_kln_2 = (p_kln_2 / 100.0) * total_tagihan_rujukan
            st.caption(f"-> Nilai KLN: Rp {temp_kln_2:,.2f}")

        st.markdown("---")

        # --- III. BIAYA ALAT KERJA ---
        st.markdown("**III. Biaya Alat Kerja / Fasilitas Kerja**")
        c_a1, c_a2 = st.columns(2)
        with c_a1:
            p_kdn_3 = st.number_input("Persentase KDN Alat Kerja (%):", value=float(saved_tkdn.get('p_kdn_3', 47.18)), step=0.01, format="%.2f", key=f"input_p_kdn_3_{selected_pi_key}")
            temp_kdn_3 = (p_kdn_3 / 100.0) * total_tagihan_rujukan
            st.caption(f"-> Nilai KDN: Rp {temp_kdn_3:,.2f}")
        with c_a2:
            p_kln_3 = st.number_input("Persentase KLN Alat Kerja (%):", value=float(saved_tkdn.get('p_kln_3', 1.51)), step=0.01, format="%.2f", key=f"input_p_kln_3_{selected_pi_key}")
            temp_kln_3 = (p_kln_3 / 100.0) * total_tagihan_rujukan
            st.caption(f"-> Nilai KLN: Rp {temp_kln_3:,.2f}")

        st.markdown("---")

        # --- IV. BIAYA JASA UMUM & BUKAN BIAYA ---
        c_j1, c_j2 = st.columns(2)
        with c_j1:
            st.markdown("**IV. Biaya Jasa Umum**")
            p_kdn_4 = st.number_input("Persentase KDN Jasa Umum (%):", value=float(saved_tkdn.get('p_kdn_4', 1.55)), step=0.01, format="%.2f", key=f"input_p_kdn_4_{selected_pi_key}")
            temp_kdn_4 = (p_kdn_4 / 100.0) * total_tagihan_rujukan
            st.caption(f"-> Nilai KDN: Rp {temp_kdn_4:,.2f}")
            
            p_kln_4 = st.number_input("Persentase KLN Jasa Umum (%):", value=float(saved_tkdn.get('p_kln_4', 0.0)), step=0.01, format="%.2f", key=f"input_p_kln_4_{selected_pi_key}")
            temp_kln_4 = (p_kln_4 / 100.0) * total_tagihan_rujukan
            st.caption(f"-> Nilai KLN: Rp {temp_kln_4:,.2f}")

        with c_j2:
            st.markdown("**B. Komponen Bukan Biaya**")
            p_non_cost = st.number_input("Persentase Komponen Bukan Biaya (%):", value=float(saved_tkdn.get('p_non_cost', 4.89)), step=0.01, format="%.2f", key=f"input_p_non_cost_{selected_pi_key}")
            temp_non_cost = (p_non_cost / 100.0) * total_tagihan_rujukan
            st.caption(f"-> Nilai Bukan Biaya: Rp {temp_non_cost:,.2f}")

        # --- TOTAL AKUMULASI PERSENTASE ---
        total_persen_akumulasi = p_kdn_1 + p_kln_1 + p_kdn_2 + p_kln_2 + p_kdn_3 + p_kln_3 + p_kdn_4 + p_kln_4 + p_non_cost
        st.markdown(f"**📊 Total Akumulasi Persentase Terdistribusi:** `{total_persen_akumulasi:.2f}%`")
        if abs(total_persen_akumulasi - 100.0) > 0.01:
            st.warning(f"⚠️ Total persentase saat ini adalah {total_persen_akumulasi:.2f}%. Pastikan total distribusi mendekati atau tepat 100%.")
        else:
            st.success("✅ Total akumulasi persentase sudah tepat 100%.")

        submit_save_tkdn = st.form_submit_button("💾 Simpan & Kunci Dokumen TKDN Ini", type="primary")
        if submit_save_tkdn:
            # Perbarui session state
            st.session_state.tkdn_saved_data[selected_pi_key].update({
                'lokasi_office': lokasi_office,
                'tanggal_dokumen': selected_date_tkdn,
                'total_tagihan': total_tagihan_rujukan,
                'nama_direktur': nama_direktur,
                'p_kdn_1': p_kdn_1, 'p_kln_1': p_kln_1,
                'p_kdn_2': p_kdn_2, 'p_kln_2': p_kln_2,
                'p_kdn_3': p_kdn_3, 'p_kln_3': p_kln_3,
                'p_kdn_4': p_kdn_4, 'p_kln_4': p_kln_4,
                'p_non_cost': p_non_cost
            })
            
            # SIMPAN PERMANEN KE HARDDISK (JSON)
            try:
                data_to_export = st.session_state.tkdn_saved_data[selected_pi_key].copy()
                # Ubah date object menjadi string agar bisa diserialisasi ke JSON
                data_to_export['tanggal_dokumen'] = str(selected_date_tkdn)
                # Hapus binary TTD jika ada dari dictionary json agar tidak error (atau simpan terpisah jika diperlukan)
                data_to_export.pop('ttd_direktur', None)
                
                with open(tkdn_file_path, "w", encoding="utf-8") as f_json:
                    json.dump(data_to_export, f_json, ensure_ascii=False, indent=4)
                
                st.success(f"✅ Dokumen TKDN untuk PI [{selected_pi_key}] berhasil disimpan secara permanen & dikunci!")
            except Exception as e:
                st.error(f"Gagal menyimpan permanen ke disk: {e}")

    # --- PENGATURAN TANDA TANGAN ---
    st.markdown("---")
    st.markdown("#### ✍️ Pengaturan Tanda Tangan Digital Direktur TKDN")
    uploaded_ttd_tkdn = st.file_uploader("Upload Tanda Tangan Direktur", type=["png", "jpg", "jpeg"], key=f"ttd_tkdn_uploader_{selected_pi_key}")
    if uploaded_ttd_tkdn is not None:
        saved_tkdn['ttd_direktur'] = uploaded_ttd_tkdn.getvalue()
    
    if saved_tkdn.get('ttd_direktur') is not None:
        if st.button("🗑️ Hapus Tanda Tangan Direktur", key=f"btn_del_tkdn_ttd_{selected_pi_key}"):
            saved_tkdn['ttd_direktur'] = None
            st.success("✅ Tanda tangan berhasil dihapus!")
            st.rerun()

    active_lokasi = saved_tkdn.get('lokasi_office', 'Luwuk')
    active_date = saved_tkdn.get('tanggal_dokumen', date.today())
    if isinstance(active_date, str):
        try:
            active_date = datetime.strptime(active_date, "%Y-%m-%d").date()
        except:
            active_date = date.today()
            
    active_tagihan = default_rujukan_tagihan
    active_direktur = saved_tkdn.get('nama_direktur', 'Ir. Ferry Tatimu')

    bulan_indo = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
        7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }
    tgl_dokumen = f"{active_date.day:02d} {bulan_indo[active_date.month]} {active_date.year}"

    kdn_1 = (saved_tkdn.get('p_kdn_1', 15.09) / 100.0) * active_tagihan
    kln_1 = (saved_tkdn.get('p_kln_1', 1.51) / 100.0) * active_tagihan
    kdn_2 = (saved_tkdn.get('p_kdn_2', 28.26) / 100.0) * active_tagihan
    kln_2 = (saved_tkdn.get('p_kln_2', 0.0) / 100.0) * active_tagihan
    kdn_3 = (saved_tkdn.get('p_kdn_3', 47.18) / 100.0) * active_tagihan
    kln_3 = (saved_tkdn.get('p_kln_3', 1.51) / 100.0) * active_tagihan
    kdn_4 = (saved_tkdn.get('p_kdn_4', 1.55) / 100.0) * active_tagihan
    kln_4 = (saved_tkdn.get('p_kln_4', 0.0) / 100.0) * active_tagihan
    komponen_bukan_biaya = (saved_tkdn.get('p_non_cost', 4.89) / 100.0) * active_tagihan

    tot_kdn_biaya = kdn_1 + kdn_2 + kdn_3 + kdn_4
    tot_kln_biaya = kln_1 + kln_2 + kln_3 + kln_4
    
    tot_biaya_1 = kdn_1 + kln_1
    tot_biaya_2 = kdn_2 + kln_2
    tot_biaya_3 = kdn_3 + kln_3
    tot_biaya_4 = kdn_4 + kln_4

    jumlah_biaya_total = tot_biaya_1 + tot_biaya_2 + tot_biaya_3 + tot_biaya_4
    jumlah_nilai_total = jumlah_biaya_total + komponen_bukan_biaya

    persen_tkdn_akhir = (tot_kdn_biaya / jumlah_nilai_total) * 100 if jumlah_nilai_total > 0 else 0

    nomor_kontrak = str(t_data.get('Nomor Kontrak', matched_db_row.get('Nomor Kontrak', '7201250141'))).strip()
    nomor_po = str(t_data.get('Nomor PO', matched_db_row.get('Nomor PO', '-'))).strip()
    judul_kontrak = str(t_data.get('Nama Kontrak', matched_db_row.get('Nama Kontrak', 'Penyediaan General Services Untuk Mendukung Kegiatan Pengboran, Kerja Ulang Dan Perawatan Sumur di Blok Senoro - Toili'))).strip()
    mata_uang = str(t_data.get('Mata Uang', 'IDR')).strip()

    ttd_bytes = saved_tkdn.get('ttd_direktur')
    ttd_html = f'<div style="margin: 4px auto; height: 90px; display: flex; align-items: center; justify-content: center;"><img src="data:image/png;base64,{base64.b64encode(ttd_bytes).decode()}" style="max-height: 85px; max-width: 220px; object-fit: contain;"></div>' if ttd_bytes is not None else '<div style="height: 80px;"></div>'

    # --- HTML RENDER DOKUMEN RESMI ---
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Formulir TKDN - Permen ESDM No. 15 Tahun 2013</title>
        <style>
            @page {{ size: A4; margin: 10mm; }}
            @media print {{
                body {{ -webkit-print-color-adjust: exact; }}
                @page {{ margin: 0; }}
                body {{ margin: 10mm; }}
                header, footer, .no-print {{ display: none !important; }}
            }}
            body {{ font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; padding: 25px; margin: 0; font-size: 10px; line-height: 1.3; }}
            .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 6px; margin-bottom: 10px; }}
            .title {{ text-align: center; font-weight: bold; font-size: 12px; margin-bottom: 5px; text-transform: uppercase; }}
            .subtitle {{ text-align: center; font-weight: bold; font-size: 10px; margin-bottom: 15px; text-transform: uppercase; }}
            
            table.info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; font-size: 10px; }}
            table.info-table td {{ border: none; padding: 2px 4px; vertical-align: top; }}
            
            table.tkdn-grid {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; }}
            table.tkdn-grid th, table.tkdn-grid td {{ border: 1px solid #000; padding: 5px 6px; font-size: 9px; vertical-align: middle; }}
            .th-header {{ background-color: #f1f5f9; font-weight: bold; text-align: center; text-transform: uppercase; }}
            .col-yellow {{ background-color: #fef08a !important; }}
            
            .footer-notes {{ font-size: 9px; margin-top: 15px; line-height: 1.4; }}
            .sign-section {{ width: 100%; border-collapse: collapse; margin-top: 20px; page-break-inside: avoid; }}
            .sign-section td {{ border: none; font-size: 10px; vertical-align: top; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2 style="margin: 0; font-size: 14px;">PT. BANGGAI SENTRAL SULAWESI</h2>
            <p style="margin: 2px 0; font-size: 8px;">Head Office: Jl. Urip Sumorharjo 53, Luwuk 94715, Phone: 0461-21025 | email: Luwuk@ptbss.com</p>
        </div>

        <div class="title">TABEL PERHITUNGAN TINGKAT KOMPONEN DALAM NEGERI - JASA</div>
        <div class="subtitle">SELF - ASSESSMENT (PERMEN ESDM NO. 15 TAHUN 2013)</div>

        <table class="info-table">
            <tr>
                <td style="width: 20%; font-weight: bold;">Nama Penyedia Jasa</td>
                <td style="width: 2%;">:</td>
                <td style="width: 48%;"><b>PT BANGGAI SENTRAL SULAWESI</b></td>
                <td style="width: 15%; font-weight: bold;">Nomor Kontrak</td>
                <td style="width: 2%;">:</td>
                <td style="width: 13%;"><b>{nomor_kontrak}</b></td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Judul Kontrak</td>
                <td>:</td>
                <td>{judul_kontrak}</td>
                <td style="font-weight: bold;">Nomor PO</td>
                <td>:</td>
                <td><b>{nomor_po}</b></td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Mata Uang</td>
                <td>:</td>
                <td>{mata_uang}</td>
                <td style="font-weight: bold;">Tanggal</td>
                <td>:</td>
                <td>{tgl_dokumen}</td>
            </tr>
        </table>

        <table class="tkdn-grid">
            <tr>
                <th class="th-header" style="width: 30%;">A. Komponen Biaya<br>(Cost Component)</th>
                <th class="th-header" style="width: 8%;">Mata Uang</th>
                <th class="th-header" style="width: 14%;">KDN<br>(a)</th>
                <th class="th-header" style="width: 14%;">KLN<br>(b)</th>
                <th class="th-header" style="width: 14%;">TOTAL<br>(c = a+b)</th>
                <th class="th-header" style="width: 10%;">% Nilai TKDN<br>(d = a/c)</th>
                <th class="th-header" style="width: 10%;">Nilai TKDN<br>(e = c x d)</th>
            </tr>
            <!-- I. BIAYA BAHAN -->
            <tr>
                <td rowspan="2"><b>I. Biaya Bahan (Material) Terpakai</b><br><span style="font-size:7px; color:#555;">(material used cost)</span></td>
                <td style="text-align: center;"><b>Rp</b></td>
                <td class="col-yellow" style="text-align: right;">Rp {kdn_1:,.2f}</td>
                <td class="col-yellow" style="text-align: right;">Rp {kln_1:,.2f}</td>
                <td style="text-align: right;">Rp {tot_biaya_1:,.2f}</td>
                <td style="text-align: center;">{(kdn_1/tot_biaya_1*100) if tot_biaya_1>0 else 0:.2f}%</td>
                <td style="text-align: right;">Rp {kdn_1:,.2f}</td>
            </tr>
            <tr>
                <td style="text-align: center;"><i>US$</i></td>
                <td class="col-yellow" style="text-align: right;">0.00</td>
                <td class="col-yellow" style="text-align: right;">0.00</td>
                <td style="text-align: right;">0.00</td>
                <td style="text-align: center;">0.00%</td>
                <td style="text-align: right;">0.00</td>
            </tr>

            <!-- II. BIAYA TENAGA KERJA -->
            <tr>
                <td rowspan="2"><b>II. Biaya Tenaga Kerja & Konsultan</b><br><span style="font-size:7px; color:#555;">(personnel & consultant cost)</span></td>
                <td style="text-align: center;"><b>Rp</b></td>
                <td class="col-yellow" style="text-align: right;">Rp {kdn_2:,.2f}</td>
                <td class="col-yellow" style="text-align: right;">Rp {kln_2:,.2f}</td>
                <td style="text-align: right;">Rp {tot_biaya_2:,.2f}</td>
                <td style="text-align: center;">{(kdn_2/tot_biaya_2*100) if tot_biaya_2>0 else 0:.2f}%</td>
                <td style="text-align: right;">Rp {kdn_2:,.2f}</td>
            </tr>
            <tr>
                <td style="text-align: center;"><i>US$</i></td>
                <td class="col-yellow" style="text-align: right;">0.00</td>
                <td class="col-yellow" style="text-align: right;">0.00</td>
                <td style="text-align: right;">0.00</td>
                <td style="text-align: center;">0.00%</td>
                <td style="text-align: right;">0.00</td>
            </tr>

            <!-- III. BIAYA ALAT KERJA -->
            <tr>
                <td rowspan="2"><b>III. Biaya Alat Kerja / Fasilitas Kerja</b><br><span style="font-size:7px; color:#555;">(equipment & work facility cost)</span></td>
                <td style="text-align: center;"><b>Rp</b></td>
                <td class="col-yellow" style="text-align: right;">Rp {kdn_3:,.2f}</td>
                <td class="col-yellow" style="text-align: right;">Rp {kln_3:,.2f}</td>
                <td style="text-align: right;">Rp {tot_biaya_3:,.2f}</td>
                <td style="text-align: center;">{(kdn_3/tot_biaya_3*100) if tot_biaya_3>0 else 0:.2f}%</td>
                <td style="text-align: right;">Rp {kdn_3:,.2f}</td>
            </tr>
            <tr>
                <td style="text-align: center;"><i>US$</i></td>
                <td class="col-yellow" style="text-align: right;">0.00</td>
                <td class="col-yellow" style="text-align: right;">0.00</td>
                <td style="text-align: right;">0.00</td>
                <td style="text-align: center;">0.00%</td>
                <td style="text-align: right;">0.00</td>
            </tr>

            <!-- IV. BIAYA JASA UMUM -->
            <tr>
                <td rowspan="2"><b>IV. Biaya Jasa Umum</b><br><span style="font-size:7px; color:#555;">(other services cost)</span></td>
                <td style="text-align: center;"><b>Rp</b></td>
                <td class="col-yellow" style="text-align: right;">Rp {kdn_4:,.2f}</td>
                <td class="col-yellow" style="text-align: right;">Rp {kln_4:,.2f}</td>
                <td style="text-align: right;">Rp {tot_biaya_4:,.2f}</td>
                <td style="text-align: center;">{(kdn_4/tot_biaya_4*100) if tot_biaya_4>0 else 0:.2f}%</td>
                <td style="text-align: right;">Rp {kdn_4:,.2f}</td>
            </tr>
            <tr>
                <td style="text-align: center;"><i>US$</i></td>
                <td class="col-yellow" style="text-align: right;">0.00</td>
                <td class="col-yellow" style="text-align: right;">0.00</td>
                <td style="text-align: right;">0.00</td>
                <td style="text-align: center;">0.00%</td>
                <td style="text-align: right;">0.00</td>
            </tr>

            <!-- V. JUMLAH BIAYA -->
            <tr style="background-color: #f8fafc; font-weight: bold;">
                <td rowspan="2">V. JUMLAH BIAYA (Σ I s/d IV)<br><span style="font-size:7px; color:#555;">(Total Cost)</span></td>
                <td style="text-align: center;"><b>Rp</b></td>
                <td style="text-align: right;">Rp {tot_kdn_biaya:,.2f}</td>
                <td style="text-align: right;">Rp {tot_kln_biaya:,.2f}</td>
                <td style="text-align: right;">Rp {jumlah_biaya_total:,.2f}</td>
                <td style="text-align: center;">{(tot_kdn_biaya/jumlah_biaya_total*100) if jumlah_biaya_total>0 else 0:.2f}%</td>
                <td style="text-align: right;">Rp {tot_kdn_biaya:,.2f}</td>
            </tr>
            <tr style="background-color: #f8fafc; font-weight: bold;">
                <td style="text-align: center;"><i>US$</i></td>
                <td style="text-align: right;">0.00</td>
                <td style="text-align: right;">0.00</td>
                <td style="text-align: right;">0.00</td>
                <td style="text-align: center;">0.00%</td>
                <td style="text-align: right;">0.00</td>
            </tr>

            <!-- B. KOMPONEN BUKAN BIAYA -->
            <tr>
                <td rowspan="2"><b>B. KOMPONEN BUKAN BIAYA</b><br><span style="font-size:7px; color:#555;">(Non-cost Component)</span></td>
                <td style="text-align: center;"><b>Rp</b></td>
                <td colspan="2"></td>
                <td class="col-yellow" style="text-align: right;"><b>Rp {komponen_bukan_biaya:,.2f}</b></td>
                <td colspan="2"></td>
            </tr>
            <tr>
                <td style="text-align: center;"><i>US$</i></td>
                <td colspan="2"></td>
                <td class="col-yellow" style="text-align: right;">0.00</td>
                <td colspan="2"></td>
            </tr>

            <!-- C. JUMLAH NILAI TOTAL -->
            <tr style="background-color: #f1f5f9; font-weight: bold; font-size: 10px;">
                <td rowspan="2">C. JUMLAH NILAI TOTAL (A + B)</td>
                <td style="text-align: center;"><b>Rp</b></td>
                <td colspan="3" style="text-align: right;"><b>Rp {jumlah_nilai_total:,.2f}</b></td>
                <td colspan="2"></td>
            </tr>
            <tr style="background-color: #f1f5f9; font-weight: bold; font-size: 10px;">
                <td style="text-align: center;"><i>US$</i></td>
                <td colspan="3" style="text-align: right;">0.00</td>
                <td colspan="2"></td>
            </tr>

            <tr style="background-color: #e2e8f0; font-weight: bold; font-size: 11px; color: #065f46;">
                <td colspan="5">CAPAIAN PERSENTASE TKDN AKHIR (%)</td>
                <td colspan="2" style="text-align: right; font-size: 12px;">{persen_tkdn_akhir:.2f} %</td>
            </tr>
        </table>

        <div class="footer-notes">
            <b>Catatan:</b><br>
            &bull; Isi hanya pada kolom yang berwarna kuning pastel.<br>
            &bull; Formulasi perhitungan mengacu pada Permen ESDM No. 15 Tahun 2013.
        </div>

        <table class="sign-section">
            <tr>
                <td style="width: 50%;"></td>
                <td style="width: 50%; text-align: center; padding-left: 20px;">
                    {active_lokasi}, {tgl_dokumen}<br>
                    <b>PT. Banggai Sentral Sulawesi</b>
                    {ttd_html}
                    <u><b>{active_direktur}</b></u><br>
                    Direktur
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
                    win.document.open();
                    win.document.write(atob("{b64_html}"));
                    win.document.close();
                    win.focus();
                    setTimeout(function(){{ win.print(); }}, 500);
                }}
            </script>
            <button onclick="printDoc()" style="width: 100%; background-color: #10b981; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
                🖨️ Cetak / Print Formulir TKDN (Permen ESDM 15/2013)
            </button>
        """
        st.components.v1.html(print_script, height=50)

    with col_btn2:
        b64_pdf = base64.b64encode(html_content.encode()).decode()
        download_link = f'<a href="data:text/html;base64,{b64_pdf}" download="Formulir_TKDN_{nomor_kontrak.replace("/", "-")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download File TKDN</button></a>'
        st.markdown(download_link, unsafe_allow_html=True)