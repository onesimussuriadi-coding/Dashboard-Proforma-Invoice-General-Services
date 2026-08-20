import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime
import calendar

def hitung_volume_bayar(total_O, total_S, total_R, total_M, hari_dalam_bulan, skema_sewa):
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
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">🕒 Pengelolaan & History Timesheet Peralatan Berbasis Kalender (FM-GS-06 Rev.03)</h3>
        </div>
    """, unsafe_allow_html=True)

    db_folder = "database_penyimpanan_aman"
    os.makedirs(db_folder, exist_ok=True)
    ts_db_path = os.path.join(db_folder, "database_timesheet_history.xlsx")

    # --- INISIALISASI SESSION STATE HARIAN ---
    if 'daily_status' not in st.session_state:
        st.session_state.daily_status = {str(i): "O" for i in range(1, 32)}

    if 'loaded_ts_record' not in st.session_state:
        st.session_state.loaded_ts_record = None

    # --- FITUR TABEL LIHAT & HAPUS HISTORY TERSIMPAN ---
    with st.expander("📋 Lihat Daftar Seluruh History Timesheet Tersimpan & Manajemen Data", expanded=False):
        if os.path.exists(ts_db_path):
            try:
                df_all_hist = pd.read_excel(ts_db_path)
                if not df_all_hist.empty:
                    st.dataframe(df_all_hist[["Nomor Kontrak", "Sub Pekerjaan", "Periode", "Skema Sewa", "Volume_Quantity", "Timestamp"]], use_container_width=True)
                    
                    st.markdown("##### 🗑️ Hapus Data Timesheet yang Keliru")
                    del_options = [f"Idx {idx}: Kontrak {row.get('Nomor Kontrak','')} - {row.get('Sub Pekerjaan','')} ({row.get('Periode','')})" for idx, row in df_all_hist.iterrows()]
                    selected_to_delete = st.selectbox("Pilih data yang ingin dihapus:", ["-- Pilih Data --"] + del_options, key="select_del_timesheet")
                    
                    if selected_to_delete != "-- Pilih Data --":
                        if st.button("🗑️ Hapus Data Terpilih", type="primary", key="btn_execute_delete_ts"):
                            idx_to_del = int(selected_to_delete.split(":")[0].replace("Idx", "").strip())
                            df_all_hist = df_all_hist.drop(idx_to_del).reset_index(drop=True)
                            df_all_hist.to_excel(ts_db_path, index=False)
                            st.success("✅ Data timesheet berhasil dihapus dari database!")
                            st.rerun()
                else:
                    st.info("Belum ada riwayat data timesheet di database.")
            except Exception as e:
                st.warning(f"Gagal memuat tabel riwayat: {e}")
        else:
            st.info("Database history timesheet belum terbentuk.")

    # --- FITUR PEMANGGILAN HISTORY / LOAD DATA TERSIMPAN ---
    st.markdown("#### 📂 Panggil History Timesheet Tersimpan (Untuk Update Harian)")
    
    if os.path.exists(ts_db_path):
        try:
            df_hist_check = pd.read_excel(ts_db_path)
            if not df_hist_check.empty:
                df_hist_check['Label_History'] = df_hist_check['Nomor Kontrak'].astype(str) + " | " + df_hist_check['Sub Pekerjaan'].astype(str) + " | Periode: " + df_hist_check['Periode'].astype(str)
                list_history_opt = df_hist_check['Label_History'].tolist()
                
                c_load1, c_load2 = st.columns([3, 1])
                with c_load1:
                    selected_hist_label = st.selectbox("Pilih Riwayat Timesheet Tersimpan:", list_history_opt, key="select_history_timesheet")
                with c_load2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("📂 Load / Panggil Data", key="btn_execute_load_history", type="secondary"):
                        matched_row = df_hist_check[df_hist_check['Label_History'] == selected_hist_label]
                        if not matched_row.empty:
                            loaded_record = matched_row.iloc[0].to_dict()
                            st.session_state.loaded_ts_record = loaded_record
                            
                            # SINKRONISASI MUTLAK KE SESSION STATE & WIDGET KEY
                            for i in range(1, 32):
                                k_day = f"Day_{i}"
                                val_day = str(loaded_record.get(k_day, "O"))
                                if val_day in ["O", "S", "R", "M"]:
                                    st.session_state.daily_status[str(i)] = val_day
                                    st.session_state[f"ts_tgl_{i}"] = val_day  
                                else:
                                    st.session_state.daily_status[str(i)] = "O"
                                    st.session_state[f"ts_tgl_{i}"] = "O"
                                    
                            st.success("✅ History timesheet berhasil dimuat ke form dan status harian!")
                            st.rerun()
        except Exception as e:
            st.warning(f"Terjadi kesalahan saat memuat data: {e}")

    loaded_record = st.session_state.loaded_ts_record

    # 1. Pilihan Bulan & Tahun sebagai basis utama periode
    col_bln1, col_bln2 = st.columns(2)
    daftar_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    default_bulan_idx = 6
    if loaded_record and 'Periode' in loaded_record:
        for idx, b in enumerate(daftar_bulan):
            if b.lower() in str(loaded_record['Periode']).lower():
                default_bulan_idx = idx
                break

    with col_bln1:
        pilih_bulan = st.selectbox("📅 Pilih Bulan:", daftar_bulan, index=default_bulan_idx, key="ts_pilih_bulan")
    with col_bln2:
        pilih_tahun = st.selectbox("📆 Pilih Tahun:", [str(y) for y in range(2026, 2036)], index=0, key="ts_pilih_tahun")

    # --- KONFIGURASI KONTRAK & SKEMA SEWA ---
    st.markdown("---")
    st.markdown("#### 📋 Konfigurasi Kontrak & Skema Perhitungan Timesheet")
    
    default_no_kontrak = str(loaded_record.get('Nomor Kontrak', '7207250142')) if loaded_record else '7207250142'
    default_no_po = str(loaded_record.get('Nomor PO', '4500011424')) if loaded_record else '4500011424'
    default_skema = str(loaded_record.get('Skema Sewa', 'Monthly')) if loaded_record else 'Monthly'
    skema_list = ["Monthly", "Daily", "Mobilisasi", "Provisional Sum"]
    default_skema_idx = skema_list.index(default_skema) if default_skema in skema_list else 0

    c_cfg1, c_cfg2, c_cfg3 = st.columns(3)
    with c_cfg1:
        nomor_kontrak = st.text_input("Nomor Kontrak Rujukan:", value=default_no_kontrak, key="ts_input_no_kontrak")
    with c_cfg2:
        nomor_po_opsional = st.text_input("Nomor PO (Opsional):", value=default_no_po, key="ts_input_no_po")
    with c_cfg3:
        skema_sewa_pilihan = st.selectbox("Skema Perhitungan Sewa:", skema_list, index=default_skema_idx, key="ts_skema_sewa_pilihan")

    default_cust = str(loaded_record.get('Customer', 'JOB Pertamina - Medco E&P Tomori Sulawesi')) if loaded_record else 'JOB Pertamina - Medco E&P Tomori Sulawesi'
    default_proyek = str(loaded_record.get('Proyek', 'Jasa Sewa Alat Berat Pendukung Operasional Senoro dan Tiaka')) if loaded_record else 'Jasa Sewa Alat Berat Pendukung Operasional Senoro dan Tiaka'

    c_usr1, c_usr2 = st.columns(2)
    with c_usr1:
        customer_user = st.text_input("Customer / User:", value=default_cust, key="ts_input_customer")
    with c_usr2:
        proyek_teks = st.text_input("Nama Proyek / Kontrak:", value=default_proyek, key="ts_input_proyek")

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

    default_sub_alat = str(loaded_record.get('Sub Pekerjaan', master_alat_list[0])) if loaded_record else master_alat_list[0]
    default_alat_idx = master_alat_list.index(default_sub_alat) if default_sub_alat in master_alat_list else 0

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

    sub_pekerjaan_teks = st.selectbox("📋 Pilih Sub Pekerjaan / Nama Alat Aktual:", master_alat_list, index=default_alat_idx, key="ts_dropdown_alat_dinamis")
    default_note = str(loaded_record.get('Note', '')) if loaded_record else ''
    note_teks = st.text_input("Catatan / Note:", value=default_note, key="ts_note_input")

    st.markdown("---")
    st.markdown("#### ⚙️ Input Status Operasional Harian (1 s/d 31)")
    st.info("💡 Keterangan Kode: **O** = Operation, **S** = Standby, **R** = Perbaikan (Breakdown), **M** = Mobilisasi.")

    status_options = ["O", "S", "R", "M"]
    
    st.markdown("**Tanggal 01 s.d. 16:**")
    cols_1 = st.columns(8)
    for i in range(1, 9):
        with cols_1[i-1]:
            cur_val = st.session_state.daily_status.get(str(i), "O")
            idx_val = status_options.index(cur_val) if cur_val in status_options else 0
            st.session_state.daily_status[str(i)] = st.selectbox(f"Tgl {i}", status_options, index=idx_val, key=f"ts_tgl_{i}")
    cols_2 = st.columns(8)
    for i in range(9, 17):
        with cols_2[i-9]:
            cur_val = st.session_state.daily_status.get(str(i), "O")
            idx_val = status_options.index(cur_val) if cur_val in status_options else 0
            st.session_state.daily_status[str(i)] = st.selectbox(f"Tgl {i}", status_options, index=idx_val, key=f"ts_tgl_{i}")

    st.markdown("**Tanggal 17 s.d. 31:**")
    cols_3 = st.columns(8)
    for i in range(17, 25):
        with cols_3[i-17]:
            cur_val = st.session_state.daily_status.get(str(i), "O")
            idx_val = status_options.index(cur_val) if cur_val in status_options else 0
            st.session_state.daily_status[str(i)] = st.selectbox(f"Tgl {i}", status_options, index=idx_val, key=f"ts_tgl_{i}")
    cols_4 = st.columns(8)
    for i in range(25, 32):
        with cols_4[i-25]:
            cur_val = st.session_state.daily_status.get(str(i), "O")
            idx_val = status_options.index(cur_val) if cur_val in status_options else 0
            st.session_state.daily_status[str(i)] = st.selectbox(f"Tgl {i}", status_options, index=idx_val, key=f"ts_tgl_{i}")

    total_O = sum(1 for i in range(1, 32) if st.session_state.daily_status.get(str(i)) == "O")
    total_S = sum(1 for i in range(1, 32) if st.session_state.daily_status.get(str(i)) == "S")
    total_R = sum(1 for i in range(1, 32) if st.session_state.daily_status.get(str(i)) == "R")
    total_M = sum(1 for i in range(1, 32) if st.session_state.daily_status.get(str(i)) == "M")

    _, last_day = calendar.monthrange(int(pilih_tahun), daftar_bulan.index(pilih_bulan) + 1)
    volume_final = hitung_volume_bayar(total_O, total_S, total_R, total_M, last_day, skema_sewa_pilihan)

    st.markdown("---")
    st.markdown("#### 👥 Otoritas Penandatangan Dokumen")
    
    default_buat = str(loaded_record.get('Dibuat', 'Elvira Sutrisno')) if loaded_record else 'Elvira Sutrisno'
    default_cek = str(loaded_record.get('Diperiksa', 'Ireine Langi')) if loaded_record else 'Ireine Langi'
    default_setuju = str(loaded_record.get('Disetujui', 'Onesimus Suriadi')) if loaded_record else 'Onesimus Suriadi'

    c_sign1, c_sign2, c_sign3 = st.columns(3)
    with c_sign1:
        dibuat_oleh = st.text_input("Dibuat Oleh (BSS):", value=default_buat, key="ts_sign_dibuat")
    with c_sign2:
        diperiksa_oleh = st.text_input("Diperiksa Oleh (BSS):", value=default_cek, key="ts_sign_diperiksa")
    with c_sign3:
        disetujui_oleh = st.text_input("Disetujui Oleh (BSS):", value=default_setuju, key="ts_sign_disetujui")

    st.markdown("<br>", unsafe_allow_html=True)
    c_btn_s1, c_btn_s2 = st.columns(2)
    with c_btn_s1:
        simpan_mode = st.button("💾 Simpan / Update Data Timesheet", use_container_width=True, type="primary")
    with c_btn_s2:
        save_as_mode = st.button("📥 Save As (Simpan Sebagai Baru)", use_container_width=True)

    if simpan_mode or save_as_mode:
        record = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Nomor Kontrak": nomor_kontrak,
            "Nomor PO": nomor_po_opsional,
            "Skema Sewa": skema_sewa_pilihan,
            "Customer": customer_user,
            "Proyek": proyek_teks,
            "Sub Pekerjaan": sub_pekerjaan_teks,
            "Periode": periode_teks_input,
            "Note": note_teks,
            "Volume_Quantity": volume_final,
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
                    if "Nomor Kontrak" in df_ts.columns and "Sub Pekerjaan" in df_ts.columns and "Periode" in df_ts.columns:
                        df_ts = df_ts[~((df_ts["Nomor Kontrak"].astype(str).str.strip() == str(nomor_kontrak)) & (df_ts["Sub Pekerjaan"].astype(str).str.strip() == str(sub_pekerjaan_teks)) & (df_ts["Periode"].astype(str).str.strip() == str(periode_teks_input)))]
                df_ts = pd.concat([df_ts, pd.DataFrame([record])], ignore_index=True)
            else:
                df_ts = pd.DataFrame([record])
            
            df_ts.to_excel(ts_db_path, index=False)
            st.success(f"✅ Data timesheet berhasil disimpan / di-update! Skema: {skema_sewa_pilihan} | Volume Tertagih: {volume_final}")
            st.rerun()
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
        <title>Rekap Timesheet Peralatan</title>
        <style>
            @page {{ size: auto; margin: 5mm; }}
            @media print {{
                body {{ margin: 0; }}
            }}
            body {{ font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; padding: 15px; margin: 0; font-size: 9px; line-height: 1.2; position: relative; min-height: 95vh; }}
            .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 4px; margin-bottom: 6px; }}
            .title {{ text-align: center; font-weight: bold; font-size: 11px; margin-bottom: 10px; text-transform: uppercase; text-decoration: underline; }}
            
            table.info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 8px; font-size: 9px; }}
            table.info-table td {{ border: none; padding: 2px 3px; vertical-align: top; }}
            
            table.ts-grid {{ width: 100%; border-collapse: collapse; margin-bottom: 6px; }}
            table.ts-grid th, table.ts-grid td {{ border: 1px solid #000; vertical-align: middle; }}
            .th-header {{ background-color: #f1f5f9; font-weight: bold; text-align: center; font-size: 8px; padding: 3px; }}
            
            .bottom-section {{ width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 25px; }}
            .bottom-section td {{ border: 1px solid #000; vertical-align: top; padding: 4px; font-size: 8px; }}

            .iso-footer-left {{
                position: absolute;
                bottom: 2px;
                left: 15px;
                font-size: 8px;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2 style="margin: 0; font-size: 12px;">PT. BANGGAI SENTRAL SULAWESI</h2>
            <p style="margin: 1px 0; font-size: 7px;">JL. URIP SUMOHARJO NO. 53, TELP 0461-21025, 21185, 21307. LUWUK</p>
        </div>

        <div class="title">REKAP TIME SHEET PERALATAN</div>

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

        <div class="iso-footer-left">FM-GS-06 Rev.03</div>
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
        download_link = f'<a href="data:text/html;base64,{b64_pdf}" download="Timesheet_ISO_{nomor_kontrak}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download File Timesheet (ISO)</button></a>'
        st.markdown(download_link, unsafe_allow_html=True)