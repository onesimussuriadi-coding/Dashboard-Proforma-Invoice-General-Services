import streamlit as st
import pandas as pd

def tampilkan_akumulasi_riwayat_transaksi(tx_data, bersih_angka_func, sort_pi_key_func, simpan_data_transaksi_func, muat_data_transaksi_func):
    
    # Identifikasi role user aktif untuk pengamanan Read-Only Mutlak Direksi
    current_role_user = str(st.session_state.get("current_role", "")).strip().lower()
    is_management = current_role_user in ["management", "direksi"]

    # Handling Aksi Hapus PI via Query Params / URL Action
    query_params = st.query_params
    if "delete_tx_pi" in query_params:
        if is_management:
            st.error("❌ Akses Ditolak! Akun Direksi berada dalam mode Read-Only dan tidak diizinkan menghapus data transaksi.")
            st.query_params.clear()
            st.rerun()
        else:
            try:
                del_pi_target = str(query_params["delete_tx_pi"]).strip()
                all_tx = muat_data_transaksi_func()
                
                # Filter buang data PI yang dihapus
                updated_tx = [t for t in all_tx if bersih_angka_func(t.get("PI No.")) != del_pi_target]
                
                if simpan_data_transaksi_func(updated_tx):
                    st.success(f"🗑️ Berhasil menghapus seluruh riwayat transaksi untuk PI [{del_pi_target}] secara permanen!")
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Gagal menghapus transaksi: {e}")

    st.markdown("""
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 18px 22px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.06); margin-bottom: 20px; border-left: 5px solid #10b981;">
            <h3 style="margin:0; color:#ffffff; font-size:18px; font-weight:700;">📊 Akumulasi Riwayat Transaksi & Breakdown Nilai Tagihan</h3>
            <p style="margin:4px 0 0 0; color:#94a3b8; font-size:13px;">Daftar terkelompok per Proforma Invoice lengkap dengan rincian breakdown item pekerjaan.</p>
        </div>
    """, unsafe_allow_html=True)

    if not tx_data:
        st.info("ℹ️ Belum ada riwayat transaksi tersimpan di database.")
        return

    df_tx = pd.DataFrame(tx_data)

    # Membersihkan kolom kunci
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

    # Sort berdasarkan PI secara profesional (Descending)
    grouped["sort_key"] = grouped["PI No Clean"].apply(sort_pi_key_func)
    grouped = grouped.sort_values(by=["Nomor Kontrak Clean", "sort_key"], ascending=[True, False]).drop(columns=["sort_key"])

    # --- METRICS RINGKASAN EKSEKUTIF ---
    total_kumulatif = grouped["Total_Tagihan"].sum()
    total_kontrak_unik = grouped["Nomor Kontrak Clean"].nunique()
    total_pi_unik = grouped["PI No Clean"].nunique()

    formatted_grand_total = f"Rp {total_kumulatif:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1:
        st.metric("💰 Total Akumulasi Tagihan", formatted_grand_total)
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

    st.markdown(f"**Menampilkan `{len(df_filtered_grp)}` paket Proforma Invoice (Klik panel di bawah untuk melihat breakdown rincian pekerjaan):**")
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

    # --- DAFTAR DENGAN BREAKDOWN EXPANDER PER PI ---
    for idx, row in df_filtered_grp.reset_index(drop=True).iterrows():
        pi_target = row["PI No Clean"]
        kontrak_target = row["Nomor Kontrak Clean"]
        val_total = row["Total_Tagihan"]
        fmt_total = f"Rp {val_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        # Zebra pastel row background
        card_bg = "#ffffff" if idx % 2 == 0 else "#f8fafc"

        # Judul Expander Berisi Ringkasan Padat
        header_title = f"#{idx+1} | PI: {pi_target} ({row['Tanggal_PI']}) | Kontrak: {kontrak_target} | PO: {row['Nomor_PO']} | WAN: {row['Nomor_WAN']} | [{row['Jumlah_Item']} Item] ➔ Total Tagihan: {fmt_total}"

        with st.expander(header_title):
            # Ambil item detail khusus PI ini
            df_pi_detail = df_tx[(df_tx["Nomor Kontrak Clean"] == kontrak_target) & (df_tx["PI No Clean"] == pi_target)].copy()
            
            col_info_left, col_info_right = st.columns([3, 1])
            with col_info_left:
                st.markdown(f"📋 **Detail Breakdown Rincian Pekerjaan PI No:** `{pi_target}`")
            
            # Tombol Hapus PI HANYA MUNCUL JIKA BUKAN MANAGEMENT
            if not is_management:
                with col_info_right:
                    st.markdown(f"""
                        <div style="text-align: right;">
                            <a href="?delete_tx_pi={pi_target}" target="_self" style="text-decoration: none;" onclick="return confirm('Apakah Anda yakin ingin menghapus seluruh riwayat transaksi PI {pi_target} ini?');">
                                <button style="background-color: #ef4444; color: white; border: none; padding: 4px 10px; border-radius: 5px; font-size: 12px; font-weight: bold; cursor: pointer;">🗑️ Hapus PI Ini</button>
                            </a>
                        </div>
                    """, unsafe_allow_html=True)

            # Tabel Breakdown Item Pekerjaan ala Data Grid Zebra
            table_breakdown_rows = ""
            for i_idx, item in df_pi_detail.reset_index(drop=True).iterrows():
                try:
                    q_val = float(item.get("Qty", 1.0) or 1.0)
                    hs_val = float(item.get("Harga Satuan", 0.0) or 0.0)
                    tot_val = float(item.get("Total Harga", 0.0) or 0.0)
                except:
                    q_val, hs_val, tot_val = 1.0, 0.0, 0.0

                fmt_hs = f"Rp {hs_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                fmt_tot = f"Rp {tot_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                sub_bg = "#ffffff" if i_idx % 2 == 0 else "#f8fafc"

                table_breakdown_rows += f"""
                <tr style="background-color: {sub_bg}; border-bottom: 1px solid #e2e8f0;">
                    <td style="border: 1px solid #cbd5e1; padding: 6px 8px; text-align: center; font-size: 12px; font-weight: bold;">{i_idx+1}</td>
                    <td style="border: 1px solid #cbd5e1; padding: 6px 8px; font-size: 12px; font-weight: 600; color: #0f172a;">{item.get('Kategori', '-')}</td>
                    <td style="border: 1px solid #cbd5e1; padding: 6px 8px; font-size: 12px; color: #334155;">{item.get('Deskripsi Pekerjaan', '-')}</td>
                    <td style="border: 1px solid #cbd5e1; padding: 6px 8px; text-align: center; font-size: 12px;">{q_val}</td>
                    <td style="border: 1px solid #cbd5e1; padding: 6px 8px; text-align: center; font-size: 12px;">{item.get('Unit', '-')}</td>
                    <td style="border: 1px solid #cbd5e1; padding: 6px 8px; text-align: right; font-size: 12px;">{fmt_hs}</td>
                    <td style="border: 1px solid #cbd5e1; padding: 6px 8px; text-align: right; font-size: 12px; font-weight: bold; color: #059669;">{fmt_tot}</td>
                </tr>
                """

            html_breakdown = f"""
            <div style="overflow-x: auto; border: 1px solid #cbd5e1; border-radius: 6px; margin-top: 8px;">
                <table style="width: 100%; border-collapse: collapse; font-family: sans-serif;">
                    <thead>
                        <tr style="background-color: #1e293b; color: #ffffff; font-size: 12px;">
                            <th style="border: 1px solid #cbd5e1; padding: 8px; text-align: center; width: 35px;">No</th>
                            <th style="border: 1px solid #cbd5e1; padding: 8px; text-align: left; width: 140px;">Kategori</th>
                            <th style="border: 1px solid #cbd5e1; padding: 8px; text-align: left;">Uraian Pekerjaan / Spesifikasi</th>
                            <th style="border: 1px solid #cbd5e1; padding: 8px; text-align: center; width: 50px;">Qty</th>
                            <th style="border: 1px solid #cbd5e1; padding: 8px; text-align: center; width: 60px;">Unit</th>
                            <th style="border: 1px solid #cbd5e1; padding: 8px; text-align: right; width: 110px;">Harga Satuan</th>
                            <th style="border: 1px solid #cbd5e1; padding: 8px; text-align: right; width: 120px;">Subtotal Nilai</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_breakdown_rows}
                    </tbody>
                </table>
            </div>
            """
            st.components.v1.html(html_breakdown, height=max(120, len(df_pi_detail) * 38 + 50), scrolling=True)