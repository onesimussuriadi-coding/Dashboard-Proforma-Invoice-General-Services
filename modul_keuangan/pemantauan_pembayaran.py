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

    def fmt_rp(val):
        num = float(val or 0.0)
        return f"Rp {num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def fmt_rp_satu_baris(val):
        formatted_num = fmt_rp(val)
        return f'<span style="white-space: nowrap; display: inline-block;">{formatted_num}</span>'

    # --- 1. MEMBACA DATA INVOICE DARI MODUL 3 ---
    def muat_invoice_tersimpan_modul3():
        semua_data = []
        if os.path.exists(DIR_DATABASE):
            for f_name in os.listdir(DIR_DATABASE):
                if f_name.endswith(".xlsx"):
                    f_path = os.path.join(DIR_DATABASE, f_name)
                    try:
                        df = pd.read_excel(f_path)
                        if df is not None and not df.empty:
                            cols_lower = [str(c).lower() for c in df.columns]
                            if any("invoice" in c or "kontrak" in c or "pi" in c for c in cols_lower):
                                records = df.to_dict(orient="records")
                                semua_data.extend(records)
                    except:
                        pass
        return semua_data

    invoice_list = muat_invoice_tersimpan_modul3()

    def cari_nama_kolom(sample_obj, kata_kunci_list):
        if not sample_obj:
            return ""
        for k in sample_obj.keys():
            k_low = str(k).strip().lower()
            for kk in kata_kunci_list:
                if kk in k_low:
                    return k
        return ""

    sample_inv = invoice_list[0] if invoice_list else {}
    col_key_inv = cari_nama_kolom(sample_inv, ["nomor invoice resmi", "invoice resmi", "nomor invoice", "invoice"])
    if not col_key_inv and sample_inv:
        col_key_inv = list(sample_inv.keys())[0]

    col_key_kontrak = cari_nama_kolom(sample_inv, ["kontrak no", "nomor kontrak", "kontrak"])
    col_key_pi = cari_nama_kolom(sample_inv, ["pi no", "nomor pi", "pi"])

    def ambil_detail_invoice_master(inv_no):
        target_inv_clean = str(inv_no).strip().lower()
        for inv in invoice_list:
            found_no = str(inv.get(col_key_inv, inv.get("Nomor Invoice Resmi", ""))).strip().lower()
            if found_no == target_inv_clean:
                dpp_val = 0.0
                ppn_val = 0.0
                total_val = 0.0
                management_fee_val = 0.0
                add_cost_val = 0.0
                
                for k, v in inv.items():
                    k_low = str(k).lower()
                    v_str = str(v).lower()
                    # Deteksi khusus Management Fee / Handling Fee
                    if any(term in k_low or term in v_str for term in ["management fee", "handling fee", "fee ("]):
                        val_fee = parse_harga_presisi(v)
                        if val_fee > 0:
                            management_fee_val = val_fee
                    if any(term in k_low or term in v_str for term in ["add cost", "add-cost", "pengiriman"]):
                        val_ac = parse_harga_presisi(v)
                        if val_ac > 0:
                            add_cost_val = val_ac

                for k, v in inv.items():
                    k_low = str(k).lower()
                    if any(kata in k_low for kata in ["dpp", "gross", "bruto", "nilai invoice"]):
                        val_p = parse_harga_presisi(v)
                        if val_p > dpp_val:
                            dpp_val = val_p
                            
                for k, v in inv.items():
                    k_low = str(k).lower()
                    if "ppn" in k_low and "wapu" not in k_low:
                        val_p = parse_harga_presisi(v)
                        if val_p > ppn_val:
                            ppn_val = val_p

                for k, v in inv.items():
                    k_low = str(k).lower()
                    if any(kata in k_low for kata in ["netto", "grand", "total netto", "total tagihan", "total amount"]):
                        val_p = parse_harga_presisi(v)
                        if val_p > total_val:
                            total_val = val_p

                if total_val == 0.0:
                    total_val = dpp_val + ppn_val
                elif dpp_val == 0.0 and total_val > 0:
                    dpp_val = total_val / 1.11 if ppn_val > 0 else total_val
                    if ppn_val == 0.0:
                        ppn_val = total_val - dpp_val

                # Jika ada management fee terdeteksi, jadikan basis khusus PPh
                basis_pph_dpp = management_fee_val if management_fee_val > 0 else dpp_val

                return {
                    "dpp": dpp_val,
                    "ppn": ppn_val,
                    "total_tagihan": total_val,
                    "management_fee": management_fee_val,
                    "add_cost": add_cost_val,
                    "basis_pph": basis_pph_dpp,
                    "is_management_fee": management_fee_val > 0
                }
        return {"dpp": 0.0, "ppn": 0.0, "total_tagihan": 0.0, "management_fee": 0.0, "add_cost": 0.0, "basis_pph": 0.0, "is_management_fee": False}

    EXCEL_PAYMENT_STATUS = os.path.join(DIR_DATABASE, "database_status_pembayaran.xlsx")

    def muat_status_pembayaran():
        if os.path.exists(EXCEL_PAYMENT_STATUS):
            try:
                df = pd.read_excel(EXCEL_PAYMENT_STATUS)
                if df is not None and not df.empty:
                    records = df.to_dict(orient="records")
                    for r in records:
                        inv_no = r.get("Nomor Invoice", "")
                        dtl = ambil_detail_invoice_master(inv_no)
                        if dtl["total_tagihan"] > 0:
                            r["Grand Total"] = dtl["total_tagihan"]
                            r["Nilai DPP"] = dtl["dpp"]
                            r["Nilai PPN"] = dtl["ppn"]
                        else:
                            r["Grand Total"] = parse_harga_presisi(r.get("Grand Total", 0.0))
                            r["Nilai DPP"] = parse_harga_presisi(r.get("Nilai DPP", r["Grand Total"] / 1.11))
                            r["Nilai PPN"] = parse_harga_presisi(r.get("Nilai PPN", r["Grand Total"] - r["Nilai DPP"]))
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

    def ambil_tanggal_invoice(inv_data_obj):
        for k, v in inv_data_obj.items():
            if any(kata in str(k).lower() for kata in ["tgl", "tanggal", "date"]) and not any(kata in str(k).lower() for kata in ["penyerahan", "tempo", "lunas"]):
                if pd.notnull(v) and str(v).strip() != "":
                    return str(v)[:10]
        return str(date.today())

    # --- 2. MASTER PLAFON KONTRAK ---
    master_kontrak_plafon_dpp = {
        "7201250141": 42997282428.98,
        "7207250142": 38711901661.00,
        "7203250036": 1971459000.00
    }
    master_kontrak_plafon_inc_ppn = {
        k: v * 1.11 for k, v in master_kontrak_plafon_dpp.items()
    }

    kontrak_from_invoice = []
    for inv in invoice_list:
        val_k = str(inv.get(col_key_kontrak, inv.get("Kontrak No.", inv.get("Nomor Kontrak", "-")))).strip()
        if val_k and val_k != '-' and val_k.lower() != 'nan':
            clean_k = val_k.replace(".0", "")
            kontrak_from_invoice.append(clean_k)

    kontrak_from_payment = [str(p.get("Nomor Kontrak", "-")).strip().replace(".0", "") for p in payment_records if p.get("Nomor Kontrak")]
    
    all_contracts = sorted(list(dict.fromkeys([k for k in (kontrak_from_invoice + kontrak_from_payment + list(master_kontrak_plafon_dpp.keys())) if k and k != '-' and k.lower() != 'nan'])))

    # --- 3. FILTER DASHBOARD UTAMA DENGAN OPSI ALL CONTRACT ---
    st.markdown("---")
    st.markdown("##### 🔍 Filter Tampilan & Rekapitulasi Berdasarkan Kontrak")
    placeholder_kontrak_filter = "... Pilih Nomor Kontrak ..."
    opsi_filter_kontrak = [placeholder_kontrak_filter, "-- Semua Nomor Kontrak (ALL) --"] + all_contracts
    filter_kontrak_pilih = st.selectbox("Pilih Nomor Kontrak untuk Filter Dashboard:", opsi_filter_kontrak, key="filter_kontrak_dashboard")

    if filter_kontrak_pilih == placeholder_kontrak_filter:
        st.info("ℹ️ Silakan pilih **Nomor Kontrak** atau opsi **-- Semua Nomor Kontrak (ALL) --** di atas untuk melihat rekapitulasi dan form pemantauan pembayaran.")
        return

    if filter_kontrak_pilih != "-- Semua Nomor Kontrak (ALL) --":
        filtered_invoice_list = []
        for inv in invoice_list:
            c_val = str(inv.get(col_key_kontrak, inv.get("Kontrak No.", inv.get("Nomor Kontrak", "-")))).strip().replace(".0", "")
            if c_val == str(filter_kontrak_pilih).strip() or str(filter_kontrak_pilih).strip() in c_val:
                filtered_invoice_list.append(inv)
        filtered_payment_records = [p for p in payment_records if str(p.get("Nomor Kontrak", "")).strip().replace(".0", "") == str(filter_kontrak_pilih).strip()]
    else:
        filtered_invoice_list = invoice_list
        filtered_payment_records = payment_records

    # --- 4. REKAPITULASI KEUANGAN & PEMANTAUAN AGING ---
    if invoice_list or payment_records or master_kontrak_plafon_dpp:
        hari_ini = date.today()
        
        plafon_dpp_aktif = 0.0
        plafon_inc_ppn_aktif = 0.0
        
        if filter_kontrak_pilih != "-- Semua Nomor Kontrak (ALL) --":
            plafon_dpp_aktif = master_kontrak_plafon_dpp.get(str(filter_kontrak_pilih).strip(), 0.0)
            plafon_inc_ppn_aktif = master_kontrak_plafon_inc_ppn.get(str(filter_kontrak_pilih).strip(), 0.0)
        else:
            plafon_dpp_aktif = sum(master_kontrak_plafon_dpp.values())
            plafon_inc_ppn_aktif = sum(master_kontrak_plafon_inc_ppn.values())

        total_seluruh_tagihan_inc_ppn = 0.0
        total_pembayaran_netto_bank = 0.0
        total_potongan_pajak_all = 0.0

        jml_aman = 0; val_aman = 0.0
        jml_warning = 0; val_warning = 0.0
        jml_overdue = 0; val_overdue = 0.0
        jml_lunas = 0; val_lunas = 0.0

        target_eval_list = filtered_invoice_list if filtered_invoice_list else filtered_payment_records

        for inv_item in target_eval_list:
            inv_no_val = str(inv_item.get(col_key_inv, inv_item.get("Nomor Invoice Resmi", ""))).strip()
            dtl = ambil_detail_invoice_master(inv_no_val)
            g_total_inc_ppn = dtl["total_tagihan"]
            
            if g_total_inc_ppn == 0.0:
                matching_pay = next((p for p in payment_records if str(p.get("Nomor Invoice", "")).strip() == inv_no_val), {})
                g_total_inc_ppn = float(matching_pay.get("Grand Total", 0.0))

            total_seluruh_tagihan_inc_ppn += g_total_inc_ppn
            
            matching_pay = next((p for p in payment_records if str(p.get("Nomor Invoice", "")).strip() == inv_no_val), {})
            status_byr = matching_pay.get("Status Pembayaran", "Belum Dibayar")
            
            bayar_aktual = float(matching_pay.get("Nominal Pembayaran Aktual", g_total_inc_ppn if status_byr == "Dibayar" else 0.0))
            pot_pph = float(matching_pay.get("Potongan PPh", 0.0))
            pot_ppn_wapu = float(matching_pay.get("Potongan PPN WAPU", 0.0))
            
            total_pembayaran_netto_bank += bayar_aktual
            total_potongan_pajak_all += (pot_pph + pot_ppn_wapu)

            if status_byr == "Dibayar" or (bayar_aktual + pot_pph + pot_ppn_wapu) >= (g_total_inc_ppn - 100):
                jml_lunas += 1
                val_lunas += g_total_inc_ppn
                continue

            try:
                dt_jt_source = matching_pay.get("Tanggal Jatuh Tempo", "")
                if not dt_jt_source:
                    dt_jt_source = inv_item.get("Tanggal Jatuh Tempo", str(date.today()))
                dt_jt = datetime.strptime(str(dt_jt_source)[:10], "%Y-%m-%d").date()
                selisih_hari = (hari_ini - dt_jt).days
                
                if selisih_hari > 0:
                    jml_overdue += 1
                    val_overdue += (g_total_inc_ppn - bayar_aktual)
                elif selisih_hari >= -7:
                    jml_warning += 1
                    val_warning += (g_total_inc_ppn - bayar_aktual)
                else:
                    jml_aman += 1
                    val_aman += (g_total_inc_ppn - bayar_aktual)
            except:
                jml_aman += 1
                val_aman += (g_total_inc_ppn - bayar_aktual)

        total_pengakuan_efektif = total_pembayaran_netto_bank + total_potongan_pajak_all
        sisa_piutang_usaha_inc_ppn = total_seluruh_tagihan_inc_ppn - total_pengakuan_efektif
        
        persen_pembayaran_realisasi = (total_pengakuan_efektif / total_seluruh_tagihan_inc_ppn * 100) if total_seluruh_tagihan_inc_ppn > 0 else 0.0
        persen_sisa_piutang = (sisa_piutang_usaha_inc_ppn / total_seluruh_tagihan_inc_ppn * 100) if total_seluruh_tagihan_inc_ppn > 0 else 0.0

        st.markdown("---")
        st.markdown(f"##### 💰 Rekapitulasi Saldo Keuangan & Tagihan ({filter_kontrak_pilih})")
        
        c_fin0, c_fin1, c_fin2, c_fin3 = st.columns(4)
        with c_fin0:
            st.markdown(f"""
                <div style="background-color: #1e293b; color: white; padding: 16px; border-radius: 8px; text-align: center; border-left: 5px solid #6366f1;">
                    <p style="margin: 0; font-size: 11px; color: #94a3b8; font-weight: 600;">TOTAL KONTRAK (PLAFON INC. PPN)</p>
                    <h3 style="margin: 4px 0 0 0; font-size: 15px; color: #ffffff;">{fmt_rp_satu_baris(plafon_inc_ppn_aktif)}</h3>
                    <p style="margin: 4px 0 0 0; font-size: 10px; color: #818cf8;">DPP: {fmt_rp(plafon_dpp_aktif)}</p>
                </div>
            """, unsafe_allow_html=True)
        with c_fin1:
            st.markdown(f"""
                <div style="background-color: #1e293b; color: white; padding: 16px; border-radius: 8px; text-align: center; border-left: 5px solid #38bdf8;">
                    <p style="margin: 0; font-size: 11px; color: #94a3b8; font-weight: 600;">TOTAL TAGIHAN (INC. PPN)</p>
                    <h3 style="margin: 6px 0 0 0; font-size: 16px; color: #ffffff;">{fmt_rp_satu_baris(total_seluruh_tagihan_inc_ppn)}</h3>
                    <p style="margin: 4px 0 0 0; font-size: 11px; color: #38bdf8;">100.00% dari Tagihan</p>
                </div>
            """, unsafe_allow_html=True)
        with c_fin2:
            st.markdown(f"""
                <div style="background-color: #1e293b; color: white; padding: 16px; border-radius: 8px; text-align: center; border-left: 5px solid #10b981;">
                    <p style="margin: 0; font-size: 11px; color: #94a3b8; font-weight: 600;">TOTAL SUDAH DIBAYARKAN</p>
                    <h3 style="margin: 6px 0 0 0; font-size: 16px; color: #34d399;">{fmt_rp_satu_baris(total_pembayaran_netto_bank)}</h3>
                    <p style="margin: 4px 0 0 0; font-size: 11px; color: #34d399;">{persen_pembayaran_realisasi:.2f}% (Realisasi)</p>
                </div>
            """, unsafe_allow_html=True)
        with c_fin3:
            st.markdown(f"""
                <div style="background-color: #1e293b; color: white; padding: 16px; border-radius: 8px; text-align: center; border-left: 5px solid #f59e0b;">
                    <p style="margin: 0; font-size: 11px; color: #94a3b8; font-weight: 600;">SISA BELUM TERBAYAR</p>
                    <h3 style="margin: 6px 0 0 0; font-size: 16px; color: #fbbf24;">{fmt_rp_satu_baris(sisa_piutang_usaha_inc_ppn)}</h3>
                    <p style="margin: 4px 0 0 0; font-size: 11px; color: #fbbf24;">{persen_sisa_piutang:.2f}% (Piutang Usaha)</p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### ⏱️ Status Pemantauan Aging Invoice & Tanggal Jatuh Tempo")
        
        c_ag1, c_ag2, c_ag3, c_ag4 = st.columns(4)
        with c_ag1:
            st.markdown(f"""
                <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 12px; border-radius: 6px; text-align: center;">
                    <span style="font-size: 12px; color: #475569; font-weight: bold;">🟢 Peredaran Aman</span>
                    <h4 style="margin: 4px 0 0 0; color: #0f172a;">{jml_aman} Invoice</h4>
                    <p style="margin: 2px 0 0 0; font-size: 11px; color: #64748b;">{fmt_rp(val_aman)}</p>
                </div>
            """, unsafe_allow_html=True)
        with c_ag2:
            st.markdown(f"""
                <div style="background-color: #fffbeb; border: 1px solid #fde68a; padding: 12px; border-radius: 6px; text-align: center;">
                    <span style="font-size: 12px; color: #b45309; font-weight: bold;">🟡 Warning (≤7 Hari)</span>
                    <h4 style="margin: 4px 0 0 0; color: #92400e;">{jml_warning} Invoice</h4>
                    <p style="margin: 2px 0 0 0; font-size: 11px; color: #b45309;">{fmt_rp(val_warning)}</p>
                </div>
            """, unsafe_allow_html=True)
        with c_ag3:
            st.markdown(f"""
                <div style="background-color: #fef2f2; border: 1px solid #fecaca; padding: 12px; border-radius: 6px; text-align: center;">
                    <span style="font-size: 12px; color: #dc2626; font-weight: bold;">🔴 Overdue (Jatuh Tempo)</span>
                    <h4 style="margin: 4px 0 0 0; color: #991b1b;">{jml_overdue} Invoice</h4>
                    <p style="margin: 2px 0 0 0; font-size: 11px; color: #dc2626;">{fmt_rp(val_overdue)}</p>
                </div>
            """, unsafe_allow_html=True)
        with c_ag4:
            st.markdown(f"""
                <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 12px; border-radius: 6px; text-align: center;">
                    <span style="font-size: 12px; color: #15803d; font-weight: bold;">✅ Dibayar</span>
                    <h4 style="margin: 4px 0 0 0; color: #166534;">{jml_lunas} Invoice</h4>
                    <p style="margin: 2px 0 0 0; font-size: 11px; color: #15803d;">{fmt_rp(val_lunas)}</p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("<h6>📊 Grafik Nominal Piutang per Status Aging</h6>", unsafe_allow_html=True)
            df_chart_bar = pd.DataFrame({
                "Status Aging": ["Aman", "Warning (7d)", "Overdue", "Dibayar"],
                "Nominal (Rp)": [val_aman, val_warning, val_overdue, val_lunas]
            })
            st.bar_chart(df_chart_bar.set_index("Status Aging"))

        with col_g2:
            st.markdown("<h6>🍩 Proporsi Jumlah Dokumen Invoice</h6>", unsafe_allow_html=True)
            df_chart_pie = pd.DataFrame({
                "Kategori": ["Aman", "Warning", "Overdue", "Dibayar"],
                "Jumlah Dokumen": [jml_aman, jml_warning, jml_overdue, jml_lunas]
            })
            st.dataframe(df_chart_pie, use_container_width=True, hide_index=True)

        # --- 5. TABEL RINCIAN AKUMULASI PER KONTRAK ---
        st.markdown("---")
        st.markdown("##### 📑 Rincian Akumulasi Tagihan per Nomor Kontrak (Dekomposisi DPP & Inc. PPN)")
        
        summary_contract_map = {}
        for k_m in all_contracts:
            summary_contract_map[k_m] = {"dpp": 0.0, "ppn": 0.0, "tagihan_inc_ppn": 0.0, "terbayar_bank": 0.0, "potongan_pajak": 0.0, "jml_inv": 0, "lunas": 0}

        for item_rc in invoice_list:
            c_no = str(item_rc.get(col_key_kontrak, item_rc.get("Kontrak No.", item_rc.get("Nomor Kontrak", "-")))).strip().replace(".0", "")
            inv_no_rc = str(item_rc.get(col_key_inv, item_rc.get("Nomor Invoice Resmi", ""))).strip()
            
            dtl_rc = ambil_detail_invoice_master(inv_no_rc)
            t_dpp = dtl_rc["dpp"]
            t_ppn = dtl_rc["ppn"]
            t_inc = dtl_rc["total_tagihan"]

            matching_pay_rc = next((p for p in payment_records if str(p.get("Nomor Invoice", "")).strip() == inv_no_rc), {})
            st_byr = matching_pay_rc.get("Status Pembayaran", "Belum Dibayar")
            b_akt = float(matching_pay_rc.get("Nominal Pembayaran Aktual", t_inc if st_byr == "Dibayar" else 0.0))
            p_pph = float(matching_pay_rc.get("Potongan PPh", 0.0))
            p_wapu = float(matching_pay_rc.get("Potongan PPN WAPU", 0.0))
            
            if c_no not in summary_contract_map:
                summary_contract_map[c_no] = {"dpp": 0.0, "ppn": 0.0, "tagihan_inc_ppn": 0.0, "terbayar_bank": 0.0, "potongan_pajak": 0.0, "jml_inv": 0, "lunas": 0}
            
            summary_contract_map[c_no]["dpp"] += t_dpp
            summary_contract_map[c_no]["ppn"] += t_ppn
            summary_contract_map[c_no]["tagihan_inc_ppn"] += t_inc
            summary_contract_map[c_no]["jml_inv"] += 1
            summary_contract_map[c_no]["terbayar_bank"] += b_akt
            summary_contract_map[c_no]["potongan_pajak"] += (p_pph + p_wapu)

            if st_byr == "Dibayar" or (b_akt + p_pph + p_wapu) >= (t_inc - 100):
                summary_contract_map[c_no]["lunas"] += 1

        table_data_list = []
        tot_dpp_contr = 0.0
        tot_inc_ppn_contr = 0.0
        tot_sum_tag_inc = 0.0
        tot_sum_byr_bank = 0.0
        tot_sum_sisa_plafon = 0.0
        tot_sum_piu_inc = 0.0
        tot_dok = 0

        for c_key, c_val in summary_contract_map.items():
            plafon_dpp_k = master_kontrak_plafon_dpp.get(c_key, 0.0)
            plafon_inc_ppn_k = master_kontrak_plafon_inc_ppn.get(c_key, 0.0)
            
            tag_inc_k = c_val["tagihan_inc_ppn"]
            byr_bank_k = c_val["terbayar_bank"]
            pot_pajak_k = c_val["potongan_pajak"]
            pengakuan_total_k = byr_bank_k + pot_pajak_k
            
            sisa_plafon_k = plafon_inc_ppn_k - tag_inc_k
            sisa_piutang_k = tag_inc_k - pengakuan_total_k
            pct_real_k = (tag_inc_k / plafon_inc_ppn_k * 100) if plafon_inc_ppn_k > 0 else 0.0

            tot_dpp_contr += plafon_dpp_k
            tot_inc_ppn_contr += plafon_inc_ppn_k
            tot_sum_tag_inc += tag_inc_k
            tot_sum_byr_bank += byr_bank_k
            tot_sum_sisa_plafon += sisa_plafon_k
            tot_sum_piu_inc += sisa_piutang_k
            tot_dok += c_val["jml_inv"]

            st_teks = "🟢 Selesai" if (c_val["jml_inv"] > 0 and c_val["lunas"] == c_val["jml_inv"]) else (f"🟡 {c_val['lunas']}/{c_val['jml_inv']} Dibayar" if c_val["jml_inv"] > 0 else "⚪ Belum Ada Transaksi")

            table_data_list.append({
                "Nomor Kontrak": c_key,
                "Jml Dok": f"{c_val['jml_inv']} Dok",
                "Nilai Kontrak (DPP)": fmt_rp(plafon_dpp_k),
                "Nilai Kontrak (Inc. PPN)": fmt_rp(plafon_inc_ppn_k),
                "Total Tagihan (Inc. PPN)": fmt_rp(tag_inc_k),
                "Sudah Dibayar (Bank)": fmt_rp(byr_bank_k),
                "Sisa Plafon (Inc. PPN)": fmt_rp(sisa_plafon_k),
                "Sisa Piutang (Inc. PPN)": fmt_rp(sisa_piutang_k),
                "Realisasi Plafon": f"{pct_real_k:.2f}%",
                "Status": st_teks
            })

        tot_pct_overall = (tot_sum_tag_inc / tot_inc_ppn_contr * 100) if tot_inc_ppn_contr > 0 else 0.0
        table_data_list.append({
            "Nomor Kontrak": "TOTAL KESELURUHAN",
            "Jml Dok": f"{tot_dok} Dok",
            "Nilai Kontrak (DPP)": fmt_rp(tot_dpp_contr),
            "Nilai Kontrak (Inc. PPN)": fmt_rp(tot_inc_ppn_contr),
            "Total Tagihan (Inc. PPN)": fmt_rp(tot_sum_tag_inc),
            "Sudah Dibayar (Bank)": fmt_rp(tot_sum_byr_bank),
            "Sisa Plafon (Inc. PPN)": fmt_rp(tot_sum_sisa_plafon),
            "Sisa Piutang (Inc. PPN)": fmt_rp(tot_sum_piu_inc),
            "Realisasi Plafon": f"{tot_pct_overall:.2f}%",
            "Status": "100%"
        })

        df_rincian_view = pd.DataFrame(table_data_list)
        st.dataframe(df_rincian_view, use_container_width=True, hide_index=True)

    # --- 6. FORM INPUT & PEMBARUAN STATUS PEMBAYARAN ---
    st.markdown("---")
    st.markdown("##### 📝 Form Input & Pembaruan Status Pembayaran (Berdasarkan Kontrak)")

    col_fc1, col_fc2 = st.columns([1.5, 2.5])
    with col_fc1:
        placeholder_form_kontrak = "... Pilih Nomor Kontrak ..."
        opsi_form_kontrak = [placeholder_form_kontrak] + all_contracts
        form_kontrak_pilih = st.selectbox("1️⃣ Pilih Nomor Kontrak:", opsi_form_kontrak, key="form_input_kontrak_sel")

    if form_kontrak_pilih == placeholder_form_kontrak:
        st.info("ℹ️ Silakan pilih **Nomor Kontrak** pada pilihan nomor 1 di atas untuk memunculkan daftar nomor invoice resmi dari Modul 3.")
        return

    inv_list_filtered_contract = []
    for inv in invoice_list:
        c_val_inv = str(inv.get(col_key_kontrak, inv.get("Kontrak No.", inv.get("Nomor Kontrak", "-")))).strip().replace(".0", "")
        if c_val_inv == str(form_kontrak_pilih).strip() or str(form_kontrak_pilih).strip() in c_val_inv:
            inv_list_filtered_contract.append(inv)

    all_inv_no_contract = []
    for inv in inv_list_filtered_contract:
        val_inv = str(inv.get(col_key_inv, inv.get("Nomor Invoice Resmi", ""))).strip()
        # Validasi ketat untuk menghindari data kosong, nan, atau stempel waktu (timestamp)
        if (val_inv and val_inv != 'nan' and len(val_inv) > 1 and 
            val_inv != str(form_kontrak_pilih).strip() and 
            not re.match(r'^\d{4}-\d{2}-\d{2}', val_inv)):
            
            all_inv_no_contract.append(val_inv)

    all_inv_no_contract = list(dict.fromkeys(all_inv_no_contract))

    saved_invoice_set = {str(p.get("Nomor Invoice", "")).strip() for p in payment_records if str(p.get("Nomor Kontrak", "")).strip().replace(".0", "") == str(form_kontrak_pilih).strip() and p.get("Nomor Invoice")}

    list_saved_payment_no = sorted(list({str(p.get("Nomor Invoice")) for p in payment_records if str(p.get("Nomor Kontrak", "")).strip().replace(".0", "") == str(form_kontrak_pilih).strip()}), reverse=True)
    opsi_panggil_bayar = ["-- Pilih Data Tersimpan untuk Diedit / Panggil Ulang --"] + list_saved_payment_no

    with col_fc2:
        pilihan_panggil_bayar = st.selectbox("2️⃣ Panggil Ulang Data Pemantauan Tersimpan (Kontrak Terpilih):", opsi_panggil_bayar, key="select_panggil_bayar")
        if st.button("📥 Panggil untuk Diedit", use_container_width=True):
            if pilihan_panggil_bayar != "-- Pilih Data Tersimpan untuk Diedit / Panggil Ulang --":
                st.session_state["active_invoice_selected"] = str(pilihan_panggil_bayar).strip()
                st.success(f"📋 Memuat data pemantauan Invoice `{pilihan_panggil_bayar}`")
                st.rerun()

    active_edit_inv = str(st.session_state.get("active_invoice_selected", "")).strip()

    list_inv_aktif = [inv_no for inv_no in all_inv_no_contract if inv_no not in saved_invoice_set or inv_no == active_edit_inv]
    if not list_inv_aktif and active_edit_inv:
        list_inv_aktif = [active_edit_inv]

    placeholder_pilih_inv = "... Pilih Nomor Invoice Resmi ..."
    opsi_dropdown_invoice = [placeholder_pilih_inv] + list_inv_aktif

    col_inv_drop, col_inv_info = st.columns([2, 2])
    with col_inv_drop:
        default_idx = 0
        if active_edit_inv in opsi_dropdown_invoice:
            default_idx = opsi_dropdown_invoice.index(active_edit_inv)
            
        selected_inv = st.selectbox("3️⃣ Pilih Nomor Invoice Resmi Aktif:", opsi_dropdown_invoice, index=default_idx, key="dropdown_master_invoice_aktif")

    if selected_inv and selected_inv != placeholder_pilih_inv and "- (" not in selected_inv:
        inv_data = next((inv for inv in invoice_list if str(inv.get(col_key_inv, inv.get("Nomor Invoice Resmi", ""))).strip() == str(selected_inv)), {})
        existing_pay = next((p for p in payment_records if str(p.get("Nomor Invoice", "")).strip() == str(selected_inv)), {})

        tgl_invoice_bawaan = ambil_tanggal_invoice(inv_data) if inv_data else str(existing_pay.get("Tanggal Invoice", date.today()))[:10]
        
        dtl_inv_selected = ambil_detail_invoice_master(selected_inv)
        dpp_otomatis = dtl_inv_selected["dpp"]
        ppn_otomatis = dtl_inv_selected["ppn"]
        total_tagihan_inc_ppn = dtl_inv_selected["total_tagihan"]
        management_fee_val = dtl_inv_selected["management_fee"]
        add_cost_val = dtl_inv_selected["add_cost"]
        basis_pph_val = dtl_inv_selected["basis_pph"]
        is_mgmt_fee = dtl_inv_selected["is_management_fee"]
        
        if total_tagihan_inc_ppn == 0.0 and existing_pay:
            total_tagihan_inc_ppn = float(existing_pay.get("Grand Total", 0.0))
            dpp_otomatis = float(existing_pay.get("Nilai DPP", total_tagihan_inc_ppn / 1.11))
            ppn_otomatis = float(existing_pay.get("Nilai PPN", total_tagihan_inc_ppn - dpp_otomatis))

        nomor_pi_val = str(inv_data.get(col_key_pi, inv_data.get("PI No.", inv_data.get("Nomor PI", "-")))).strip() if inv_data else "-"

        with col_inv_info:
            info_kategori_teks = f"• <b>Kategori:</b> Management Fee / Add Cost (Fee: {fmt_rp(management_fee_val)})<br>" if is_mgmt_fee else "• <b>Kategori:</b> Standar / Penawaran Biasa<br>"
            st.markdown(f"""
                <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 10px; border-radius: 6px; font-size: 12px; margin-top: 22px;">
                    <b>📈 Rincian Performa Invoice Terpilih:</b><br>
                    {info_kategori_teks}
                    • DPP Utama: <code>{fmt_rp(dpp_otomatis)}</code><br>
                    • Basis PPh: <code>{fmt_rp(basis_pph_val)}</code><br>
                    • PPN (11%): <code>{fmt_rp(ppn_otomatis)}</code><br>
                    • <b>Total Tagihan (Inc. PPN):</b> <span style="color: #0284c7; font-weight: bold;">{fmt_rp(total_tagihan_inc_ppn)}</span>
                </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
            <div style="background-color: #f1f5f9; border: 1px solid #cbd5e1; padding: 15px; border-radius: 8px; margin-top: 15px; margin-bottom: 15px;">
                <h5 style="margin: 0 0 8px 0; color: #0f172a;">📄 Pengakuan Piutang Usaha Resmi (Invoice Inc. PPN):</h5>
                <div style="display: flex; gap: 20px; flex-wrap: wrap; font-size: 13px;">
                    <span>📌 <b>Nomor Kontrak:</b> <code>{form_kontrak_pilih}</code></span>
                    <span>📑 <b>Nomor Invoice Resmi:</b> <code>{selected_inv}</code></span>
                    <span>📋 <b>Nomor PI:</b> <code>{nomor_pi_val}</code></span>
                    <span>📅 <b>Tanggal Invoice:</b> <code>{tgl_invoice_bawaan}</code></span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        status_opsi = ["Belum Dibayar", "Dibayar"]
        def_status = existing_pay.get("Status Pembayaran", "Belum Dibayar")
        if def_status not in status_opsi:
            def_status = "Dibayar" if "Lunas" in def_status or "Dibayar" in def_status else "Belum Dibayar"
        idx_st = status_opsi.index(def_status) if def_status in status_opsi else 0
        status_pembayaran = st.selectbox("Status Pembayaran:", status_opsi, index=idx_st, key="select_status_pembayaran_live")

        default_faktur = existing_pay.get("Nomor Faktur Pajak", "")
        nomor_faktur_pajak = st.text_input("Nomor Faktur Pajak (Diterbitkan setelah Invoice):", value=str(default_faktur), key="input_faktur_pajak")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            default_tgl_serah = datetime.today().date()
            if existing_pay.get("Tanggal Penyerahan"):
                try:
                    default_tgl_serah = datetime.strptime(str(existing_pay.get("Tanggal Penyerahan"))[:10], "%Y-%m-%d").date()
                except:
                    pass
            tgl_penyerahan = st.date_input("Tanggal Invoice Diserahkan ke Klien:", value=default_tgl_serah, key="input_tgl_serah")

            default_top = int(existing_pay.get("TOP Hari", 30))
            top_hari = st.number_input("Term of Payment (TOP dalam Hari):", min_value=0, value=default_top, step=5, key="input_top_hari")

        with col_p2:
            raw_tgl_lunas_exist = str(existing_pay.get("Tanggal Pelunasan", "-"))
            ada_tgl_lunas_exist = (raw_tgl_lunas_exist != "-" and raw_tgl_lunas_exist.strip() != "")

            if status_pembayaran == "Dibayar":
                default_tgl_lunas = datetime.today().date()
                if ada_tgl_lunas_exist:
                    try:
                        default_tgl_lunas = datetime.strptime(raw_tgl_lunas_exist[:10], "%Y-%m-%d").date()
                    except:
                        pass
                tgl_pelunasan = st.date_input("Tanggal Pelunasan / Pembayaran Aktual:", value=default_tgl_lunas, key="input_tgl_lunas")
            else:
                st.markdown("📅 Tanggal Pelunasan Aktual: **... (Belum Ada Pembayaran / Kosong)**")
                tgl_pelunasan = None

        st.markdown("---")
        st.markdown("##### 💵 Rincian Potongan Pajak & Penerimaan Kas/Bank (Deteksi Otomatis Management Fee)")

        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            opsi_tarif_pph = ["Tanpa PPh / 0%", "1%", "1.5%", "1.75%", "2%", "2.5%", "3%", "4%", "Custom (Manual)"]
            selected_tarif_pph = st.selectbox("Pilih Tarif PPh (Otomatis membaca Management Fee / DPP):", opsi_tarif_pph, index=4, key="select_tarif_pph_auto")
        
        calculated_auto_pph = 0.0
        if selected_tarif_pph == "1%":
            calculated_auto_pph = basis_pph_val * 0.01
        elif selected_tarif_pph == "1.5%":
            calculated_auto_pph = basis_pph_val * 0.015
        elif selected_tarif_pph == "1.75%":
            calculated_auto_pph = basis_pph_val * 0.0175
        elif selected_tarif_pph == "2%":
            calculated_auto_pph = basis_pph_val * 0.02
        elif selected_tarif_pph == "2.5%":
            calculated_auto_pph = basis_pph_val * 0.025
        elif selected_tarif_pph == "3%":
            calculated_auto_pph = basis_pph_val * 0.03
        elif selected_tarif_pph == "4%":
            calculated_auto_pph = basis_pph_val * 0.04
        else:
            calculated_auto_pph = float(existing_pay.get("Potongan PPh", 0.0))

        with col_opt2:
            st.markdown(f"<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("⚡ Terapkan PPh & PPN WAPU Otomatis", use_container_width=True):
                st.session_state["val_pph_auto_set"] = calculated_auto_pph
                st.session_state["val_wapu_auto_set"] = ppn_otomatis
                st.rerun()

        if "val_pph_auto_set" in st.session_state:
            default_pot_pph = float(st.session_state.pop("val_pph_auto_set"))
        else:
            default_pot_pph = float(existing_pay.get("Potongan PPh", calculated_auto_pph if selected_tarif_pph != "Custom (Manual)" else 0.0))

        if "val_wapu_auto_set" in st.session_state:
            default_pot_wapu = float(st.session_state.pop("val_wapu_auto_set"))
        else:
            default_pot_wapu = float(existing_pay.get("Potongan PPN WAPU", ppn_otomatis))

        col_pp1, col_pp2 = st.columns(2)
        with col_pp1:
            potongan_pph = st.number_input("Potongan PPh (Pasal 23 / 22 - Otomatis dari Fee/DPP atau Manual):", min_value=0.0, value=default_pot_pph, step=1000.0, key="input_pot_pph")

        with col_pp2:
            potongan_ppn_wapu = st.number_input("Potongan PPN WAPU (Otomatis dari PPN Tagihan):", min_value=0.0, value=default_pot_wapu, step=1000.0, key="input_pot_wapu")

        nominal_bank_seharusnya = max(0.0, total_tagihan_inc_ppn - potongan_pph - potongan_ppn_wapu)
        st.markdown(f"💡 **Nilai Bersih Seharusnya Diterima Bank (Otomatis):** `{fmt_rp(nominal_bank_seharusnya)}` *(Total Tagihan - PPh - PPN WAPU)*")
        
        col_b1, col_b2 = st.columns([3, 1])
        with col_b2:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("⚡ Set Nilai Diterima Bank Otomatis", use_container_width=True):
                st.session_state["val_bayar_aktual_set"] = nominal_bank_seharusnya
                st.rerun()

        if "val_bayar_aktual_set" in st.session_state:
            default_bayar_akt = float(st.session_state.pop("val_bayar_aktual_set"))
        else:
            default_bayar_akt = float(existing_pay.get("Nominal Pembayaran Aktual", nominal_bank_seharusnya))

        with col_b1:
            nominal_pembayaran_aktual = st.number_input("Nominal Pembayaran Diterima (Input Manual Aktual Perbankan/Kas):", min_value=0.0, value=default_bayar_akt, step=1000.0, key="input_bayar_aktual")

        selisih_pembayaran = nominal_pembayaran_aktual - nominal_bank_seharusnya
        
        if abs(selisih_pembayaran) < 1.0:
            st.success(f"✅ Pembayaran diterima di Bank pas `{fmt_rp(nominal_pembayaran_aktual)}` (Tidak ada selisih).")
        else:
            st.markdown(f"""
                <div style="background-color: #fef2f2; border: 1px solid #fecaca; padding: 12px; border-radius: 6px; margin-top: 8px; margin-bottom: 8px;">
                    <span style="font-size: 13px; color: #dc2626; font-weight: bold;">⚠️ KOLOM INFORMASI SELISIH PEMBAYARAN:</span><br>
                    <span style="font-size: 15px; color: #991b1b; font-weight: bold;">Selisih Nominal: {fmt_rp(selisih_pembayaran)}</span> 
                    <i style="color: #64748b; font-size: 12px;">(Terjadi {'Kelebihan' if selisih_pembayaran > 0 else 'Kekurangan'} dari nilai seharusnya)</i>
                </div>
            """, unsafe_allow_html=True)

        default_catatan = str(existing_pay.get("Catatan", "Lengkap"))
        catatan_bayar = st.text_area("Catatan / Keterangan Pembayaran (Justifikasi Admin Bank / Selisih / Kekurangan / Lengkap):", value=default_catatan, key="input_catatan_bayar")

        if st.button("💾 Simpan Pemantauan Pembayaran", type="primary", use_container_width=True):
            tgl_jatuh_tempo = tgl_penyerahan + timedelta(days=int(top_hari))

            durasi_riil_hari = 0
            str_tgl_pelunasan_final = "-"
            if status_pembayaran == "Dibayar" and tgl_pelunasan:
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
                "Nilai DPP": dpp_otomatis,
                "Nilai PPN": ppn_otomatis,
                "Grand Total": total_tagihan_inc_ppn,
                "Nominal Pembayaran Aktual": nominal_pembayaran_aktual,
                "Potongan PPh": potongan_pph,
                "Potongan PPN WAPU": potongan_ppn_wapu,
                "Selisih Lainnya": selisih_pembayaran,
                "Status Pembayaran": status_pembayaran,
                "Catatan": catatan_bayar,
                "Update Terakhir": datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            }

            clean_records = [p for p in payment_records if str(p.get("Nomor Invoice", "")).strip() != str(selected_inv).strip()]
            clean_records.append(data_update)
            simpan_status_pembayaran(clean_records)
            st.success(f"🎉 Berhasil menyimpan data pemantauan untuk Invoice Resmi [{selected_inv}]! Total Piutang: {fmt_rp(total_tagihan_inc_ppn)} | Netto Bank: {fmt_rp(nominal_pembayaran_aktual)}")
            if "active_invoice_selected" in st.session_state:
                del st.session_state["active_invoice_selected"]
            st.rerun()
    else:
        st.info("ℹ️ Silakan pilih **Nomor Invoice Resmi Aktif** terlebih dahulu pada dropdown di atas untuk menampilkan form pengisian dan rincian performa invoice.")

    # --- 7. TABEL RINGKASAN & LAPORAN AGING INVOICE ---
    st.markdown("---")
    st.markdown(f"#### 📋 Ringkasan & Laporan Aging Invoice ({filter_kontrak_pilih})")

    current_payment_records = muat_status_pembayaran()
    if filter_kontrak_pilih != "-- Semua Nomor Kontrak (ALL) --":
        current_payment_records = [p for p in current_payment_records if str(p.get("Nomor Kontrak", "")).strip().replace(".0", "") == str(filter_kontrak_pilih).strip()]

    if current_payment_records:
        aging_data_list = []
        for row_p in current_payment_records:
            inv_num_row = row_p.get('Nomor Invoice', '-')
            cust_row = row_p.get('Customer', '-')
            no_kontrak_row = row_p.get('Nomor Kontrak', '-')
            
            tgl_penyerahan_str = str(row_p.get('Tanggal Penyerahan', ''))[:10]
            tgl_pelunasan_raw = str(row_p.get('Tanggal Pelunasan', '-'))
            tgl_pelunasan_str = tgl_pelunasan_raw[:10] if tgl_pelunasan_raw and tgl_pelunasan_raw != "-" else "-"

            top_hari_val = int(row_p.get('TOP Hari', 30))
            realisasi_hari_val = "-"
            deviasi_val = "-"
            
            if tgl_pelunasan_raw and tgl_pelunasan_raw != "-":
                try:
                    dt_serah = datetime.strptime(tgl_penyerahan_str, "%Y-%m-%d").date()
                    dt_lunas = datetime.strptime(tgl_pelunasan_raw[:10], "%Y-%m-%d").date()
                    r_hari = (dt_lunas - dt_serah).days
                    realisasi_hari_val = f"{r_hari} Hari"
                    deviasi_val = f"{r_hari - top_hari_val} Hari"
                except:
                    pass

            gt_val = float(row_p.get('Grand Total', 0))
            b_akt = float(row_p.get('Nominal Pembayaran Aktual', gt_val))
            p_pph = float(row_p.get('Potongan PPh', 0.0))
            p_wapu = float(row_p.get('Potongan PPN WAPU', 0.0))
            catatan_ket = str(row_p.get('Catatan', 'Lengkap'))

            aging_data_list.append({
                "No. Kontrak": no_kontrak_row,
                "No. Invoice Resmi": inv_num_row,
                "Customer": cust_row,
                "Tgl Inv": str(row_p.get('Tanggal Invoice', ''))[:10],
                "Tgl Serah": tgl_penyerahan_str,
                "TOP": f"{top_hari_val} Hari",
                "Realisasi": realisasi_hari_val,
                "Deviasi": deviasi_val,
                "Tgl JT": str(row_p.get('Tanggal Jatuh Tempo', ''))[:10],
                "Tgl Lunas": tgl_pelunasan_str,
                "Total Tagihan": fmt_rp(gt_val),
                "Potongan PPN": fmt_rp(p_wapu),
                "Potongan PPh": fmt_rp(p_pph),
                "Netto Diterima": fmt_rp(b_akt),
                "Status": row_p.get('Status Pembayaran', '-'),
                "Catatan Keterangan": catatan_ket
            })

        df_aging_view = pd.DataFrame(aging_data_list)
        st.dataframe(df_aging_view, use_container_width=True, hide_index=True)

        st.markdown("##### ⚙️ Aksi Cepat Data Pemantauan Invoice")
        for idx, row_p in enumerate(current_payment_records):
            inv_num_row = row_p.get('Nomor Invoice', '-')
            c_ak1, c_ak2 = st.columns([3, 1])
            with c_ak1:
                st.markdown(f"<small>Invoice Resmi: <b>{inv_num_row}</b> (Kontrak: {row_p.get('Nomor Kontrak', '-')})</small>", unsafe_allow_html=True)
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