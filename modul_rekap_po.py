import streamlit as st
import pandas as pd
import os
import altair as alt

def tampilkan_rekap_penyerapan_po(
    muat_data_transaksi_func,
    bersih_angka_func
):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📊 Rekapitulasi & Kontrol Penyerapan Purchase Order (PO) - Master Plafon & Multi-PI Tracking</h3>
            <p style="margin-bottom:0; font-size:12px; color:#4b5563;">Kontrol anggaran berbasis Master Plafon PO terpusat vs penyerapan kumulatif lintas Proforma Invoice (PI).</p>
        </div>
    """, unsafe_allow_html=True)

    # --- PENGATURAN PENYIMPANAN MASTER PO LOKAL ---
    DIR_DB_LOKAL = os.path.join("database_penyimpanan_aman")
    if not os.path.exists(DIR_DB_LOKAL):
        os.makedirs(DIR_DB_LOKAL)
    path_master_po_excel = os.path.join(DIR_DB_LOKAL, "database_master_po.xlsx")

    # Inisialisasi atau muat Master PO
    def muat_master_po():
        if os.path.exists(path_master_po_excel):
            try:
                df = pd.read_excel(path_master_po_excel)
                return df
            except:
                pass
        return pd.DataFrame(columns=["Nomor Kontrak", "Nomor PO", "Kategori", "Deskripsi Pekerjaan", "UOM", "Volume PO", "Unit Price", "Total Plafon (IDR)"])

    def simpan_master_po(df):
        try:
            df.to_excel(path_master_po_excel, index=False)
            return True
        except:
            return false

    df_master = muat_master_po()

    # --- TAB / SUB-MENU: INPUT MASTER PLAFON PO & REKAPITULASI ---
    tab_pilih, tab_input = st.tabs(["📊 Lihat Rekapitulasi & Kontrol PO", "➕ Input / Kelola Master Plafon PO"])

    with tab_input:
        st.markdown("#### 📝 Form Input / Tambah Master Plafon PO")
        st.info("ℹ️ Definisikan batas anggaran tetap (*budget ceiling*) untuk setiap Nomor PO dan item pekerjaannya di sini agar terhindar dari *double counting*.")

        with st.form(key="form_input_master_po"):
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                in_kontrak = st.text_input("📂 Nomor Kontrak:", value="7201250141")
            with c_m2:
                in_po = st.text_input("🔍 Nomor PO:", value="4500011739")

            c_m3, c_m4, c_m5 = st.columns(3)
            with c_m3:
                in_kategori = st.text_input("🏷️ Kategori:", value="ADDITIONAL CAMP SERVICES")
            with c_m4:
                in_deskripsi = st.text_input("📋 Deskripsi Uraian Pekerjaan:", value="Food & beverage, main course")
            with c_m5:
                in_uom = st.selectbox("📏 Satuan (UOM):", ["Day", "Unit", "AU", "Month", "Ls", "Pcs"], index=0)

            c_m6, c_m7 = st.columns(2)
            with c_m6:
                in_vol = st.number_input("📦 Quantity / Volume PO:", value=18300.0, step=1.0, format="%.2f")
            with c_m7:
                in_price = st.number_input("💵 Unit Price / Harga Satuan (IDR):", value=65000.0, step=1000.0, format="%.2f")

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
                    st.success(f"✅ Master Plafon untuk PO `{in_po}` berhasil disimpan!")
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

        # Normalisasi kolom master
        df_master["PO Clean"] = df_master["Nomor PO"].astype(str).str.strip()
        df_master["Kontrak Clean"] = df_master["Nomor Kontrak"].astype(str).str.strip()
        df_master["Desc Clean"] = df_master["Deskripsi Pekerjaan"].astype(str).str.strip()

        # Muat data realisasi penyerapan dari database opname parameter
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
        
        # Filter Berjenjang
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

        # KONDISI 1: TABEL REKAP GLOBAL
        if is_all_kontrak and is_all_po:
            st.markdown("### 📑 Tabel Rekapitulasi Global Berdasarkan Master Plafon PO")
            st.info("ℹ️ Menampilkan ringkasan total plafon tetap dan penyerapan kumulatif lintas PI per PO.")

            global_summary_rows = []
            tot_plafon_global, tot_serap_global, tot_sisa_global = 0.0, 0.0, 0.0

            for po_item in df_master["PO Clean"].unique():
                df_m_sub = df_master[df_master["PO Clean"] == po_item]
                k_info = df_m_sub["Kontrak Clean"].iloc[0]

                p_po = df_m_sub["Total Plafon (IDR)"].sum()
                
                # Hitung penyerapan kumulatif dari database opname berdasarkan kecocokan PO
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

        # KONDISI 2 & 3: KONTRAK / PO TERTENTU DIPILIH (DETAIL BREAKDOWN MULTI-PI)
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

                # Lacak penyerapan dari database opname berdasarkan deskripsi
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
                alt.Chart(chart_data.reset_index()).mark_arc(innerRadius=50).encode(
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