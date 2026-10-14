import streamlit as st
import pandas as pd
import os

@st.cache_data(show_spinner=False)
def muat_master_po_cached(path_file):
    if os.path.exists(path_file):
        try:
            return pd.read_excel(path_file)
        except:
            pass
    return pd.DataFrame(columns=["Nomor Kontrak", "Nomor PO", "Kategori", "Deskripsi Pekerjaan", "UOM", "Volume PO", "Unit Price", "Total Plafon (IDR)", "Keterangan"])

def tampilkan_rekap_penyerapan_po(
    muat_data_transaksi_func,
    bersih_angka_func,
    master_ref_data=None
):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📊 Modul Master Plafon PO & Laporan Analisis Interaktif</h3>
            <p style="margin-bottom:0; font-size:12px; color:#4b5563;">Manajemen Plafon PO fleksibel (Dropdown PO & Input Nomor PO Manual Opsional), Rekapitulasi Sisa Anggaran, Persentase Penyerapan, Accordion per PO, dan Grafik Porsi Anggaran.</p>
        </div>
    """, unsafe_allow_html=True)

    # --- 1. SETUP PENYIMPANAN LOKAL MASTER PO ---
    DIR_DB_LOKAL = os.path.join("database_penyimpanan_aman")
    if not os.path.exists(DIR_DB_LOKAL):
        os.makedirs(DIR_DB_LOKAL)
    path_master_po_excel = os.path.join(DIR_DB_LOKAL, "database_master_po.xlsx")

    def simpan_master_po(df):
        try:
            df.to_excel(path_master_po_excel, index=False)
            st.cache_data.clear()
            return True
        except:
            return False

    df_master = muat_master_po_cached(path_master_po_excel)

    # --- 2. VALIDASI & NORMALISASI DATA REFERENSI BERBASIS POSISI KOLOM ---
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

    df_ref = pd.DataFrame(master_ref_data)

    def safe_col_idx(df, idx, default_val=""):
        if df.shape[1] > idx:
            s = df.iloc[:, idx]
            if isinstance(s, pd.DataFrame):
                s = s.iloc[:, 0]
            return s
        return pd.Series([default_val] * len(df))

    df_ref["Nomor Kontrak Clean"] = safe_col_idx(df_ref, 0).astype(str).str.strip()
    df_ref["Kategori Clean"] = safe_col_idx(df_ref, 1).astype(str).str.strip().str.upper()
    df_ref["Uraian Clean"] = safe_col_idx(df_ref, 2).astype(str).str.strip()
    df_ref["Unit Clean"] = safe_col_idx(df_ref, 3).astype(str).str.strip()

    raw_price_series = safe_col_idx(df_ref, 4)

    def parse_harga_exact(val):
        if pd.isna(val):
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).strip()
        val_clean = "".join([ch for ch in val_str if ch.isdigit() or ch in ['.', ',']])
        if not val_clean:
            return 0.0
        if ',' in val_clean and '.' in val_clean:
            if val_clean.rfind(',') > val_clean.rfind('.'):
                val_clean = val_clean.replace('.', '').replace(',', '.')
            else:
                val_clean = val_clean.replace(',', '')
        elif ',' in val_clean:
            parts = val_clean.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                val_clean = val_clean.replace(',', '.')
            else:
                val_clean = val_clean.replace(',', '')
        elif val_clean.count('.') > 1:
            val_clean = val_clean.replace('.', '')
        try:
            return float(val_clean)
        except:
            return 0.0

    df_ref["Harga Clean"] = raw_price_series.apply(parse_harga_exact)

    list_kontrak = sorted(list(set([str(k).strip() for k in df_ref["Nomor Kontrak Clean"].unique() if k and k != "nan" and k != "-"])))

    transaksi_list = muat_data_transaksi_func()
    df_tx = pd.DataFrame(transaksi_list) if transaksi_list else pd.DataFrame()
    list_po = sorted(df_tx["Nomor PO"].dropna().astype(str).str.strip().unique().tolist()) if not df_tx.empty and "Nomor PO" in df_tx.columns else ["4500011739", "4500011740", "4500010745"]

    # --- 3. FORM INPUT HIERARKI MASTER PO ---
    st.markdown("#### 📝 Form Input Master Plafon PO")
    st.info("ℹ️ Pilih Kontrak. Nomor PO dapat dipilih dari dropdown transaksi atau diketik manual secara opsional jika PO terbit di awal/akhir.")

    c_top1, c_top2, c_top3 = st.columns(3)
    with c_top1:
        selected_kontrak = st.selectbox("📂 Pilih Nomor Kontrak", list_kontrak if list_kontrak else [""], key="po_sel_kontrak_rep_v10")
    with c_top2:
        selected_po_dd = st.selectbox("🔍 Pilih Nomor PO (Dropdown)", ["- (Pilih atau Ketik Manual)"] + list_po, key="po_sel_dropdown_rep_v10")
    with c_top3:
        manual_po_input = st.text_input("✍️ Atau Ketik No. PO Baru (Opsional)", value="", placeholder="Contoh: 4500011800", key="po_manual_input_rep_v10")

    final_po_number = manual_po_input.strip() if manual_po_input.strip() else (selected_po_dd if selected_po_dd != "- (Pilih atau Ketik Manual)" else "-")

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
        kat_pilih = st.selectbox("🏷️ Kategori Pekerjaan", base_list_kat if base_list_kat else ["-"], key="po_kat_pilih_rep_v10")
    
    kat_lower = str(kat_pilih).lower()
    is_provisional = "provisional" in kat_lower or "professional" in kat_lower
    is_estimated_sum = "estimated" in kat_lower or "estimasi" in kat_lower

    with c_k2:
        if is_provisional:
            spek_pilih = st.text_input("📋 Uraian Pekerjaan / Spesifikasi (Manual)", value="At Cost + Fee 15%", key="po_spek_manual_rep_v10")
        else:
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

            selected_display_spek = st.selectbox("📋 Uraian Pekerjaan / Spesifikasi", spek_options_formatted if spek_options_formatted else ["-"], key=f"po_spek_rep_v10_{selected_kontrak}_{kat_pilih}")
            spek_pilih = spek_display_map.get(selected_display_spek, selected_display_spek)

    hs_otomatis = 0.0
    unit_otomatis = "Month"

    if not is_provisional and spek_pilih != "- (Tidak ada data uraian)":
        match_rows = df_ref_kontrak[
            (df_ref_kontrak["Kategori Clean"] == str(kat_pilih).strip().upper()) & 
            (df_ref_kontrak["Uraian Clean"].str.lower() == str(spek_pilih).strip().lower())
        ]
        if match_rows.empty:
            match_rows = df_ref[
                (df_ref["Kategori Clean"] == str(kat_pilih).strip().upper()) & 
                (df_ref["Uraian Clean"].str.lower() == str(spek_pilih).strip().lower())
            ]
        if not match_rows.empty:
            r_final = match_rows.iloc[0]
            hs_otomatis = float(r_final.get("Harga Clean", 0.0) or 0.0)
            unit_otomatis = str(r_final.get("Unit Clean", "Month"))

    c_item1, c_item2 = st.columns(2)
    with c_item1:
        q_val = st.number_input("📦 Quantity / Volume PO (Isi Manual):", min_value=0.0, value=1.0, step=1.0, format="%.2f", key="po_qty_rep_v10")
    with c_item2:
        default_u_opts = ["Month", "Day", "Ls", "Unit", "Trip", "Jam", "EA", "AU", "Kg", "Pallet", "Ltr"]
        existing_u_from_master = df_ref["Unit Clean"].dropna().astype(str).unique().tolist() if "Unit Clean" in df_ref.columns else []
        u_opts = sorted(list(set(default_u_opts + existing_u_from_master)))
        
        def_unit = unit_otomatis if not is_provisional else "AU"
        if def_unit not in u_opts and def_unit:
            u_opts.insert(0, def_unit)
        idx_u = u_opts.index(def_unit) if def_unit in u_opts else 0
        u_val = st.selectbox("📏 Satuan / UOM (Aktif & Bisa Dipilih):", u_opts, index=idx_u, key=f"po_unit_rep_v10_{selected_kontrak}_{kat_pilih}")

    # --- INPUT KHUSUS PROVISIONAL / PROFESSIONAL SUM ---
    if is_provisional:
        st.markdown("---")
        st.markdown("##### ⚙️ Pengaturan Khusus At Cost + Fee 15%")
        harga_at_cost = st.number_input("💵 Harga At / Nilai Dasar At Cost (Rp):", min_value=0.0, value=0.0, step=1000.0, format="%.2f", key="po_at_cost_rep_v10")
        hs_final = harga_at_cost * 1.15
        total_plafon_item = q_val * hs_final
        keterangan_input = st.text_input("📝 Keterangan / Justifikasi Pekerjaan", value="", placeholder="Contoh: Garam Kasar Untuk Pekerjaan Sealant di Cluster B", key="po_ket_rep_v10")
    else:
        hs_final = hs_otomatis
        if is_estimated_sum:
            total_plafon_item = (q_val * hs_final * 0.9)
        else:
            total_plafon_item = q_val * hs_final
        keterangan_input = "-"

    formatted_hs = f"Rp {hs_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    formatted_total = f"Rp {total_plafon_item:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    st.markdown(f"💵 **Unit Price / Harga Satuan Final:** `{formatted_hs}`")
    st.markdown(f"💰 **Total Plafon / Total PO:** <span style='font-size:16px; font-weight:bold; color:#065f46;'>{formatted_total}</span>", unsafe_allow_html=True)

    with st.form(key="form_aksi_simpan_plafon_po_rep_v10"):
        submitted = st.form_submit_button("💾 Simpan Item ke Master Plafon PO", type="primary")
        if submitted:
            if q_val <= 0:
                st.warning("⚠️ Quantity / Volume PO harus diisi lebih besar dari 0.")
            elif final_po_number == "-" or not final_po_number:
                st.warning("⚠️ Nomor PO wajib dipilih dari dropdown atau diketik manual di kolom opsional!")
            else:
                new_record = {
                    "Nomor Kontrak": str(selected_kontrak).strip(),
                    "Nomor PO": str(final_po_number).strip(),
                    "Kategori": str(kat_pilih).strip(),
                    "Deskripsi Pekerjaan": str(spek_pilih).strip(),
                    "UOM": str(u_val).strip(),
                    "Volume PO": float(q_val),
                    "Unit Price": float(hs_final),
                    "Total Plafon (IDR)": float(total_plafon_item),
                    "Keterangan": str(keterangan_input).strip()
                }

                df_master = pd.concat([df_master, pd.DataFrame([new_record])], ignore_index=True)
                if simpan_master_po(df_master):
                    st.success(f"✅ Berhasil! Uraian [{spek_pilih}] untuk PO [{final_po_number}] berhasil disimpan.")
                    st.rerun()
                else:
                    st.error("⚠️ Gagal menyimpan ke file database master PO.")

    st.markdown("---")
    st.markdown("#### 📂 Daftar Master Plafon PO Tersimpan")
    if not df_master.empty:
        df_display = df_master.copy()
        if "Unit Price" in df_display.columns:
            df_display["Unit Price"] = df_display["Unit Price"].apply(lambda x: f"Rp {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        if "Total Plafon (IDR)" in df_display.columns:
            df_display["Total Plafon (IDR)"] = df_display["Total Plafon (IDR)"].apply(lambda x: f"Rp {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        st.dataframe(df_display, use_container_width=True)

        st.markdown("##### ⚙️ Kontrol & Hapus Data Tersimpan")
        col_del1, col_del2 = st.columns([2, 1])

        with col_del1:
            row_idx_to_delete = st.selectbox(
                "Pilih Nomor Baris (Index) yang ingin dihapus:",
                options=list(range(len(df_master))),
                format_func=lambda x: f"Baris #{x} — PO: {df_master.iloc[x].get('Nomor PO', '-')} | {str(df_master.iloc[x].get('Deskripsi Pekerjaan', ''))[:40]}...",
                key="sel_idx_hapus_baris_rep_v10"
            )
            if st.button("🗑️ Hapus Baris Terpilih Saja", type="secondary"):
                df_master = df_master.drop(index=row_idx_to_delete).reset_index(drop=True)
                if simpan_master_po(df_master):
                    st.success(f"✅ Berhasil menghapus Baris #{row_idx_to_delete}!")
                    st.rerun()
                else:
                    st.error("⚠️ Gagal memperbarui file database.")

        with col_del2:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("⚠️ Reset Seluruh Data PO", type="primary"):
                if os.path.exists(path_master_po_excel):
                    os.remove(path_master_po_excel)
                st.cache_data.clear()
                st.success("✅ Seluruh data Plafon PO berhasil direset!")
                st.rerun()
    else:
        st.info("Belum ada data Plafon PO tersimpan.")

    # =========================================================================
    # --- 4. LAPORAN ANALISIS PENYERAPAN & SISA ANGGARAN PO (SMART MATCH_KEY) ---
    # =========================================================================
    st.markdown("---")
    st.markdown("### 📈 Laporan Rekapitulasi Penyerapan & Sisa Anggaran PO (Interaktif)")
    st.info("ℹ️ Klik pada Accordion Nomor PO di bawah untuk membuka detail transaksi, persentase penyerapan, dan grafik porsi anggaran per PO.")

    if df_master.empty:
        st.warning("⚠️ Belum ada data Master Plafon PO untuk menghasilkan laporan analisis.")
        return

    tx_records = muat_data_transaksi_func()
    df_actual = pd.DataFrame(tx_records) if transaksi_list else pd.DataFrame()

    df_plafon = df_master.copy()
    df_plafon["Nomor PO"] = df_plafon["Nomor PO"].astype(str).str.strip()
    df_plafon["Kategori_Clean"] = df_plafon["Kategori"].astype(str).str.strip().str.upper()
    df_plafon["Deskripsi_Clean"] = df_plafon["Deskripsi Pekerjaan"].astype(str).str.strip().str.lower()
    df_plafon["Keterangan_Clean"] = df_plafon.get("Keterangan", "").astype(str).str.strip().str.lower()

    df_plafon["Volume PO"] = pd.to_numeric(df_plafon["Volume PO"], errors="coerce").fillna(0.0)
    df_plafon["Total Plafon (IDR)"] = pd.to_numeric(df_plafon["Total Plafon (IDR)"], errors="coerce").fillna(0.0)

    if not df_actual.empty:
        df_actual["Nomor PO"] = df_actual.get("Nomor PO", "-").astype(str).str.strip()
        df_actual["Kategori_Clean"] = df_actual.get("Kategori", "-").astype(str).str.strip().str.upper()
        
        if "Deskripsi Pekerjaan" in df_actual.columns:
            df_actual["Deskripsi_Clean"] = df_actual["Deskripsi Pekerjaan"].astype(str).str.strip().str.lower()
        elif "Uraian Pekerjaan" in df_actual.columns:
            df_actual["Deskripsi_Clean"] = df_actual["Uraian Pekerjaan"].astype(str).str.strip().str.lower()
        else:
            df_actual["Deskripsi_Clean"] = ""

        if "Keterangan" in df_actual.columns:
            df_actual["Keterangan_Clean"] = df_actual["Keterangan"].astype(str).str.strip().str.lower()
        elif "Catatan" in df_actual.columns:
            df_actual["Keterangan_Clean"] = df_actual["Catatan"].astype(str).str.strip().str.lower()
        else:
            df_actual["Keterangan_Clean"] = ""

        df_actual["Qty_Aktual"] = pd.to_numeric(df_actual.get("Qty", 0.0), errors="coerce").fillna(0.0)
        df_actual["Total_Aktual"] = pd.to_numeric(df_actual.get("Total Harga", 0.0), errors="coerce").fillna(0.0)
    else:
        df_actual = pd.DataFrame(columns=["Nomor PO", "Kategori_Clean", "Deskripsi_Clean", "Keterangan_Clean", "Qty_Aktual", "Total_Aktual"])

    # --- STRATEGI PENCOCOKAN CERDAS (SMART MATCH_KEY) ---
    # Jika Provisional/Professional Sum -> Match pakai Keterangan
    # Jika Master Kontrak Standard -> Match pakai Uraian / Deskripsi Pekerjaan
    if not df_actual.empty:
        df_plafon["Match_Key"] = df_plafon.apply(
            lambda r: r["Keterangan_Clean"] if "provisional" in str(r["Kategori_Clean"]).lower() or "professional" in str(r["Kategori_Clean"]).lower() else r["Deskripsi_Clean"],
            axis=1
        )
        df_actual["Match_Key"] = df_actual.apply(
            lambda r: r["Keterangan_Clean"] if "provisional" in str(r["Kategori_Clean"]).lower() or "professional" in str(r["Kategori_Clean"]).lower() else r["Deskripsi_Clean"],
            axis=1
        )

        df_realisasi_agg = df_actual.groupby(["Nomor PO", "Match_Key"], as_index=False).agg({
            "Qty_Aktual": "sum",
            "Total_Aktual": "sum"
        })
        
        df_report = pd.merge(
            df_plafon,
            df_realisasi_agg,
            on=["Nomor PO", "Match_Key"],
            how="left"
        )
    else:
        df_report = df_plafon.copy()
        df_report["Qty_Aktual"] = 0.0
        df_report["Total_Aktual"] = 0.0

    df_report["Qty_Aktual"] = df_report["Qty_Aktual"].fillna(0.0)
    df_report["Total_Aktual"] = df_report["Total_Aktual"].fillna(0.0)

    df_report["Sisa Volume"] = df_report["Volume PO"] - df_report["Qty_Aktual"]
    df_report["Sisa Anggaran (IDR)"] = df_report["Total Plafon (IDR)"] - df_report["Total_Aktual"]

    df_report["% Penyerapan Nilai"] = df_report.apply(
        lambda r: (r["Total_Aktual"] / r["Total Plafon (IDR)"] * 100) if r["Total Plafon (IDR)"] > 0 else 0.0, axis=1
    )
    df_report["% Penyerapan Volume"] = df_report.apply(
        lambda r: (r["Qty_Aktual"] / r["Volume PO"] * 100) if r["Volume PO"] > 0 else 0.0, axis=1
    )

    list_po_unique = sorted(df_report["Nomor PO"].unique().tolist())

    for po_num in list_po_unique:
        df_po_sub = df_report[df_report["Nomor PO"] == po_num]
        tot_plafon_po = df_po_sub["Total Plafon (IDR)"].sum()
        tot_real_po = df_po_sub["Total_Aktual"].sum()
        tot_sisa_po = df_po_sub["Sisa Anggaran (IDR)"].sum()
        pct_po = (tot_real_po / tot_plafon_po * 100) if tot_plafon_po > 0 else 0.0

        with st.expander(f"📦 Nomor PO: {po_num} | Plafon: Rp {tot_plafon_po:,.2f} | Penyerapan: Rp {tot_real_po:,.2f} ({pct_po:.1f}%)".replace(",", "X").replace(".", ",").replace("X", ".")):
            
            mc1, mc2, mc3, mc4 = st.columns(4)
            with mc1:
                st.metric("Plafon PO", f"Rp {tot_plafon_po:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            with mc2:
                st.metric("Realisasi", f"Rp {tot_real_po:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            with mc3:
                st.metric("Sisa Anggaran", f"Rp {tot_sisa_po:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            with mc4:
                st.metric("% Penyerapan", f"{pct_po:.1f}%")

            st.markdown("---")
            st.markdown("##### 📋 Detail Breakdown Item Pekerjaan")

            df_po_tbl = df_po_sub[[
                "Nomor Kontrak", "Kategori", "Deskripsi Pekerjaan", "Keterangan", "UOM",
                "Volume PO", "Qty_Aktual", "Sisa Volume", "% Penyerapan Volume",
                "Total Plafon (IDR)", "Total_Aktual", "Sisa Anggaran (IDR)", "% Penyerapan Nilai"
            ]].copy()

            df_po_tbl.columns = [
                "No. Kontrak", "Kategori", "Uraian Pekerjaan", "Keterangan / Justifikasi", "UOM",
                "Vol PO", "Real Qty", "Sisa Qty", "% Vol Penyerapan",
                "Total Plafon", "Real Nilai", "Sisa Nilai", "% Nilai Penyerapan"
            ]

            for col in ["Total Plafon", "Real Nilai", "Sisa Nilai"]:
                df_po_tbl[col] = df_po_tbl[col].apply(lambda x: f"Rp {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            for col in ["% Vol Penyerapan", "% Nilai Penyerapan"]:
                df_po_tbl[col] = df_po_tbl[col].apply(lambda x: f"{float(x):,.1f}%")

            st.dataframe(df_po_tbl, use_container_width=True)

            st.markdown("##### 🥧 Grafik Porsi Anggaran / Penyerapan Berdasarkan Uraian Pekerjaan")
            if not df_po_sub.empty and tot_plafon_po > 0:
                try:
                    import matplotlib.pyplot as plt

                    fig, ax = plt.subplots(figsize=(7, 4))
                    pie_data = df_po_sub.groupby("Deskripsi Pekerjaan")["Total Plafon (IDR)"].sum()
                    pie_data = pie_data[pie_data > 0]

                    if not pie_data.empty:
                        wedges, texts, autotexts = ax.pie(
                            pie_data,
                            labels=None,
                            autopct='%1.1f%%',
                            startangle=140,
                            colors=plt.cm.Pastel1.colors
                        )
                        for autotext in autotexts:
                            autotext.set_color('black')
                            autotext.set_fontsize(9)
                            autotext.set_weight('bold')

                        ax.legend(
                            wedges,
                            [f"{str(k)[:30]}... (Rp {v:,.0f})" for k, v in pie_data.items()],
                            title="Uraian Pekerjaan",
                            loc="center left",
                            bbox_to_anchor=(1, 0, 0.5, 1),
                            fontsize=8
                        )
                        ax.set_title(f"Porsi Plafon PO {po_num}", fontsize=11, fontweight='bold', color='#065f46')
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
                    else:
                        st.info("Data nilai plafon bernilai 0 untuk grafik.")
                except Exception as e:
                    st.warning(f"⚠️ Gagal merender grafik lingkaran: {e}")
            else:
                st.info("Belum ada data untuk ditampilkan dalam grafik.")