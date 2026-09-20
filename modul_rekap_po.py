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
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📊 Modul Master Plafon PO — Sinkronisasi Modul 0 (Kontrak, Kategori, Uraian & Harga)</h3>
            <p style="margin-bottom:0; font-size:12px; color:#4b5563;">Fokus penyempurnaan hierarki: Nomor Kontrak ➔ Kategori ➔ Uraian Pekerjaan ➔ Harga Satuan Otomatis.</p>
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

    # --- 2. PEMBACAAN & NORMALISASI MASTER REFERENSI KONTRAK (MODUL 0) ---
    path_kontrak_excel = os.path.join("database_penyimpanan_aman", "database_kontrak.xlsx")
    df_ref = pd.DataFrame()

    # Prioritas 1: Baca langsung dari parameter master_ref_data yang dikirim dari aplikasi utama
    if master_ref_data:
        try:
            df_ref = pd.DataFrame(master_ref_data)
        except:
            pass

    # Prioritas 2: Jika kosong, baca dari file fisik database_kontrak.xlsx
    if df_ref.empty and os.path.exists(path_kontrak_excel):
        try:
            df_ref = pd.read_excel(path_kontrak_excel)
        except:
            pass

    # Fallback terakhir jika benar-benar kosong
    if df_ref.empty:
        df_ref = pd.DataFrame([
            {"Nomor Kontrak": "7207250142", "Kategori": "MONTHLY BASIS", "Uraian Pekerjaan": "Jasa Sewa Alat Berat Monthly Basis", "Unit": "Month", "Harga Satuan": 131224000.0}
        ])

    # Normalisasi Kolom Presisi Sesuai Standar Modul 0
    col_mapping = {}
    for c in df_ref.columns:
        c_lower = str(c).strip().lower()
        if "kontrak" in c_lower:
            col_mapping[c] = "Nomor Kontrak"
        elif "kategori" in c_lower:
            col_mapping[c] = "Kategori"
        elif "uraian" in c_lower or "deskripsi" in c_lower:
            col_mapping[c] = "Uraian Pekerjaan"
        elif c_lower in ["unit", "uom"]:
            col_mapping[c] = "Unit"
        elif "harga" in c_lower:
            col_mapping[c] = "Harga Satuan"

    df_ref = df_ref.rename(columns=col_mapping)

    # Pembersihan Data (Clean Columns)
    df_ref["Nomor Kontrak Clean"] = df_ref["Nomor Kontrak"].astype(str).str.strip() if "Nomor Kontrak" in df_ref.columns else ""
    df_ref["Kategori Clean"] = df_ref["Kategori"].astype(str).str.strip().str.upper() if "Kategori" in df_ref.columns else ""
    
    if "Uraian Pekerjaan" in df_ref.columns:
        df_ref["Uraian Clean"] = df_ref["Uraian Pekerjaan"].astype(str).str.strip()
    else:
        df_ref["Uraian Clean"] = ""
        
    if "Unit" in df_ref.columns:
        df_ref["Unit Clean"] = df_ref["Unit"].astype(str).str.strip()
    else:
        df_ref["Unit Clean"] = "Month"
        
    if "Harga Satuan" in df_ref.columns:
        df_ref["Harga Clean"] = pd.to_numeric(df_ref["Harga Satuan"], errors='coerce').fillna(0.0)
    else:
        df_ref["Harga Clean"] = 0.0

    # Ambil Seluruh Daftar Nomor Kontrak Unik secara Lengkap dari Modul 0
    list_kontrak_ref = sorted(df_ref["Nomor Kontrak Clean"].dropna().unique().tolist())
    list_kontrak_ref = [k for k in list_kontrak_ref if k and k != 'nan' and k != '-']

    transaksi_list = muat_data_transaksi_func()
    df_tx = pd.DataFrame(transaksi_list) if transaksi_list else pd.DataFrame()
    list_po_ref = sorted(df_tx["Nomor PO"].dropna().astype(str).str.strip().unique().tolist()) if not df_tx.empty and "Nomor PO" in df_tx.columns else ["4500011739", "4500011740"]

    # --- 3. FORM INPUT & HIERARKI KONTRAK ➔ KATEGORI ➔ URAIAN ➔ HARGA ---
    st.markdown("#### 📝 Form Input & Validasi Master Plafon PO (Hierarki Modul 0)")
    st.info("ℹ️ Pilih Nomor Kontrak untuk memuat daftar kategori dan uraian pekerjaan yang sesuai secara spesifik.")

    with st.form(key="form_input_master_po_hierarki"):
        c_m1, c_m2 = st.columns(2)
        with c_m1:
            in_kontrak = st.selectbox("📂 Pilih Nomor Kontrak:", list_kontrak_ref if list_kontrak_ref else [""], key="input_master_kontrak")
        with c_m2:
            in_po = st.selectbox("🔍 Pilih Nomor PO:", list_po_ref if list_po_ref else [""], key="input_master_po")

        # FILTER HIERARKI 1: Filter Berdasarkan Nomor Kontrak yang Dipilih
        df_ref_kontrak = df_ref[df_ref["Nomor Kontrak Clean"] == str(in_kontrak).strip()]
        if df_ref_kontrak.empty:
            df_ref_kontrak = df_ref  # Fallback jika nomor kontrak spesifik tidak ada barisnya

        base_list_kat = sorted(df_ref_kontrak["Kategori Clean"].dropna().unique().tolist())
        base_list_kat = [k for k in base_list_kat if k and k != 'nan']

        if "PROFESSIONAL SUM" not in base_list_kat and "PROVISIONAL SUM" not in base_list_kat:
            base_list_kat.append("PROVISIONAL SUM")
        if "ESTIMATED SUM" not in base_list_kat:
            base_list_kat.append("ESTIMATED SUM")

        c_m3, c_m4, c_m5 = st.columns(3)
        with c_m3:
            in_kategori = st.selectbox("🏷️ Kategori Pekerjaan:", base_list_kat if base_list_kat else ["-"], key="input_master_kategori")

        # Deteksi Kategori Khusus (Provisional/Professional Sum)
        kat_lower = str(in_kategori).lower()
        is_provisional = "provisional" in kat_lower or "professional" in kat_lower

        # FILTER HIERARKI 2: Filter Uraian Pekerjaan Murni Berdasarkan Kontrak & Kategori yang Aktif
        with c_m4:
            if is_provisional:
                in_deskripsi = st.text_input("📋 Uraian Pekerjaan / Spesifikasi (Manual):", value="At Cost + Fee 15%", key="input_master_desc_manual")
                df_f_kat = pd.DataFrame()
            else:
                # Saring data spesifik berdasarkan Kontrak DAN Kategori yang dipilih
                df_f_kat = df_ref_kontrak[df_ref_kontrak["Kategori Clean"] == str(in_kategori).strip().upper()]
                if df_f_kat.empty:
                    df_f_kat = df_ref[df_ref["Kategori Clean"] == str(in_kategori).strip().upper()]
                
                raw_list_spek = sorted(df_f_kat["Uraian Clean"].dropna().unique().tolist()) if not df_f_kat.empty else ["- (Tidak ada data uraian)"]
                raw_list_spek = [s for s in raw_list_spek if s and s != 'nan']
                if not raw_list_spek:
                    raw_list_spek = ["- (Tidak ada data uraian)"]

                spek_display_map = {}
                spek_options_formatted = []
                for orig_text in raw_list_spek:
                    if "BBM & " in orig_text:
                        parts = orig_text.split("BBM & ")
                        unique_part = parts[-1].strip() if len(parts) > 1 else orig_text
                        display_text = f"⭐ [{unique_part}] — ({orig_text})"
                    else:
                        display_text = orig_text
                    spek_display_map[display_text] = orig_text
                    spek_options_formatted.append(display_text)

                selected_display_spek = st.selectbox("📋 Uraian Pekerjaan / Spesifikasi:", spek_options_formatted, key="input_master_deskripsi")
                in_deskripsi = spek_display_map.get(selected_display_spek, selected_display_spek)

        # --- PENGAMBILAN OTOMATIS: HARGA SATUAN & UNIT MENGACU PADA URAIAN PEKERJAAN ---
        hs_otomatis = 0.0
        unit_otomatis = "Month"
        
        if not is_provisional and not df_f_kat.empty and in_deskripsi != "- (Tidak ada data uraian)":
            # Cari baris yang Uraian Clean-nya sama persis dengan in_deskripsi
            m_row = df_f_kat[df_f_kat["Uraian Clean"] == str(in_deskripsi).strip()]
            if m_row.empty:
                m_row = df_f_kat[df_f_kat["Uraian Clean"].str.lower() == str(in_deskripsi).strip().lower()]
            
            if not m_row.empty:
                row_m = m_row.iloc[0]
                try:
                    hs_otomatis = float(row_m.get("Harga Clean", row_m.get("Harga Satuan", 0.0)) or 0.0)
                except:
                    hs_otomatis = 0.0
                unit_otomatis = str(row_m.get("Unit Clean", row_m.get("Unit", "Month")))

        with c_m5:
            u_opts = [unit_otomatis] if is_provisional else sorted(list(set([unit_otomatis, "Month", "Day", "Ls", "Unit", "Trip", "Jam", "EA", "AU", "Kg"])))
            idx_u = u_opts.index(unit_otomatis) if unit_otomatis in u_opts else 0
            in_uom = st.selectbox("📏 Satuan / UOM (Otomatis Modul 0):", u_opts, index=idx_u, key="input_master_uom")

        c_m6, c_m7 = st.columns(2)
        with c_m6:
            in_vol = st.number_input("📦 Quantity / Volume PO:", value=1.0, step=1.0, format="%.2f")
        with c_m7:
            in_price = st.number_input("💵 Unit Price / Harga Satuan (IDR - Mengacu ke Uraian):", value=hs_otomatis, step=1000.0, format="%.2f")

        submit_master = st.form_submit_button("💾 Simpan Item Plafon PO", type="primary")
        if submit_master:
            total_plafon_item = in_vol * in_price
            new_row = {
                "Nomor Kontrak": str(in_kontrak).strip(),
                "Nomor PO": str(in_po).strip(),
                "Kategori": str(in_kategori).strip(),
                "Deskripsi Pekerjaan": str(in_deskripsi).strip(),
                "UOM": str(in_uom).strip(),
                "Volume PO": float(in_vol),
                "Unit Price": float(in_price),
                "Total Plafon (IDR)": float(total_plafon_item)
            }
            
            df_master = pd.concat([df_master, pd.DataFrame([new_row])], ignore_index=True)
            if simpan_master_po(df_master):
                st.success(f"✅ Berhasil! Uraian [{in_deskripsi}] dengan Harga Satuan Rp {in_price:,.2f} tersimpan.")
                st.rerun()
            else:
                st.error("⚠️ Gagal menyimpan data.")

    st.markdown("---")
    st.markdown("#### 📂 Daftar Plafon PO yang Tersimpan")
    if not df_master.empty:
        st.dataframe(df_master, use_container_width=True)
        if st.button("🗑️ Hapus / Reset Data Plafon PO"):
            if os.path.exists(path_master_po_excel):
                os.remove(path_master_po_excel)
            st.success("✅ Data berhasil direset!")
            st.rerun()
    else:
        st.info("Belum ada data tersimpan.")