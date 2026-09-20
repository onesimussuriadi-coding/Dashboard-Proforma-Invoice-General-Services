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
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📊 Modul Master Plafon PO — Sinkronisasi Standar Modul 2</h3>
            <p style="margin-bottom:0; font-size:12px; color:#4b5563;">Menggunakan pola arsitektur hierarki referensi murni yang identik dengan Modul 2.</p>
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

    # --- 2. VALIDASI DATA REFERENSI (STANDAR MODUL 2) ---
    if not master_ref_data:
        path_file = os.path.join("database_penyimpanan_aman", "database_master_referensi.xlsx")
        if os.path.exists(path_file):
            try:
                df_load = pd.read_excel(path_file)
                master_ref_data = df_load.to_dict('records')
            except:
                pass

    if not master_ref_data:
        st.warning("⚠️ Belum ada data di Master Referensi Harga (Modul 0 / database_master_referensi.xlsx).")
        return

    # Normalisasi DataFrame Referensi Sesuai Pola Modul 2 dengan Pengaman Series
    df_ref = pd.DataFrame(master_ref_data)
    
    # Deteksi kolom secara aman
    col_map = {}
    for c in df_ref.columns:
        c_low = str(c).strip().lower()
        if "kontrak" in c_low:
            col_map[c] = "Nomor Kontrak"
        elif "kategori" in c_low:
            col_map[c] = "Kategori"
        elif any(k in c_low for k in ["uraian", "deskripsi", "pekerjaan"]):
            col_map[col] = "Uraian Pekerjaan"
        elif any(k in c_low for k in ["unit", "uom", "satuan"]):
            col_map[col] = "Unit"
        elif "harga" in c_low:
            col_map[col] = "Harga Satuan"

    df_ref = df_ref.rename(columns=col_map)

    def safe_s(col_name, default_val=""):
        if col_name in df_ref.columns:
            s = df_ref[col_name]
            if isinstance(s, pd.DataFrame):
                s = s.iloc[:, 0]
            return s.astype(str).str.strip()
        else:
            return pd.Series([default_val] * len(df_ref))

    df_ref["Nomor Kontrak Clean"] = safe_s("Nomor Kontrak")
    df_ref["Kategori Clean"] = safe_s("Kategori").str.upper()
    
    if "Uraian Pekerjaan" in df_ref.columns:
        df_ref["Uraian Clean"] = safe_s("Uraian Pekerjaan")
    elif "Deskripsi Pekerjaan" in df_ref.columns:
        df_ref["Uraian Clean"] = safe_s("Deskripsi Pekerjaan")
    else:
        df_ref["Uraian Clean"] = safe_s("Uraian", "")

    df_ref["Unit Clean"] = safe_s("Unit", "Month")

    if "Harga Satuan" in df_ref.columns:
        hs_col = df_ref["Harga Satuan"]
        if isinstance(hs_col, pd.DataFrame):
            hs_col = hs_col.iloc[:, 0]
        df_ref["Harga Clean"] = pd.to_numeric(hs_col, errors='coerce').fillna(0.0)
    else:
        df_ref["Harga Clean"] = 0.0

    # Ambil list Nomor Kontrak unik
    list_kontrak = sorted(list(set([str(k).strip() for k in df_ref["Nomor Kontrak Clean"].unique() if k and k != "nan" and k != "-"])))

    # Ambil list Nomor PO dari transaksi
    transaksi_list = muat_data_transaksi_func()
    df_tx = pd.DataFrame(transaksi_list) if transaksi_list else pd.DataFrame()
    list_po = sorted(df_tx["Nomor PO"].dropna().astype(str).str.strip().unique().tolist()) if not df_tx.empty and "Nomor PO" in df_tx.columns else ["4500011739", "4500011740", "4500010745"]

    # --- 3. FORM INPUT BERBASIS POLA HIERARKI MODUL 2 ---
    st.markdown("#### 📝 Form Input Master Plafon PO (Pola Standar Modul 2)")
    st.info("ℹ️ Pilih Nomor Kontrak, Kategori, dan Uraian Pekerjaan. Vlookup harga dan UOM aktif mengacu presisi seperti Modul 2.")

    with st.form(key="form_master_po_modul2_style"):
        c_top1, c_top2 = st.columns(2)
        with c_top1:
            selected_kontrak = st.selectbox("📂 Pilih Nomor Kontrak", list_kontrak if list_kontrak else [""], key="po_sel_kontrak")
        with c_top2:
            selected_po = st.selectbox("🔍 Pilih Nomor PO", list_po if list_po else [""], key="po_sel_nomor_po")

        # Filter Referensi Berdasarkan Kontrak Aktif (Sesuai Pola Modul 2)
        df_ref_kontrak = df_ref[df_ref["Nomor Kontrak Clean"] == str(selected_kontrak).strip()]
        if df_ref_kontrak.empty:
            df_ref_kontrak = df_ref 

        base_list_kat = sorted(df_ref_kontrak["Kategori Clean"].dropna().unique().tolist())
        if "PROFESSIONAL SUM" not in base_list_kat and "PROVISIONAL SUM" not in base_list_kat:
            base_list_kat.append("PROVISIONAL SUM")
        if "ESTIMATED SUM" not in base_list_kat:
            base_list_kat.append("ESTIMATED SUM")

        c_k1, c_k2 = st.columns(2)
        with c_k1:
            kat_pilih = st.selectbox("🏷️ Kategori Pekerjaan", base_list_kat if base_list_kat else ["-"], key="po_kat_pilih")
        
        kat_lower = str(kat_pilih).lower()
        is_provisional = "provisional" in kat_lower or "professional" in kat_lower
        is_estimated_sum = "estimated" in kat_lower or "estimasi" in kat_lower

        with c_k2:
            if is_provisional:
                spek_pilih = st.text_input("📋 Uraian Pekerjaan / Spesifikasi (Manual)", value="At Cost + Fee 15%", key="po_spek_manual")
            else:
                # Saring murni berdasarkan Kategori Clean yang aktif pada kontrak tersebut
                df_f_kat = df_ref_kontrak[df_ref_kontrak["Kategori Clean"] == str(kat_pilih).strip().upper()]
                if df_f_kat.empty:
                    df_f_kat = df_ref[df_ref["Kategori Clean"] == str(kat_pilih).strip().upper()]
                    
                raw_list_spek = sorted(df_f_kat["Uraian Clean"].dropna().unique().tolist()) if not df_f_kat.empty else ["- (Tidak ada data uraian)"]
                
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

                selected_display_spek = st.selectbox("📋 Uraian Pekerjaan / Spesifikasi", spek_options_formatted if spek_options_formatted else ["-"], key="po_spek_pilih")
                spek_pilih = spek_display_map.get(selected_display_spek, selected_display_spek)

        # VLOOKUP OTOMATIS HARGA & UOM (Sesuai Logika Modul 2)
        hs_otomatis = 0.0
        unit_otomatis = "Month"
        if not is_provisional:
            df_f_kat = df_ref_kontrak[df_ref_kontrak["Kategori Clean"] == str(kat_pilih).strip().upper()]
            if df_f_kat.empty:
                df_f_kat = df_ref[df_ref["Kategori Clean"] == str(kat_pilih).strip().upper()]

            if not df_f_kat.empty and spek_pilih != "- (Tidak ada data uraian)":
                m_row = df_f_kat[df_f_kat["Uraian Clean"] == str(spek_pilih).strip()]
                if m_row.empty:
                    m_row = df_f_kat[df_f_kat["Uraian Clean"].str.lower() == str(spek_pilih).strip().lower()]

                if not m_row.empty:
                    row_m = m_row.iloc[0]
                    try:
                        hs_otomatis = float(row_m.get("Harga Clean", row_m.get("Harga Satuan", 0.0)) or 0.0)
                    except:
                        hs_otomatis = 0.0
                    unit_otomatis = str(row_m.get("Unit Clean", row_m.get("Unit", "Month")))

        c_item1, c_item2 = st.columns(2)
        with c_item1:
            q_val = st.number_input("📦 Quantity / Volume PO (Isi Manual):", min_value=0.0, value=0.0, step=1.0, format="%.2f", key="po_qty")
        with c_item2:
            default_u_opts = ["Month", "Day", "Ls", "Unit", "Trip", "Jam", "EA", "AU", "Kg", "Pallet", "Ltr"]
            existing_u_from_master = df_ref["Unit Clean"].dropna().astype(str).unique().tolist() if "Unit Clean" in df_ref.columns else []
            u_opts = sorted(list(set(default_u_opts + existing_u_from_master)))
            
            def_unit = unit_otomatis if not is_provisional else "AU"
            if def_unit not in u_opts and def_unit:
                u_opts.insert(0, def_unit)
            idx_u = u_opts.index(def_unit) if def_unit in u_opts else 0
            u_val = st.selectbox("📏 Satuan / UOM (Aktif & Bisa Dipilih):", u_opts, index=idx_u, key="po_unit")

        hs_final = hs_otomatis
        formatted_hs = f"Rp {hs_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        st.markdown(f"💵 **Unit Price / Harga Satuan Final (Modul 0):** `{formatted_hs}`")

        submitted = st.form_submit_button("💾 Simpan Item ke Master Plafon PO", type="primary")
        if submitted:
            if q_val <= 0:
                st.warning("⚠️ Quantity / Volume PO harus diisi lebih besar dari 0.")
            else:
                total_plafon_item = q_val * hs_final
                new_record = {
                    "Nomor Kontrak": str(selected_kontrak).strip(),
                    "Nomor PO": str(selected_po).strip(),
                    "Kategori": str(kat_pilih).strip(),
                    "Deskripsi Pekerjaan": str(spek_pilih).strip(),
                    "UOM": str(u_val).strip(),
                    "Volume PO": float(q_val),
                    "Unit Price": float(hs_final),
                    "Total Plafon (IDR)": float(total_plafon_item)
                }

                df_master = pd.concat([df_master, pd.DataFrame([new_record])], ignore_index=True)
                if simpan_master_po(df_master):
                    st.success(f"✅ Berhasil! Uraian [{spek_pilih}] dengan Plafon Rp {total_plafon_item:,.2f} berhasil disimpan.")
                    st.rerun()
                else:
                    st.error("⚠️ Gagal menyimpan ke file database master PO.")

    st.markdown("---")
    st.markdown("#### 📂 Daftar Master Plafon PO Tersimpan")
    if not df_master.empty:
        st.dataframe(df_master, use_container_width=True)
        if st.button("🗑️ Reset / Hapus Data Plafon PO", key="reset_plafon_modul2_style"):
            if os.path.exists(path_master_po_excel):
                os.remove(path_master_po_excel)
            st.success("✅ Data berhasil direset!")
            st.rerun()
    else:
        st.info("Belum ada data Plafon PO tersimpan.")