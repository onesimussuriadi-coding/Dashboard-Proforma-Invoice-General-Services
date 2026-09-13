import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime, date, timedelta

def tampilkan_pemantauan_pembayaran():
    st.markdown("#### 📊 Modul Analisis Keuangan, Pemantauan Pembayaran & Aging Invoice")
    
    DIR_DATABASE = "database_penyimpanan_aman"
    
    def parse_harga_presisi(val):
        if val is None:
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        
        s = str(val).strip()
        if not s or s.lower() == 'nan':
            return 0.0
        
        s = s.replace("Rp", "").replace(" ", "")
        
        if ',' in s and '.' in s:
            if s.rfind(',') > s.rfind('.'):
                s = s.replace('.', '').replace(',', '.')
            else:
                s = s.replace(',', '')
        elif ',' in s:
            if s.count(',') == 1 and len(s.split(',')[1]) <= 2:
                s = s.replace(',', '.')
            else:
                s = s.replace(',', '')
        
        cleaned_digits = "".join(re.findall(r'[0-9\.]+', s))
        try:
            return float(cleaned_digits)
        except:
            return 0.0

    # --- 1. MODUL 3: MEMBACA DARI FILE TERSIMPAN MODUL 3 ---
    def muat_invoice_tersimpan_modul3():
        spesifik_file = [
            os.path.join(DIR_DATABASE, "database_billing_tax.xlsx"),
            os.path.join(DIR_DATABASE, "database_invoice_resmi.xlsx"),
            os.path.join(DIR_DATABASE, "database_invoice.xlsx")
        ]
        for file_path in spesifik_file:
            if os.path.exists(file_path):
                try:
                    df = pd.read_excel(file_path)
                    if df is not None and not df.empty:
                        return df.to_dict(orient="records")
                except:
                    pass
        return []

    invoice_list = muat_invoice_tersimpan_modul3()

    def cari_nama_kolom_invoice(sample_obj):
        if not sample_obj:
            return "Nomor Invoice"
        for k in sample_obj.keys():
            k_low = str(k).lower()
            if "resmi" in k_low or ("invoice" in k_low and "tanggal" not in k_low and "tgl" not in k_low):
                return k
        return list(sample_obj.keys())[0]

    sample_inv = invoice_list[0] if invoice_list else {}
    inv_key = cari_nama_kolom_invoice(sample_inv)

    def ambil_grand_total_invoice_master(inv_no):
        for inv in invoice_list:
            found_no = str(inv.get(inv_key, inv.get("Nomor Invoice Resmi", inv.get("Nomor Invoice", "")))).strip()
            if found_no == str(inv_no).strip():
                for k, v in inv.items():
                    k_low = str(k).lower()
                    if any(kata in k_low for kata in ["netto", "grand", "total", "jumlah", "tagihan", "nilai", "amount"]):
                        val_parsed = parse_harga_presisi(v)
                        if val_parsed > 0:
                            return val_parsed
        return 0.0

    EXCEL_PAYMENT_STATUS = os.path.join(DIR_DATABASE, "database_status_pembayaran.xlsx")

    def muat_status_pembayaran():
        if os.path.exists(EXCEL_PAYMENT_STATUS):
            try:
                df = pd.read_excel(EXCEL_PAYMENT_STATUS)
                if df is not None and not df.empty:
                    records = df.to_dict(orient="records")
                    for r in records:
                        inv_no = r.get("Nomor Invoice", "")
                        master_gt = ambil_grand_total_invoice_master(inv_no)
                        if master_gt > 0:
                            r["Grand Total"] = master_gt
                        else:
                            r["Grand Total"] = parse_harga_presisi(r.get("Grand Total", 0.0))
                    return records
            except:
                pass
        return []

    def simpan_status_pembayaran(data_list):
        df_baru = pd.DataFrame(data_list)
        df_baru.to_excel(EXCEL_PAYMENT_STATUS, index=False)
        st.session_state["db_payment"] = data_list

    if "db_payment" not in st.session_state:
        st.session_state["db_payment"] = muat_status_pembayaran()

    payment_records = st.session_state["db_payment"]

    if not invoice_list and not payment_records:
        st.warning("⚠️ Belum ada Data Invoice Tersimpan di Modul 3.")
        return

    def ambil_tanggal_invoice(inv_data_obj):
        for k, v in inv_data_obj.items():
            if any(kata in str(k).lower() for kata in ["tgl", "tanggal", "date"]) and not any(kata in str(k).lower() for kata in ["penyerahan", "tempo", "lunas"]):
                if pd.notnull(v) and str(v).strip() != "":
                    return str(v)[:10]
        return str(date.today())

    # --- 2. AMBIL TOTAL KONTRAK (PLAFON) DARI MODUL 2 SECARA PRESISI ---
    def muat_total_kontrak_modul2():
        plafon_files = [
            os.path.join(DIR_DATABASE, "database_plafon_kontrak.xlsx"),
            os.path.join(DIR_DATABASE, "database_kontrak.xlsx"),
            os.path.join(DIR_DATABASE, "database_master_kontrak.xlsx")
        ]
        kontrak_master_map = {}
        for file_path in plafon_files:
            if os.path.exists(file_path):
                try:
                    df = pd.read_excel(file_path)
                    if df is not None and not df.empty:
                        for _, row in df.iterrows():
                            c_num = ""
                            c_val = 0.0
                            for col in df.columns:
                                val_col = str(row[col]).strip()
                                col_l = str(col).lower().replace(" ", "").replace(".", "")
                                # Deteksi nomor kontrak
                                if "kontrak" in col_l or "nomor" in col_l:
                                    if val_col and val_col != '-' and val_col.lower() != 'nan' and len(val_col) >= 8:
                                        c_num = val_col
                                # Deteksi nilai plafon / kontrak
                                if any(k in col_l for k in ["plafon", "nilaikontrak", "totalkontrak", "pagu", "total"]):
                                    parsed_val = parse_harga_presisi(row[col])
                                    if parsed_val > c_val:
                                        c_val = parsed_val
                            if c_num and c_val > 0:
                                kontrak_master_map[c_num] = c_val
                except:
                    pass
        return kontrak_master_map

    master_kontrak_plafon = muat_total_kontrak_modul2()

    # Fallback: ambil nomor kontrak langsung dari invoice list jika file Modul 2 belum terindeks
    kontrak_from_invoice = [str(inv.get("Kontrak No.", inv.get("Nomor Kontrak", "-"))).strip() for inv in invoice_list if inv.get("Kontrak No.") or inv.get("Nomor Kontrak")]
    kontrak_from_payment = [str(p.get("Nomor Kontrak", "-")).strip() for p in payment_records if p.get("Nomor Kontrak")]
    
    all_contracts = sorted(list(dict.fromkeys([k for k in (kontrak_from_invoice + kontrak_from_payment) if k and k != '-' and k.lower() != 'nan'])))

    st.markdown("---")
    st.markdown("##### 🔍 Filter Tampilan & Rekapitulasi Berdasarkan Kontrak")
    opsi_filter_kontrak = ["-- Semua Nomor Kontrak (ALL) --"] + all_contracts
    filter_kontrak_pilih = st.selectbox("Pilih Nomor Kontrak untuk Filter Dashboard:", opsi_filter_kontrak, key="filter_kontrak_dashboard")

    if filter_kontrak_pilih != "-- Semua Nomor Kontrak (ALL) --":
        filtered_invoice_list = [inv for inv in invoice_list if str(inv.get("Kontrak No.", inv.get("Nomor Kontrak", "-"))).strip() == str(filter_kontrak_pilih).strip()]
        filtered_payment_records = [p for p in payment_records if str(p.get("Nomor Kontrak", "")).strip() == str(filter_kontrak_pilih).strip()]
    else:
        filtered_invoice_list = invoice_list
        filtered_payment_records = payment_records

    # --- 3. REKAPITULASI KEUANGAN DENGAN 4 KOTAK STATISTIK ---
    if invoice_list or payment_records:
        hari_ini = date.today()
        
        total_nilai_kontrak_aktif = 0.0
        if filter_kontrak_pilih != "-- Semua Nomor Kontrak (ALL) --":
            total_nilai_kontrak_aktif = master_kontrak_plafon.get(str(filter_kontrak_pilih).strip(), 0.0)
        else:
            total_nilai_kontrak_aktif = sum(master_kontrak_plafon.values())

        total_seluruh_tagihan = 0.0
        total_sudah_dibayar = 0.0

        jml_aman = 0; val_aman = 0.0
        jml_warning = 0; val_warning = 0.0
        jml_overdue = 0; val_overdue = 0.0
        jml_lunas = 0; val_lunas = 0.0

        target_eval_list = filtered_invoice_list if filtered_invoice_list else filtered_payment_records

        for inv_item in target_eval_list:
            inv_no_val = str(inv_item.get(inv_key, inv_item.get("Nomor Invoice Resmi", inv_item.get("Nomor Invoice", "")))).strip()
            g_total = ambil_grand_total_invoice_master(inv_no_val)
            if g_total == 0.0:
                matching_pay = next((p for p in payment_records if str(p.get("Nomor Invoice", "")).strip() == inv_no_val), {})
                g_total = float(matching_pay.get("Grand Total", 0.0))

            total_seluruh_tagihan += g_total
            
            matching_pay = next((p for p in payment_records if str(p.get("Nomor Invoice", "")).strip() == inv_no_val), {})
            status_byr = matching_pay.get("Status Pembayaran", "Belum Dibayar")

            if status_byr == "Lunas":
                total_sudah_dibayar += g_total
                jml_lunas += 1
                val_lunas += g_total
                continue
            elif status_byr == "Sebagian (DP / Termin)":
                total_sudah_dibayar += (g_total * 0.5)

            try:
                dt_jt_source = matching_pay.get("Tanggal Jatuh Tempo", "")
                if not dt_jt_source:
                    dt_jt_source = inv_item.get("Tanggal Jatuh Tempo", str(date.today()))
                dt_jt = datetime.strptime(str(dt_jt_source)[:10], "%Y-%m-%d").date()
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
        
        persen_dibayar = (total_sudah_dibayar / total_seluruh_tagihan * 100) if total_seluruh_tagihan > 0 else 0.0
        persen_sisa = (sisa_belum_terbayar / total_seluruh_tagihan * 100) if total_seluruh_tagihan > 0 else 0.0

        def fmt_rp_satu_baris(val):
            formatted_num = f"Rp {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f'<span style="white-space: nowrap; display: inline-block;">{formatted_num}</span>'

        st.markdown("---")
        st.markdown(f"##### 💰 Rekapitulasi Saldo Keuangan & Tagihan ({filter_kontrak_pilih})")
        
        c_fin0, c_fin1, c_fin2, c_fin3 = st.columns(4)
        with c_fin0:
            st.markdown(f"""
                <div style="background-color: #1e293b; color: white; padding: 16px; border-radius: 8px; text-align: center; border-left: 5px solid #6366f1;">
                    <p style="margin: 0; font-size: 12px; color: #94a3b8; font-weight: 600;">TOTAL KONTRAK (PLAFON)</p>
                    <h3 style="margin: 6px 0 0 0; font-size: 17px; color: #ffffff;">{fmt_rp_satu_baris(total_nilai_kontrak_aktif)}</h3>
                    <p style="margin: 4px 0 0 0; font-size: 11px; color: #818cf8;">Master Plafon Kontrak</p>
                </div>
            """, unsafe_allow_html=True)
        with c_fin1:
            st.markdown(f"""
                <div style="background-color: #1e293b; color: white; padding: 16px; border-radius: 8px; text-align: center; border-left: 5px solid #38bdf8;">
                    <p style="margin: 0; font-size: 12px; color: #94a3b8; font-weight: 600;">TOTAL SELURUH TAGIHAN</p>
                    <h3 style="margin: 6px 0 0 0; font-size: 17px; color: #ffffff;">{fmt_rp_satu_baris(total_seluruh_tagihan)}</h3>
                    <p style="margin: 4px 0 0 0; font-size: 11px; color: #38bdf8;">100.00% dari Tagihan</p>
                </div>
            """, unsafe_allow_html=True)
        with c_fin2:
            st.markdown(f"""
                <div style="background-color: #1e293b; color: white; padding: 16px; border-radius: 8px; text-align: center; border-left: 5px solid #10b981;">
                    <p style="margin: 0; font-size: 12px; color: #94a3b8; font-weight: 600;">TOTAL SUDAH DIBAYARKAN</p>
                    <h3 style="margin: 6px 0 0 0; font-size: 17px; color: #34d399;">{fmt_rp_satu_baris(total_sudah_dibayar)}</h3>
                    <p style="margin: 4px 0 0 0; font-size: 11px; color: #34d399;">{persen_dibayar:.2f}% (Realisasi)</p>
                </div>
            """, unsafe_allow_html=True)
        with c_fin3:
            st.markdown(f"""
                <div style="background-color: #1e293b; color: white; padding: 16px; border-radius: 8px; text-align: center; border-left: 5px solid #f59e0b;">
                    <p style="margin: 0; font-size: 12px; color: #94a3b8; font-weight: 600;">SISA BELUM TERBAYAR</p>
                    <h3 style="margin: 6px 0 0 0; font-size: 17px; color: #fbbf24;">{fmt_rp_satu_baris(sisa_belum_terbayar)}</h3>
                    <p style="margin: 4px 0 0 0; font-size: 11px; color: #fbbf24;">{persen_sisa:.2f}% (Piutang)</p>
                </div>
            """, unsafe_allow_html=True)

        # --- TABEL RINCIAN AKUMULASI PER NOMOR KONTRAK ---
        st.markdown("---")
        st.markdown("##### 📑 Rincian Akumulasi Tagihan per Nomor Kontrak")
        
        summary_contract_map = {}
        for item_rc in invoice_list:
            c_no = str(item_rc.get("Kontrak No.", item_rc.get("Nomor Kontrak", "-"))).strip()
            inv_no_rc = str(item_rc.get(inv_key, item_rc.get("Nomor Invoice Resmi", item_rc.get("Nomor Invoice", "")))).strip()
            gt = ambil_grand_total_invoice_master(inv_no_rc)
            if gt == 0.0:
                gt = float(item_rc.get("Grand Total", 0.0))

            matching_pay_rc = next((p for p in payment_records if str(p.get("Nomor Invoice", "")).strip() == inv_no_rc), {})
            st_byr = matching_pay_rc.get("Status Pembayaran", "Belum Dibayar")
            
            if c_no not in summary_contract_map:
                summary_contract_map[c_no] = {"tagihan": 0.0, "terbayar": 0.0, "jml_inv": 0, "lunas": 0}
            
            summary_contract_map[c_no]["tagihan"] += gt
            summary_contract_map[c_no]["jml_inv"] += 1
            if st_byr == "Lunas":
                summary_contract_map[c_no]["terbayar"] += gt
                summary_contract_map[c_no]["lunas"] += 1
            elif st_byr == "Sebagian (DP / Termin)":
                summary_contract_map[c_no]["terbayar"] += (gt * 0.5)

        rh_cols = st.columns([1.5, 0.8, 2.0, 2.0, 2.0, 2.0, 1.0, 0.9])
        r_headers = ["Nomor Kontrak", "Jml Dok", "Total Nilai Kontrak", "Total Tagihan", "Sudah Dibayar", "Sisa Piutang", "Realisasi", "Status"]
        for rh, rht in zip(rh_cols, r_headers):
            with rh:
                st.markdown(f"<span style='font-size: 11px; font-weight: bold; color: #0f172a; white-space: nowrap;'>{rht}</span>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 4px 0; border-top: 2px solid #cbd5e1;'>", unsafe_allow_html=True)

        tot_sum_tagihan = 0.0
        tot_sum_terbayar = 0.0
        tot_sum_piutang = 0.0
        tot_sum_plafon = 0.0
        tot_jml_dok = 0

        def fmt_small_rp(val):
            formatted_num = f"Rp {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f'<small style="white-space: nowrap; display: inline-block; font-size: 11px;">{formatted_num}</small>'

        for c_key, c_val in summary_contract_map.items():
            t_tag = c_val["tagihan"]
            t_byr = c_val["terbayar"]
            t_piu = t_tag - t_byr
            
            t_plafon = master_kontrak_plafon.get(c_key, 0.0)
            if t_plafon == 0.0:
                for k_plf, v_plf in master_kontrak_plafon.items():
                    if k_plf in c_key or c_key in k_plf:
                        t_plafon = v_plf
                        break

            pct_real = (t_byr / t_tag * 100) if t_tag > 0 else 0.0
            
            tot_sum_tagihan += t_tag
            tot_sum_terbayar += t_byr
            tot_sum_piutang += t_piu
            tot_sum_plafon += t_plafon
            tot_jml_dok += c_val["jml_inv"]

            st_teks = "🟢 Lengkap" if c_val["lunas"] == c_val["jml_inv"] else f"🟡 {c_val['lunas']}/{c_val['jml_inv']} Lunas"

            rc_cols = st.columns([1.5, 0.8, 2.0, 2.0, 2.0, 2.0, 1.0, 0.9])
            with rc_cols[0]:
                st.markdown(f"<small style='font-size: 11px; white-space: nowrap;'><b>{c_key}</b></small>", unsafe_allow_html=True)
            with rc_cols[1]:
                st.markdown(f"<small style='font-size: 11px; white-space: nowrap;'>{c_val['jml_inv']} Dok</small>", unsafe_allow_html=True)
            with rc_cols[2]:
                st.markdown(fmt_small_rp(t_plafon), unsafe_allow_html=True)
            with rc_cols[3]:
                st.markdown(fmt_small_rp(t_tag), unsafe_allow_html=True)
            with rc_cols[4]:
                st.markdown(fmt_small_rp(t_byr), unsafe_allow_html=True)
            with rc_cols[5]:
                st.markdown(fmt_small_rp(t_piu), unsafe_allow_html=True)
            with rc_cols[6]:
                st.markdown(f"<small style='font-size: 11px; white-space: nowrap;'><b>{pct_real:.2f}%</b></small>", unsafe_allow_html=True)
            with rc_cols[7]:
                st.markdown(f"<small style='font-size: 11px; white-space: nowrap;'>{st_teks}</small>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 2px 0; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

        tot_pct_overall = (tot_sum_terbayar / tot_sum_tagihan * 100) if tot_sum_tagihan > 0 else 0.0
        tot_cols = st.columns([1.5, 0.8, 2.0, 2.0, 2.0, 2.0, 1.0, 0.9])
        with tot_cols[0]:
            st.markdown("<small style='font-size: 11px; white-space: nowrap;'><b>TOTAL KESELURUHAN</b></small>", unsafe_allow_html=True)
        with tot_cols[1]:
            st.markdown(f"<small style='font-size: 11px; white-space: nowrap;'><b>{tot_jml_dok} Dok</b></small>", unsafe_allow_html=True)
        with tot_cols[2]:
            st.markdown(f"**<span style='white-space: nowrap; font-size: 11px;'>Rp {tot_sum_plafon:,.2f}</span>**".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
        with tot_cols[3]:
            st.markdown(f"**<span style='white-space: nowrap; font-size: 11px;'>Rp {tot_sum_tagihan:,.2f}</span>**".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
        with tot_cols[4]:
            st.markdown(f"**<span style='white-space: nowrap; font-size: 11px;'>Rp {tot_sum_terbayar:,.2f}</span>**".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
        with tot_cols[5]:
            st.markdown(f"**<span style='white-space: nowrap; font-size: 11px;'>Rp {tot_sum_piutang:,.2f}</span>**".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
        with tot_cols[6]:
            st.markdown(f"<small style='font-size: 11px; white-space: nowrap;'><b>{tot_pct_overall:.2f}%</b></small>", unsafe_allow_html=True)
        with tot_cols[7]:
            st.markdown("<small style='font-size: 11px; white-space: nowrap;'><b>100%</b></small>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 4px 0; border-top: 2px solid #0f172a;'>", unsafe_allow_html=True)

        # --- DIAGRAM / GRAFIK KOMPARASI KEUANGAN ---
        st.markdown("---")
        st.markdown("##### 📈 Grafik Visualisasi Komparasi Keuangan & Kinerja Pembayaran")
        
        col_g1, col_g2 = st.columns([2, 1])
        with col_g1:
            df_grafik = pd.DataFrame({
                "Komponen Keuangan": ["Total Plafon Kontrak", "Total Tagihan", "Sudah Dibayar", "Sisa Piutang"],
                "Nominal (Rp)": [total_nilai_kontrak_aktif if total_nilai_kontrak_aktif > 0 else tot_sum_plafon, total_seluruh_tagihan, total_sudah_dibayar, sisa_belum_terbayar]
            }).set_index("Komponen Keuangan")
            st.bar_chart(df_grafik, color="#38bdf8")
            
        with col_g2:
            st.markdown(f"""
                <div style="background-color: #0f172a; color: #f8fafc; padding: 16px; border-radius: 8px; font-size: 13px;">
                    <p style="font-weight: bold; color: #38bdf8; margin-bottom: 8px;">💡 Ringkasan Analisis Eksekutif:</p>
                    <ul style="padding-left: 18px; margin: 0; color: #cbd5e1;">
                        <li><b>Rasio Realisasi:</b> <code>{persen_dibayar:.2f}%</code></li>
                        <li><b>Rasio Piutang:</b> <code>{persen_sisa:.2f}%</code></li>
                        <li><b>Dokumen Lunas:</b> <code>{jml_lunas} Dokumen</code></li>
                        <li><b>Dokumen Overdue:</b> <code>{jml_overdue} Dokumen</code></li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

    # --- 5. TABEL RINGKASAN & LAPORAN AGING DENGAN SCROLL HORIZONTAL (AGAR TIDAK MENIMPA) ---
    st.markdown("---")
    st.markdown(f"#### 📋 Ringkasan & Laporan Aging Invoice ({filter_kontrak_pilih})")

    current_payment_records = muat_status_pembayaran()
    if filter_kontrak_pilih != "-- Semua Nomor Kontrak (ALL) --":
        current_payment_records = [p for p in current_payment_records if str(p.get("Nomor Kontrak", "")).strip() == str(filter_kontrak_pilih).strip()]

    if current_payment_records:
        st.markdown('<div style="overflow-x: auto; width: 100%; padding-bottom: 12px;">', unsafe_allow_html=True)
        
        hdr_cols = st.columns([1.2, 1.5, 1.4, 2.2, 1.0, 1.0, 0.8, 1.0, 1.0, 1.3, 1.1, 0.9])
        headers_text = ["No. Kontrak", "No. Invoice", "No. Faktur Pajak", "Customer", "Tgl Inv", "Tgl Serah", "TOP", "Tgl JT", "Tgl Lunas", "Grand Total", "Status", "Aksi (Edit / Hapus)"]
        for hc, ht in zip(hdr_cols, headers_text):
            with hc:
                st.markdown(f"<span style='font-size: 11px; font-weight: bold; color: #0f172a; white-space: nowrap;'>{ht}</span>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 4px 0; border-top: 2px solid #cbd5e1;'>", unsafe_allow_html=True)

        for idx, row_p in enumerate(current_payment_records):
            inv_num_row = row_p.get('Nomor Invoice', '-')
            faktur_pajak_row = row_p.get('Nomor Faktur Pajak', '-')
           
            tgl_penyerahan_str = str(row_p.get('Tanggal Penyerahan', ''))[:10]
            tgl_pelunasan_raw = str(row_p.get('Tanggal Pelunasan', '-'))
            tgl_pelunasan_str = tgl_pelunasan_raw[:10] if tgl_pelunasan_raw and tgl_pelunasan_raw != "-" else "..."

            durasi_info = f"{row_p.get('TOP Hari', 0)}d"
            if tgl_pelunasan_raw and tgl_pelunasan_raw != "-":
                try:
                    dt_serah = datetime.strptime(tgl_penyerahan_str, "%Y-%m-%d").date()
                    dt_lunas = datetime.strptime(tgl_pelunasan_raw[:10], "%Y-%m-%d").date()
                    selisih_riil = (dt_lunas - dt_serah).days
                    durasi_info = f"{row_p.get('TOP Hari', 0)}d (R: {selisih_riil}d)"
                except:
                    pass

            cols_r = st.columns([1.2, 1.5, 1.4, 2.2, 1.0, 1.0, 0.8, 1.0, 1.0, 1.3, 1.1, 0.9])
            with cols_r[0]:
                st.markdown(f"<small style='white-space: nowrap;'>{row_p.get('Nomor Kontrak', '-')}</small>", unsafe_allow_html=True)
            with cols_r[1]:
                st.markdown(f"<b style='white-space: nowrap;'>{inv_num_row}</b>", unsafe_allow_html=True)
            with cols_r[2]:
                st.markdown(f"<small style='white-space: nowrap;'>{faktur_pajak_row if faktur_pajak_row else '-'}</small>", unsafe_allow_html=True)
            with cols_r[3]:
                st.markdown(f"<small style='white-space: normal; display: inline-block; max-width: 180px;'>{row_p.get('Customer', '-')}</small>", unsafe_allow_html=True)
            with cols_r[4]:
                st.markdown(f"<small style='white-space: nowrap;'>{str(row_p.get('Tanggal Invoice', ''))[:10]}</small>", unsafe_allow_html=True)
            with cols_r[5]:
                st.markdown(f"<small style='white-space: nowrap;'>{tgl_penyerahan_str}</small>", unsafe_allow_html=True)
            with cols_r[6]:
                st.markdown(f"<small style='white-space: nowrap;'>{durasi_info}</small>", unsafe_allow_html=True)
            with cols_r[7]:
                st.markdown(f"<small style='white-space: nowrap;'>{str(row_p.get('Tanggal Jatuh Tempo', ''))[:10]}</small>", unsafe_allow_html=True)
            with cols_r[8]:
                st.markdown(f"<small style='white-space: nowrap;'>{tgl_pelunasan_str}</small>", unsafe_allow_html=True)
            with cols_r[9]:
                gt_val = float(row_p.get('Grand Total', 0))
                st.markdown(f"<small style='white-space: nowrap;'>Rp {gt_val:,.2f}</small>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
            with cols_r[10]:
                st.markdown(f"<small style='white-space: nowrap;'>{row_p.get('Status Pembayaran', '-')}</small>", unsafe_allow_html=True)
            with cols_r[11]:
                aksi_pilih = st.selectbox("Aksi", ["-- Pilih --", "✏️ Edit", "🗑️ Hapus"], key=f"aksi_{idx}_{inv_num_row}", label_visibility="collapsed")
                if aksi_pilih == "✏️ Edit":
                    st.session_state["active_invoice_selected"] = str(inv_num_row).strip()
                    st.rerun()
                elif aksi_pilih == "🗑️ Hapus":
                    st.session_state[f"confirm_del_{idx}"] = True
                    st.rerun()

            if st.session_state.get(f"confirm_del_{idx}", False):
                st.error(f"⚠️ Konfirmasi Keamanan: Masukkan Password Admin untuk menghapus Invoice [{inv_num_row}]")
                pass_input = st.text_input(f"Password Verifikasi ({inv_num_row}):", type="password", key=f"pwd_del_{idx}")
                col_vk1, col_vk2 = st.columns(2)
                with col_vk1:
                    if st.button("✔️ Konfirmasi", key=f"btn_yes_del_{idx}"):
                        if pass_input in ["bss2026", "admin123", "admin"]:
                            all_master_recs = muat_status_pembayaran()
                            updated_recs = [p for p in all_master_recs if str(p.get("Nomor Invoice", "")).strip() != str(inv_num_row).strip()]
                            simpan_status_pembayaran(updated_recs)
                            st.success(f"🗑️ Data pemantauan Invoice [{inv_num_row}] berhasil dihapus!")
                            if f"confirm_del_{idx}" in st.session_state:
                                del st.session_state[f"confirm_del_{idx}"]
                            if "active_invoice_selected" in st.session_state:
                                del st.session_state["active_invoice_selected"]
                            st.rerun()
                        else:
                            st.error("❌ Password verifikasi salah!")
                with col_vk2:
                    if st.button("❌ Batal", key=f"btn_no_del_{idx}"):
                        if f"confirm_del_{idx}" in st.session_state:
                            del st.session_state[f"confirm_del_{idx}"]
                        st.rerun()

            st.markdown("<hr style='margin: 2px 0; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("ℹ️ Belum ada data pemantauan pembayaran yang tersimpan untuk filter kontrak ini.")