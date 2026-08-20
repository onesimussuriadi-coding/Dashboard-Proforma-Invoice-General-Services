import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime

def tampilkan_tkdn(transaksi_list):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📋 Pratinjau, Cetak & Download Formulir TKDN (Permen ESDM No. 15 Tahun 2013)</h3>
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
    
    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        selected_idx = st.selectbox("Pilih Dokumen Transaksi Tersimpan:", range(len(pilihan_tx)), format_func=lambda x: pilihan_tx[x], key="tkdn_select_pi_dropdown")
    with col_sel2:
        lokasi_office = st.text_input("📍 Lokasi Office (Tempat Dokumen):", value="Luwuk", key="tkdn_lokasi_office")

    t_data = unique_tx_list[selected_idx]
    pi_sekarang = str(t_data.get('PI No.', '')).strip()

    db_invoice_path = os.path.join("database_penyimpanan_aman", "database_proforma_invoice.xlsx")
    matched_db_row = {}
    if os.path.exists(db_invoice_path):
        try:
            df_inv = pd.read_excel(db_invoice_path)
            row_match = df_inv[df_inv['Proforma Invoice No.'].astype(str).str.strip() == pi_sekarang]
            if not row_match.empty:
                matched_db_row = row_match.iloc[0].to_dict()
        except:
            pass

    aktual_total_tagihan = float(t_data.get('Total Harga', 0.0))

    # --- INISIALISASI SESSION STATE AMAN ---
    if 'master_tagihan_val' not in st.session_state:
        st.session_state.master_tagihan_val = aktual_total_tagihan

    if 'current_pi_tracking' not in st.session_state or st.session_state.current_pi_tracking != pi_sekarang:
        st.session_state.current_pi_tracking = pi_sekarang
        st.session_state.master_tagihan_val = aktual_total_tagihan

    if 'val_p_kdn_1' not in st.session_state: st.session_state.val_p_kdn_1 = 15.09
    if 'val_p_kln_1' not in st.session_state: st.session_state.val_p_kln_1 = 1.51
    if 'val_p_kdn_2' not in st.session_state: st.session_state.val_p_kdn_2 = 28.26
    if 'val_p_kln_2' not in st.session_state: st.session_state.val_p_kln_2 = 0.0
    if 'val_p_kdn_3' not in st.session_state: st.session_state.val_p_kdn_3 = 47.18
    if 'val_p_kln_3' not in st.session_state: st.session_state.val_p_kln_3 = 1.51
    if 'val_p_kdn_4' not in st.session_state: st.session_state.val_p_kdn_4 = 1.55
    if 'val_p_kln_4' not in st.session_state: st.session_state.val_p_kln_4 = 0.0
    if 'val_p_non_cost' not in st.session_state: st.session_state.val_p_non_cost = 4.89

    st.markdown("#### ⚙️ Pengaturan Parameter & Rujukan Perhitungan TKDN")
    
    c_master1, c_master2, c_master3 = st.columns(3)
    with c_master1:
        total_tagihan_rujukan = st.number_input(
            "💰 Rujukan Total Tagihan (Rp):", 
            value=st.session_state.master_tagihan_val, 
            step=100000.0, 
            key="master_tagihan_val"
        )
    with c_master2:
        selected_date_tkdn = st.date_input("📅 Tanggal Dokumen TKDN:", value=datetime.now(), key="tkdn_date_picker_val")
        bulan_indo = {
            1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
            7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
        }
        tgl_dokumen = f"{selected_date_tkdn.day:02d} {bulan_indo[selected_date_tkdn.month]} {selected_date_tkdn.year}"
    with c_master3:
        nama_direktur = st.text_input("Nama Direktur / Penandatangan:", value="Ir. Ferry Tatimu", key="tkdn_nama_dir")

    st.markdown("---")
    st.markdown("#### 🧮 Rincian Komponen Biaya & Non-Biaya (Berbasis Persentase)")
    st.info("💡 Masukkan persentase (%) untuk setiap komponen. Nilai nominal dihitung otomatis dari Total Tagihan aktual PI.")

    # --- I. BIAYA BAHAN ---
    st.markdown("**I. Biaya Bahan (Material)**")
    c_b1, c_b2 = st.columns(2)
    with c_b1:
        p_kdn_1 = st.number_input("Persentase KDN Bahan (%):", value=st.session_state.val_p_kdn_1, step=0.1, key="input_p_kdn_1")
        st.session_state.val_p_kdn_1 = p_kdn_1
        kdn_1 = (p_kdn_1 / 100.0) * total_tagihan_rujukan
        st.caption(f"-> Nilai KDN: Rp {kdn_1:,.2f}")
    with c_b2:
        p_kln_1 = st.number_input("Persentase KLN Bahan (%):", value=st.session_state.val_p_kln_1, step=0.1, key="input_p_kln_1_kln")
        st.session_state.val_p_kln_1 = p_kln_1
        kln_1 = (p_kln_1 / 100.0) * total_tagihan_rujukan
        st.caption(f"-> Nilai KLN: Rp {kln_1:,.2f}")

    st.markdown("---")

    # --- II. BIAYA TENAGA KERJA ---
    st.markdown("**II. Biaya Tenaga Kerja & Konsultan**")
    c_t1, c_t2 = st.columns(2)
    with c_t1:
        p_kdn_2 = st.number_input("Persentase KDN Tenaga Kerja (%):", value=st.session_state.val_p_kdn_2, step=0.1, key="input_p_kdn_2")
        st.session_state.val_p_kdn_2 = p_kdn_2
        kdn_2 = (p_kdn_2 / 100.0) * total_tagihan_rujukan
        st.caption(f"-> Nilai KDN: Rp {kdn_2:,.2f}")
    with c_t2:
        p_kln_2 = st.number_input("Persentase KLN Tenaga Kerja (%):", value=st.session_state.val_p_kln_2, step=0.1, key="input_p_kln_2_kln")
        st.session_state.val_p_kln_2 = p_kln_2
        kln_2 = (p_kln_2 / 100.0) * total_tagihan_rujukan
        st.caption(f"-> Nilai KLN: Rp {kln_2:,.2f}")

    st.markdown("---")

    # --- III. BIAYA ALAT KERJA ---
    st.markdown("**III. Biaya Alat Kerja / Fasilitas Kerja**")
    c_a1, c_a2 = st.columns(2)
    with c_a1:
        p_kdn_3 = st.number_input("Persentase KDN Alat Kerja (%):", value=st.session_state.val_p_kdn_3, step=0.1, key="input_p_kdn_3")
        st.session_state.val_p_kdn_3 = p_kdn_3
        kdn_3 = (p_kdn_3 / 100.0) * total_tagihan_rujukan
        st.caption(f"-> Nilai KDN: Rp {kdn_3:,.2f}")
    with c_a2:
        p_kln_3 = st.number_input("Persentase KLN Alat Kerja (%):", value=st.session_state.val_p_kln_3, step=0.1, key="input_p_kln_3_kln")
        st.session_state.val_p_kln_3 = p_kln_3
        kln_3 = (p_kln_3 / 100.0) * total_tagihan_rujukan
        st.caption(f"-> Nilai KLN: Rp {kln_3:,.2f}")

    st.markdown("---")

    # --- IV. BIAYA JASA UMUM & BUKAN BIAYA ---
    c_j1, c_j2 = st.columns(2)
    with c_j1:
        st.markdown("**IV. Biaya Jasa Umum**")
        p_kdn_4 = st.number_input("Persentase KDN Jasa Umum (%):", value=st.session_state.val_p_kdn_4, step=0.1, key="input_p_kdn_4")
        st.session_state.val_p_kdn_4 = p_kdn_4
        kdn_4 = (p_kdn_4 / 100.0) * total_tagihan_rujukan
        st.caption(f"-> Nilai KDN: Rp {kdn_4:,.2f}")
        
        p_kln_4 = st.number_input("Persentase KLN Jasa Umum (%):", value=st.session_state.val_p_kln_4, step=0.1, key="input_p_kln_4_kln")
        st.session_state.val_p_kln_4 = p_kln_4
        kln_4 = (p_kln_4 / 100.0) * total_tagihan_rujukan
        st.caption(f"-> Nilai KLN: Rp {kln_4:,.2f}")

    with c_j2:
        st.markdown("**B. Komponen Bukan Biaya**")
        p_non_cost = st.number_input("Persentase Komponen Bukan Biaya (%):", value=st.session_state.val_p_non_cost, step=0.1, key="input_p_non_cost")
        st.session_state.val_p_non_cost = p_non_cost
        komponen_bukan_biaya = (p_non_cost / 100.0) * total_tagihan_rujukan
        st.caption(f"-> Nilai Bukan Biaya: Rp {komponen_bukan_biaya:,.2f}")

    # --- PERHITUNGAN OTOMATIS FORMULA PERMEN ESDM NO. 15 / 2013 ---
    tot_kdn_biaya = kdn_1 + kdn_2 + kdn_3 + kdn_4
    tot_kln_biaya = kln_1 + kln_2 + kln_3 + kln_4
    
    tot_biaya_1 = kdn_1 + kln_1
    tot_biaya_2 = kdn_2 + kln_2
    tot_biaya_3 = kdn_3 + kln_3
    tot_biaya_4 = kdn_4 + kln_4

    jumlah_biaya_total = tot_biaya_1 + tot_biaya_2 + tot_biaya_3 + tot_biaya_4
    jumlah_nilai_total = jumlah_biaya_total + komponen_bukan_biaya

    persen_tkdn_akhir = (tot_kdn_biaya / jumlah_nilai_total) * 100 if jumlah_nilai_total > 0 else 0

    nomor_kontrak = str(t_data.get('Nomor Kontrak', matched_db_row.get('Nomor Kontrak', '7207250142'))).strip()
    nomor_po = str(t_data.get('Nomor PO', matched_db_row.get('Nomor PO', '4500011425'))).strip()
    judul_kontrak = str(t_data.get('Nama Kontrak', matched_db_row.get('Nama Kontrak', 'Jasa Sewa Alat Berat Pendukung Operasional Senoro dan Tiaka'))).strip()
    mata_uang = str(t_data.get('Mata Uang', 'IDR')).strip()

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
            .sign-section {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
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
                <td style="width: 60%;"></td>
                <td style="width: 40%; text-align: center;">
                    {lokasi_office}, {tgl_dokumen}<br>
                    <b>PT. Banggai Sentral Sulawesi</b><br><br><br><br>
                    <u><b>{nama_direktur}</b></u><br>
                    Direktur
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
                🖨️ Cetak / Print Formulir TKDN (Permen ESDM 15/2013)
            </button>
        """
        st.components.v1.html(print_script, height=50)

    with col_btn2:
        b64_pdf = base64.b64encode(html_content.encode()).decode()
        download_link = f'<a href="data:text/html;base64,{b64_pdf}" download="Formulir_TKDN_{nomor_kontrak}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download File TKDN</button></a>'
        st.markdown(download_link, unsafe_allow_html=True)