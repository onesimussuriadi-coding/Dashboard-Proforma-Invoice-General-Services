import streamlit as st
import pandas as pd
import os

def tampilkan_rekap_penyerapan_po(
    muat_data_transaksi_func,
    bersih_angka_func
):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📊 Rekapitulasi & Kontrol Penyerapan Mutasi Purchase Order (PO)</h3>
            <p style="margin-bottom:0; font-size:12px; color:#4b5563;">Kontrol anggaran dan penyerapan per item (Kategori & Uraian Pekerjaan) berdasarkan Nomor PO.</p>
        </div>
    """, unsafe_allow_html=True, help=None)

    # 1. Muat data transaksi dari Modul 2
    transaksi_list = muat_data_transaksi_func()
    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi tersimpan untuk dianalisis penyerapan PO-nya.")
        return

    df_tx = pd.DataFrame(transaksi_list)
    if df_tx.empty or "Nomor PO" not in df_tx.columns:
        st.warning("⚠️ Kolom Nomor PO tidak ditemukan pada data transaksi.")
        return

    # Bersihkan spasi & format Nomor PO
    df_tx["PO Clean"] = df_tx["Nomor PO"].astype(str).str.strip()
    df_tx = df_tx[(df_tx["PO Clean"] != "") & (df_tx["PO Clean"] != "-") & (df_tx["PO Clean"] != "nan")]

    if df_tx.empty:
        st.warning("⚠️ Tidak ada Nomor PO yang valid pada data transaksi.")
        return

    # Ambil daftar unik Nomor PO
    list_po_unik = sorted(df_tx["PO Clean"].unique().tolist())
    selected_po = st.selectbox("🔍 Pilih / Filter Berdasarkan Nomor PO:", ["-- SEMUA PO --"] + list_po_unik, key="rekap_po_select")

    if selected_po != "-- SEMUA PO --":
        df_filtered = df_tx[df_tx["PO Clean"] == selected_po]
    else:
        df_filtered = df_tx

    st.markdown("---")
    st.markdown("### 📋 Rincian Penyerapan Anggaran per Item Pekerjaan (Kategori & Uraian)")

    # Iterasi per Nomor PO untuk menampilkan tabel detail per item
    for po_item in df_filtered["PO Clean"].unique():
        df_sub_po = df_filtered[df_filtered["PO Clean"] == po_item]
        
        kontrak_info = df_sub_po.get("Nomor Kontrak", pd.Series([""])).iloc[0]
        lingkup_info = df_sub_po.get("Deskripsi PO", pd.Series([""])).iloc[0]

        st.markdown(f"#### 📁 Nomor PO: `{po_item}` (Kontrak: `{kontrak_info}`)")
        if lingkup_info and lingkup_info != "-":
            st.caption(f"Lingkup Pekerjaan: {lingkup_info}")

        # Grouping berdasarkan Kategori & Uraian Pekerjaan (Deskripsi Pekerjaan) untuk melihat akumulasi penyerapan
        # Asumsi: Plafon / Volume PO diambil dari total yang diinput atau dihitung dari akumulasi transaksi, 
        # atau kita kelompokkan per kombinasi Kategori & Uraian Pekerjaan.
        grouped_item = df_sub_po.groupby(["Kategori", "Deskripsi Pekerjaan", "Unit"]).agg(
            Qty_Terserap=('Qty', 'sum'),
            Total_Nilai_Terserap=('Total Harga', 'sum'),
            Harga_Satuan_Rata=('Harga Satuan', 'mean'),
            Jumlah_PI=('PI No.', lambda x: len(x.unique()))
        ).reset_index()

        tabel_detail_rows = []
        for idx, row in grouped_item.iterrows():
            kat = row["Kategori"]
            uraian = row["Deskripsi Pekerjaan"]
            unit = row["Unit"]
            qty_serap = row["Qty_Terserap"]
            harga_satuan = row["Harga_Satuan_Rata"]
            nilai_serap = row["Total_Nilai_Terserap"]

            # Catatan: Jika data kuota awal PO tersimpan di modul opname atau referensi, bisa disandingkan di sini.
            # Sementara ditampilkan secara jelas berdasarkan realisasi akumulasi penyerapan dari Modul 2 per item.
            tabel_detail_rows.append({
                "No.": idx + 1,
                "Kategori Pekerjaan": kat,
                "Uraian Pekerjaan / Spesifikasi": uraian,
                "Unit": unit,
                "Harga Satuan (IDR)": f"Rp {harga_satuan:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "Qty Terserap": f"{qty_serap:,.2f}",
                "Total Nilai Terserap (IDR)": f"Rp {nilai_serap:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "Jml PI": row["Jumlah_PI"]
            })

        df_view = pd.DataFrame(tabel_detail_rows)
        st.dataframe(df_view, use_container_width=True)
        st.markdown("---")