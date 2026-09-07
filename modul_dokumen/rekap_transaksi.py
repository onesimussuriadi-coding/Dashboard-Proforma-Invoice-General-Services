import streamlit as st
import pandas as pd
from datetime import datetime

def tampilkan_rekap_transaksi(transaksi_list):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📊 Master Rekapitulasi & Analisis Agregat Transaksi</h3>
            <p style="margin: 4px 0 0 0; font-size: 12px; color: #475569;">
                Rekapitulasi komprehensif multi-tahun berdasarkan kategori, uraian pekerjaan, serta rentang periode (tahun & bulan).
            </p>
        </div>
    """, unsafe_allow_html=True)

    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi rincian pekerjaan yang tersedia untuk direkap.")
        return

    # Konversi data transaksi ke DataFrame Pandas
    data_rows = []
    total_len = len(transaksi_list)
    for idx, t in enumerate(transaksi_list, start=1):
        kategori = str(t.get('Kategori', '-'))
        deskripsi = str(t.get('Deskripsi Pekerjaan', '-'))
        qty = float(t.get('Qty', 0.0))
        harga_satuan = float(t.get('Harga Satuan', 0.0))
        percent = float(t.get('Percent', 100.0))
        unit = str(t.get('Unit', '-'))
        tgl_mulai_str = str(t.get('Tanggal Mulai', ''))
        tgl_selesai_str = str(t.get('Tanggal Selesai', ''))
        keterangan = str(t.get('Keterangan', '-'))
        pi_no = str(t.get('PI No.', '-'))
        nomor_kontrak = str(t.get('Nomor Kontrak', '-'))
        nomor_po = str(t.get('Nomor PO', t.get('No PO', '-')))
        nomor_wan = str(t.get('Nomor WAN / SA', t.get('Nomor WAN', t.get('WAN', '-'))))

        # Parsing Tahun dan Bulan dari Tanggal Mulai
        tahun_val = "-"
        bulan_val = "-"
        bulan_idx = 0
        try:
            dt_parsed = pd.to_datetime(tgl_mulai_str, errors='coerce')
            if pd.notnull(dt_parsed):
                tahun_val = str(dt_parsed.year)
                bulan_idx = dt_parsed.month
                bulan_val = dt_parsed.strftime('%B')
        except:
            pass

        # Perhitungan Total Harga Bersih
        kat_lower = kategori.lower()
        if "provisional" in kat_lower or "professional" in kat_lower:
            total_harga = (qty * harga_satuan) * 1.15 * (percent / 100.0)
        elif "estimated" in kat_lower or "estimasi" in kat_lower:
            total_harga = (qty * harga_satuan * 0.9) * (percent / 100.0)
        else:
            total_harga = (qty * harga_satuan) * (percent / 100.0)

        data_rows.append({
            "Original_No": idx,
            "Nomor Kontrak": nomor_kontrak,
            "Nomor PO": nomor_po,
            "Nomor WAN / SA": nomor_wan,
            "PI No.": pi_no,
            "Kategori": kategori,
            "Uraian Pekerjaan": deskripsi,
            "Volume (Qty)": qty,
            "Satuan": unit,
            "Harga Satuan (IDR)": harga_satuan,
            "Persentase (%)": percent,
            "Total Harga (IDR)": total_harga,
            "Tanggal Mulai": tgl_mulai_str,
            "Tanggal Selesai": tgl_selesai_str,
            "Tahun": tahun_val,
            "Bulan": bulan_val,
            "Bulan_Idx": bulan_idx,
            "Keterangan": keterangan
        })

    df_rekap = pd.DataFrame(data_rows)

    # --- FILTER PENCARIAN & RENTANG PERIODE MULTIYEAR ---
    st.markdown("#### 🔍 Filter & Rentang Periode Multiyear")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        unique_contracts = ["Semua Kontrak"] + sorted(list(df_rekap["Nomor Kontrak"].unique()))
        selected_contract_filter = st.selectbox("📌 Filter Nomor Kontrak:", unique_contracts)
    
    with col_f2:
        unique_years = ["Semua Tahun"] + sorted(list([y for y in df_rekap["Tahun"].unique() if y != "-"]), reverse=True)
        selected_year_filter = st.selectbox("📅 Filter Tahun Proyek:", unique_years)

    with col_f3:
        unique_pi = ["Semua PI"] + sorted(list(df_rekap["PI No."].unique()))
        selected_pi_filter = st.selectbox("📄 Filter PI No.:", unique_pi)

    list_bulan_nama = [
        "Semua Bulan", "January", "February", "March", "April", "May", "June", 
        "July", "August", "September", "October", "November", "December"
    ]
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        selected_bulan_mulai = st.selectbox("Dari Bulan:", list_bulan_nama, index=0)
    with col_b2:
        selected_bulan_selesai = st.selectbox("Sampai Bulan:", list_bulan_nama, index=0)

    # Terapkan Filter
    df_filtered = df_rekap.copy()
    if selected_contract_filter != "Semua Kontrak":
        df_filtered = df_filtered[df_filtered["Nomor Kontrak"] == selected_contract_filter]
    if selected_year_filter != "Semua Tahun":
        df_filtered = df_filtered[df_filtered["Tahun"] == selected_year_filter]
    if selected_pi_filter != "Semua PI":
        df_filtered = df_filtered[df_filtered["PI No."] == selected_pi_filter]
    
    if selected_bulan_mulai != "Semua Bulan" and selected_bulan_selesai != "Semua Bulan":
        idx_mulai = list_bulan_nama.index(selected_bulan_mulai)
        idx_selesai = list_bulan_nama.index(selected_bulan_selesai)
        if idx_mulai <= idx_selesai:
            df_filtered = df_filtered[(df_filtered["Bulan_Idx"] >= idx_mulai) & (df_filtered["Bulan_Idx"] <= idx_selesai)]

    st.markdown(f"**Menampilkan {len(df_filtered)} baris data transaksi terfilter dari total {len(df_rekap)} data keseluruhan.**")
    st.markdown("---")

    # --- BAGIAN 1: RINGKASAN AGREGAT ---
    st.markdown("#### 📋 Ringkasan Agregat (Total Berdasarkan Kategori & Uraian Pekerjaan)")
    if not df_filtered.empty:
        df_agregat = df_filtered.groupby(["Kategori", "Uraian Pekerjaan", "Satuan"]).agg({
            "Volume (Qty)": "sum",
            "Total Harga (IDR)": "sum",
            "Original_No": "count"
        }).reset_index().rename(columns={"Original_No": "Frekuensi Tagihan"})

        df_agregat_display = df_agregat.copy()
        df_agregat_display["Volume (Qty)"] = df_agregat_display["Volume (Qty)"].map("{:,.2f}".format)
        df_agregat_display["Total Harga (IDR)"] = df_agregat_display["Total Harga (IDR)"].map("{:,.2f}".format)

        st.dataframe(df_agregat_display, use_container_width=True, hide_index=True)

        st.markdown("#### 📈 Visualisasi Grafik Rekapitulasi")
        tab_grafik1, tab_grafik2 = st.tabs(["📊 Grafik Total Biaya per Kategori", "🍩 Tren Biaya Pekerjaan"])
        with tab_grafik1:
            df_chart_kat = df_filtered.groupby("Kategori")["Total Harga (IDR)"].sum().reset_index().set_index("Kategori")
            st.bar_chart(df_chart_kat, use_container_width=True)
        with tab_grafik2:
            df_chart_uraian = df_filtered.groupby("Uraian Pekerjaan")["Total Harga (IDR)"].sum().reset_index().set_index("Uraian Pekerjaan")
            st.area_chart(df_chart_uraian, use_container_width=True)
    else:
        st.info("ℹ️ Tidak ada data yang sesuai dengan kriteria filter.")

    st.markdown("---")

    # --- BAGIAN 2: DETAIL TRANSAKSI (DISUSUN DARI NOMOR BESAR KE KECIL / TERBARU DI ATAS) ---
    st.markdown("#### 📑 Detail Seluruh Baris Transaksi (Urutan Terbaru di Atas)")
    
    df_display = df_filtered.copy()
    if "Bulan_Idx" in df_display.columns:
        df_display = df_display.drop(columns=["Bulan_Idx"])

    # Urutkan dari nomor besar ke kecil (Descending berdasarkan Original_No)
    df_display = df_display.sort_values(by="Original_No", ascending=False).reset_index(drop=True)
    # Ganti nomor urut tampilan menjadi descending (total_len, total_len-1, dst.)
    total_filtered_rows = len(df_display)
    df_display["No"] = [total_filtered_rows - i for i in range(total_filtered_rows)]
    
    # Pindahkan kolom 'No' ke paling depan
    cols = ["No"] + [col for col in df_display.columns if col not in ["No", "Original_No"]]
    df_display = df_display[cols]

    # Format angka
    df_display["Volume (Qty)"] = df_display["Volume (Qty)"].map("{:,.2f}".format)
    df_display["Harga Satuan (IDR)"] = df_display["Harga Satuan (IDR)"].map("{:,.2f}".format)
    df_display["Persentase (%)"] = df_display["Persentase (%)"].map("{:,.2f}%".format)
    df_display["Total Harga (IDR)"] = df_display["Total Harga (IDR)"].map("{:,.2f}".format)

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    grand_total_filtered = df_filtered["Total Harga (IDR)"].sum()
    st.markdown(f"""
        <div style="background-color: #f8fafc; padding: 12px; border: 1px solid #cbd5e1; border-radius: 6px; margin-top: 10px; font-weight: bold; font-size: 14px; text-align: right;">
            GRAND TOTAL KESELURUHAN (TERFILTER) : Rp {grand_total_filtered:,.2f}
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Master Rekap Transaksi (CSV)",
            data=csv_data,
            file_name=f"Master_Rekap_Multiyear_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_dl2:
        st.info("💡 Tabel detail di atas telah diurutkan dengan baris transaksi terbaru berada di posisi paling atas.")