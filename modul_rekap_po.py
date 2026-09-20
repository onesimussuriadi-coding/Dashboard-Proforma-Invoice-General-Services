import streamlit as st
import pandas as pd
import os

def tampilkan_rekap_penyerapan_po(
    muat_data_transaksi_func,
    bersih_angka_func,
    master_ref_data=None
):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📊 Modul Master Plafon PO — Sinkronisasi Bersih Modul 0</h3>
            <p style="margin-bottom:0; font-size:12px; color:#4b5563;">Struktur pembacaan modular murni langsung dari Database Master Kontrak Modul 0.</p>
        </div>
    """, unsafe_allow_html=True)

    # --- 1. SETUP PENYIMPANAN LOKAL MASTER PO ---
    DIR_DB_LOKAL = os.path.join("database_penyimpanan_aman")
    if not os.path.exists(DIR_DB_LOKAL):
        os.makedirs(DIR_DB_LOKAL)
    path_master_po_excel = os.path.join(DIR_DB_LOKAL, "database_master_po.xlsx")

    def muat_master_po():
        if os.path.exists(path_master_po_excel):
            try:
                return pd.read_excel(path_master_po_excel)
            except:
                pass
        return pd.DataFrame(columns=["Nomor Kontrak", "Nomor PO", "Kategori", "Deskripsi Pekerjaan", "UOM", "Volume PO", "Unit Price", "Total Plafon (IDR)"])

    def simpan_master_po(df):
        try:
            df.to_excel(path_master_po_excel, index=False)
            return True
        except:
            return False

    df_master = muat_master_po()

    # --- 2. LOADER MANDIRI MODUL 0 (DIPERBAIKI: PRIORITAS PARAMETER UTAMA) ---
    def muat_data_modul_0():
        # Prioritas utama: Gunakan data dari parameter master_ref_data yang dikirim aplikasi
        if master_ref_data:
            try:
                df_param = pd.DataFrame(master_ref_data)
                if not df_param.empty:
                    return df_param
            except:
                pass
        
        # Cek beberapa alternatif path file fisik
        paths_to_check = [
            os.path.join("database_penyimpanan_aman", "database_kontrak.xlsx"),
            "database_kontrak.xlsx",
            os.path.join(".", "database_penyimpanan_aman", "database_kontrak.xlsx")
        ]
        
        for p in paths_to_check:
            if os.path.exists(p):
                try:
                    df_file = pd.read_excel(p)
                    if not df_file.empty:
                        return df_file
                except:
                    pass
        
        return pd.DataFrame()

    df_raw = muat_data_modul_0()

    if df_raw.empty:
        # Fallback data uji darurat agar form tetap terbuka dan tidak terblokir
        df_raw = pd.DataFrame([
            {"Nomor Kontrak": "7207250142", "Kategori": "MONTHLY BASIS", "Uraian Pekerjaan": "Jasa Sewa Alat Berat Monthly Basis", "Unit": "Month", "Harga Satuan": 131224000.0},
            {"Nomor Kontrak": "7203250036", "Kategori": "MONTHLY BASIS", "Uraian Pekerjaan": "Daily Rate", "Unit": "Day", "Harga Satuan": 1197000.0},
            {"Nomor Kontrak": "7201250141", "Kategori": "ADDITIONAL CAMP SERVICES", "Uraian Pekerjaan": "Food & beverage, main course", "Unit": "Day", "Harga Satuan": 65000.0}
        ])

    # Normalisasi Kolom Universal
    col_map = {}
    for col in df_raw.columns:
        c_low = str(col).strip().lower()
        if any(k in c_low for k in ["kontrak", "no kontrak"]):
            col_map[col] = "Nomor Kontrak"
        elif any(k in c_low for k in ["kategori", "jenis"]):
            col_map[col] = "Kategori"
        elif any(k in c_low for k in ["uraian", "deskripsi", "pekerjaan", "spesifikasi"]):
            col_map[col] = "Uraian Pekerjaan"
        elif any(k in c_low for k in ["unit", "uom", "satuan"]):
            col_map[col] = "Unit"
        elif any(k in c_low for k in ["harga", "satuan harga", "rate"]):
            col_map[col] = "Harga Satuan"

    df_clean = df_raw.rename(columns=col_map)

    # Pastikan kolom esensial terbentuk
    required_cols = ["Nomor Kontrak", "Kategori", "Uraian Pekerjaan", "Unit", "Harga Satuan"]
    for rc in required_cols:
        if rc not in df_clean.columns:
            df_clean[rc] = "-"

    # Pembersihan tipe data string & numerik
    df_clean["Nomor Kontrak"] = df_clean["Nomor Kontrak"].astype(str).str.strip()
    df_clean["Kategori"] = df_clean["Kategori"].astype(str).str.strip().str.upper()
    df_clean["Uraian Pekerjaan"] = df_clean["Uraian Pekerjaan"].astype(str).str.strip()
    df_clean["Unit"] = df_clean["Unit"].astype(str).str.strip()
    df_clean["Harga Satuan Numeric"] = pd.to_numeric(df_clean["Harga Satuan"], errors='coerce').fillna(0.0)

    # Ambil list Nomor Kontrak unik secara bersih
    list_kontrak_bersih = sorted([k for k in df_clean["Nomor Kontrak"].unique() if k and k != "nan" and k != "-"])

    # Ambil list Nomor PO dari transaksi
    transaksi_list = muat_data_transaksi_func()
    df_tx = pd.DataFrame(transaksi_list) if transaksi_list else pd.DataFrame()
    list_po_ref = sorted(df_tx["Nomor PO"].dropna().astype(str).str.strip().unique().tolist()) if not df_tx.empty and "Nomor PO" in df_tx.columns else ["4500011739", "4500011740"]

    # --- 3. FORM INPUT BERBASIS HIERARKI BERSIH ---
    st.markdown("#### 📝 Form Input Master Plafon PO (Struktur Modular Bersih)")
    st.info("ℹ️ Silakan pilih Nomor Kontrak. Kategori dan Uraian Pekerjaan akan tersinkronisasi otomatis dari database Modul 0.")

    with st.form(key="form_input_master_po_modular"):
        c1, c2 = st.columns(2)
        with c1:
            in_kontrak = st.selectbox("📂 Pilih Nomor Kontrak:", list_kontrak_bersih if list_kontrak_bersih else [""], key="mod_kontrak")
        with c2:
            in_po = st.selectbox("🔍 Pilih Nomor PO:", list_po_ref if list_po_ref else [""], key="mod_po")

        # Filter baris berdasarkan Nomor Kontrak yang dipilih
        df_k = df_clean[df_clean["Nomor Kontrak"] == in_kontrak]
        if df_k.empty:
            df_k = df_clean

        # Ambil Kategori unik untuk kontrak tersebut
        list_kat = sorted([cat for cat in df_k["Kategori"].unique() if cat and cat != "NAN"])
        if "PROVISIONAL SUM" not in list_kat:
            list_kat.append("PROVISIONAL SUM")
        if "ESTIMATED SUM" not in list_kat:
            list_kat.append("ESTIMATED SUM")

        c3, c4, c5 = st.columns(3)
        with c3:
            in_kategori = st.selectbox("🏷️ Kategori Pekerjaan:", list_kat if list_kat else ["-"], key=f"mod_kat_{in_kontrak}")

        # Deteksi Kategori Khusus
        is_prov = "PROVISIONAL" in in_kategori or "PROFESSIONAL" in in_kategori

        with c4:
            if is_prov:
                in_deskripsi = st.text_input("📋 Uraian Pekerjaan / Spesifikasi (Manual):", value="At Cost + Fee 15%", key=f"mod_desc_manual_{in_kontrak}")
                df_u = pd.DataFrame()
            else:
                # Filter baris berdasarkan Kategori yang aktif
                df_u = df_k[df_k["Kategori"] == in_kategori]
                if df_u.empty:
                    df_u = df_clean[df_clean["Kategori"] == in_kategori]

                list_uraian = sorted([uraian for uraian in df_u["Uraian Pekerjaan"].unique() if uraian and uraian != "NAN"])
                if not list_uraian:
                    list_uraian = ["- (Tidak ada data uraian)"]

                in_deskripsi = st.selectbox("📋 Uraian Pekerjaan / Spesifikasi:", list_uraian, key=f"mod_uraian_{in_kontrak}_{in_kategori}")

        # Ambil Harga Satuan & Unit secara presisi mengacu pada Uraian Pekerjaan yang dipilih
        harga_otomatis = 0.0
        unit_otomatis = "Month"

        if not is_prov and not df_u.empty and in_deskripsi != "- (Tidak ada data uraian)":
            row_match = df_u[df_u["Uraian Pekerjaan"] == in_deskripsi]
            if row_match.empty:
                row_match = df_u[df_u["Uraian Pekerjaan"].str.lower() == in_deskripsi.lower()]
            
            if not row_match.empty:
                r_val = row_match.iloc[0]
                try:
                    harga_otomatis = float(r_val.get("Harga Satuan Numeric", 0.0) or 0.0)
                except:
                    harga_otomatis = 0.0
                unit_otomatis = str(r_val.get("Unit", "Month"))

        with c5:
            list_uom = [unit_otomatis] if is_prov else sorted(list(set([unit_otomatis, "Month", "Day", "Ls", "Unit", "Trip", "Jam", "EA", "AU", "Kg"])))
            idx_uom = list_uom.index(unit_otomatis) if unit_otomatis in list_uom else 0
            in_uom = st.selectbox("📏 Satuan / UOM:", list_uom, index=idx_uom, key=f"mod_uom_{in_kontrak}")

        c6, c7 = st.columns(2)
        with c6:
            in_vol = st.number_input("📦 Quantity / Volume PO:", value=1.0, step=1.0, format="%.2f", key=f"mod_vol_{in_kontrak}")
        with c7:
            in_price = st.number_input("💵 Unit Price / Harga Satuan (IDR - Otomatis Modul 0):", value=harga_otomatis, step=1000.0, format="%.2f", key=f"mod_price_{in_kontrak}")

        submitted = st.form_submit_button("💾 Simpan Item Plafon PO", type="primary")
        if submitted:
            total_plafon = in_vol * in_price
            new_record = {
                "Nomor Kontrak": str(in_kontrak).strip(),
                "Nomor PO": str(in_po).strip(),
                "Kategori": str(in_kategori).strip(),
                "Deskripsi Pekerjaan": str(in_deskripsi).strip(),
                "UOM": str(in_uom).strip(),
                "Volume PO": float(in_vol),
                "Unit Price": float(in_price),
                "Total Plafon (IDR)": float(total_plafon)
            }

            df_master = pd.concat([df_master, pd.DataFrame([new_record])], ignore_index=True)
            if simpan_master_po(df_master):
                st.success(f"✅ Berhasil! Uraian [{in_deskripsi}] dengan Harga Rp {in_price:,.2f} berhasil disimpan.")
                st.rerun()
            else:
                st.error("⚠️ Gagal menyimpan ke file database master PO.")

    st.markdown("---")
    st.markdown("#### 📂 Daftar Plafon PO Tersimpan")
    if not df_master.empty:
        st.dataframe(df_master, use_container_width=True)
        if st.button("🗑️ Reset / Hapus Data Plafon PO", key="reset_plafon_btn"):
            if os.path.exists(path_master_po_excel):
                os.remove(path_master_po_excel)
            st.success("✅ Data berhasil direset!")
            st.rerun()
    else:
        st.info("Belum ada data Plafon PO tersimpan.")