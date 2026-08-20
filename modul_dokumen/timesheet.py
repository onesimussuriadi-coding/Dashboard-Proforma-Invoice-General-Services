import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime
import calendar

def hitung_volume_bayar(total_O, total_S, total_R, total_M, hari_dalam_bulan, skema_sewa):
    """
    Logika perhitungan dinamis berdasarkan pilihan skema sewa:
    - Monthly: Full bulan dikurangi hari rusak (R) / prorata
    - Daily: Operation (O) + Mobilisasi (M)
    - Mobilisasi: Berdasarkan hari mobilisasi (M)
    - Provisional Sum: Berdasarkan realisasi aktual
    """
    if skema_sewa == "Monthly":
        volume_bayar = hari_dalam_bulan - total_R
        return max(0, volume_bayar)
    elif skema_sewa == "Daily":
        return total_O + total_M
    elif skema_sewa == "Mobilisasi":
        return total_M
    elif skema_sewa == "Provisional Sum":
        return total_O
    return total_O

def tampilkan_timesheet(transaksi_list):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">🕒 Pengelolaan Timesheet Peralatan Berbasis Kalender & Pilihan Tahun (FM-GS-06 Rev.03)</h3>
        </div>
    """, unsafe_allow_html=True)

    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi kontrak atau proforma invoice yang tersedia.")
        return

    # 1. Rujukan Nomor Proforma Invoice (PI) & Kontrak
    seen_pi = set()
    unique_pi_list = []
    for t in transaksi_list:
        pi_no = str(t.get('PI No.', t.get('Proforma Invoice No.', ''))).strip()
        if pi_no and pi_no not in seen_pi:
            seen_pi.add(pi_no)
            unique_pi_list.append(t)

    if not unique_pi_list:
        unique_pi_list = transaksi_list

    pilihan_pi = [f"PI No: {p.get('PI No.', 'PI-001')} | Kontrak: {p.get('Nomor Kontrak', '7207250142')} | User: {p.get('Ditujukan Kepada', 'JOB Pertamina-Medco')}" for p in unique_pi_list]

    col_pi1, col_pi2, col_pi3 = st.columns([2, 1, 1])
    with col_pi1:
        selected_pi_idx = st.selectbox("📌 Rujukan Nomor Proforma Invoice (PI):", range(len(pilihan_pi)), format_func=lambda x: pilihan_pi[x], key="ts_select_pi_ref")
    with col_pi2:
        daftar_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        pilih_bulan = st.selectbox("📅 Pilih Bulan:", daftar_bulan, index=6, key="ts_pilih_bulan")
    with col_pi3:
        pilih_tahun = st.selectbox("📆 Pilih Tahun:", [str(y) for y in range(2026, 2036)], index=0, key="ts_pilih_tahun")

    selected_pi_data = unique_pi_list[selected_pi_idx]
    nomor_pi_ref = str(selected_pi_data.get('PI No.', selected_pi_data.get('Proforma Invoice No.', 'PI-042/BSS-JOB/AB/VII/2026'))).strip()
    
    # --- INPUT TAMBAHAN: NOMOR KONTRAK, PO OPSIONAL, & SKEMA SEWA ---
    st.markdown("---")
    st.markdown("#### 📋 Konfigurasi Kontrak & Skema Perhitungan Timesheet")
    c_cfg1, c_cfg2, c_cfg3 = st.columns(3)
    with c_cfg1:
        nomor_kontrak = st.text_input("Nomor Kontrak Rujukan:", value=str(selected_pi_data.get('Nomor Kontrak', '7207250142')), key="ts_input_no_kontrak")
    with c_cfg2:
        nomor_po_opsional = st.text_input("Nomor PO (Opsional):", value=str(selected_pi_data.get('Nomor PO', '4500011425')), key="ts_input_no_po")
    with c_cfg3:
        skema_sewa_pilihan = st.selectbox("Skema Perhitungan Sewa:", ["Monthly", "Daily", "Mobilisasi", "Provisional Sum"], index=0, key="ts_skema_sewa_pilihan")

    customer_user = str(selected_pi_data.get('Ditujukan Kepada', 'JOB Pertamina - Medco E&P Tomori Sulawesi')).strip()
    proyek_teks = str(selected_pi_data.get('Nama Kontrak', 'Jasa Sewa Alat Berat Pendukung Operasional Senoro dan Tiaka')).strip()

    st.markdown("---")
    st.markdown("#### 🗓️ Rentang Tanggal Kalender Periode Timesheet")
    c_cal1, c_cal2 = st.columns(2)
    with c_cal1:
        tanggal_mulai = st.date_input("Tanggal Mulai:", value=datetime(2026, 7, 1), key="ts_tgl_mulai")
    with c_cal2:
        tanggal_selesai = st.date_input("Tanggal Selesai:", value=datetime(2026, 7, 31), key="ts_tgl_selesai")

    periode_teks_input = f"{tanggal_mulai.day:02d} s/d {tanggal_selesai.day:02d} {pilih_bulan} {pilih_tahun}"

    st.markdown("---")
    
    # MANAJEMEN MASTER NAMA ALAT DINAMIS
    db_folder = "database_penyimpanan_aman"
    os.makedirs(db_folder, exist_ok=True)
    master_alat_path = os.path.join(db_folder, "database_master_nama_alat.xlsx")

    master_alat_list = [
        "Truck Mounted Crane (TMC) Capacity 8 T",
        "Man Lift Capacity 227 Kg",
        "Mobile Crane Capacity 80 T",
        "Backhoe Loader"
    ]
    
    if os.path.exists(master_alat_path):
        try:
            df_m_alat = pd.read_excel(master_alat_path)
            if "Nama Alat" in df_m_alat.columns:
                master_alat_list = df_m_alat["Nama Alat"].dropna().astype(str).tolist()
        except:
            pass

    col_m1, col_m2 = st.columns([3, 1])
    with col_m1:
        input_nama_alat_baru = st.text_input("Tambah / Edit Nama Alat Baru:", value="", placeholder="Contoh: Mobile Crane Capacity 50 T", key="input_master_alat_baru")
    with col_m2:
        st.markdown("<br>", unsafe_allow_html=True)
        col_sub_m1, col_sub_m2 = st.columns(2)
        with col_sub_m1:
            if st.button("➕ Tambah", key="btn_add_alat"):
                if input_nama_alat_baru and input_nama_alat_baru not in master_alat_list:
                    master_alat_list.append(input_nama_alat_baru)
                    df_save_m = pd.DataFrame({"Nama Alat": master_alat_list})
                    df_save_m.to_excel(master_alat_path, index=False)
                    st.success("✅ Alat ditambahkan!")
                    st.rerun()
        with col_sub_m2:
            if st.button("💾 Update", key="btn_update_master_alat"):
                df_save_m = pd.DataFrame({"Nama Alat": master_alat_list})
                df_save_m.to_excel(master_alat_path, index=False)
                st.success("✅ Master diperbarui!")

    sub_pekerjaan_teks = st.selectbox("📋 Pilih Sub Pekerjaan / Nama Alat Aktual:", master_alat_list, key="ts_dropdown_alat_dinamis")
    note_teks = st.text_input("Catatan / Note:", value="", key="ts_note_input")

    # SIMPAN, LOAD, UPDATE TIMESHEET
    ts_db_path = os.path.join(db_folder, "database_timesheet_history.xlsx")
    loaded_record = None

    if os.path.exists(ts_db_path):
        try:
            df_check = pd.read_excel(ts_db_path)
            match_rec = df_check[(df_check["PI No."].astype(str).str.strip() == nomor_pi_ref) & (df_check["Periode"].astype(str).str.strip() == periode_teks_input) & (df_check["Sub Pekerjaan"].astype(str).str.strip() == sub_pekerjaan_teks)]
            if not match_rec.empty:
                st.info(f"📂 Ditemukan riwayat timesheet tersimpan untuk PI: {nomor_pi_ref} ({sub_pekerjaan_teks}).")
                if st.button("📂 Panggil Kembali Data Tersimpan (Load Data)", key="btn_load_ts"):
                    loaded_record = match_rec.iloc[0].to_dict()
                    st.success("✅ Data timesheet berhasil dimuat kembali!")
        except Exception as e:
            pass

    if 'daily_status' not in st.session_state:
        st.session_state.daily_status = {str(i): "O" for i in range(1, 32)}

    if loaded_record and 'loaded_ts_id' not in st.session_state:
        st.session_state.loaded_ts_id = True
        for i in range(1, 32):
            key_day = f"Day_{i}"
            if key_day in loaded_record:
                st.session_state.daily_status[str(i)] = str(loaded_record[key_day])

    st.markdown("---")
    st.markdown("#### ⚙️ Input Status Operasional Harian (1 s/d 31)")
    st.info("💡 Keterangan Kode: **O** = Operation, **S** = Standby, **R** = Perbaikan (Breakdown), **M** = Mobilisasi.")

    status_options = ["O", "S", "R", "M"]
    
    st.markdown("**Tanggal 01 s.d. 16:**")
    cols_1 = st.columns(8)
    for i in range(1, 9):
        with cols_1[i-1]:
            st.session_state.daily_status[str(i)] = st.selectbox(f"Tgl {i}", status_options, index=status_options.index(st.session_state.daily_status.get(str(i), "O")), key=f"ts_tgl_{i}")
    cols_2 = st.columns(8)
    for i in range(9, 17):
        with cols_2[i-9]:
            st.session_state.daily_status[str(i)] = st.selectbox(f"Tgl {i}", status_options, index=status_options.index(st.session_state.daily_status.get(str(i), "O")), key=f"ts_tgl_{i}")

    st.markdown("**Tanggal 17 s.d. 31:**")
    cols_3 = st.columns(8)
    for i in range(17, 25):
        with cols_3[i-17]:
            st.session_state.daily_status[str(i)] = st.selectbox(f"Tgl {i}", status_options, index=status_options.index(st.session_state.daily_status.get(str(i), "O")), key=f"ts_tgl_{i}")
    cols_4 = st.columns(8)
    for i in range(25, 32):
        with cols_4[i-25]:
            st.session_state.daily_status[str(i)] = st.selectbox(f"Tgl {i}", status_options, index=status_options.index(st.session_state.daily_status.get(str(i), "O")), key=f"ts_tgl_{i}")

    total_O = sum(1 for i in range(1, 32) if st.session_state.daily_status.get(str(i)) == "O")
    total_S = sum(1 for i in range(1, 32) if st.session_state.daily_status.get(str(i)) == "S")
    total_R = sum(1 for i in range(1, 32) if st.session_state.daily_status.get(str(i)) == "R")
    total_M = sum(1 for i in range(1, 32) if st.session_state.daily_status.get(str(i)) == "M")

    # Hitung jumlah hari dalam bulan terpilih untuk perhitungan prorata
    _, last_day = calendar.monthrange(int(pilih_tahun), daftar_bulan.index(pilih_bulan) + 1)
    
    # Kalkulasi Volume Final Berdasarkan Pilihan Skema Sewa
    volume_final = hitung_volume_bayar(total_O, total_S, total_R, total_M, last_day, skema_sewa_pilihan)

    st.markdown("---")
    st.markdown("#### 👥 Otoritas Penandatangan Dokumen")
    c_sign1, c_sign2, c_sign3 = st.columns(3)
    with c_sign1:
        dibuat_oleh = st.text_input("Dibuat Oleh (BSS):", value="Elvira Sutrisno")
    with c_sign2:
        diperiksa_oleh = st.text_input("Diperiksa Oleh (BSS):", value="Ireine Langi")
    with c_sign3:
        disetujui_oleh = st.text_input("Disetujui Oleh (BSS):", value="Onesimus Suriadi")

    st.markdown("<br>", unsafe_allow_html=True)
    c_btn_s1, c_btn_s2 = st.columns(2)
    with c_btn_s1:
        simpan_mode = st.button("💾 Simpan / Update Data Timesheet", use_container_width=True, type="primary")
    with c_btn_s2:
        save_as_mode = st.button("📥 Save As (Simpan Sebagai Baru)", use_container_width=True)

    if simpan_mode or save_as_mode:
        record = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "PI No.": nomor_pi_ref,
            "Nomor Kontrak": nomor_kontrak,
            "Nomor PO": nomor_po_opsional,
            "Skema Sewa": skema_sewa_pilihan,
            "Customer": customer_user,
            "Proyek": proyek_teks,
            "Sub Pekerjaan": sub_pekerjaan_teks,
            "Periode": periode_teks_input,
            "Note": note_teks,
            "Volume_Quantity": volume_final,  # Volume final untuk ditarik ke Rincian Pekerjaan & PI
            "Satuan": "Hari" if skema_sewa_pilihan == "Monthly" else "Unit",
            "Total Operation (O)": total_O,
            "Total Standby (S)": total_S,
            "Total Perbaikan (R)": total_R,
            "Total Mobilisasi (M)": total_M,
            "Dibuat": dibuat_oleh,
            "Diperiksa": diperiksa_oleh,
            "Disetujui": disetujui_oleh
        }
        for i in range(1, 32):
            record[f"Day_{i}"] = st.session_state.daily_status.get(str(i), "O")

        try:
            if os.path.exists(ts_db_path):
                df_ts = pd.read_excel(ts_db_path)
                if simpan_mode:
                    if "PI No." in df_ts.columns and "Sub Pekerjaan" in df_ts.columns:
                        df_ts = df_ts[~((df_ts["PI No."].astype(str).str.strip() == nomor_pi_ref) & (df_ts["Sub Pekerjaan"].astype(str).str.strip() == sub_pekerjaan_teks))]
                df_ts = pd.concat([df_ts, pd.DataFrame([record])], ignore_index=True)
            else:
                df_ts = pd.DataFrame([record])
            
            df_ts.to_excel(ts_db_path, index=False)
            st.success(f"✅ Data timesheet berhasil disimpan! Skema: {skema_sewa_pilihan} | Volume Tertagih: {volume_final}")
        except Exception as e:
            st.error(f"Gagal menyimpan data timesheet: {e}")

    # --- HTML RENDER FORMAT ISO ---
    th_cells = "".join([f"<th style='border:1px solid #000; padding:2px; text-align:center; font-size:8px;'>{i}</th>" for i in range(1, 32)])
    td_cells = "".join([f"<td style='border:1px solid #000; padding:2px; text-align:center; font-size:8px;'><b>{st.session_state.daily_status.get(str(i), 'O')}</b></td>" for i in range(1, 32)])

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Rekap Timesheet Peralatan - FM-GS-06 Rev.03</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; padding: 15px; margin: 0; font-size: 9px; line-height: 1.2; }}
            .iso-code {{ text-align: right; font-weight: bold; font-size: 9px; margin-bottom: 2px; }}
            .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 4px; margin-bottom: 6px; }}
            .title {{ text-align: center; font-weight: bold; font-size: 11px; margin-bottom: 10px; text-transform: uppercase; text-decoration: underline; }}
            
            table.info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 8px; font-size: 9px; }}
            table.info-table td {{ border: none; padding: 2px 3px; vertical-align: top; }}
            
            table.ts-grid {{ width: 100%; border-collapse: collapse; margin-bottom: 6px; }}
            table.ts-grid th, table.ts-grid td {{ border: 1px solid #000; vertical-align: middle; }}
            .th-header {{ background-color: #f1f5f9; font-weight: bold; text-align: center; font-size: 8px; padding: 3px; }}
            
            .bottom-section {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            .bottom-section td {{ border: 1px solid #000; vertical-align: top; padding: 4px; font-size: 8px; }}
        </style>
    </head>
    <body>
        <div class="iso-code">FM-GS-06 Rev.03</div>
        <div class="header">
            <h2 style="margin: 0; font-size: 12px;">PT. BANGGAI SENTRAL SULAWESI</h2>
            <p style="margin: 1px 0; font-size: 7px;">JL. URIP SUMOHARJO NO. 53, TELP 0461-21025, 21185, 21307. LUWUK</p>
        </div>

        <div class="title">REKAP TIME SHEET PERALATAN (PI REF: {nomor_pi_ref})</div>

        <table class="info-table">
            <tr>
                <td style="width: 15%; font-weight: bold;">Customer / User</td>
                <td style="width: 2%;">:</td>
                <td style="width: 45%;"><b>{customer_user}</b></td>
                <td style="width: 15%; font-weight: bold;">Skema Sewa</td>
                <td style="width: 2%;">:</td>
                <td style="width: 21%;"><b>{skema_sewa_pilihan}</b></td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Nomor Kontrak</td>
                <td>:</td>
                <td><b>{nomor_kontrak}</b></td>
                <td style="font-weight: bold;">Nomor PO</td>
                <td>:</td>
                <td><b>{nomor_po_opsional}</b></td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Proyek</td>
                <td>:</td>
                <td colspan="4">{proyek_teks}</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Sub Pekerjaan</td>
                <td>:</td>
                <td colspan="4"><b>{sub_pekerjaan_teks}</b></td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Periode</td>
                <td>:</td>
                <td colspan="4"><b>{periode_teks_input}</b></td>
            </tr>
        </table>

        <table class="ts-grid">
            <tr>
                <th class="th-header" rowspan="2" style="width: 20%;">No / Nama Alat / Status</th>
                <th class="th-header" colspan="31">TANGGAL BULAN {pilih_bulan.upper()} {pilih_tahun}</th>
                <th class="th-header" colspan="4">TOTAL</th>
            </tr>
            <tr>
                {th_cells}
                <th class="th-header" style="background:#e2e8f0;">O</th>
                <th class="th-header" style="background:#e2e8f0;">S</th>
                <th class="th-header" style="background:#e2e8f0;">R</th>
                <th class="th-header" style="background:#e2e8f0;">M</th>
            </tr>
            <tr>
                <td style="padding: 4px; font-size: 8px; text-align: center;"><b>1. {sub_pekerjaan_teks}</b></td>
                {td_cells}
                <td style="text-align:center; font-weight:bold; background:#f8fafc;">{total_O}</td>
                <td style="text-align:center; font-weight:bold; background:#f8fafc;">{total_S}</td>
                <td style="text-align:center; font-weight:bold; background:#f8fafc;">{total_R}</td>
                <td style="text-align:center; font-weight:bold; background:#f8fafc;">{total_M}</td>
            </tr>
        </table>

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 5px;">
            <tr>
                <td style="font-size: 8px; width: 50%;">
                    <b>KODE STATUS :</b> &nbsp;
                    <b>O</b> Operation &nbsp;|&nbsp; 
                    <b>S</b> Standby &nbsp;|&nbsp; 
                    <b>R</b> Perbaikan &nbsp;|&nbsp; 
                    <b>M</b> Mobilisasi
                </td>
                <td style="text-align: right; font-weight: bold; font-size: 9px; background: #e2e8f0; border: 1px solid #000; padding: 3px;">
                    GRAND TOTAL &nbsp;&nbsp;&nbsp; {total_O} &nbsp;&nbsp; {total_S} &nbsp;&nbsp; {total_R} &nbsp;&nbsp; {total_M}
                </td>
            </tr>
        </table>

        <table class="bottom-section">
            <tr>
                <td style="width: 35%;">
                    <b>NOTE :</b><br>
                    {note_teks}<br><br><br>
                </td>
                <td style="width: 30%;">
                    <div style="text-align: center; font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 2px; margin-bottom: 2px;">{customer_user}</div>
                    <table style="width: 100%; border-collapse: collapse; text-align: center;">
                        <tr>
                            <td style="border: 1px solid #000; height: 55px; width: 33%;"></td>
                            <td style="border: 1px solid #000; height: 55px; width: 33%;"></td>
                            <td style="border: 1px solid #000; height: 55px; width: 34%;"></td>
                        </tr>
                    </table>
                </td>
                <td style="width: 35%;">
                    <div style="text-align: center; font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 2px; margin-bottom: 2px;">PT. Banggai Sentral Sulawesi</div>
                    <table style="width: 100%; border-collapse: collapse; text-align: center; font-size: 7px;">
                        <tr>
                            <td style="border: 1px solid #000; width: 33%; vertical-align: top; height: 55px; padding-top: 2px; position: relative;">
                                Dibuat
                                <div style="position: absolute; bottom: 3px; left: 0; right: 0; font-weight: bold;">{dibuat_oleh}</div>
                            </td>
                            <td style="border: 1px solid #000; width: 33%; vertical-align: top; height: 55px; padding-top: 2px; position: relative;">
                                Diperiksa
                                <div style="position: absolute; bottom: 3px; left: 0; right: 0; font-weight: bold;">{diperiksa_oleh}</div>
                            </td>
                            <td style="border: 1px solid #000; width: 34%; vertical-align: top; height: 55px; padding-top: 2px; position: relative;">
                                Disetujui
                                <div style="position: absolute; bottom: 3px; left: 0; right: 0; font-weight: bold;">{disetujui_oleh}</div>
                            </td>
                        </tr>
                    </table>
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
                    win.document.open();
                    win.document.write(atob("{b64_html}"));
                    win.document.close();
                    win.focus();
                    setTimeout(function(){{ win.print(); }}, 500);
                }}
            </script>
            <button onclick="printDoc()" style="width: 100%; background-color: #10b981; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
                🖨️ Cetak / Print Timesheet (ISO Standard)
            </button>
        """
        st.components.v1.html(print_script, height=50)

    with col_btn2:
        b64_pdf = base64.b64encode(html_content.encode()).decode()
        download_link = f'<a href="data:text/html;base64,{b64_pdf}" download="Timesheet_ISO_{nomor_pi_ref.replace("/", "_")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download File Timesheet (ISO)</button></a>'
        st.markdown(download_link, unsafe_allow_html=True)