import streamlit as st
import pandas as pd
import os
from datetime import datetime, date, timedelta

def tampilkan_pemantauan_pembayaran():
    st.markdown("#### 📊 Modul Pemantauan Proses Pembayaran & Aging Invoice")
    
    DIR_DATABASE = "database_penyimpanan_aman"
    
    def muat_invoice_resmi():
        kemungkinan_file = [
            os.path.join(DIR_DATABASE, "database_billing_tax.xlsx"),
            os.path.join(DIR_DATABASE, "database_invoice_resmi.xlsx"),
            os.path.join(DIR_DATABASE, "database_invoice.xlsx")
        ]
        for file_path in kemungkinan_file:
            if os.path.exists(file_path):
                try:
                    df = pd.read_excel(file_path)
                    if df is not None and not df.empty:
                        return df.to_dict(orient="records")
                except:
                    pass
        return []

    EXCEL_PAYMENT_STATUS = os.path.join(DIR_DATABASE, "database_status_pembayaran.xlsx")

    def muat_status_pembayaran():
        if os.path.exists(EXCEL_PAYMENT_STATUS):
            try:
                df = pd.read_excel(EXCEL_PAYMENT_STATUS)
                if df is not None and not df.empty:
                    return df.to_dict(orient="records")
            except:
                pass
        return []

    def simpan_status_pembayaran(data_list):
        df_baru = pd.DataFrame(data_list)
        df_baru.to_excel(EXCEL_PAYMENT_STATUS, index=False)

    invoice_list = muat_invoice_resmi()
    payment_records = muat_status_pembayaran()

    if not invoice_list:
        st.warning("⚠️ Belum ada Data Invoice Resmi yang tersimpan. Pastikan Anda sudah menyimpan data invoice di menu Billing & Tax.")
        return

    def ambil_tanggal_invoice(inv_data_obj):
        for k, v in inv_data_obj.items():
            if any(kata in str(k).lower() for kata in ["tgl", "tanggal", "date"]) and not any(kata in str(k).lower() for kata in ["penyerahan", "tempo", "lunas"]):
                if pd.notnull(v) and str(v).strip() != "":
                    return str(v)[:10]
        return str(date.today())

    def ambil_grand_total_invoice(inv_data_obj):
        for k, v in inv_data_obj.items():
            if any(kata in str(k).lower() for kata in ["grand", "total", "jumlah", "tagihan", "nilai", "amount"]):
                try:
                    val_str = str(v).replace("Rp", "").replace(".", "").replace(",", ".").strip()
                    num_val = float(val_str)
                    if num_val > 0:
                        return num_val
                except:
                    pass
        return 0.0

    sample_inv = invoice_list[0]
    inv_key = "Nomor Invoice Resmi" if "Nomor Invoice Resmi" in sample_inv else ("Nomor Invoice" if "Nomor Invoice" in sample_inv else list(sample_inv.keys())[0])

    list_inv_no = [str(inv.get(inv_key, "")) for inv in invoice_list if inv.get(inv_key)]
    
    selected_inv = st.selectbox("Pilih Nomor Invoice untuk Dipantau:", list_inv_no)

    inv_data = next((inv for inv in invoice_list if str(inv.get(inv_key)) == str(selected_inv)), {})
    existing_pay = next((p for p in payment_records if str(p.get("Nomor Invoice")) == str(selected_inv)), {})

    tgl_invoice_bawaan = ambil_tanggal_invoice(inv_data)
    grand_total_otomatis = ambil_grand_total_invoice(inv_data)

    # --- BAGIAN 1: KARTU REKAPITULASI KEUANGAN UTAMA & STATUS PEMBAYARAN ---
    if payment_records:
        hari_ini = date.today()
        
        # Variabel Akumulasi Keuangan Utama
        total_seluruh_tagihan = 0.0
        total_sudah_dibayar = 0.0

        # Variabel Status Dokumen
        jml_aman = 0; val_aman = 0.0
        jml_warning = 0; val_warning = 0.0
        jml_overdue = 0; val_overdue = 0.0
        jml_lunas = 0; val_lunas = 0.0

        for p in payment_records:
            try:
                g_total = float(p.get("Grand Total", 0.0))
            except:
                g_total = 0.0

            total_seluruh_tagihan += g_total
            status_byr = p.get("Status Pembayaran", "Belum Dibayar")

            if status_byr == "Lunas":
                total_sudah_dibayar += g_total
                jml_lunas += 1
                val_lunas += g_total
                continue
            elif status_byr == "Sebagian (DP / Termin)":
                # Asumsi jika sebagian, bisa disesuaikan atau dihitung penuh jika lunas
                total_sudah_dibayar += (g_total * 0.5) # Contoh asumsi parsial atau sesuai catatan

            try:
                dt_jt = datetime.strptime(str(p.get("Tanggal Jatuh Tempo"))[:10], "%Y-%m-%d").date()
                selisih = (hari_ini - dt_jt).days
                if selisih > 0:
                    jml_overdue += 1
                    val_overdue += g_total
                elif selisih >= -7:
                    jml_warning += 1
                    val_warning += g_total
                else:
                    jml_aman += 1
                    val_aman += g_total
            except:
                jml_aman += 1
                val_aman += g_total

        sisa_belum_terbayar = total_seluruh_tagihan - total_sudah_dibayar

        def fmt_rp(val):
            return f"Rp {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        # TAMPILAN KARTU UTAMA: RINGKASAN SALDO KEUANGAN Keseluruhan
        st.markdown("---")
        st.markdown("##### 💰 Rekapitulasi Saldo Keuangan & Tagihan Keseluruhan")
        c_fin1, c_fin2, c_fin3 = st.columns(3)
        with c_fin1:
            st.markdown(f"""
                <div style="background-color: #1e293b; color: white; padding: 18px; border-radius: 8px; text-align: center; border-left: 5px solid #38bdf8;">
                    <p style="margin: 0; font-size: 13px; color: #94a3b8; font-weight: 600;">TOTAL SELURUH TAGIHAN</p>
                    <h3 style="margin: 6px 0 0 0; font-size: 20px; color: #ffffff;">{fmt_rp(total_seluruh_tagihan)}</h3>
                </div>
            """, unsafe_allow_html=True)
        with c_fin2:
            st.markdown(f"""
                <div style="background-color: #1e293b; color: white; padding: 18px; border-radius: 8px; text-align: center; border-left: 5px solid #10b981;">
                    <p style="margin: 0; font-size: 13px; color: #94a3b8; font-weight: 600;">TOTAL SUDAH DIBAYARKAN</p>
                    <h3 style="margin: 6px 0 0 0; font-size: 20px; color: #34d399;">{fmt_rp(total_sudah_dibayar)}</h3>
                </div>
            """, unsafe_allow_html=True)
        with c_fin3:
            st.markdown(f"""
                <div style="background-color: #1e293b; color: white; padding: 18px; border-radius: 8px; text-align: center; border-left: 5px solid #f59e0b;">
                    <p style="margin: 0; font-size: 13px; color: #94a3b8; font-weight: 600;">SISA SALDO BELUM TERBAYAR</p>
                    <h3 style="margin: 6px 0 0 0; font-size: 20px; color: #fbbf24;">{fmt_rp(sisa_belum_terbayar)}</h3>
                </div>
            """, unsafe_allow_html=True)

        # TAMPILAN KARTU KEDUA: INDIKATOR STATUS PERINGATAN (WARNA-WARNI)
        st.markdown("---")
        st.markdown("##### 🚨 Indikator Peringatan & Aging Status Pembayaran")
        c_m1, c_m2, c_m3, c_m4 = st.columns(4)
        with c_m1:
            st.markdown(f"""
                <div style="background-color: #3b82f6; color: white; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 8px;">
                    <h3 style="margin: 0; font-size: 18px;">{jml_aman} Dokumen</h3>
                    <p style="margin: 4px 0 0 0; font-size: 13px; font-weight: 700;">{fmt_rp(val_aman)}</p>
                    <p style="margin: 4px 0 0 0; font-size: 11px;">🔵 Aman / Terkendali</p>
                </div>
            """, unsafe_allow_html=True)
        with c_m2:
            st.markdown(f"""
                <div style="background-color: #eab308; color: white; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 8px;">
                    <h3 style="margin: 0; font-size: 18px;">{jml_warning} Dokumen</h3>
                    <p style="margin: 4px 0 0 0; font-size: 13px; font-weight: 700;">{fmt_rp(val_warning)}</p>
                    <p style="margin: 4px 0 0 0; font-size: 11px;">🟡 Mendekati Due Date (≤7 Hr)</p>
                </div>
            """, unsafe_allow_html=True)
        with c_m3:
            st.markdown(f"""
                <div style="background-color: #ef4444; color: white; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 8px;">
                    <h3 style="margin: 0; font-size: 18px;">{jml_overdue} Dokumen</h3>
                    <p style="margin: 4px 0 0 0; font-size: 13px; font-weight: 700;">{fmt_rp(val_overdue)}</p>
                    <p style="margin: 4px 0 0 0; font-size: 11px;">🔴 OVERDUE (Terlambat)</p>
                </div>
            """, unsafe_allow_html=True)
        with c_m4:
            st.markdown(f"""
                <div style="background-color: #10b981; color: white; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 8px;">
                    <h3 style="margin: 0; font-size: 18px;">{jml_lunas} Dokumen</h3>
                    <p style="margin: 4px 0 0 0; font-size: 13px; font-weight: 700;">{fmt_rp(val_lunas)}</p>
                    <p style="margin: 4px 0 0 0; font-size: 11px;">🟢 Lunas (Selesai)</p>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("##### 🔍 Perbarui Tanggal & Status Pemantauan Pembayaran")

    formatted_grand_total = f"Rp {grand_total_otomatis:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.markdown(f"📄 **Informasi Invoice Terpilih:**  \n- Tanggal Invoice: `{tgl_invoice_bawaan}`  \n- Nilai Nominal Invoice (Grand Total): **{formatted_grand_total}**")

    with st.form("form_update_pembayaran"):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            default_tgl_serah = datetime.today().date()
            if existing_pay.get("Tanggal Penyerahan"):
                try:
                    default_tgl_serah = datetime.strptime(str(existing_pay.get("Tanggal Penyerahan"))[:10], "%Y-%m-%d").date()
                except:
                    pass
            tgl_penyerahan = st.date_input("Tanggal Invoice Diserahkan ke Klien:", value=default_tgl_serah)

            default_top = int(existing_pay.get("TOP Hari", 30))
            top_hari = st.number_input("Term of Payment (TOP dalam Hari):", min_value=0, value=default_top, step=5)

        with col_p2:
            status_opsi = ["Belum Dibayar", "Sebagian (DP / Termin)", "Lunas"]
            def_status = existing_pay.get("Status Pembayaran", "Belum Dibayar")
            idx_st = status_opsi.index(def_status) if def_status in status_opsi else 0
            status_pembayaran = st.selectbox("Status Pembayaran:", status_opsi, index=idx_st)

            default_tgl_lunas = datetime.today().date()
            if existing_pay.get("Tanggal Pelunasan"):
                try:
                    default_tgl_lunas = datetime.strptime(str(existing_pay.get("Tanggal Pelunasan"))[:10], "%Y-%m-%d").date()
                except:
                    pass
            tgl_pelunasan = st.date_input("Tanggal Pelunasan Aktual (Jika sudah dibayar):", value=default_tgl_lunas)

        catatan_bayar = st.text_area("Catatan / Keterangan Pembayaran:", value=str(existing_pay.get("Catatan", "")))

        if st.form_submit_button("💾 Simpan Pemantauan Pembayaran", type="primary"):
            tgl_jatuh_tempo = tgl_penyerahan + timedelta(days=int(top_hari))

            data_update = {
                "Nomor Kontrak": inv_data.get("Kontrak No.", inv_data.get("Nomor Kontrak", "-")),
                "Nomor Invoice": selected_inv,
                "Customer": inv_data.get("Customer", "-"),
                "Tanggal Invoice": tgl_invoice_bawaan,
                "Tanggal Penyerahan": tgl_penyerahan.strftime("%Y-%m-%d"),
                "TOP Hari": top_hari,
                "Tanggal Jatuh Tempo": tgl_jatuh_tempo.strftime("%Y-%m-%d"),
                "Grand Total": grand_total_otomatis,
                "Status Pembayaran": status_pembayaran,
                "Tanggal Pelunasan": tgl_pelunasan.strftime("%Y-%m-%d") if status_pembayaran == "Lunas" else "-",
                "Catatan": catatan_bayar,
                "Update Terakhir": datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            }

            clean_records = [p for p in payment_records if str(p.get("Nomor Invoice")) != str(selected_inv)]
            clean_records.append(data_update)
            simpan_status_pembayaran(clean_records)
            st.success(f"🎉 Berhasil menyimpan data pemantauan untuk Invoice [{selected_inv}] dengan nilai {formatted_grand_total} (Jatuh tempo: Tanggal Penyerahan + {top_hari} hari)!")

    st.markdown("---")
    st.markdown("#### 📋 Ringkasan & Laporan Aging Invoice Keseluruhan")

    if payment_records:
        df_report = pd.DataFrame(payment_records)
        hari_ini = date.today()
        
        def hitung_aging(row):
            if row["Status Pembayaran"] == "Lunas":
                return "🟢 Lunas (Selesai)"
            try:
                dt_jt = datetime.strptime(str(row["Tanggal Jatuh Tempo"])[:10], "%Y-%m-%d").date()
                selisih = (hari_ini - dt_jt).days
                if selisih > 0:
                    return f"🔴 OVERDUE ({selisih} Hari)"
                elif selisih >= -7:
                    return f"🟡 Warning (Kurang {-selisih} Hari)"
                else:
                    return f"🔵 Aman (Kurang {-selisih} Hari)"
            except:
                return "Belum Dipetakan"

        df_report["Keterangan Aging"] = df_report.apply(hitung_aging, axis=1)
        
        if "Grand Total" in df_report.columns:
            df_report["Grand Total Format"] = df_report["Grand Total"].apply(
                lambda x: f"Rp {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notnull(x) else "Rp 0,00"
            )

        st.dataframe(df_report, use_container_width=True)
    else:
        st.info("ℹ️ Belum ada data pemantauan pembayaran yang tersimpan. Silakan simpan pemantauan dari form di atas.")