# modul_input/modul_2_akumulasi.py
import streamlit as st
import pandas as pd

def tampilkan_akumulasi_riwayat_transaksi(tx_data, bersih_angka_func, sort_pi_key_func):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📊 Akumulasi Riwayat Transaksi & Nilai Tagihan Invoice</h3>
        </div>
    """, unsafe_allow_html=True)

    if not tx_data:
        st.info("ℹ️ Belum ada riwayat transaksi tersimpan di database.")
        return

    df_tx = pd.DataFrame(tx_data)

    # Memastikan kolom angka dan string bersih
    df_tx["Nomor Kontrak Clean"] = df_tx["Nomor Kontrak"].apply(lambda x: bersih_angka_func(x))
    df_tx["PI No Clean"] = df_tx["PI No."].apply(lambda x: bersih_angka_func(x))
    df_tx["Nomor PO Clean"] = df_tx["Nomor PO"].apply(lambda x: bersih_angka_func(x) if bersih_angka_func(x) else "-")
    df_tx["Nomor WAN Clean"] = df_tx["Nomor WAN / SA"].apply(lambda x: bersih_angka_func(x) if bersih_angka_func(x) else "-")
    
    if "Total Harga" in df_tx.columns:
        df_tx["Total Harga Num"] = pd.to_numeric(df_tx["Total Harga"], errors='coerce').fillna(0.0)
    else:
        df_tx["Total Harga Num"] = 0.0

    # Grouping Data per (Nomor Kontrak + Nomor PI)
    grouped = df_tx.groupby(["Nomor Kontrak Clean", "PI No Clean"]).agg(
        Nomor_PO=("Nomor PO Clean", "first"),
        Nomor_WAN=("Nomor WAN Clean", "first"),
        Tanggal_PI=("Tanggal PI", "first"),
        Total_Tagihan=("Total Harga Num", "sum"),
        Jumlah_Item=("Kategori", "count")
    ).reset_index()

    # Sort berdasarkan PI secara profesional
    grouped["sort_key"] = grouped["PI No Clean"].apply(sort_pi_key_func)
    grouped = grouped.sort_values(by=["Nomor Kontrak Clean", "sort_key"], ascending=[True, False]).drop(columns=["sort_key"])

    # --- METRICS RINGKASAN ---
    total_kumulatif = grouped["Total_Tagihan"].sum()
    total_kontrak_unik = grouped["Nomor Kontrak Clean"].nunique()
    total_pi_unik = grouped["PI No Clean"].nunique()

    formatted_grand_total = f"Rp {total_kumulatif:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1:
        st.metric("💰 Total akumulasi Tagihan", formatted_grand_total)
    with c_m2:
        st.metric("📜 Jumlah Kontrak Terdaftar", f"{total_kontrak_unik} Kontrak")
    with c_m3:
        st.metric("🧾 Total Dokumen PI Issued", f"{total_pi_unik} PI")

    st.markdown("---")

    # --- DROPDOWN FILTER KONTRAK & PI ---
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        list_kontrak_opt = ["-- Semua Nomor Kontrak --"] + sorted(list(grouped["Nomor Kontrak Clean"].unique()))
        sel_kontrak = st.selectbox("📌 Filter Nomor Kontrak:", list_kontrak_opt, key="akml_filter_kontrak")

    df_filtered_grp = grouped.copy()
    if sel_kontrak != "-- Semua Nomor Kontrak --":
        df_filtered_grp = df_filtered_grp[df_filtered_grp["Nomor Kontrak Clean"] == sel_kontrak]

    with col_f2:
        list_pi_opt = ["-- Semua Nomor PI --"] + sorted(list(df_filtered_grp["PI No Clean"].unique()), key=sort_pi_key_func, reverse=True)
        sel_pi = st.selectbox("🧾 Filter Nomor PI:", list_pi_opt, key="akml_filter_pi")

    if sel_pi != "-- Semua Nomor PI --":
        df_filtered_grp = df_filtered_grp[df_filtered_grp["PI No Clean"] == sel_pi]

    st.markdown(f"**Menampilkan {len(df_filtered_grp)} data paket Proforma Invoice:**")
    st.markdown("---")

    # --- TABEL EKSEKUTIF RAPI (HTML COMPONENT) ---
    table_rows = ""
    for idx, row in df_filtered_grp.reset_index(drop=True).iterrows():
        val_total = row['Total_Tagihan']
        fmt_total = f"Rp {val_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        table_rows += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 10px; text-align: center; font-weight: bold; color: #475569; font-size: 13px;">#{idx+1}</td>
            <td style="padding: 10px; font-weight: bold; color: #0f172a; font-size: 13px;">{row['Nomor Kontrak Clean']}</td>
            <td style="padding: 10px; color: #0284c7; font-weight: 700; font-size: 13px;">{row['PI No Clean']}<br><span style="font-size: 11px; color: #64748b; font-weight: normal;">({row['Tanggal_PI']})</span></td>
            <td style="padding: 10px; color: #334155; font-size: 13px;">{row['Nomor_PO']}</td>
            <td style="padding: 10px; color: #334155; font-size: 13px;">{row['Nomor_WAN']}</td>
            <td style="padding: 10px; text-align: center; color: #475569; font-size: 13px;">{row['Jumlah_Item']} Item</td>
            <td style="padding: 10px; text-align: right; color: #059669; font-weight: 700; font-size: 14px;">{fmt_total}</td>
        </tr>
        """

    table_html = f"""
    <div style="overflow-x: auto; border: 1px solid #cbd5e1; border-radius: 8px; background-color: #ffffff; box-shadow: 0 2px 5px rgba(0,0,0,0.03);">
        <table style="width: 100%; border-collapse: collapse; text-align: left; font-family: sans-serif;">
            <thead>
                <tr style="background-color: #1e293b; color: #ffffff; font-size: 13px;">
                    <th style="padding: 11px; text-align: center; width: 45px;">No</th>
                    <th style="padding: 11px;">Nomor Kontrak</th>
                    <th style="padding: 11px;">Nomor PI & Tanggal</th>
                    <th style="padding: 11px;">Nomor PO</th>
                    <th style="padding: 11px;">Nomor WAN / SA</th>
                    <th style="padding: 11px; text-align: center;">Rincian</th>
                    <th style="padding: 11px; text-align: right;">Total Nilai Invoice</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>
    """
    st.components.v1.html(table_html, height=420, scrolling=True)

    # --- RINCIAN PEKERJAAN DETAIL (EXPANDER) ---
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🔍 Klik di sini untuk melihat Rincian Pekerjaan Item Per Item (Detail Raw Data)"):
        df_raw_filtered = df_tx.copy()
        if sel_kontrak != "-- Semua Nomor Kontrak --":
            df_raw_filtered = df_raw_filtered[df_raw_filtered["Nomor Kontrak Clean"] == sel_kontrak]
        if sel_pi != "-- Semua Nomor PI --":
            df_raw_filtered = df_raw_filtered[df_raw_filtered["PI No Clean"] == sel_pi]

        cols_to_show = ["Nomor Kontrak", "PI No.", "Nomor PO", "Kategori", "Deskripsi Pekerjaan", "Qty", "Unit", "Harga Satuan", "Total Harga"]
        existing_cols = [c for c in cols_to_show if c in df_raw_filtered.columns]
        st.dataframe(df_raw_filtered[existing_cols], use_container_width=True)