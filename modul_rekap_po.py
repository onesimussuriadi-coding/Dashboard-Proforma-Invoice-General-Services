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
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📊 Rekapitulasi & Kontrol Penyerapan Mutasi Purchase Order (PO)</h3>
            <p style="margin-bottom:0; font-size:12px; color:#4b5563;">Analisis berjenjang murni bersumber dari database opname parameter (Volume & Unit Price terpisah Nomor PI & PO) vs realisasi transaksi.</p>
        </div>
    """, unsafe_allow_html=True)

    # 1. SUMBER UTAMA PARAMETER: Muat data murni dari database_opname_parameter.xlsx
    path_opname_excel = os.path.join("database_penyimpanan_aman", "database_opname_parameter.xlsx")
    if not os.path.exists(path_opname_excel):
        st.error(f"⚠️ File database opname parameter tidak ditemukan di: {path_opname_excel}")
        return

    try:
        df_opname = pd.read_excel(path_opname_excel)
    except Exception as e:
        st.error(f"⚠️ Gagal membaca file database opname parameter: {e}")
        return

    if df_opname.empty:
        st.warning("⚠️ Database opname parameter kosong.")
        return

    # Normalisasi kolom Nomor PI dan Nomor PO
    if "Nomor PO" in df_opname.columns:
        df_opname["PO Clean"] = df_opname["Nomor PO"].astype(str).str.strip()
    elif "doc_key" in df_opname.columns:
        # Fallback ekstraksi dari doc_key jika kolom Nomor PO belum ada
        def extract_po(key):
            try:
                parts = str(key).split('_')
                if parts:
                    p = parts[-1].strip()
                    if p.isdigit(): return p
            except: pass
            return "UNKNOWN"
        df_opname["PO Clean"] = df_opname["doc_key"].apply(extract_po)
    else:
        df_opname["PO Clean"] = "UNKNOWN"

    if "Nomor PI" in df_opname.columns:
        df_opname["PI Clean"] = df_opname["Nomor PI"].astype(str).str.strip()
    else:
        df_opname["PI Clean"] = "-"

    df_opname = df_opname[(df_opname["PO Clean"] != "") & (df_opname["PO Clean"] != "nan") & (df_opname["PO Clean"] != "UNKNOWN")]

    if df_opname.empty:
        st.warning("⚠️ Tidak ada data Nomor PO yang valid di database opname parameter.")
        return

    # 2. Muat data transaksi (Modul 2) untuk pemetaan Nomor Kontrak
    transaksi_list = muat_data_transaksi_func()
    df_tx = pd.DataFrame(transaksi_list) if transaksi_list else pd.DataFrame()
    if not df_tx.empty and "Nomor PO" in df_tx.columns:
        df_tx["PO Clean"] = df_tx["Nomor PO"].astype(str).str.strip()
    else:
        df_tx["PO Clean"] = pd.Series(dtype=str)

    po_to_kontrak = {}
    if not df_tx.empty and "Nomor Kontrak" in df_tx.columns:
        for _, r in df_tx.iterrows():
            p_val = str(r.get("PO Clean", "")).strip()
            k_val = str(r.get("Nomor Kontrak", "")).strip()
            if p_val and k_val and p_val != "nan":
                po_to_kontrak[p_val] = k_val

    df_opname["Kontrak Clean"] = df_opname["PO Clean"].map(po_to_kontrak).fillna("KONTRAK BELUM TERMAPING")

    st.markdown("---")
    
    # 3. Filter Berjenjang berdasarkan data murni opname parameter
    list_kontrak_unik = sorted(df_opname["Kontrak Clean"].unique().tolist())
    selected_kontrak = st.selectbox("📂 Pilih Nomor Kontrak:", ["-- SEMUA KONTRAK --"] + list_kontrak_unik, key="rekap_kontrak_select")

    if selected_kontrak != "-- SEMUA KONTRAK --":
        df_filtered_kontrak = df_opname[df_opname["Kontrak Clean"] == selected_kontrak]
    else:
        df_filtered_kontrak = df_opname

    list_po_unik = sorted(df_filtered_kontrak["PO Clean"].unique().tolist())
    selected_po = st.selectbox("🔍 Pilih Nomor PO:", ["-- SEMUA PO DALAM KONTRAK INI --"] + list_po_unik, key="rekap_po_select")

    if selected_po != "-- SEMUA PO DALAM KONTRAK INI --":
        df_filtered = df_filtered_kontrak[df_filtered_kontrak["PO Clean"] == selected_po]
    else:
        df_filtered = df_filtered_kontrak

    st.markdown("---")

    is_all_kontrak = (selected_kontrak == "-- SEMUA KONTRAK --")
    is_all_po = (selected_po == "-- SEMUA PO DALAM KONTRAK INI --")

    # KONDISI 1: Jika SEMUA KONTRAK & SEMUA PO dipilih -> Tabel Rekap Global
    if is_all_kontrak and is_all_po:
        st.markdown("### 📑 Tabel Rekapitulasi Global Berdasarkan Database Opname Parameter")
        st.info("ℹ️ Menampilkan rangkuman total plafon (berdasarkan seluruh baris item di database opname parameter) dan penyerapan aktual.")

        global_summary_rows = []
        tot_plafon_global, tot_serap_global, tot_sisa_global = 0.0, 0.0, 0.0

        for po_item in df_opname["PO Clean"].unique():
            df_op_sub = df_opname[df_opname["PO Clean"] == po_item]
            k_info = df_op_sub["Kontrak Clean"].iloc[0]
            
            lingkup_info = "-"
            if not df_tx.empty:
                df_tx_sub = df_tx[df_tx["PO Clean"] == po_item]
                if not df_tx_sub.empty and "Deskripsi PO" in df_tx_sub.columns:
                    lingkup_info = df_tx_sub["Deskripsi PO"].iloc[0]

            p_po = 0.0
            for _, op_row in df_op_sub.iterrows():
                try:
                    v_po = float(op_row.get("Volume PO", 0))
                    u_prc = float(op_row.get("Unit Price", 0))
                    p_po += v_po * u_prc
                except:
                    pass

            t_serap = 0.0
            if not df_tx.empty:
                df_tx_sub = df_tx[df_tx["PO Clean"] == po_item]
                if not df_tx_sub.empty and "Total Harga" in df_tx_sub.columns:
                    t_serap = pd.to_numeric(df_tx_sub["Total Harga"], errors='coerce').sum()

            sisa_val = p_po - t_serap
            rasio = (t_serap / p_po * 100) if p_po > 0 else 0.0

            tot_plafon_global += p_po
            tot_serap_global += t_serap
            tot_sisa_global += sisa_val

            global_summary_rows.append({
                "Nomor Kontrak": k_info,
                "Nomor PO": po_item,
                "Lingkup Pekerjaan": lingkup_info,
                "Total Plafon PO (IDR)": p_po,
                "Total Terserap (IDR)": t_serap,
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

    # KONDISI 2 & 3: Kontrak atau PO tertentu dipilih
    target_po_list = df_filtered["PO Clean"].unique().tolist()
    if not target_po_list:
        st.info("ℹ️ Tidak ada data PO yang sesuai dengan filter yang dipilih.")
        return

    st.markdown(f"### 📋 Tabel Kontrol Anggaran & Penyerapan PO (Berdasarkan Database Opname Parameter)")

    for po_item in target_po_list:
        df_op_sub = df_opname[df_opname["PO Clean"] == po_item]
        kontrak_info = df_op_sub["Kontrak Clean"].iloc[0]
        
        lingkup_info = "-"
        if not df_tx.empty:
            df_tx_sub = df_tx[df_tx["PO Clean"] == po_item]
            if not df_tx_sub.empty and "Deskripsi PO" in df_tx_sub.columns:
                lingkup_info = df_tx_sub["Deskripsi PO"].iloc[0]

        st.markdown(f"#### 📁 Nomor PO: `{po_item}` | Kontrak: `{kontrak_info}`")
        if lingkup_info and lingkup_info != "-":
            st.caption(f"Lingkup Pekerjaan: {lingkup_info}")

        df_tx_sub = pd.DataFrame()
        if not df_tx.empty:
            df_tx_sub = df_tx[df_tx["PO Clean"] == po_item]

        tabel_rows = []
        tot_vol_po, tot_val_po = 0.0, 0.0
        tot_vol_serap, tot_val_serap = 0.0, 0.0
        tot_vol_sisa, tot_val_sisa = 0.0, 0.0

        for idx, row in df_op_sub.reset_index(drop=True).iterrows():
            item_idx = row.get("Item Index", idx + 1)
            vol_po = float(row.get("Volume PO", 0))
            unit_price = float(row.get("Unit Price", 0))
            total_price_po = vol_po * unit_price

            vol_aktual = 0.0
            val_aktual = 0.0
            if not df_tx_sub.empty:
                if idx < len(df_tx_sub):
                    vol_aktual = float(df_tx_sub.iloc[idx].get("Qty", 0))
                    val_aktual = float(df_tx_sub.iloc[idx].get("Total Harga", 0))

            vol_sisa = vol_po - vol_aktual
            total_price_sisa = total_price_po - val_aktual

            tot_vol_po += vol_po
            tot_val_po += total_price_po
            tot_vol_serap += vol_aktual
            tot_val_serap += val_aktual
            tot_vol_sisa += vol_sisa
            tot_val_sisa += total_price_sisa

            pi_asal = row.get("PI Clean", "-")
            tabel_rows.append({
                "No.": item_idx,
                "Item Description": f"Item Parameter #{item_idx} (PI: {pi_asal})",
                "UOM": "Day / Unit",
                "Volume PO": f"{vol_po:,.2f}",
                "Unit Price (IDR)": f"{unit_price:,.2f}",
                "Total Price PO (IDR)": f"{total_price_po:,.2f}",
                "Volume Akumulasi": f"{vol_aktual:,.2f}",
                "Total Akumulasi (IDR)": f"{val_aktual:,.2f}",
                "Sisa Volume": f"{vol_sisa:,.2f}",
                "Sisa Nilai (IDR)": f"{total_price_sisa:,.2f}"
            })

        df_laporan = pd.DataFrame(tabel_rows)
        st.dataframe(df_laporan, use_container_width=True)

        st.markdown(f"#### 📌 Ringkasan Rekapitulasi Total untuk PO: `{po_item}`")
        
        pct_serap = (tot_val_serap / tot_val_po * 100) if tot_val_po > 0 else 0.0
        pct_sisa = (tot_val_sisa / tot_val_po * 100) if tot_val_po > 0 else 0.0

        st.markdown("""
            <style>
            div[data-testid="metric-container"] label { font-size: 13px !important; color: #475569 !important; }
            div[data-testid="metric-container"] div[data-testid="stMetricValue"] { font-size: 20px !important; font-weight: 700 !important; color: #0f172a !important; }
            </style>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Plafon PO", f"Rp {tot_val_po:,.2f}")
        with c2:
            st.metric("Total Terserap", f"Rp {tot_val_serap:,.2f}", delta=f"{pct_serap:.1f}% dari PO")
        with c3:
            st.metric("Sisa Anggaran", f"Rp {tot_val_sisa:,.2f}", delta=f"-{pct_sisa:.1f}% sisa", delta_color="inverse")
        with c4:
            st.metric("Rasio Penyerapan", f"{pct_serap:.2f}%")

        st.markdown(f"##### 📉 Grafik Proporsi Penyerapan Anggaran PO `{po_item}`")
        
        chart_data = pd.DataFrame({
            'Kategori': ['Sisa Anggaran', 'Sudah Terserap'],
            'Nilai': [max(0.0, tot_val_sisa), max(0.0, tot_val_serap)]
        }).set_index('Kategori')

        st.altair_chart(
            alt.Chart(chart_data.reset_index()).mark_arc(innerRadius=50).encode(
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

        st.markdown("---")