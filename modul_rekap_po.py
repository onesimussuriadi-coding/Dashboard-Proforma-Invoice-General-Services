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
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📊 Modul Master Plafon PO — Sinkronisasi Sempurna Modul 0</h3>
            <p style="margin-bottom:0; font-size:12px; color:#4b5563;">Pembacaan langsung dari database_master_referensi.xlsx dengan hierarki Kontrak ➔ Kategori ➔ Uraian ➔ Harga Satuan.</p>
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

    # --- 2. PEMBACAAN LANGSUNG DARI database_master_referensi.xlsx ---
    def muat_master_referensi_fisik():
        paths = [
            os.path.join("database_penyimpanan_aman", "database_master_referensi.xlsx"),
            os.path.join("database_penyimpanan_aman", "database_kontrak.xlsx"),
            "database_master_referensi.xlsx",
            "database_kontrak.xlsx"
        ]
        for p in paths:
            if os.path.exists(p):
                try:
                    df_f = pd.read_excel(p)
                    if not df_f.empty:
                        return df_f
                except:
                    pass
        
        # Fallback jika parameter utama terisi
        if master_ref_data:
            try:
                return pd.DataFrame(master_ref_data)
            except:
                pass
                
        return pd.DataFrame()

    df_raw = muat_master_referensi_fisik()

    if df_raw.empty:
        st.warning("⚠️ File `database_master_referensi.xlsx` tidak ditemukan di folder `database_penyimpanan_aman`. Pastikan file tersedia.")
        return

    # Normalisasi Nama Kolom secara Universal
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

    # Pastikan kolom esensial ada
    for rc in ["Nomor Kontrak", "Kategori", "Uraian Pekerjaan", "Unit", "Harga Satuan"]:
        if rc not in df_clean.columns:
            df_clean[rc] = "-"

    # Pembersihan Data yang Aman dari konflik DataFrame/Series
    def clean_s(s):
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
        return s.astype(str).str.strip()

    df_clean["Nomor Kontrak"] = clean_s(df_clean["Nomor Kontrak"])
    df_clean["Kategori"] = clean_s(df_clean["Kategori"]).str.upper()
    df_clean["Uraian Pekerjaan"] = clean_s(df_clean["Uraian Pekerjaan"])
    df_clean["Unit"] = clean_s(df_clean["Unit"])
    
    hs = df_clean["Harga Satuan"]
    if isinstance(hs, pd.DataFrame):
        hs = hs.iloc[:, 0]
    df_clean["Harga Satuan Numeric"] = pd.to_numeric(hs, errors='coerce').fillna(0.0)

    # Ambil Daftar Nomor Kontrak Unik
    list_kontrak = sorted([k for k in df_clean["Nomor Kontrak"].unique() if k and k != "nan" and k != "-"])

    # Ambil Daftar Nomor PO dari Transaksi (atau fallback list PO yang ada)
    transaksi_list = muat_data_transaksi_func()
    df_tx = pd.DataFrame(transaksi_list) if transaksi_list else pd.DataFrame()
    list_po = sorted(df_tx["Nomor PO"].dropna().astype(str).str.strip().unique().tolist()) if not df_tx.empty and "Nomor PO" in df_tx.columns else ["4500011739", "4500011740", "4500010745", "4500010746"]

    # --- 3. FORM INPUT HIERARKI KONTRAK ➔ KATEGORI ➔ URAIAN ➔ HARGA ---
    st.markdown("#### 📝 Form Input Master Plafon PO (Sinkronisasi Penuh Modul 0)")
    st.info("ℹ️ Pilih Nomor Kontrak untuk memuat kategori dan uraian pekerjaan secara lengkap dan akurat.")

    with st.form(key="form_master_po_final_v2"):
        c1, c2 = st.columns(2)
        with c1:
            in_kontrak = st.selectbox("📂 Pilih Nomor Kontrak:", list_kontrak if list_kontrak else [""], key="sel_kontrak_master")
        with c2:
            in_po = st.selectbox("🔍 Pilih Nomor PO:", list_po if list_po else [""], key="sel_po_master")

        # FILTER LEVEL 1: Berdasarkan Nomor Kontrak
        df_filtered_kontrak = df_clean[df_clean["Nomor Kontrak"] == in_kontrak]
        if df_filtered_kontrak.empty:
            df_filtered_kontrak = df_clean

        list_kat = sorted([c for c in df_filtered_kontrak["Kategori"].unique() if c and c != "NAN" and c != "-"])
        if "PROVISIONAL SUM" not in list_kat:
            list_kat.append("PROVISIONAL SUM")
        if "ESTIMATED SUM" not in list_kat:
            list_kat.append("ESTIMATED SUM")

        c3, c4, c5 = st.columns(3)
        with c3:
            in_kategori = st.selectbox("🏷️ Kategori Pekerjaan:", list_kat if list_kat else ["-"], key=f"sel_kat_{in_kontrak}")

        is_prov = "PROVISIONAL" in in_kategori or "PROFESSIONAL" in in_kategori

        # FILTER LEVEL 2: Berdasarkan Kategori yang Dipilih
        with c4:
            if is_prov:
                in_deskripsi = st.text_input("📋 Uraian Pekerjaan / Spesifikasi (Manual):", value="At Cost + Fee 15%", key=f"desc_manual_{in_kontrak}")
                df_filtered_uraian = pd.DataFrame()
            else:
                df_filtered_uraian = df_filtered_kontrak[df_filtered_kontrak["Kategori"] == in_kategori]
                if df_filtered_uraian.empty:
                    df_filtered_uraian = df_clean[df_clean["Kategori"] == in_kategori]

                list_uraian = sorted([u for u in df_filtered_uraian["Uraian Pekerjaan"].unique() if u and u != "NAN" and u != "-"])
                if not list_uraian:
                    list_uraian = ["- (Tidak ada data uraian)"]

                in_deskripsi = st.selectbox("📋 Uraian Pekerjaan / Spesifikasi:", list_uraian, key=f"sel_uraian_{in_kontrak}_{in_kategori}")

        # PENGAMBILAN OTOMATIS HARGA SATUAN & UOM MENGACU TEPAT PADA URAIAN PEKERJAAN
        harga_otomatis = 0.0
        unit_otomatis = "Month"

        if not is_prov and not df_filtered_uraian.empty and in_deskripsi != "- (Tidak ada data uraian)":
            row_match = df_filtered_uraian[df_filtered_uraian["Uraian Pekerjaan"] == in_deskripsi]
            if row_match.empty:
                row_match = df_filtered_uraian[df_filtered_uraian["Uraian Pekerjaan"].str.lower() == in_deskripsi.lower()]
            
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
            in_uom = st.selectbox("📏 Satuan / UOM:", list_uom, index=idx_uom, key=f"sel_uom_{in_kontrak}")

        c6, c7 = st.columns(2)
        with c6:
            in_vol = st.number_input("📦 Quantity / Volume PO:", value=1.0, step=1.0, format="%.2f", key=f"vol_{in_kontrak}")
        with c7:
            in_price = st.number_input("💵 Unit Price / Harga Satuan (IDR - Otomatis Modul 0):", value=harga_otomatis, step=1000.0, format="%.2f", key=f"price_{in_kontrak}")

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
                st.success(f"✅ Berhasil! Uraian [{in_deskripsi}] dengan Harga Rp {in_price:,.2f} tersimpan.")
                st.rerun()
            else:
                st.error("⚠️ Gagal menyimpan ke file database master PO.")

    st.markdown("---")
    st.markdown("#### 📂 Daftar Plafon PO Tersimpan")
    if not df_master.empty:
        st.dataframe(df_master, use_container_width=True)
        if st.button("🗑️ Reset / Hapus Data Plafon PO", key="reset_plafon_final"):
            if os.path.exists(path_master_po_excel):
                os.remove(path_master_po_excel)
            st.success("✅ Data berhasil direset!")
            st.rerun()
    else:
        st.info("Belum ada data Plafon PO tersimpan.")