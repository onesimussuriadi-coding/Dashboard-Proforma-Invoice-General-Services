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
            <p style="margin-bottom:0; font-size:12px; color:#4b5563;">Modul mandiri untuk memantau akumulasi penyerapan (usage), sisa anggaran, dan deviasi kuota PO lintas periode tagihan/PI.</p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Muat data transaksi dari Modul 2 / database tersimpan
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
    
    # PERBAIKAN: Menggunakan tanda kurung di setiap kondisi boolean agar operator & berjalan benar di Pandas
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

    # 2. Ambil data acuan plafon awal dari data opname / transaksi tersimpan
    st.markdown("---")
    st.markdown("### 📈 Ringkasan Akumulasi Penyerapan per Nomor PO")

    # Grouping berdasarkan Nomor PO untuk melihat Total Qty dan Total Nilai Terserap
    summary_po = df_filtered.groupby("PO Clean").agg(
        Jumlah_PI=('PI No.', lambda x: len(x.unique())),
        Total_Qty_Terserap=('Qty', 'sum'),
        Total_Nilai_Terserap=('Total Harga', 'sum'),
        Nomor_Kontrak=('Nomor Kontrak', 'first'),
        Lingkup_Pekerjaan=('Deskripsi PO', 'first')
    ).reset_index()

    # Tampilkan tabel rekap utama
    summary_table_display = []
    for _, row in summary_po.iterrows():
        po_num = row["PO Clean"]
        kontrak = row["Nomor_Kontrak"]
        lingkup = row["Lingkup_Pekerjaan"]
        jml_pi = row["Jumlah_PI"]
        qty_serap = row["Total_Qty_Terserap"]
        nilai_serap = row["Total_Nilai_Terserap"]

        summary_table_display.append({
            "Nomor PO": po_num,
            "Nomor Kontrak": kontrak,
            "Lingkup Pekerjaan": lingkup,
            "Jumlah PI / Tagihan": jml_pi,
            "Akumulasi Qty Terserap": qty_serap,
            "Total Nilai Terserap (IDR)": f"Rp {nilai_serap:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        })

    df_summary_view = pd.DataFrame(summary_table_display)
    st.dataframe(df_summary_view, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📋 Rincian Mutasi Transaksi Berdasarkan PO Terpilih")

    # Tampilkan detail baris transaksi di bawahnya
    for po_item in summary_po["PO Clean"].tolist():
        with st.expander(f"📁 Detail Mutasi untuk Nomor PO: {po_item}", expanded=(selected_po != "-- SEMUA PO --")):
            df_sub = df_filtered[df_filtered["PO Clean"] == po_item]
            
            detail_rows = []
            for idx, r in df_sub.iterrows():
                detail_rows.append({
                    "PI No.": r.get("PI No.", "-"),
                    "Tanggal PI": r.get("Tanggal PI", "-"),
                    "Kategori": r.get("Kategori", "-"),
                    "Uraian Pekerjaan": r.get("Deskripsi Pekerjaan", "-"),
                    "Qty": r.get("Qty", 0),
                    "Unit": r.get("Unit", "-"),
                    "Harga Satuan": f"Rp {float(r.get('Harga Satuan', 0)):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    "Total Harga": f"Rp {float(r.get('Total Harga', 0)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                })
            
            st.dataframe(pd.DataFrame(detail_rows), use_container_width=True)