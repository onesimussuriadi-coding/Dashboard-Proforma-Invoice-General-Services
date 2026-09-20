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
            <p style="margin-bottom:0; font-size:12px; color:#4b5563;">Analisis berjenjang (Kontrak &rarr; PO), tabel kontrol anggaran, rekapitulasi total, dan grafik diagram lingkaran persentase penyerapan.</p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Muat data transaksi (Modul 2)
    transaksi_list = muat_data_transaksi_func()
    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi tersimpan untuk dianalisis penyerapan PO-nya.")
        return

    df_tx = pd.DataFrame(transaksi_list)
    if df_tx.empty or "Nomor PO" not in df_tx.columns or "Nomor Kontrak" not in df_tx.columns:
        st.warning("⚠️ Kolom Nomor PO atau Nomor Kontrak tidak ditemukan pada data transaksi.")
        return

    df_tx["PO Clean"] = df_tx["Nomor PO"].astype(str).str.strip()
    df_tx["Kontrak Clean"] = df_tx["Nomor Kontrak"].astype(str).str.strip()
    
    df_tx = df_tx[
        (df_tx["PO Clean"] != "") & (df_tx["PO Clean"] != "-") & (df_tx["PO Clean"] != "nan") &
        (df_tx["Kontrak Clean"] != "") & (df_tx["Kontrak Clean"] != "-") & (df_tx["Kontrak Clean"] != "nan")
    ]

    if df_tx.empty:
        st.warning("⚠️ Tidak ada data transaksi dengan Nomor Kontrak dan PO yang valid.")
        return

    # 2. Muat data parameter opname untuk mengambil Volume PO & Unit Price awal
    path_opname_excel = os.path.join("database_penyimpanan_aman", "database_opname_parameter.xlsx")
    df_opname = pd.DataFrame()
    if os.path.exists(path_opname_excel):
        try:
            df_opname = pd.read_excel(path_opname_excel)
        except:
            pass

    st.markdown("---")
    
    # 3. Filter Berjenjang: Pilih Kontrak dulu, baru Pilih PO
    list_kontrak_unik = sorted(df_tx["Kontrak Clean"].unique().tolist())
    selected_kontrak = st.selectbox("📂 Pilih Nomor Kontrak:", ["-- SEMUA KONTRAK --"] + list_kontrak_unik, key="rekap_kontrak_select")

    if selected_kontrak != "-- SEMUA KONTRAK --":
        df_filtered_kontrak = df_tx[df_tx["Kontrak Clean"] == selected_kontrak]
    else:
        df_filtered_kontrak = df_tx

    list_po_unik = sorted(df_filtered_kontrak["PO Clean"].unique().tolist())
    selected_po = st.selectbox("🔍 Pilih Nomor PO:", ["-- SEMUA PO DALAM KONTRAK INI --"] + list_po_unik, key="rekap_po_select")

    if selected_po != "-- SEMUA PO DALAM KONTRAK INI --":
        df_filtered = df_filtered_kontrak[df_filtered_kontrak["PO Clean"] == selected_po]
    else:
        df_filtered = df_filtered_kontrak

    st.markdown("---")
    st.markdown("### 📋 Tabel Kontrol Anggaran & Penyerapan PO (Base vs Realisasi)")

    target_po_list = df_filtered["PO Clean"].unique().tolist()
    if not target_po_list:
        st.info("ℹ️ Tidak ada data PO yang sesuai dengan filter yang dipilih.")
        return

    for po_item in target_po_list:
        df_sub_po = df_filtered[df_filtered["PO Clean"] == po_item]
        
        kontrak_info = df_sub_po.get("Kontrak Clean", pd.Series([""])).iloc[0]
        lingkup_info = df_sub_po.get("Deskripsi PO", pd.Series([""])).iloc[0]

        st.markdown(f"#### 📁 Nomor PO: `{po_item}` | Kontrak: `{kontrak_info}`")
        if lingkup_info and lingkup_info != "-":
            st.caption(f"Lingkup Pekerjaan: {lingkup_info}")

        df_opname_sub = pd.DataFrame()
        if not df_opname.empty and "doc_key" in df_opname.columns:
            df_opname_sub = df_opname[df_opname["doc_key"].astype(str).str.contains(str(po_item))]

        grouped_aktual = df_sub_po.groupby(["Kategori", "Deskripsi Pekerjaan", "Unit"]).agg(
            Volume_Aktual=('Qty', 'sum'),
            Total_Aktual=('Total Harga', 'sum'),
            Harga_Satuan=('Harga Satuan', 'mean')
        ).reset_index()

        tabel_rows = []
        tot_vol_po, tot_val_po = 0.0, 0.0
        tot_vol_serap, tot_val_serap = 0.0, 0.0
        tot_vol_sisa, tot_val_sisa = 0.0, 0.0

        for idx, row in grouped_aktual.iterrows():
            kat = row["Kategori"]
            uraian = row["Deskripsi Pekerjaan"]
            unit = row["Unit"]
            vol_aktual = row["Volume_Aktual"]
            val_aktual = row["Total_Aktual"]
            unit_price = row["Harga_Satuan"]

            vol_po = vol_aktual * 2
            if not df_opname_sub.empty and idx < len(df_opname_sub):
                try:
                    vol_po = float(df_opname_sub.iloc[idx].get("Volume PO", vol_aktual))
                    unit_price = float(df_opname_sub.iloc[idx].get("Unit Price", unit_price))
                except:
                    pass

            total_price_po = vol_po * unit_price
            vol_sisa = vol_po - vol_aktual
            total_price_sisa = total_price_po - val_aktual

            tot_vol_po += vol_po
            tot_val_po += total_price_po
            tot_vol_serap += vol_aktual
            tot_val_serap += val_aktual
            tot_vol_sisa += vol_sisa
            tot_val_sisa += total_price_sisa

            tabel_rows.append({
                "No.": idx + 1,
                "Item Description": f"[{kat}] {uraian}",
                "UOM": unit,
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

        # --- KOTAK REKAPITULASI TOTAL PER PO ---
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

        # --- DIAGRAM LINGKARAN (PIE CHART) ---
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