import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime

def tampilkan_timesheet(transaksi_list):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">🕒 Pengelolaan & Pratinjau Rekap Timesheet Peralatan</h3>
        </div>
    """, unsafe_allow_html=True)

    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi kontrak atau alat yang tersedia.")
        return

    # Ambil daftar unik kontrak / alat dari transaksi
    seen_contract = set()
    unique_contracts = []
    for t in transaksi_list:
        kontrak_key = str(t.get('Nomor Kontrak', ''))
        if kontrak_key not in seen_contract:
            seen_contract.add(kontrak_key)
            unique_contracts.append(t)

    pilihan_kontrak = [f"Kontrak: {c['Nomor Kontrak']} | User: {c.get('Ditujukan Kepada', 'JOB Pertamina-Medco')} | Alat: {c.get('Nama Kontrak', 'Sewa Alat Berat')}" for c in unique_contracts]
    
    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        selected_idx = st.selectbox("Pilih Kontrak / Proyek Alat:", range(len(pilihan_kontrak)), format_func=lambda x: pilihan_kontrak[x], key="ts_select_kontrak")
    with col_s2:
        periode_bulan = st.selectbox("Periode Bulan:", ["Juli 2026", "Agustus 2026", "September 2026", "Oktober 2026", "November 2026", "Desember 2026"], key="ts_periode_bulan")

    c_data = unique_contracts[selected_idx]
    nomor_kontrak = str(c_data.get('Nomor Kontrak', '7207250142')).strip()
    customer_user = str(c_data.get('Ditujukan Kepada', 'JOB Pertamina - Medco E&P Tomori Sulawesi')).strip()
    nama_alat = str(c_data.get('Nama Kontrak', 'Boom Truck ( TMC ) 8 ton / Backhoe Loader')).strip()

    st.markdown("---")
    st.markdown("#### ⚙️ Input Status Operasional Harian (1 s/d 31)")
    st.info("💡 Keterangan Kode: **O** = Operation, **S** = Standby, **R** = Perbaikan, **M** = Mobilisasi[cite: 2].")

    # Inisialisasi state status harian 1-31 jika belum ada
    if 'daily_status' not in st.session_state:
        st.session_state.daily_status = {str(i): "O" for i in range(1, 32)}

    # Buat form input grid per tanggal (dibagi dalam beberapa kolom agar rapi)
    status_options = ["O", "S", "R", "M"]
    
    # Grid Tanggal 1 s.d 16
    st.markdown("**Tanggal 01 s.d. 16:**")
    cols_1 = st.columns(8)
    for i in range(1, 9):
        with cols_1[i-1]:
            st.session_state.daily_status[str(i)] = st.selectbox(f"Tgl {i}", status_options, index=status_options.index(st.session_state.daily_status.get(str(i), "O")), key=f"ts_tgl_{i}")
    cols_2 = st.columns(8)
    for i in range(9, 17):
        with cols_2[i-9]:
            st.session_state.daily_status[str(i)] = st.selectbox(f"Tgl {i}", status_options, index=status_options.index(st.session_state.daily_status.get(str(i), "O")), key=f"ts_tgl_{i}")

    # Grid Tanggal 17 s.d 31
    st.markdown("**Tanggal 17 s.d. 31:**")
    cols_3 = st.columns(8)
    for i in range(17, 25):
        with cols_3[i-17]:
            st.session_state.daily_status[str(i)] = st.selectbox(f"Tgl {i}", status_options, index=status_options.index(st.session_state.daily_status.get(str(i), "O")), key=f"ts_tgl_{i}")
    cols_4 = st.columns(8)
    for i in range(25, 32):
        with cols_4[i-25]:
            st.session_state.daily_status[str(i)] = st.selectbox(f"Tgl {i}", status_options, index=status_options.index(st.session_state.daily_status.get(str(i), "O")), key=f"ts_tgl_{i}")

    # Hitung Akumulasi Total Status Secara Otomatis
    total_O = sum(1 for i in range(1, 32) if st.session_state.daily_status.get(str(i)) == "O")
    total_S = sum(1 for i in range(1, 32) if st.session_state.daily_status.get(str(i)) == "S")
    total_R = sum(1 for i in range(1, 32) if st.session_state.daily_status.get(str(i)) == "R")
    total_M = sum(1 for i in range(1, 32) if st.session_state.daily_status.get(str(i)) == "M")
    grand_total = total_O + total_S + total_R + total_M

    st.markdown("---")
    st.markdown("#### 👥 Otoritas Penandatangan Dokumen")
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        dibuat_oleh = st.text_input("Dibuat Oleh:", value="Elvira Sutrisno / Ireine Langi")
    with col_p2:
        diperiksa_oleh = st.text_input("Diperiksa Oleh:", value="Onesimus Suriadi")
    with col_p3:
        disetujui_oleh = st.text_input("Disetujui Oleh (User):", value="Representative User JOB")

    # Fitur Simpan ke Database Histori Timesheet
    if st.button("💾 Simpan Rekap Timesheet ke Database", use_container_width=True, type="primary"):
        db_folder = "database_penyimpanan_aman"
        os.makedirs(db_folder, exist_ok=True)
        ts_db_path = os.path.join(db_folder, "database_timesheet_history.xlsx")

        record = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Nomor Kontrak": nomor_kontrak,
            "Customer": customer_user,
            "Nama Alat": nama_alat,
            "Periode": periode_bulan,
            "Total Operation (O)": total_O,
            "Total Standby (S)": total_S,
            "Total Perbaikan (R)": total_R,
            "Total Mobilisasi (M)": total_M,
            "Dibuat": dibuat_oleh,
            "Diperiksa": diperiksa_oleh,
            "Disetujui": disetujui_oleh
        }

        try:
            if os.path.exists(ts_db_path):
                df_ts = pd.read_excel(ts_db_path)
                df_ts = df_ts[df_ts["Nomor Kontrak"].astype(str).str.strip() != nomor_kontrak]
                df_ts = pd.concat([df_ts, pd.DataFrame([record])], ignore_index=True)
            else:
                df_ts = pd.DataFrame([record])
            
            df_ts.to_excel(ts_db_path, index=False)
            st.success("✅ Rekap timesheet berhasil disimpan ke database historis!")
        except Exception as e:
            st.error(f"Gagal menyimpan rekap timesheet: {e}")

    # --- HTML RENDER DOKUMEN RESMI TIMESHEET ---
    # Membangun baris tabel tanggal 1 sampai 31 untuk HTML pratinjau/cetak
    th_cells = "".join([f"<th style='border:1px solid #000; padding:4px; text-align:center; font-size:9px;'>{i}</th>" for i in range(1, 32)])
    td_cells = "".join([f"<td style='border:1px solid #000; padding:4px; text-align:center; font-size:9px;'><b>{st.session_state.daily_status.get(str(i), 'O')}</b></td>" for i in range(1, 32)])

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Rekap Timesheet Peralatan - PT BSS</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; padding: 25px; margin: 0; font-size: 10px; line-height: 1.3; }}
            .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 6px; margin-bottom: 10px; }}
            .title {{ text-align: center; font-weight: bold; font-size: 12px; margin-bottom: 15px; text-transform: uppercase; text-decoration: underline; }}
            
            table.info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 10px; }}
            table.info-table td {{ border: none; padding: 2px 4px; vertical-align: top; }}
            
            table.ts-grid {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
            table.ts-grid th, table.ts-grid td {{ border: 1px solid #000; vertical-align: middle; }}
            .th-header {{ background-color: #f1f5f9; font-weight: bold; text-align: center; font-size: 9px; padding: 5px; }}
            
            .legend {{ font-size: 9px; margin-top: 10px; margin-bottom: 15px; }}
            .sign-section {{ width: 100%; border-collapse: collapse; margin-top: 25px; text-align: center; }}
            .sign-section td {{ border: 1px solid #000; padding: 6px; font-size: 9px; width: 33%; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2 style="margin: 0; font-size: 14px;">PT. BANGGAI SENTRAL SULAWESI</h2>
            <p style="margin: 2px 0; font-size: 8px;">JL. URIP SUMOHARJO NO. 53, TELP 0461-21025, 21185, 21307. LUWUK[cite: 2]</p>
        </div>

        <div class="title">REKAP TIME SHEET PERALATAN</div>

        <table class="info-table">
            <tr>
                <td style="width: 18%; font-weight: bold;">Customer / User</td>
                <td style="width: 2%;">:</td>
                <td style="width: 45%;"><b>{customer_user}</b></td>
                <td style="width: 15%; font-weight: bold;">Periode</td>
                <td style="width: 2%;">:</td>
                <td style="width: 18%;"><b>01 s/d {periode_bulan}</b>[cite: 2]</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Kontrak / SO No.</td>
                <td>:</td>
                <td><b>{nomor_kontrak}</b>[cite: 2]</td>
                <td style="font-weight: bold;">Nomor Alat</td>
                <td>:</td>
                <td><b>1</b>[cite: 2]</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Sub Pekerjaan</td>
                <td colspan="5">{nama_alat}[cite: 2]</td>
            </tr>
        </table>

        <table class="ts-grid">
            <tr>
                <th class="th-header" rowspan="2" style="width: 25%;">No / Nama Alat / Status[cite: 2]</th>
                <th class="th-header" colspan="31">TANGGAL BULAN {periode_bulan.upper()}</th>
                <th class="th-header" colspan="4">TOTAL[cite: 2]</th>
            </tr>
            <tr>
                {th_cells}
                <th class="th-header" style="background:#e2e8f0;">O</th>
                <th class="th-header" style="background:#e2e8f0;">S</th>
                <th class="th-header" style="background:#e2e8f0;">R</th>
                <th class="th-header" style="background:#e2e8f0;">M</th>
            </tr>
            <tr>
                <td style="padding: 6px; font-size: 9px;"><b>1. {nama_alat}</b></td>
                {td_cells}
                <td style="text-align:center; font-weight:bold; background:#f8fafc;">{total_O}</td>
                <td style="text-align:center; font-weight:bold; background:#f8fafc;">{total_S}</td>
                <td style="text-align:center; font-weight:bold; background:#f8fafc;">{total_R}</td>
                <td style="text-align:center; font-weight:bold; background:#f8fafc;">{total_M}</td>
            </tr>
        </table>

        <div class="legend">
            <b>KODE STATUS[cite: 2]:</b><br>
            <b>O</b> = Operation (Operasi) &nbsp;|&nbsp; <b>S</b> = Standby &nbsp;|&nbsp; <b>R</b> = Perbaikan (Breakdown) &nbsp;|&nbsp; <b>M</b> = Mobilisasi[cite: 2]
        </div>

        <table class="sign-section">
            <tr>
                <td><b>Dibuat[cite: 2]</b><br><br><br><br><u>{dibuat_oleh}</u></td>
                <td><b>Diperiksa[cite: 2]</b><br><br><br><br><u>{diperiksa_oleh}</u><br>Manager General Services</td>
                <td><b>Disetujui[cite: 2]</b><br><br><br><br><u>{disetujui_oleh}</u><br>Representative User</td>
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
                🖨️ Cetak / Print Timesheet (Klik Disini)
            </button>
        """
        st.components.v1.html(print_script, height=50)

    with col_btn2:
        b64_pdf = base64.b64encode(html_content.encode()).decode()
        download_link = f'<a href="data:text/html;base64,{b64_pdf}" download="Timesheet_{nomor_kontrak}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download File Timesheet</button></a>'
        st.markdown(download_link, unsafe_allow_html=True)