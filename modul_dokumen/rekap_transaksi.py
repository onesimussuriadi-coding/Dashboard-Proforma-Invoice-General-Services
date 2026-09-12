import streamlit as st
import pandas as pd
import os
import altair as alt
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

    # --- MANAJEMEN DATABASE PLATFON / TOTAL NILAI KONTRAK ---
    DIR_DATABASE = "database_penyimpanan_aman"
    EXCEL_PLAFON = os.path.join(DIR_DATABASE, "database_plafon_kontrak.xlsx")

    def muat_database_plafon():
        if os.path.exists(EXCEL_PLAFON):
            try:
                df = pd.read_excel(EXCEL_PLAFON)
                if df is not None and not df.empty:
                    return dict(zip(df["Nomor Kontrak"].astype(str), df["Total Nilai Kontrak"].astype(float)))
            except:
                pass
        return {}

    def simpan_database_plafon(data_dict):
        df_baru = pd.DataFrame(list(data_dict.items()), columns=["Nomor Kontrak", "Total Nilai Kontrak"])
        os.makedirs(DIR_DATABASE, exist_ok=True)
        df_baru.to_excel(EXCEL_PLAFON, index=False)
        st.session_state["db_plafon"] = data_dict

    if "db_plafon" not in st.session_state:
        st.session_state["db_plafon"] = muat_database_plafon()

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

    # --- PANEL PENGATURAN PLAFON KONTRAK ---
    st.markdown("---")
    st.markdown("#### ⚙️ Pengaturan Total Nilai Plafon (Kontrak)")

    db_plafon = st.session_state["db_plafon"]

    with st.expander("📝 Input / Update Total Nilai Plafon Masing-Masing Kontrak", expanded=False):
        with st.form("form_atur_plafon"):
            st.markdown("Masukkan atau perbarui Total Nilai Plafon untuk setiap Nomor Kontrak:")
            form_plafon_inputs = {}
            for k_num in [c for c in unique_contracts if c != "Semua Kontrak"]:
                val_existing = float(db_plafon.get(k_num, 0.0))
                form_plafon_inputs[k_num] = st.number_input(f"Total Nilai Kontrak [{k_num}] (Rp)", min_value=0.0, value=val_existing, step=1000000.0, format="%.2f")
            
            submit_plafon = st.form_submit_button("💾 Simpan Nilai Plafon Kontrak")
            if submit_plafon:
                for k_num, v_val in form_plafon_inputs.items():
                    db_plafon[k_num] = v_val
                simpan_database_plafon(db_plafon)
                st.success("✅ Nilai Plafon Kontrak berhasil disimpan secara permanen!")
                st.rerun()

    # --- TABEL RINGKASAN & STATISTIK PENYERAPAN PER KONTRAK (DENGAN BARIS GRAND TOTAL) ---
    st.markdown("#### 📋 Tabel Ringkasan Statistik & Penyerapan Kontrak")
    
    kontrak_tabel_list = [selected_contract_filter] if selected_contract_filter != "Semua Kontrak" else [c for c in unique_contracts if c != "Semua Kontrak"]
    
    summary_rows = []
    for k_num in kontrak_tabel_list:
        df_k = df_rekap[df_rekap["Nomor Kontrak"] == k_num]
        
        plafon_val = float(db_plafon.get(k_num, 0.0))
        penyerapan_val = float(df_k["Total Harga (IDR)"].sum())
        
        df_po_k = df_k[df_k["Nomor PO"].notnull() & (df_k["Nomor PO"] != "-") & (df_k["Nomor PO"] != "")]
        po_val = float(df_po_k["Total Harga (IDR)"].sum())
        
        df_wan_k = df_k[df_k["Nomor WAN / SA"].notnull() & (df_k["Nomor WAN / SA"] != "-") & (df_k["Nomor WAN / SA"] != "")]
        wan_val = float(df_wan_k["Total Harga (IDR)"].sum())
        
        sisa_val = plafon_val - penyerapan_val

        # Perhitungan Persentase Presisi
        pct_penyerapan = (penyerapan_val / plafon_val * 100.0) if plafon_val > 0 else 0.0
        pct_sisa = (sisa_val / plafon_val * 100.0) if plafon_val > 0 else 0.0
        
        summary_rows.append({
            "Nomor Kontrak": k_num,
            "Total Nilai Kontrak (Rp)": plafon_val,
            "Total Penyerapan (Rp)": penyerapan_val,
            "% Penyerapan": pct_penyerapan,
            "Terbit PO (Rp)": po_val,
            "Terbit WAN / SA (Rp)": wan_val,
            "Sisa Penyerapan (Rp)": sisa_val,
            "% Sisa Anggaran": pct_sisa
        })

    df_summary = pd.DataFrame(summary_rows)

    if not df_summary.empty:
        # Hitung Grand Total untuk baris terakhir
        gt_plafon = df_summary["Total Nilai Kontrak (Rp)"].sum()
        gt_penyerapan = df_summary["Total Penyerapan (Rp)"].sum()
        gt_po = df_summary["Terbit PO (Rp)"].sum()
        gt_wan = df_summary["Terbit WAN / SA (Rp)"].sum()
        gt_sisa = gt_plafon - gt_penyerapan
        
        gt_pct_penyerapan = (gt_penyerapan / gt_plafon * 100.0) if gt_plafon > 0 else 0.0
        gt_pct_sisa = (gt_sisa / gt_plafon * 100.0) if gt_plafon > 0 else 0.0

        df_summary_display = df_summary.copy()
        
        # Format angka menjadi rupiah koma dan persentase untuk baris data reguler
        for col in ["Total Nilai Kontrak (Rp)", "Total Penyerapan (Rp)", "Terbit PO (Rp)", "Terbit WAN / SA (Rp)", "Sisa Penyerapan (Rp)"]:
            df_summary_display[col] = df_summary_display[col].map("Rp {:,.2f}".format)
        
        df_summary_display["% Penyerapan"] = df_summary_display["% Penyerapan"].map("{:,.2f}%".format)
        df_summary_display["% Sisa Anggaran"] = df_summary_display["% Sisa Anggaran"].map("{:,.2f}%".format)

        # Tambahkan baris Grand Total ke DataFrame Tampilan
        grand_total_row = pd.DataFrame([{
            "Nomor Kontrak": "GRAND TOTAL",
            "Total Nilai Kontrak (Rp)": f"Rp {gt_plafon:,.2f}",
            "Total Penyerapan (Rp)": f"Rp {gt_penyerapan:,.2f}",
            "% Penyerapan": f"{gt_pct_penyerapan:,.2f}%",
            "Terbit PO (Rp)": f"Rp {gt_po:,.2f}",
            "Terbit WAN / SA (Rp)": f"Rp {gt_wan:,.2f}",
            "Sisa Penyerapan (Rp)": f"Rp {gt_sisa:,.2f}",
            "% Sisa Anggaran": f"{gt_pct_sisa:,.2f}%"
        }])

        df_summary_display = pd.concat([df_summary_display, grand_total_row], ignore_index=True)
        st.dataframe(df_summary_display, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ Tidak ada data ringkasan kontrak yang tersedia.")

    # --- GRAFIK PERBANDINGAN KONTRAK VS PENYERAPAN ---
    if not df_summary.empty:
        st.markdown("#### 📊 Grafik Perbandingan Kontrak vs Penyerapan")
        
        df_melted = df_summary.melt(
            id_vars=["Nomor Kontrak"],
            value_vars=["Total Nilai Kontrak (Rp)", "Total Penyerapan (Rp)"],
            var_name="Kategori Nilai",
            value_name="Jumlah (Rp)"
        )

        chart_grouped = alt.Chart(df_melted).mark_bar().encode(
            x=alt.X('Nomor Kontrak:N', title='Nomor Kontrak', sort=None),
            xOffset=alt.XOffset('Kategori Nilai:N', sort=None),
            y=alt.Y('Jumlah (Rp):Q', title='Nilai dalam Rupiah (Rp)'),
            color=alt.Color(
                'Kategori Nilai:N',
                scale=alt.Scale(
                    domain=["Total Nilai Kontrak (Rp)", "Total Penyerapan (Rp)"],
                    range=["#1e3a8a", "#facc15"]  # Biru Tua (#1e3a8a) untuk Kontrak & Kuning Menyala (#facc15) untuk Penyerapan
                ),
                legend=alt.Legend(title="Keterangan")
            ),
            tooltip=['Nomor Kontrak', 'Kategori Nilai', alt.Tooltip('Jumlah (Rp):Q', format=',.2f')]
        ).properties(
            height=420
        )

        st.altair_chart(chart_grouped, use_container_width=True)

    st.markdown("---")

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
        tab_grafik1, tab_grafik2, tab_grafik3 = st.tabs(["📊 Grafik Volume per Kategori", "📊 Grafik Total Biaya per Kategori", "🍩 Tren Biaya Pekerjaan"])
        with tab_grafik1:
            df_chart_kat_vol = df_filtered.groupby("Kategori")["Volume (Qty)"].sum().reset_index().set_index("Kategori")
            st.bar_chart(df_chart_kat_vol, use_container_width=True)
        with tab_grafik2:
            df_chart_kat = df_filtered.groupby("Kategori")["Total Harga (IDR)"].sum().reset_index().set_index("Kategori")
            st.bar_chart(df_chart_kat, use_container_width=True)
        with tab_grafik3:
            df_chart_uraian = df_filtered.groupby("Uraian Pekerjaan")["Total Harga (IDR)"].sum().reset_index().set_index("Uraian Pekerjaan")
            st.area_chart(df_chart_uraian, use_container_width=True)
    else:
        st.info("ℹ️ Tidak ada data yang sesuai dengan kriteria filter.")

    st.markdown("---")

    # --- BAGIAN 2: DETAIL TRANSAKSI ---
    st.markdown("#### 📑 Detail Seluruh Baris Transaksi (Urutan Terbaru di Atas)")
    
    df_display = df_filtered.copy()
    if "Bulan_Idx" in df_display.columns:
        df_display = df_display.drop(columns=["Bulan_Idx"])

    df_display = df_display.sort_values(by="Original_No", ascending=False).reset_index(drop=True)
    total_filtered_rows = len(df_display)
    df_display["No"] = [total_filtered_rows - i for i in range(total_filtered_rows)]
    
    cols = ["No"] + [col for col in df_display.columns if col not in ["No", "Original_No"]]
    df_display = df_display[cols]

    df_display["Volume (Qty)"] = df_display["Volume (Qty)"].map("{:,.2f}".format)
    df_display["Harga Satuan (IDR)"] = df_display["Harga Satuan (IDR)"].map("{:,.2f}".format)
    df_display["Persentase (%)"] = df_display["Persentase (%)"].map("{:,.2f}%".format)
    df_display["Total Harga (IDR)"] = df_display["Total Harga (IDR)"].map("{:,.2f}".format)

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    grand_total_filtered = df_filtered["Total Harga (IDR)"].sum()
    st.markdown(f"""
        <div style="background-color: #f8fafc; tab-size: 4; padding: 12px; border: 1px solid #cbd5e1; border-radius: 6px; margin-top: 10px; font-weight: bold; font-size: 14px; text-align: right;">
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