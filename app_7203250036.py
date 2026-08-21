import streamlit as st
import os
import pandas as pd

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="PT BSS - Kontrak 7203250036",
    page_icon="🏗️",
    layout="wide"
)

# --- DIREKTORI DATABASE KHUSUS KONTRAK INI ---
DIR_KONTRAK_BARU = "database_penyimpanan_aman_7203250036"

# --- VERIFIKASI LOGIN & MODUL ---
try:
    from modul_keamanan.autentikasi import form_login_sistem, render_panel_manajemen_akun
    import modul_invoice
except Exception as e:
    pass

if 'form_login_sistem' in globals():
    if not form_login_sistem():
        st.stop()
    render_panel_manajemen_akun()

# --- HEADER UTAMA DASHBOARD ---
st.markdown("""
    <div style="padding: 20px; background: #065f46; border-radius: 10px; color: white; text-align: center; margin-bottom: 25px;">
        <h2 style="margin: 0; font-size: 24px;">PT. BANGGAI SENTRAL SULAWESI</h2>
        <p style="margin: 5px 0 0 0; font-size: 14px;">Kontrak No: <b>7203250036</b> | Penyediaan Jasa Penyewaan Alat Berat Warehouse</p>
        <p style="margin: 3px 0 0 0; font-size: 12px; opacity: 0.9;">Klien: JOB Pertamina - Medco E&P Tomori Sulawesi</p>
    </div>
""", unsafe_allow_html=True)

# --- NAVIGASI MODUL UTAMA DI SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 📂 Navigasi Kontrak 7203250036")
pilih_modul = st.sidebar.selectbox("Pilih Modul Utama:", [
    "Modul 0: Master Referensi Harga & Pekerjaan",
    "Modul 1: Database & Master Kontrak",
    "Modul 2: Invoice & Dokumen Turunan"
])

# --- SUB-MENU DI SIDEBAR BERDASARKAN MODUL ---
pilih_sub_menu = ""
if "Modul 0" in pilih_modul:
    st.sidebar.markdown("---")
    pilih_sub_menu = st.sidebar.radio("Pilih Menu:", [
        "Input & Kelola Master Referensi",
        "Lihat Daftar Master Referensi Tersimpan"
    ])
elif "Modul 1" in pilih_modul:
    st.sidebar.markdown("---")
    pilih_sub_menu = st.sidebar.radio("Pilih Menu:", [
        "Input Database & Invoice (29 Kolom)",
        "Lihat Database Tersimpan"
    ])

# Indikator Status Folder Aman di Sidebar
st.sidebar.markdown("---")
st.sidebar.success(f"Status Sistem:\nTerhubung ke Folder Aman\n(`{DIR_KONTRAK_BARU}`)")

# --- PATH FILE DATABASE ---
file_path_master = os.path.join(DIR_KONTRAK_BARU, "database_master_referensi.xlsx")
file_path_transaksi = os.path.join(DIR_KONTRAK_BARU, "database_transaksi_rincian.xlsx")

# ==========================================
# EKSEKUSI MODUL 0: MASTER REFERENSI
# ==========================================
if "Modul 0" in pilih_modul:
    if pilih_sub_menu == "Input & Kelola Master Referensi":
        st.subheader("📌 Input & Panggil Kembali Master Referensi Harga Tetap")
        
        list_uraian = ["-- Buat Data Referensi Baru --"]
        try:
            if os.path.exists(file_path_master):
                df_ex = pd.read_excel(file_path_master)
                if "Uraian Pekerjaan" in df_ex.columns:
                    list_uraian.extend(df_ex["Uraian Pekerjaan"].dropna().unique().tolist())
        except Exception:
            pass
        
        col_panggil1, col_panggil2 = st.columns([3, 1])
        with col_panggil1:
            pilihan_panggil = st.selectbox("Panggil Ulang Berdasarkan Uraian Pekerjaan:", list_uraian)
        with col_panggil2:
            st.markdown("<br>", unsafe_allow_html=True)
            btn_panggil = st.button("🔄 Panggil Data Ini", use_container_width=True)
        
        default_uraian = ""
        default_kategori = "MONTHLY BASIS"
        default_harga = 0.0
        default_satuan = "Month"
        
        if btn_panggil and pilihan_panggil != "-- Buat Data Referensi Baru --":
            try:
                if os.path.exists(file_path_master):
                    df_ex = pd.read_excel(file_path_master)
                    matched = df_ex[df_ex["Uraian Pekerjaan"] == pilihan_panggil]
                    if not matched.empty:
                        default_uraian = matched.iloc[0].get("Uraian Pekerjaan", "")
                        default_kategori = matched.iloc[0].get("Kategori", "MONTHLY BASIS")
                        default_harga = float(matched.iloc[0].get("Harga Satuan", 0.0))
                        default_satuan = matched.iloc[0].get("Satuan", "Month")
                        st.success(f"Berhasil memanggil data: {pilihan_panggil}")
            except Exception:
                pass

        with st.form("form_master_lengkap_36"):
            c1, c2 = st.columns(2)
            with c1:
                no_kontrak_ref = st.text_input("Nomor Kontrak Rujukan", value="7203250036")
                
                kategori_list = ["MONTHLY BASIS", "DAILY BASIS", "ADHOC / SPOT HIRE", "JASA MOBILISASI"]
                idx_kat = kategori_list.index(default_kategori) if default_kategori in kategori_list else 0
                kategori_pekerjaan = st.selectbox("Kategori Pekerjaan", kategori_list, index=idx_kat)
                
                satuan_list = ["Month", "Day", "Trip", "Unit", "AU"]
                idx_sat = satuan_list.index(default_satuan) if default_satuan in satuan_list else 0
                satuan_unit = st.selectbox("Satuan Unit", satuan_list, index=idx_sat)
            with c2:
                uraian_pekerjaan = st.text_area("Uraian Pekerjaan / Spesifikasi Alat", value=default_uraian, height=105)
                harga_satuan = st.number_input("Harga Satuan Tetap (Rp)", min_value=0.0, value=default_harga, step=1000.0)
            
            st.markdown("---")
            b_simpan1, b_simpan2 = st.columns(2)
            with b_simpan1:
                btn_simpan_baru = st.form_submit_button("💾 Simpan Master Baru", use_container_width=True)
            with b_simpan2:
                btn_update_saveas = st.form_submit_button("📝 Update Data Dipanggil / Save As", use_container_width=True)
            
            if btn_simpan_baru or btn_update_saveas:
                if not uraian_pekerjaan:
                    st.warning("⚠️ Uraian pekerjaan wajib diisi!")
                else:
                    new_row = {
                        "Nomor Kontrak": no_kontrak_ref,
                        "Kategori": kategori_pekerjaan,
                        "Uraian Pekerjaan": uraian_pekerjaan,
                        "Satuan": satuan_unit,
                        "Harga Satuan": harga_satuan
                    }
                    df_new = pd.DataFrame([new_row])
                    try:
                        if os.path.exists(file_path_master):
                            df_old = pd.read_excel(file_path_master)
                            if btn_update_saveas and pilihan_panggil != "-- Buat Data Referensi Baru --":
                                df_old = df_old[df_old["Uraian Pekerjaan"] != pilihan_panggil]
                            df_combined = pd.concat([df_old, df_new], ignore_index=True)
                            df_combined.to_excel(file_path_master, index=False)
                        else:
                            df_new.to_excel(file_path_master, index=False)
                        st.success("🎉 Master referensi berhasil disimpan ke database kontrak 7203250036!")
                    except Exception as e:
                        st.error(f"Gagal menyimpan file: {e}")
    
    elif pilih_sub_menu == "Lihat Daftar Master Referensi Tersimpan":
        st.markdown("""
            <div style="padding: 15px; background: #ffffff; border-radius: 8px; border-left: 5px solid #065f46; box-shadow: 0 2px 10px rgba(0,0,0,0.03); margin-bottom: 20px;">
                <h3 style="margin: 0; color: #065f46; font-size: 20px;">📂 Tabel Master Referensi Harga & Pekerjaan</h3>
                <p style="margin: 5px 0 0 0; color: #475569; font-size: 13px;">Menampilkan seluruh daftar harga tetap yang tersimpan untuk Kontrak 7203250036.</p>
            </div>
        """, unsafe_allow_html=True)
        
        try:
            if os.path.exists(file_path_master):
                df_show = pd.read_excel(file_path_master)
                kolom_prioritas = ["Nomor Kontrak", "Kategori", "Uraian Pekerjaan", "Satuan", "Harga Satuan"]
                for col in kolom_prioritas:
                    if col not in df_show.columns:
                        df_show[col] = ""
                df_show = df_show[kolom_prioritas]
                
                for idx, row in df_show.iterrows():
                    cols = st.columns([0.5, 1.3, 1.5, 3.0, 0.8, 1.2, 0.6, 0.6])
                    with cols[0]:
                        st.markdown(f"**{idx + 1}**")
                    with cols[1]:
                        st.write(str(row["Nomor Kontrak"]))
                    with cols[2]:
                        st.write(str(row["Kategori"]))
                    with cols[3]:
                        st.write(str(row["Uraian Pekerjaan"]))
                    with cols[4]:
                        st.write(str(row["Satuan"]))
                    with cols[5]:
                        harga_val = float(row["Harga Satuan"]) if pd.notnull(row["Harga Satuan"]) else 0.0
                        st.write(f"Rp {harga_val:,.2f}")
                    with cols[6]:
                        if st.button("✏️", key=f"edit_m_{idx}", help="Edit Baris Ini"):
                            st.info(f"Fitur edit aktif untuk baris ke-{idx+1}.")
                    with cols[7]:
                        if st.button("🗑️", key=f"del_m_{idx}", help="Hapus Baris Ini"):
                            df_show = df_show.drop(idx).reset_index(drop=True)
                            df_show.to_excel(file_path_master, index=False)
                            st.success(f"Baris {idx+1} berhasil dihapus!")
                            st.rerun()
                    st.markdown("---")
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Reset / Hapus Semua Master Referensi", type="primary"):
                    os.remove(file_path_master)
                    st.success("Seluruh data master referensi berhasil di-reset!")
                    st.rerun()
            else:
                st.info("Belum ada data master referensi yang tersimpan untuk kontrak ini.")
        except Exception:
            st.info("Belum ada data master referensi yang tersimpan untuk kontrak ini.")

# ==========================================
# EKSEKUSI MODUL 1: LEMBAR KERJA 29 KOLOM
# ==========================================
elif "Modul 1" in pilih_modul:
    if pilih_sub_menu == "Input Database & Invoice (29 Kolom)":
        st.markdown("🔍 **Panggil Ulang Data Historis atau Buat Entri Baru**")
        
        list_db_kontrak = ["-- Buat Data Baru (Formulir Kosong) --"]
        try:
            if os.path.exists(file_path_transaksi):
                df_db_ex = pd.read_excel(file_path_transaksi)
                if "Nomor Kontrak" in df_db_ex.columns:
                    list_db_kontrak.extend(df_db_ex["Nomor Kontrak"].dropna().unique().tolist())
        except Exception:
            pass
        
        col_pg1, col_pg2 = st.columns([3, 1])
        with col_pg1:
            pilihan_db_panggil = st.selectbox("Pilih Data:", list_db_kontrak, label_visibility="collapsed")
        with col_pg2:
            st.markdown("<br>", unsafe_allow_html=True)
            btn_panggil_db = st.button("🔄 Panggil Ulang", use_container_width=True)
        
        # Ambil data jika tombol panggil ditekan
        data_isi = {}
        if pilihan_db_panggil != "-- Buat Data Baru (Formulir Kosong) --" and btn_panggil_db:
            try:
                df_db_ex = pd.read_excel(file_path_transaksi)
                matched_db = df_db_ex[df_db_ex["Nomor Kontrak"] == pilihan_db_panggil]
                if not matched_db.empty:
                    data_isi = matched_db.iloc[0].to_dict()
                    st.success(f"Data historis untuk kontrak {pilihan_db_panggil} berhasil dipanggil ke formulir!")
            except Exception as e:
                st.error(f"Gagal memanggil data: {e}")

        st.markdown("---")
        st.subheader("📑 Lembar Kerja 29 Kolom Identifikasi Kontrak & PI (Berbasis Indeks Presisi 1-29)")
        
        with st.form("form_29_kolom_struktur_tabel_36"):
            th1, th2, th3 = st.columns([0.6, 2.5, 4.5])
            with th1: st.markdown("**No**")
            with th2: st.markdown("**Item**")
            with th3: st.markdown("**Kolom Input Data (Bersih & Standar)**")
            st.markdown("---")
            
            c_no1, c_item1, c_in1 = st.columns([0.6, 2.5, 4.5])
            with c_no1: st.markdown("1.")
            with c_item1: st.markdown("Nomor Kontrak")
            with c_in1: val_1 = st.text_input("1_in", value=data_isi.get("Nomor Kontrak", ""), label_visibility="collapsed")

            c_no2, c_item2, c_in2 = st.columns([0.6, 2.5, 4.5])
            with c_no2: st.markdown("2.")
            with c_item2: st.markdown("Nomor Tender")
            with c_in2: val_2 = st.text_input("2_in", value=data_isi.get("Nomor Tender", ""), label_visibility="collapsed")

            c_no3, c_item3, c_in3 = st.columns([0.6, 2.5, 4.5])
            with c_no3: st.markdown("3.")
            with c_item3: st.markdown("Judul Kontrak")
            with c_in3: val_3 = st.text_area("3_in", value=data_isi.get("Judul Kontrak", ""), height=70, label_visibility="collapsed")

            c_no4, c_item4, c_in4 = st.columns([0.6, 2.5, 4.5])
            with c_no4: st.markdown("4.")
            with c_item4: st.markdown("Tanggal Kontrak")
            with c_in4: val_4 = st.text_input("4_in", value=data_isi.get("Tanggal Kontrak", ""), label_visibility="collapsed")

            c_no5, c_item5, c_in5 = st.columns([0.6, 2.5, 4.5])
            with c_no5: st.markdown("5.")
            with c_item5: st.markdown("Jangka Waktu Kontrak")
            with c_in5: val_5 = st.text_input("5_in", value=data_isi.get("Jangka Waktu Kontrak", ""), label_visibility="collapsed")

            c_no6, c_item6, c_in6 = st.columns([0.6, 2.5, 4.5])
            with c_no6: st.markdown("6.")
            with c_item6: st.markdown("Proforma Invoice No.")
            with c_in6: val_6 = st.text_input("6_in", value=data_isi.get("Proforma Invoice No.", ""), label_visibility="collapsed")

            c_no7, c_item7, c_in7 = st.columns([0.6, 2.5, 4.5])
            with c_no7: st.markdown("7.")
            with c_item7: st.markdown("Tanggal Proforma Invoice")
            with c_in7: val_7 = st.text_input("7_in", value=data_isi.get("Tanggal Proforma Invoice", ""), label_visibility="collapsed")

            c_no8, c_item8, c_in8 = st.columns([0.6, 2.5, 4.5])
            with c_no8: st.markdown("8.")
            with c_item8: st.markdown("Nomor Purchase Order")
            with c_in8: val_8 = st.text_input("8_in", value=data_isi.get("Nomor Purchase Order", ""), label_visibility="collapsed")

            c_no9, c_item9, c_in9 = st.columns([0.6, 2.5, 4.5])
            with c_no9: st.markdown("9.")
            with c_item9: st.markdown("Tanggal Purchase Order")
            with c_in9: val_9 = st.text_input("9_in", value=data_isi.get("Tanggal Purchase Order", ""), label_visibility="collapsed")

            c_no10, c_item10, c_in10 = st.columns([0.6, 2.5, 4.5])
            with c_no10: st.markdown("10.")
            with c_item10: st.markdown("Lingkup Pekerjaan")
            with c_in10: val_10 = st.text_area("10_in", value=data_isi.get("Lingkup Pekerjaan", ""), height=70, label_visibility="collapsed")

            c_no11, c_item11, c_in11 = st.columns([0.6, 2.5, 4.5])
            with c_no11: st.markdown("11.")
            with c_item11: st.markdown("Pihak Pertama")
            with c_in11: val_11 = st.text_input("11_in", value=data_isi.get("Pihak Pertama", ""), label_visibility="collapsed")

            c_no12, c_item12, c_in12 = st.columns([0.6, 2.5, 4.5])
            with c_no12: st.markdown("12.")
            with c_item12: st.markdown("Alamat Pihak Pertama")
            with c_in12: val_12 = st.text_area("12_in", value=data_isi.get("Alamat Pihak Pertama", ""), height=70, label_visibility="collapsed")

            # DIUBAH MENJADI TEXT INPUT FLEKSIBEL (MANUAL SESUAI PERSONEL ON DUTY)
            c_no13, c_item13, c_in13 = st.columns([0.6, 2.5, 4.5])
            with c_no13: st.markdown("13.")
            with c_item13: st.markdown("Diwakili Oleh")
            with c_in13: val_13 = st.text_input("13_in", value=data_isi.get("Diwakili Oleh", ""), label_visibility="collapsed")

            c_no14, c_item14, c_in14 = st.columns([0.6, 2.5, 4.5])
            with c_no14: st.markdown("14.")
            with c_item14: st.markdown("Selaku")
            with c_in14: val_14 = st.text_input("14_in", value=data_isi.get("Selaku", ""), label_visibility="collapsed")

            c_no15, c_item15, c_in15 = st.columns([0.6, 2.5, 4.5])
            with c_no15: st.markdown("15.")
            with c_item15: st.markdown("Pihak Kedua")
            with c_in15: val_15 = st.text_input("15_in", value=data_isi.get("Pihak Kedua", ""), label_visibility="collapsed")

            c_no16, c_item16, c_in16 = st.columns([0.6, 2.5, 4.5])
            with c_no16: st.markdown("16.")
            with c_item16: st.markdown("Alamat Pihak Kedua")
            with c_in16: val_16 = st.text_area("16_in", value=data_isi.get("Alamat Pihak Kedua", ""), height=70, label_visibility="collapsed")

            c_no17, c_item17, c_in17 = st.columns([0.6, 2.5, 4.5])
            with c_no17: st.markdown("17.")
            with c_item17: st.markdown("Diwakili Oleh (P2)")
            with c_in17: val_17 = st.text_input("17_in", value=data_isi.get("Diwakili Oleh (P2)", ""), label_visibility="collapsed")

            c_no18, c_item18, c_in18 = st.columns([0.6, 2.5, 4.5])
            with c_no18: st.markdown("18.")
            with c_item18: st.markdown("Selaku (P2)")
            with c_in18: val_18 = st.text_input("18_in", value=data_isi.get("Selaku (P2)", ""), label_visibility="collapsed")

            c_no19, c_item19, c_in19 = st.columns([0.6, 2.5, 4.5])
            with c_no19: st.markdown("19.")
            with c_item19: st.markdown("Periode Pekerjaan")
            with c_in19: val_19 = st.text_input("19_in", value=data_isi.get("Periode Pekerjaan", ""), label_visibility="collapsed")

            c_no20, c_item20, c_in20 = st.columns([0.6, 2.5, 4.5])
            with c_no20: st.markdown("20.")
            with c_item20: st.markdown("Nomor WCC")
            with c_in20: val_20 = st.text_input("20_in", value=data_isi.get("Nomor WCC", ""), label_visibility="collapsed")

            c_no21, c_item21, c_in21 = st.columns([0.6, 2.5, 4.5])
            with c_no21: st.markdown("21.")
            with c_item21: st.markdown("Tanggal WCC")
            with c_in21: val_21 = st.text_input("21_in", value=data_isi.get("Tanggal WCC", ""), label_visibility="collapsed")

            c_no22, c_item22, c_in22 = st.columns([0.6, 2.5, 4.5])
            with c_no22: st.markdown("22.")
            with c_item22: st.markdown("Nomor WO")
            with c_in22: val_22 = st.text_input("22_in", value=data_isi.get("Nomor WO", ""), label_visibility="collapsed")

            c_no23, c_item23, c_in23 = st.columns([0.6, 2.5, 4.5])
            with c_no23: st.markdown("23.")
            with c_item23: st.markdown("Keterangan WO")
            with c_in23: val_23 = st.text_area("23_in", value=data_isi.get("Keterangan WO", ""), height=70, label_visibility="collapsed")

            c_no24, c_item24, c_in24 = st.columns([0.6, 2.5, 4.5])
            with c_no24: st.markdown("24.")
            with c_item24: st.markdown("Nomor CTR")
            with c_in24: val_24 = st.text_input("24_in", value=data_isi.get("Nomor CTR", ""), label_visibility="collapsed")

            c_no25, c_item25, c_in25 = st.columns([0.6, 2.5, 4.5])
            with c_no25: st.markdown("25.")
            with c_item25: st.markdown("Progress Pekerjaan")
            with c_in25: val_25 = st.text_input("25_in", value=data_isi.get("Progress Pekerjaan", ""), label_visibility="collapsed")

            c_no26, c_item26, c_in26 = st.columns([0.6, 2.5, 4.5])
            with c_no26: st.markdown("26.")
            with c_item26: st.markdown("Prepared by Name")
            with c_in26: val_26 = st.text_input("26_in", value=data_isi.get("Prepared by Name", ""), label_visibility="collapsed")

            c_no27, c_item27, c_in27 = st.columns([0.6, 2.5, 4.5])
            with c_no27: st.markdown("27.")
            with c_item27: st.markdown("Prepared by Title")
            with c_in27: val_27 = st.text_input("27_in", value=data_isi.get("Prepared by Title", ""), label_visibility="collapsed")

            # DIUBAH MENJADI TEXT INPUT FLEKSIBEL (MANUAL SESUAI PERSONEL ON DUTY)
            c_no28, c_item28, c_in28 = st.columns([0.6, 2.5, 4.5])
            with c_no28: st.markdown("28.")
            with c_item28: st.markdown("Pejabat berwenang")
            with c_in28: val_28 = st.text_input("28_in", value=data_isi.get("Pejabat berwenang", ""), label_visibility="collapsed")

            c_no29, c_item29, c_in29 = st.columns([0.6, 2.5, 4.5])
            with c_no29: st.markdown("29.")
            with c_item29: st.markdown("Jabatan Field Manager")
            with c_in29: val_29 = st.text_input("29_in", value=data_isi.get("Jabatan Field Manager", ""), label_visibility="collapsed")
            
            st.markdown("---")
            b_col1, b_col2, b_col3 = st.columns(3)
            with b_col1:
                btn_simpan_baru = st.form_submit_button("💾 Simpan Data Baru", use_container_width=True)
            with b_col2:
                btn_save_as = st.form_submit_button("📥 Save As (Buat PI Baru)", use_container_width=True)
            with b_col3:
                btn_update_ini = st.form_submit_button("📝 Update Data Ini", use_container_width=True)
            
            if btn_simpan_baru or btn_save_as or btn_update_ini:
                data_dict = {
                    "Nomor Kontrak": [val_1], "Nomor Tender": [val_2], "Judul Kontrak": [val_3],
                    "Tanggal Kontrak": [val_4], "Jangka Waktu Kontrak": [val_5], "Proforma Invoice No.": [val_6],
                    "Tanggal Proforma Invoice": [val_7], "Nomor Purchase Order": [val_8], "Tanggal Purchase Order": [val_9],
                    "Lingkup Pekerjaan": [val_10], "Pihak Pertama": [val_11], "Alamat Pihak Pertama": [val_12],
                    "Diwakili Oleh": [val_13], "Selaku": [val_14], "Pihak Kedua": [val_15],
                    "Alamat Pihak Kedua": [val_16], "Diwakili Oleh (P2)": [val_17], "Selaku (P2)": [val_18],
                    "Periode Pekerjaan": [val_19], "Nomor WCC": [val_20], "Tanggal WCC": [val_21],
                    "Nomor WO": [val_22], "Keterangan WO": [val_23], "Nomor CTR": [val_24],
                    "Progress Pekerjaan": [val_25], "Prepared by Name": [val_26], "Prepared by Title": [val_27],
                    "Pejabat berwenang": [val_28], "Jabatan Field Manager": [val_29]
                }
                df_new_29 = pd.DataFrame(data_dict)
                try:
                    if os.path.exists(file_path_transaksi):
                        df_old_29 = pd.read_excel(file_path_transaksi)
                        if btn_update_ini and val_1 in df_old_29["Nomor Kontrak"].values:
                            df_old_29 = df_old_29[df_old_29["Nomor Kontrak"] != val_1]
                        df_combined_29 = pd.concat([df_old_29, df_new_29], ignore_index=True)
                        df_combined_29.to_excel(file_path_transaksi, index=False)
                    else:
                        df_new_29.to_excel(file_path_transaksi, index=False)
                    st.success("🎉 Data Identifikasi Kontrak & PI 29 Kolom berhasil disimpan!")
                except Exception as e:
                    st.error(f"Gagal menyimpan database: {e}")

    elif pilih_sub_menu == "Lihat Database Tersimpan":
        st.subheader("📂 Daftar Database Identifikasi Tersimpan")
        st.info("Menampilkan seluruh rekaman lembar kerja 29 kolom untuk Kontrak 7203250036.")
        try:
            if os.path.exists(file_path_transaksi):
                df_show_29 = pd.read_excel(file_path_transaksi)
                st.dataframe(df_show_29, use_container_width=True)
                
                if st.button("🗑️ Hapus / Reset Semua Database", type="primary"):
                    os.remove(file_path_transaksi)
                    st.success("Database berhasil di-reset!")
                    st.rerun()
            else:
                st.info("Belum ada data database tersimpan untuk kontrak ini.")
        except Exception:
            st.info("Belum ada data database tersimpan untuk kontrak ini.")

# ==========================================
# EKSEKUSI MODUL 2: INVOICE & DOKUMEN
# ==========================================
elif "Modul 2" in pilih_modul:
    try:
        if hasattr(modul_invoice, 'jalankan'):
            modul_invoice.jalankan()
        else:
            st.subheader("📄 Modul 2: Invoice & Dokumen Turunan")
            st.info("Penerbitan proforma invoice, timesheet peralatan, berita acara, dan WCC.")
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat Modul Invoice: {e}")

# --- FOOTER INFO ---
st.sidebar.markdown("---")
st.sidebar.caption("PT Banggai Sentral Sulawesi © 2026\nSistem Manajemen Kontrak Terpusat")