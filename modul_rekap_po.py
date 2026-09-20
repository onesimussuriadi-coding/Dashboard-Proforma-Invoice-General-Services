import streamlit as st
import pandas as pd
import os
import altair as alt

def tampilkan_rekap_penyerapan_po(
    muat_data_transaksi_func,
    bersih_angka_func,
    master_ref_data=None
):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📊 Rekapitulasi & Kontrol Penyerapan Purchase Order (PO) - Master Plafon & Multi-PI Tracking</h3>
            <p style="margin-bottom:0; font-size:12px; color:#4b5563;">Kontrol anggaran berbasis Master Plafon PO terpusat (Sinkronisasi mutlak langsung dari Master Kontrak Modul 0).</p>
        </div>
    """, unsafe_allow_html=True)

    # --- PENGATURAN PENYIMPANAN MASTER PO LOKAL ---
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

    # --- PEMBACAAN FISIK MASTER REFERENSI KONTRAK (MODUL 0) ---
    path_kontrak_excel = os.path.join("database_penyimpanan_aman", "database_kontrak.xlsx")
    df_ref = pd.DataFrame()

    if os.path.exists(path_kontrak_excel):
        try:
            df_ref = pd.read_excel(path_kontrak_excel)
        except:
            pass

    if df_ref.empty and master_ref_data:
        df_ref = pd.DataFrame(master_ref_data)

    if df_ref.empty:
        df_ref = pd.DataFrame([
            {"Nomor Kontrak": "7207250142", "Kategori": "MONTHLY BASIS", "Uraian Pekerjaan": "Jasa Sewa Alat Berat Monthly Basis", "Unit": "Month", "Harga Satuan": 131224000.0}
        ])

    # Normalisasi Kolom secara Presisi sesuai Pola Modul Referensi Bapak
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

    # --- KODE KONTRAK & PO (DIJAMIN TIDAK DIGANTI / SESUAI PILIHAN AWAL BAPAK) ---
    list_kontrak_ref = sorted(df_ref["Nomor Kontrak Clean"].dropna().unique().tolist())

    transaksi_list = muat_data_transaksi_func()
    df_tx = pd.DataFrame(transaksi_list) if transaksi_list else pd.DataFrame()
    list_po_ref = sorted(df_tx["Nomor PO"].dropna().astype(str).str.strip().unique().tolist()) if not df_tx.empty and "Nomor PO" in df_tx.columns else ["4500011739", "4500011740"]

    # --- TAB / SUB-MENU ---
    tab_pilih, tab_input = st.tabs(["📊 Lihat Rekapitulasi & Kontrol PO", "➕ Input / Kelola Master Plafon PO"])

    with tab_input:
        st.markdown("#### 📝 Form Input Master Plafon PO (Sinkronisasi Mutlak Kategori & Uraian)")
        st.info("ℹ️ Pilih Nomor Kontrak. Kategori dan Uraian Pekerjaan kini disempurnakan persis mengikuti pola modul referensi.")

        with st.form(key="form_input_master_po"):
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                in_kontrak = st.selectbox("📂 Pilih Nomor Kontrak:", list_kontrak_ref if list_kontrak_ref else [""], key="input_master_kontrak")
            with c_m2:
                in_po = st.selectbox("🔍 Pilih Nomor PO:", list_po_ref if list_po_ref else [""], key="input_master_po")

            # --- PERBAIKAN FOKUS UTAMA: KATEGORI & URAIAN BERDASARKAN POLA MODUL REFERENSI ---
            df_ref_kontrak = df_ref[df_ref["Nomor Kontrak Clean"] == str(in_kontrak).strip()]
            if df_ref_kontrak.empty:
                df_ref_kontrak = df_ref

            base_list_kat = sorted(df_ref_kontrak["Kategori Clean"].dropna().unique().tolist())
            if not base_list_kat:
                base_list_kat = sorted(df_ref["Kategori Clean"].dropna().unique().tolist())

            if "PROFESSIONAL SUM" not in base_list_kat and "PROVISIONAL SUM" not in base_list_kat:
                base_list_kat.append("PROVISIONAL SUM")
            if "ESTIMATED SUM" not in base_list_kat:
                base_list_kat.append("ESTIMATED SUM")

            c_m3, c_m4, c_m5 = st.columns(3)
            with c_m3:
                in_kategori = st.selectbox("🏷️ Kategori Pekerjaan:", base_list_kat if base_list_kat else ["-"], key="input_master_kategori")

            # Filter Uraian secara presisi murni berdasarkan Kategori yang aktif pada Kontrak tersebut
            kat_lower = str(in_kategori).lower()
            is_provisional = "provisional" in kat_lower or "professional" in kat_lower

            with c_m4:
                if is_provisional:
                    in_deskripsi = st.text_input("📋 Uraian Pekerjaan / Spesifikasi (Manual):", value="At Cost + Fee 15%", key="input_master_desc_manual")
                    df_f_kat = pd.DataFrame()
                else:
                    df_f_kat = df_ref_kontrak[df_ref_kontrak["Kategori Clean"] == str(in_kategori).strip().upper()]
                    if df_f_kat.empty:
                        df_f_kat = df_ref[df_ref["Kategori Clean"] == str(in_kategori).strip().upper()]
                    
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

                    selected_display_spek = st.selectbox("📋 Uraian Pekerjaan / Spesifikasi:", spek_options_formatted if spek_options_formatted else ["-"], key="input_master_deskripsi")
                    in_deskripsi = spek_display_map.get(selected_display_spek, selected_display_spek)

            # --- SATUAN / UOM & HARGA SATUAN OTOMATIS DARI EXCEL ---
            hs_otomatis = 0.0
            unit_otomatis = "Month"
            
            if not is_provisional and not df_f_kat.empty and in_deskripsi != "- (Tidak ada data uraian)":
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
                
                in_uom = st.selectbox("📏 Satuan / UOM (Otomatis Excel):", u_opts, index=idx_u, key="input_master_uom")

            c_m6, c_m7 = st.columns(2)
            with c_m6:
                in_vol = st.number_input("📦 Quantity / Volume PO (Isi Manual):", value=0.0, step=1.0, format="%.2f")
            with c_m7:
                in_price = st.number_input("💵 Unit Price / Harga Satuan (IDR - Otomatis dari Excel):", value=hs_otomatis, step=1000.0, format="%.2f")

            submit_master = st.form_submit_button("💾 Simpan Item ke Master Plafon PO", type="primary")
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
                    st.success(f"✅ Master Plafon untuk PO `{in_po}` berhasil disimpan secara presisi!")
                    st.rerun()
                else:
                    st.error("⚠️ Gagal menyimpan ke file master PO.")

        st.markdown("---")
        st.markdown("#### 📂 Daftar Master Plafon PO Tersimpan")
        if not df_master.empty:
            st.dataframe(df_master, use_container_width=True)
            if st.button("🗑️ Reset / Hapus Seluruh Master PO"):
                if os.path.exists(path_master_po_excel):
                    os.remove(path_master_po_excel)
                st.success("✅ Master PO berhasil direset!")
                st.rerun()
        else:
            st.info("Belum ada data Master Plafon PO yang diinput.")

    with tab_pilih:
        if df_master.empty:
            st.warning("⚠️ Belum ada data Master Plafon PO. Silakan input terlebih dahulu melalui tab **'Input / Kelola Master Plafon PO'**.")
            return

        df_master["PO Clean"] = df_master["Nomor PO"].astype(str).str.strip()
        df_master["Kontrak Clean"] = df_master["Nomor Kontrak"].astype(str).str.strip()
        df_master["Desc Clean"] = df_master["Deskripsi Pekerjaan"].astype(str).str.strip()

        path_opname_excel = os.path.join("database_penyimpanan_aman", "database_opname_parameter.xlsx")
        df_opname = pd.DataFrame()
        if os.path.exists(path_opname_excel):
            try:
                df_opname = pd.read_excel(path_opname_excel)
                if "Nomor PO" in df_opname.columns:
                    df_opname["PO Clean"] = df_opname["Nomor PO"].astype(str).str.strip()
                if "Nomor PI" in df_opname.columns:
                    df_opname["PI Clean"] = df_opname["Nomor PI"].astype(str).str.strip()
                if "Item Description" in df_opname.columns:
                    df_opname["Desc Clean"] = df_opname["Item Description"].astype(str).str.strip()
            except:
                pass

        st.markdown("---")
        
        list_kontrak_unik = sorted(df_master["Kontrak Clean"].unique().tolist())
        selected_kontrak = st.selectbox("📂 Pilih Nomor Kontrak:", ["-- SEMUA KONTRAK --"] + list_kontrak_unik, key="rekap_kontrak_select")

        if selected_kontrak != "-- SEMUA KONTRAK --":
            df_filtered_kontrak = df_master[df_master["Kontrak Clean"] == selected_kontrak]
        else:
            df_filtered_kontrak = df_master

        list_po_unik = sorted(df_filtered_kontrak["PO Clean"].unique().tolist())
        selected_po = st.selectbox("🔍 Pilih Nomor PO:", ["-- SEMUA PO DALAM KONTRAK INI --"] + list_po_unik, key="rekap_po_select")

        if selected_po != "-- SEMUA PO DALAM KONTRAK INI --":
            df_filtered = df_filtered_kontrak[df_filtered_kontrak["PO Clean"] == selected_po]
        else:
            df_filtered = df_filtered_kontrak

        st.markdown("---")

        is_all_kontrak = (selected_kontrak == "-- SEMUA KONTRAK --")
        is_all_po = (selected_po == "-- SEMUA PO DALAM KONTRAK INI --")

        if is_all_kontrak and is_all_po:
            st.markdown("### 📑 Tabel Rekapitulasi Global Berdasarkan Master Plafon PO")
            st.info("ℹ️ Menampilkan ringkasan total plafon tetap dan penyerapan kumulatif lintas PI per PO.")

            global_summary_rows = []
            tot_plafon_global, tot_serap_global, tot_sisa_global = 0.0, 0.0, 0.0

            for po_item in df_master["PO Clean"].unique():
                df_m_sub = df_master[df_master["PO Clean"] == po_item]
                k_info = df_m_sub["Kontrak Clean"].iloc[0]

                p_po = df_m_sub["Total Plafon (IDR)"].sum()
                
                t_serap_val = 0.0
                if not df_opname.empty and "PO Clean" in df_opname.columns:
                    df_op_sub = df_opname[df_opname["PO Clean"] == po_item]
                    for _, m_row in df_m_sub.iterrows():
                        d_text = m_row["Desc Clean"]
                        u_prc = float(m_row["Unit Price"])
                        
                        df_item_pi = df_op_sub[df_op_sub["Desc Clean"].str.contains(d_text, case=False, na=False)]
                        v_cum = 0.0
                        for _, sub_row in df_item_pi.iterrows():
                            try:
                                v_cum += float(sub_row.get("Volume Previous", 0)) + float(sub_row.get("Volume Aktual", 0))
                            except: pass
                        t_serap_val += v_cum * u_prc

                sisa_val = p_po - t_serap_val
                rasio = (t_serap_val / p_po * 100) if p_po > 0 else 0.0

                tot_plafon_global += p_po
                tot_serap_global += t_serap_val
                tot_sisa_global += sisa_val

                global_summary_rows.append({
                    "Nomor Kontrak": k_info,
                    "Nomor PO": po_item,
                    "Total Plafon PO (IDR)": p_po,
                    "Total Terserap (IDR)": t_serap_val,
                    "Sisa Anggaran (IDR)": sisa_val,
                    "Rasio (%)": f"{rasio:.2f}%"
                })

            df_global = pd.DataFrame(global_summary_rows)
            
            df_global_display = df_global.copy()
            df_global_display["Total Plafon PO (IDR)"] = df_global_display["Total Plafon PO (IDR)"].apply(lambda x: f"Rp {x:,.2f}")
            df_global_display["Total Terserap (IDR)"] = df_global_display["Total Terserap (IDR)"].apply(lambda x: f"Rp {x:,.2f}")
            df_global_display["Sisa Anggaran (IDR)"] = df_global_display["Sisa Anggaran (IDR)"].apply(lambda x: f"Rp {x:,.2f}")

            st.dataframe(df_global_display, use_container_width=True)

            st.markdown("#### 📌 Total / Jumlah Keseluruhan Global")
            rasio_global = (tot_serap_global / tot_plafon_global * 100) if tot_plafon_global > 0 else 0.0
            
            st.markdown("""
                <style>
                div[data-testid="metric-container"] label { font-size: 13px !important; color: #475569 !important; }
                div[data-testid="metric-container"] div[data-testid="stMetricValue"] { font-size: 20px !important; font-weight: 700 !important; color: #0f172a !important; }
                </style>
            """, unsafe_allow_html=True)

            gc1, gc2, gc3, gc4 = st.columns(4)
            with gc1:
                st.metric("Total Plafon Global", f"Rp {tot_plafon_global:,.2f}")
            with gc2:
                st.metric("Total Terserap Global", f"Rp {tot_serap_global:,.2f}", delta=f"{rasio_global:.1f}%")
            with gc3:
                st.metric("Total Sisa Anggaran", f"Rp {tot_sisa_global:,.2f}")
            with gc4:
                st.metric("Rasio Global", f"{rasio_global:.2f}%")

            st.markdown("##### 📉 Grafik Proporsi Penyerapan Anggaran Global")
            chart_global = pd.DataFrame({
                'Kategori': ['Sisa Anggaran', 'Sudah Terserap'],
                'Nilai': [max(0.0, tot_sisa_global), max(0.0, tot_serap_global)]
            }).set_index('Kategori')

            st.altair_chart(
                alt.Chart(chart_global.reset_index()).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="Nilai", type="quantitative"),
                    color=alt.Color(
                        field="Kategori", 
                        type="nominal", 
                        scale=alt.Scale(domain=['Sisa Anggaran', 'Sudah Terserap'], range=["#10b981", "#cbd5e1"])
                    ),
                    tooltip=['Kategori', alt.Tooltip('Nilai:Q', format=',.2f')]
                ).properties(width=400, height=300),
                use_container_width=True
            )
            return

        target_po_list = df_filtered["PO Clean"].unique().tolist()
        if not target_po_list:
            st.info("ℹ️ Tidak ada data PO yang sesuai dengan filter.")
            return

        st.markdown(f"### 📋 Detail Breakdown Kontrol Anggaran & Penyerapan PO (Master Plafon vs Multi-PI)")

        for po_item in target_po_list:
            df_m_sub = df_master[df_master["PO Clean"] == po_item]
            kontrak_info = df_m_sub["Kontrak Clean"].iloc[0]

            st.markdown(f"#### 📁 Nomor PO: `{po_item}` | Kontrak: `{kontrak_info}`")

            df_op_sub = df_opname[df_opname["PO Clean"] == po_item] if not df_opname.empty and "PO Clean" in df_opname.columns else pd.DataFrame()

            tabel_rows = []
            tot_val_po, tot_val_cum, tot_val_sisa = 0.0, 0.0, 0.0

            for idx, (_, m_row) in enumerate(df_m_sub.iterrows(), start=1):
                desc_text = str(m_row.get("Deskripsi Pekerjaan", f"Item #{idx}"))
                cat_text = str(m_row.get("Kategori", ""))
                uom_text = str(m_row.get("UOM", "Day"))
                vol_po = float(m_row.get("Volume PO", 0))
                unit_price = float(m_row.get("Unit Price", 0))
                total_price_po = vol_po * unit_price

                df_item_all_pi = df_op_sub[df_op_sub["Desc Clean"].str.contains(desc_text, case=False, na=False)] if not df_op_sub.empty else pd.DataFrame()
                list_pi_used = df_item_all_pi["PI Clean"].unique().tolist() if not df_item_all_pi.empty and "PI Clean" in df_item_all_pi.columns else []
                pi_str_note = ", ".join(list_pi_used) if list_pi_used else "Belum ada penyerapan PI"

                prev_vol_total, curr_vol_total = 0.0, 0.0
                if not df_item_all_pi.empty:
                    for _, sub_row in df_item_all_pi.iterrows():
                        try:
                            prev_vol_total += float(sub_row.get("Volume Previous", 0))
                        except: pass
                        try:
                            curr_vol_total += float(sub_row.get("Volume Aktual", 0))
                        except: pass

                cumulative_vol = prev_vol_total + curr_vol_total
                cumulative_val = cumulative_vol * unit_price

                sisa_vol = vol_po - cumulative_vol
                sisa_val = total_price_po - cumulative_val

                tot_val_po += total_price_po
                tot_val_cum += cumulative_val
                tot_val_sisa += sisa_val

                tabel_rows.append({
                    "No.": idx,
                    "Item Description": f"<b>{cat_text}</b> - {desc_text}<br><span style='font-size:10px; color:#64748b;'>Ditagih via PI: {pi_str_note}</span>",
                    "UOM": uom_text,
                    "Volume PO": f"{vol_po:,.2f}",
                    "Unit Price (IDR)": f"{unit_price:,.2f}",
                    "Total Plafon (IDR)": f"{total_price_po:,.2f}",
                    "Volume Previous": f"{prev_vol_total:,.2f}",
                    "Volume Aktual": f"{curr_vol_total:,.2f}",
                    "Cumulative Volume": f"{cumulative_vol:,.2f}",
                    "Cumulative Nilai (IDR)": f"{cumulative_val:,.2f}",
                    "Sisa Volume": f"{sisa_vol:,.2f}",
                    "Sisa Nilai (IDR)": f"{sisa_val:,.2f}"
                })

            df_laporan = pd.DataFrame(tabel_rows)
            st.markdown(df_laporan.to_html(escape=False, index=False), unsafe_allow_html=True)

            st.markdown(f"#### 📌 Ringkasan Akumulasi Total untuk PO: `{po_item}`")
            
            pct_serap = (tot_val_cum / tot_val_po * 100) if tot_val_po > 0 else 0.0
            pct_sisa = (tot_val_sisa / tot_val_po * 100) if tot_val_po > 0 else 0.0

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Total Plafon PO", f"Rp {tot_val_po:,.2f}")
            with c2:
                st.metric("Total Kumulatif Diserap", f"Rp {tot_val_cum:,.2f}", delta=f"{pct_serap:.1f}% dari PO")
            with c3:
                st.metric("Total Sisa Saldo Akhir", f"Rp {tot_val_sisa:,.2f}", delta=f"-{pct_sisa:.1f}% sisa", delta_color="inverse")
            with c4:
                st.metric("Rasio Akumulasi", f"{pct_serap:.2f}%")

            st.markdown(f"##### 📉 Grafik Proporsi Akumulasi Penyerapan PO `{po_item}`")
            
            chart_data = pd.DataFrame({
                'Kategori': ['Sisa Anggaran', 'Sudah Terserap Kumulatif'],
                'Nilai': [max(0.0, tot_val_sisa), max(0.0, tot_val_cum)]
            }).set_index('Kategori')

            st.altair_chart(
                alt.Chart(chart_global.reset_index()).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="Nilai", type="quantitative"),
                    color=alt.Color(
                        field="Kategori", 
                        type="nominal", 
                        scale=alt.Scale(domain=['Sisa Anggaran', 'Sudah Terserap Kumulatif'], range=["#10b981", "#cbd5e1"])
                    ),
                    tooltip=['Kategori', alt.Tooltip('Nilai:Q', format=',.2f')]
                ).properties(width=400, height=300),
                use_container_width=True
            )

            st.markdown("---")