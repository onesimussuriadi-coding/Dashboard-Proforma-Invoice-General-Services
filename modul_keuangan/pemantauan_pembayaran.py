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

    # --- 2. AMBIL TOTAL KONTRAK (PLAFON) DARI MODUL 2 DENGAN BREAKDOWN PRESISI ---
    def muat_total_kontrak_modul2():
        plafon_files = [
            os.path.join(DIR_DATABASE, "database_plafon_kontrak.xlsx"),
            os.path.join(DIR_DATABASE, "database_kontrak.xlsx"),
            os.path.join(DIR_DATABASE, "database_master_kontrak.xlsx"),
            os.path.join(DIR_DATABASE, "database_rekap_transaksi.xlsx")
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
                                if "kontrak" in col_l or "nomor" in col_l:
                                    if val_col and val_col != '-' and val_col.lower() != 'nan' and len(val_col) >= 8:
                                        c_num = val_col
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

    fallback_plafon_standard = {
        "7201250141": 42997282428.98,
        "7207250142": 38711901661.00,
        "7203250036": 1971459000.00
    }
    for k_std, v_std in fallback_plafon_standard.items():
        if k_std not in master_kontrak_plafon or master_kontrak_plafon[k_std] == 0.0:
            master_kontrak_plafon[k_std] = v_std

    kontrak_from_invoice = [str(inv.get("Kontrak No.", inv.get("Nomor Kontrak", "-"))).strip() for inv in invoice_list if inv.get("Kontrak No.") or inv.get("Nomor Kontrak")]
    kontrak_from_payment = [str(p.get("Nomor Kontrak", "-")).strip() for p in payment_records if p.get("Nomor Kontrak")]
    kontrak_from_master = list(master_kontrak_plafon.keys())
    
    all_contracts = sorted(list(dict.fromkeys([k for k in (kontrak_from_invoice + kontrak_from_payment + kontrak_from_master) if k and k != '-' and k.lower() != 'nan' and k.lower() != 'grand total'])))

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
    if invoice_list or payment_records or master_kontrak_plafon:
        hari_ini = date.today()
        
        total_nilai_kontrak_aktif = 0.0
        if filter_kontrak_pilih != "-- Semua Nomor Kontrak (ALL) --":
            total_nilai_kontrak_aktif = master_kontrak_plafon.get(str(filter_kontrak_pilih).strip(), 0.0)
            if total_nilai_kontrak_aktif == 0.0:
                for k_plf, v_plf in master_kontrak_plafon.items():
                    if k_plf in filter_kontrak_pilih or filter_kontrak_pilih in k_plf:
                        total_nilai_kontrak_aktif = v_plf
                        break
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

        # --- 4. TABEL RINCIAN AKUMULASI PER NOMOR KONTRAK (HTML AMAN & RAPI) ---
        st.markdown("---")
        st.markdown("##### 📑 Rincian Akumulasi Tagihan per Nomor Kontrak")
        
        summary_contract_map = {}
        for k_m in all_contracts:
            summary_contract_map[k_m] = {"tagihan": 0.0, "terbayar": 0.0, "jml_inv": 0, "lunas": 0}

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

        def fmt_html_rp(val):
            formatted_num = f"Rp {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return formatted_num

        html_table_rincian = """
        <div style="overflow-x: auto; width: 100%; padding-bottom: 10px;">
        <table style="width: 100%; border-collapse: collapse; font-size: 13px; font-family: sans-serif;">
            <thead>
                <tr style="border-bottom: 2px solid #cbd5e1; text-align: left; color: #0f172a;">
                    <th style="padding: 8px; white-space: nowrap;">Nomor Kontrak</th>
                    <th style="padding: 8px; white-space: nowrap;">Jml Dok</th>
                    <th style="padding: 8px; white-space: nowrap;">Total Nilai Kontrak</th>
                    <th style="padding: 8px; white-space: nowrap;">Total Tagihan</th>
                    <th style="padding: 8px; white-space: nowrap;">Sudah Dibayar</th>
                    <th style="padding: 8px; white-space: nowrap;">Sisa Piutang</th>
                    <th style="padding: 8px; white-space: nowrap;">Realisasi</th>
                    <th style="padding: 8px; white-space: nowrap;">Status</th>
                </tr>
            </thead>
            <tbody>
        """

        tot_sum_tagihan = 0.0
        tot_sum_terbayar = 0.0
        tot_sum_piutang = 0.0
        tot_sum_plafon = 0.0
        tot_jml_dok = 0

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

            st_teks = "🟢 Lengkap" if (c_val["jml_inv"] > 0 and c_val["lunas"] == c_val["jml_inv"]) else (f"🟡 {c_val['lunas']}/{c_val['jml_inv']} Lunas" if c_val["jml_inv"] > 0 else "⚪ Belum Ada Transaksi")

            html_table_rincian += f"""
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 8px; white-space: nowrap; font-weight: bold;">{c_key}</td>
                    <td style="padding: 8px; white-space: nowrap;">{c_val['jml_inv']} Dok</td>
                    <td style="padding: 8px; white-space: nowrap;">{fmt_html_rp(t_plafon)}</td>
                    <td style="padding: 8px; white-space: nowrap;">{fmt_html_rp(t_tag)}</td>
                    <td style="padding: 8px; white-space: nowrap;">{fmt_html_rp(t_byr)}</td>
                    <td style="padding: 8px; white-space: nowrap;">{fmt_html_rp(t_piu)}</td>
                    <td style="padding: 8px; white-space: nowrap; font-weight: bold;">{pct_real:.2f}%</td>
                    <td style="padding: 8px; white-space: nowrap;">{st_teks}</td>
                </tr>
            """

        tot_pct_overall = (tot_sum_terbayar / tot_sum_tagihan * 100) if tot_sum_tagihan > 0 else 0.0
        grand_total_plafon_real = sum(master_kontrak_plafon.values()) if sum(master_kontrak_plafon.values()) > 0 else tot_sum_plafon

        html_table_rincian += f"""
                <tr style="border-top: 2px solid #0f172a; font-weight: bold;">
                    <td style="padding: 8px; white-space: nowrap;">TOTAL KESELURUHAN</td>
                    <td style="padding: 8px; white-space: nowrap;">{tot_jml_dok} Dok</td>
                    <td style="padding: 8px; white-space: nowrap;">{fmt_html_rp(grand_total_plafon_real)}</td>
                    <td style="padding: 8px; white-space: nowrap;">{fmt_html_rp(tot_sum_tagihan)}</td>
                    <td style="padding: 8px; white-space: nowrap;">{fmt_html_rp(tot_sum_terbayar)}</td>
                    <td style="padding: 8px; white-space: nowrap;">{fmt_html_rp(tot_sum_piutang)}</td>
                    <td style="padding: 8px; white-space: nowrap;">{tot_pct_overall:.2f}%</td>
                    <td style="padding: 8px; white-space: nowrap;">100%</td>
                </tr>
            </tbody>
        </table>
        </div>
        """

        st.markdown(html_table_rincian, unsafe_allow_html=True)

        # --- DIAGRAM / GRAFIK KOMPARASI KEUANGAN ---
        st.markdown("---")
        st.markdown("##### 📈 Grafik Visualisasi Komparasi Keuangan & Kinerja Pembayaran")
        
        col_g1, col_g2 = st.columns([2, 1])
        with col_g1:
            df_grafik = pd.DataFrame({
                "Komponen Keuangan": ["Total Plafon Kontrak", "Total Tagihan", "Sudah Dibayar", "Sisa Piutang"],
                "Nominal (Rp)": [grand_total_plafon_real, total_seluruh_tagihan, total_sudah_dibayar, sisa_belum_terbayar]
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

    # --- 5. FORM INPUT & PEMBARUAN STATUS PEMBAYARAN ---
    st.markdown("---")
    st.markdown("##### 📝 Form Input & Pembaruan Status Pembayaran (Berdasarkan Kontrak)")

    col_fc1, col_fc2 = st.columns([1.5, 2.5])
    with col_fc1:
        form_kontrak_pilih = st.selectbox("1️⃣ Pilih Nomor Kontrak:", all_contracts if all_contracts else ["-"], key="form_input_kontrak_sel")
    
    inv_list_filtered_contract = [inv for inv in invoice_list if str(inv.get("Kontrak No.", inv.get("Nomor Kontrak", "-"))).strip() == str(form_kontrak_pilih).strip()]
    
    all_inv_no_contract = []
    for inv in inv_list_filtered_contract:
        val_inv = str(inv.get(inv_key, "")).strip()
        if val_inv and not val_inv.startswith("2026-") and len(val_inv) > 3:
            all_inv_no_contract.append(val_inv)
            
    if not all_inv_no_contract:
        all_inv_no_contract = [str(inv.get(inv_key, "")).strip() for inv in inv_list_filtered_contract if inv.get(inv_key)]

    if not all_inv_no_contract and payment_records:
        all_inv_no_contract = sorted(list(dict.fromkeys([str(p.get("Nomor Invoice", "")).strip() for p in payment_records if str(p.get("Nomor Kontrak", "")).strip() == str(form_kontrak_pilih).strip() and p.get("Nomor Invoice")])))

    saved_invoice_set = {str(p.get("Nomor Invoice", "")).strip() for p in payment_records if p.get("Nomor Invoice")}

    active_edit_inv = str(st.session_state.get("active_invoice_selected", "")).strip()
    list_inv_aktif = [inv_no for inv_no in all_inv_no_contract if inv_no not in saved_invoice_set or inv_no == active_edit_inv]
    if not list_inv_aktif and all_inv_no_contract:
        list_inv_aktif = all_inv_no_contract

    list_saved_payment_no = sorted(list({str(p.get("Nomor Invoice")) for p in payment_records if str(p.get("Nomor Kontrak")) == str(form_kontrak_pilih)}), reverse=True)
    opsi_panggil_bayar = ["-- Pilih Data Tersimpan untuk Diedit / Panggil Ulang --"] + list_saved_payment_no

    with col_fc2:
        pilihan_panggil_bayar = st.selectbox("2️⃣ Panggil Ulang Data Pemantauan Tersimpan (Kontrak Terpilih):", opsi_panggil_bayar, key="select_panggil_bayar")
        if st.button("📥 Panggil untuk Diedit", use_container_width=True):
            if pilihan_panggil_bayar != "-- Pilih Data Tersimpan untuk Diedit / Panggil Ulang --":
                st.session_state["active_invoice_selected"] = str(pilihan_panggil_bayar).strip()
                st.success(f"📋 Memuat data pemantauan Invoice `{pilihan_panggil_bayar}`")
                st.rerun()

    default_select_idx = 0
    if active_edit_inv in list_inv_aktif:
        default_select_idx = list_inv_aktif.index(active_edit_inv)

    if not list_inv_aktif:
        selected_inv = st.text_input("3️⃣ Ketik Nomor Invoice Aktif:", value=active_edit_inv)
    else:
        selected_inv = st.selectbox("3️⃣ Pilih Nomor Invoice Aktif:", list_inv_aktif, index=default_select_idx if default_select_idx < len(list_inv_aktif) else 0, key="dropdown_master_invoice_aktif")

    inv_data = next((inv for inv in invoice_list if str(inv.get(inv_key, "")).strip() == str(selected_inv)), {})
    existing_pay = next((p for p in payment_records if str(p.get("Nomor Invoice", "")).strip() == str(selected_inv)), {})

    tgl_invoice_bawaan = ambil_tanggal_invoice(inv_data) if inv_data else str(existing_pay.get("Tanggal Invoice", date.today()))[:10]
    grand_total_otomatis = ambil_grand_total_invoice_master(selected_inv)
    if grand_total_otomatis == 0.0 and existing_pay:
        grand_total_otomatis = float(existing_pay.get("Grand Total", 0.0))

    formatted_grand_total = f"Rp {grand_total_otomatis:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    st.markdown(f"""
        📄 **Informasi Invoice Terpilih:**  
        - **Nomor Kontrak:** `{form_kontrak_pilih}`  
        - **Nomor Invoice:** `{selected_inv}`  
        - **Tanggal Invoice:** `{tgl_invoice_bawaan}`  
        - **Nilai Nominal Invoice (Grand Total):** **{formatted_grand_total}**
    """)

    status_opsi = ["Belum Dibayar", "Sebagian (DP / Termin)", "Lunas"]
    def_status = existing_pay.get("Status Pembayaran", "Belum Dibayar")
    idx_st = status_opsi.index(def_status) if def_status in status_opsi else 0
    status_pembayaran = st.selectbox("Status Pembayaran:", status_opsi, index=idx_st, key="select_status_pembayaran_live")

    with st.form("form_update_pembayaran"):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            default_faktur = existing_pay.get("Nomor Faktur Pajak", "")
            nomor_faktur_pajak = st.text_input("Nomor Faktur Pajak (Diterbitkan setelah Invoice):", value=str(default_faktur))

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
            st.markdown(f"**Status Pembayaran Terpilih:** `{status_pembayaran}`")

            raw_tgl_lunas_exist = str(existing_pay.get("Tanggal Pelunasan", "-"))
            ada_tgl_lunas_exist = (raw_tgl_lunas_exist != "-" and raw_tgl_lunas_exist.strip() != "")

            if status_pembayaran in ["Sebagian (DP / Termin)", "Lunas"]:
                default_tgl_lunas = datetime.today().date()
                if ada_tgl_lunas_exist:
                    try:
                        default_tgl_lunas = datetime.strptime(raw_tgl_lunas_exist[:10], "%Y-%m-%d").date()
                    except:
                        pass
                tgl_pelunasan = st.date_input("Tanggal Pelunasan Aktual:", value=default_tgl_lunas)
            else:
                st.markdown("📅 Tanggal Pelunasan Aktual: **... (Belum Ada Pembayaran / Kosong)**")
                tgl_pelunasan = None

        catatan_bayar = st.text_area("Catatan / Keterangan Pembayaran:", value=str(existing_pay.get("Catatan", "")))

        submit_simpan = st.form_submit_button("💾 Simpan Pemantauan Pembayaran", type="primary", use_container_width=True)

        if submit_simpan:
            if not selected_inv.strip():
                st.error("❌ Nomor Invoice tidak boleh kosong!")
            else:
                tgl_jatuh_tempo = tgl_penyerahan + timedelta(days=int(top_hari))

                durasi_riil_hari = 0
                str_tgl_pelunasan_final = "-"
                if status_pembayaran in ["Sebagian (DP / Termin)", "Lunas"] and tgl_pelunasan:
                    str_tgl_pelunasan_final = tgl_pelunasan.strftime("%Y-%m-%d")
                    durasi_riil_hari = (tgl_pelunasan - tgl_penyerahan).days

                data_update = {
                    "Nomor Kontrak": form_kontrak_pilih,
                    "Nomor Invoice": selected_inv,
                    "Nomor Faktur Pajak": nomor_faktur_pajak,
                    "Customer": inv_data.get("Customer", existing_pay.get("Customer", "-")),
                    "Tanggal Invoice": tgl_invoice_bawaan,
                    "Tanggal Penyerahan": tgl_penyerahan.strftime("%Y-%m-%d"),
                    "TOP Hari": top_hari,
                    "Tanggal Jatuh Tempo": tgl_jatuh_tempo.strftime("%Y-%m-%d"),
                    "Tanggal Pelunasan": str_tgl_pelunasan_final,
                    "Durasi Riil Hari": durasi_riil_hari,
                    "Grand Total": grand_total_otomatis,
                    "Status Pembayaran": status_pembayaran,
                    "Catatan": catatan_bayar,
                    "Update Terakhir": datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                }

                clean_records = [p for p in payment_records if str(p.get("Nomor Invoice", "")).strip() != str(selected_inv).strip()]
                clean_records.append(data_update)
                simpan_status_pembayaran(clean_records)
                st.success(f"🎉 Berhasil menyimpan data pemantauan untuk Invoice [{selected_inv}]!")
                if "active_invoice_selected" in st.session_state:
                    del st.session_state["active_invoice_selected"]
                st.rerun()

    # --- 6. TABEL RINGKASAN & LAPORAN AGING DENGAN HTML TABLE & HORIZONTAL SCROLL PENUH ---
    st.markdown("---")
    st.markdown(f"#### 📋 Ringkasan & Laporan Aging Invoice ({filter_kontrak_pilih})")

    current_payment_records = muat_status_pembayaran()
    if filter_kontrak_pilih != "-- Semua Nomor Kontrak (ALL) --":
        current_payment_records = [p for p in current_payment_records if str(p.get("Nomor Kontrak", "")).strip() == str(filter_kontrak_pilih).strip()]

    if current_payment_records:
        html_table_aging = """
        <div style="overflow-x: auto; width: 100%; padding-bottom: 15px;">
        <table style="width: 100%; border-collapse: collapse; font-size: 13px; font-family: sans-serif;">
            <thead>
                <tr style="border-bottom: 2px solid #cbd5e1; text-align: left; color: #0f172a;">
                    <th style="padding: 8px; white-space: nowrap;">No. Kontrak</th>
                    <th style="padding: 8px; white-space: nowrap;">No. Invoice</th>
                    <th style="padding: 8px; white-space: nowrap;">No. Faktur Pajak</th>
                    <th style="padding: 8px; white-space: nowrap;">Customer</th>
                    <th style="padding: 8px; white-space: nowrap;">Tgl Inv</th>
                    <th style="padding: 8px; white-space: nowrap;">Tgl Serah</th>
                    <th style="padding: 8px; white-space: nowrap;">TOP</th>
                    <th style="padding: 8px; white-space: nowrap;">Tgl JT</th>
                    <th style="padding: 8px; white-space: nowrap;">Tgl Lunas</th>
                    <th style="padding: 8px; white-space: nowrap;">Grand Total</th>
                    <th style="padding: 8px; white-space: nowrap;">Status</th>
                </tr>
            </thead>
            <tbody>
        """

        for idx, row_p in enumerate(current_payment_records):
            inv_num_row = row_p.get('Nomor Invoice', '-')
            faktur_pajak_row = row_p.get('Nomor Faktur Pajak', '-')
            cust_row = row_p.get('Customer', '-')
            no_kontrak_row = row_p.get('Nomor Kontrak', '-')
           
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

            gt_val = float(row_p.get('Grand Total', 0))
            gt_str = f"Rp {gt_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            status_p = row_p.get('Status Pembayaran', '-')

            html_table_aging += f"""
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 8px; white-space: nowrap;">{no_kontrak_row}</td>
                    <td style="padding: 8px; white-space: nowrap;">{inv_num_row}</td>
                    <td style="padding: 8px; white-space: nowrap;">{faktur_pajak_row if faktur_pajak_row else '-'}</td>
                    <td style="padding: 8px; white-space: nowrap;">{cust_row}</td>
                    <td style="padding: 8px; white-space: nowrap;">{str(row_p.get('Tanggal Invoice', ''))[:10]}</td>
                    <td style="padding: 8px; white-space: nowrap;">{tgl_penyerahan_str}</td>
                    <td style="padding: 8px; white-space: nowrap;">{durasi_info}</td>
                    <td style="padding: 8px; white-space: nowrap;">{str(row_p.get('Tanggal Jatuh Tempo', ''))[:10]}</td>
                    <td style="padding: 8px; white-space: nowrap;">{tgl_pelunasan_str}</td>
                    <td style="padding: 8px; white-space: nowrap;">{gt_str}</td>
                    <td style="padding: 8px; white-space: nowrap;">{status_p}</td>
                </tr>
            """

        html_table_aging += """
            </tbody>
        </table>
        </div>
        """

        st.markdown(html_table_aging, unsafe_allow_html=True)

        # Bagian Aksi / Edit / Hapus via Selectbox per baris untuk kemudahan interaksi
        st.markdown("##### ⚙️ Aksi Cepat Data Pemantauan Invoice")
        for idx, row_p in enumerate(current_payment_records):
            inv_num_row = row_p.get('Nomor Invoice', '-')
            c_ak1, c_ak2 = st.columns([3, 1])
            with c_ak1:
                st.markdown(f"<small>Invoice: <b>{inv_num_row}</b> (Kontrak: {row_p.get('Nomor Kontrak', '-')})</small>", unsafe_allow_html=True)
            with c_ak2:
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
    else:
        st.info("ℹ️ Belum ada data pemantauan pembayaran yang tersimpan untuk filter kontrak ini.")