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
            v = float(val)
            while v > 10_000_000_000:
                v /= 10.0
            return v
        
        s = str(val).strip()
        if not s or s.lower() == 'nan':
            return 0.0
        
        s = s.replace("Rp", "").replace(" ", "")
        
        if ',' in s:
            parts = s.split(',')
            integer_part = parts[0]
            decimal_part = parts[1] if len(parts) > 1 else '00'
            integer_digits = "".join(re.findall(r'\d+', integer_part))
            clean_str = f"{integer_digits}.{decimal_part[:2]}"
        elif '.' in s:
            parts = s.split('.')
            if len(parts) > 2:
                integer_digits = "".join(re.findall(r'\d+', s))
                clean_str = integer_digits
            elif len(parts) == 2 and len(parts[1]) <= 2:
                clean_str = s
            else:
                integer_digits = "".join(re.findall(r'\d+', s))
                clean_str = integer_digits
        else:
            integer_digits = "".join(re.findall(r'\d+', s))
            clean_str = integer_digits

        try:
            res = float(clean_str)
            if res > 5_000_000_000 and res < 50_000_000_000:
                res /= 10.0
            return res
        except:
            return 0.0

    def muat_invoice_resmi():
        if not os.path.exists(DIR_DATABASE):
            return []
        
        semua_file = os.listdir(DIR_DATABASE)
        kemungkinan_file = [
            os.path.join(DIR_DATABASE, f) for f in semua_file
            if f.endswith('.xlsx') and not f.startswith('~$')
        ]
        
        gabungan_invoice = []
        for file_path in kemungkinan_file:
            try:
                df = pd.read_excel(file_path)
                if df is not None and not df.empty:
                    gabungan_invoice.extend(df.to_dict(orient="records"))
            except:
                pass

        if gabungan_invoice:
            return gabungan_invoice

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

    invoice_list = muat_invoice_resmi()

    # --- KOREKSI PRESISI TINGGI: PENCARIAN KOLOM NOMOR INVOICE SEBENARNYA ---
    def cari_nama_kolom_invoice(sample_obj):
        if not sample_obj:
            return "Nomor Invoice"
        
        # Cari prioritas yang mengandung kata 'resmi' atau 'invoice'
        for k in sample_obj.keys():
            k_low = str(k).lower()
            if "resmi" in k_low or ("invoice" in k_low and "tanggal" not in k_low and "tgl" not in k_low):
                return k
                
        # Jika tidak ketemu, cari kolom string yang format isinya tidak menyerupai timestamp (YYYY-MM-DD)
        for k in sample_obj.keys():
            k_low = str(k).lower()
            if not any(exc in k_low for exc in ["waktu", "time", "date", "tanggal", "tgl", "timestamp", "update", "created"]):
                return k
                
        return list(sample_obj.keys())[0]

    sample_inv = invoice_list[0] if invoice_list else {}
    inv_key = cari_nama_kolom_invoice(sample_inv)

    def ambil_grand_total_invoice_master(inv_no):
        for inv in invoice_list:
            found_no = str(inv.get(inv_key, inv.get("Nomor Invoice Resmi", inv.get("Nomor Invoice", "")))).strip()
            if found_no == str(inv_no).strip():
                for k, v in inv.items():
                    if any(kata in str(k).lower() for kata in ["grand", "total", "jumlah", "tagihan", "nilai", "amount"]):
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
        st.warning("⚠️ Belum ada Data Invoice Resmi atau Status Pembayaran yang tersimpan di direktori.")
        return

    def ambil_tanggal_invoice(inv_data_obj):
        for k, v in inv_data_obj.items():
            if any(kata in str(k).lower() for kata in ["tgl", "tanggal", "date"]) and not any(kata in str(k).lower() for kata in ["penyerahan", "tempo", "lunas"]):
                if pd.notnull(v) and str(v).strip() != "":
                    return str(v)[:10]
        return str(date.today())

    # --- PENGUMPULAN DAFTAR KONTRAK ---
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

    # --- KARTU REKAPITULASI KEUANGAN UTAMA ---
    if invoice_list or payment_records:
        hari_ini = date.today()
        
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
        c_fin1, c_fin2, c_fin3 = st.columns(3)
        with c_fin1:
            st.markdown(f"""
                <div style="background-color: #1e293b; color: white; padding: 18px; border-radius: 8px; text-align: center; border-left: 5px solid #38bdf8;">
                    <p style="margin: 0; font-size: 13px; color: #94a3b8; font-weight: 600;">TOTAL SELURUH TAGIHAN</p>
                    <h3 style="margin: 6px 0 0 0; font-size: 19px; color: #ffffff;">{fmt_rp_satu_baris(total_seluruh_tagihan)}</h3>
                    <p style="margin: 4px 0 0 0; font-size: 11px; color: #38bdf8;">100.00% dari Total Portofolio</p>
                </div>
            """, unsafe_allow_html=True)
        with c_fin2:
            st.markdown(f"""
                <div style="background-color: #1e293b; color: white; padding: 18px; border-radius: 8px; text-align: center; border-left: 5px solid #10b981;">
                    <p style="margin: 0; font-size: 13px; color: #94a3b8; font-weight: 600;">TOTAL SUDAH DIBAYARKAN</p>
                    <h3 style="margin: 6px 0 0 0; font-size: 19px; color: #34d399;">{fmt_rp_satu_baris(total_sudah_dibayar)}</h3>
                    <p style="margin: 4px 0 0 0; font-size: 11px; color: #34d399;">{persen_dibayar:.2f}% (Rasio Realisasi)</p>
                </div>
            """, unsafe_allow_html=True)
        with c_fin3:
            st.markdown(f"""
                <div style="background-color: #1e293b; color: white; padding: 18px; border-radius: 8px; text-align: center; border-left: 5px solid #f59e0b;">
                    <p style="margin: 0; font-size: 13px; color: #94a3b8; font-weight: 600;">SISA SALDO BELUM TERBAYAR</p>
                    <h3 style="margin: 6px 0 0 0; font-size: 19px; color: #fbbf24;">{fmt_rp_satu_baris(sisa_belum_terbayar)}</h3>
                    <p style="margin: 4px 0 0 0; font-size: 11px; color: #fbbf24;">{persen_sisa:.2f}% (Outstanding Piutang)</p>
                </div>
            """, unsafe_allow_html=True)

        # --- TABEL RINCIAN REKAPITULASI PER NOMOR KONTRAK ---
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

        rh_cols = st.columns([1.5, 1.0, 1.8, 1.8, 1.8, 1.2, 1.0])
        r_headers = ["Nomor Kontrak", "Jml Dok", "Total Tagihan (Rp)", "Sudah Dibayar (Rp)", "Sisa Piutang (Rp)", "Realisasi (%)", "Status"]
        for rh, rht in zip(rh_cols, r_headers):
            with rh:
                st.markdown(f"<span style='font-size: 11px; font-weight: bold; color: #0f172a;'>{rht}</span>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 4px 0; border-top: 2px solid #cbd5e1;'>", unsafe_allow_html=True)

        tot_sum_tagihan = 0.0
        tot_sum_terbayar = 0.0
        tot_sum_piutang = 0.0
        tot_jml_dok = 0

        def fmt_small_rp(val):
            formatted_num = f"Rp {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f'<small style="white-space: nowrap; display: inline-block;">{formatted_num}</small>'

        for c_key, c_val in summary_contract_map.items():
            t_tag = c_val["tagihan"]
            t_byr = c_val["terbayar"]
            t_piu = t_tag - t_byr
            pct_real = (t_byr / t_tag * 100) if t_tag > 0 else 0.0
            
            tot_sum_tagihan += t_tag
            tot_sum_terbayar += t_byr
            tot_sum_piutang += t_piu
            tot_jml_dok += c_val["jml_inv"]

            st_teks = "🟢 Lengkap" if c_val["lunas"] == c_val["jml_inv"] else f"🟡 {c_val['lunas']}/{c_val['jml_inv']} Lunas"

            rc_cols = st.columns([1.5, 1.0, 1.8, 1.8, 1.8, 1.2, 1.0])
            with rc_cols[0]:
                st.markdown(f"**{c_key}**", unsafe_allow_html=True)
            with rc_cols[1]:
                st.markdown(f"<small>{c_val['jml_inv']} Dok</small>", unsafe_allow_html=True)
            with rc_cols[2]:
                st.markdown(fmt_small_rp(t_tag), unsafe_allow_html=True)
            with rc_cols[3]:
                st.markdown(fmt_small_rp(t_byr), unsafe_allow_html=True)
            with rc_cols[4]:
                st.markdown(fmt_small_rp(t_piu), unsafe_allow_html=True)
            with rc_cols[5]:
                st.markdown(f"<small><b>{pct_real:.2f}%</b></small>", unsafe_allow_html=True)
            with rc_cols[6]:
                st.markdown(f"<small>{st_teks}</small>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 2px 0; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

        tot_pct_overall = (tot_sum_terbayar / tot_sum_tagihan * 100) if tot_sum_tagihan > 0 else 0.0
        tot_cols = st.columns([1.5, 1.0, 1.8, 1.8, 1.8, 1.2, 1.0])
        with tot_cols[0]:
            st.markdown("**TOTAL KESELURUHAN**", unsafe_allow_html=True)
        with tot_cols[1]:
            st.markdown(f"**{tot_jml_dok} Dok**", unsafe_allow_html=True)
        with tot_cols[2]:
            st.markdown(f"**<span style='white-space: nowrap;'>Rp {tot_sum_tagihan:,.2f}</span>**".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
        with tot_cols[3]:
            st.markdown(f"**<span style='white-space: nowrap;'>Rp {tot_sum_terbayar:,.2f}</span>**".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
        with tot_cols[4]:
            st.markdown(f"**<span style='white-space: nowrap;'>Rp {tot_sum_piutang:,.2f}</span>**".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
        with tot_cols[5]:
            st.markdown(f"**{tot_pct_overall:.2f}%**", unsafe_allow_html=True)
        with tot_cols[6]:
            st.markdown("**100%**", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 4px 0; border-top: 2px solid #0f172a;'>", unsafe_allow_html=True)

    # --- FORM INPUT & PEMBARUAN STATUS PEMBAYARAN ---
    st.markdown("---")
    st.markdown("##### 📝 Form Input & Pembaruan Status Pembayaran (Berdasarkan Kontrak)")

    col_fc1, col_fc2 = st.columns([1.5, 2.5])
    with col_fc1:
        form_kontrak_pilih = st.selectbox("1️⃣ Pilih Nomor Kontrak:", all_contracts if all_contracts else ["-"], key="form_input_kontrak_sel")
    
    inv_list_filtered_contract = [inv for inv in invoice_list if str(inv.get("Kontrak No.", inv.get("Nomor Kontrak", "-"))).strip() == str(form_kontrak_pilih).strip()]
    
    # Filter ketat nomor invoice agar hanya mengambil string format nomor invoice asli (misal mengandung '/' atau 'BSS')
    all_inv_no_contract = []
    for inv in inv_list_filtered_contract:
        val_inv = str(inv.get(inv_key, "")).strip()
        if val_inv and not val_inv.startswith("2026-") and ("/" in val_inv or "BSS" in val_inv or len(val_inv) > 5):
            all_inv_no_contract.append(val_inv)
            
    # Fallback jika list kosong
    if not all_inv_no_contract:
        all_inv_no_contract = [str(inv.get(inv_key, "")).strip() for inv in inv_list_filtered_contract if inv.get(inv_key) and not str(inv.get(inv_key, "")).startswith("2026-")]

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

    # --- TABEL RINGKASAN & LAPORAN AGING ---
    st.markdown("---")
    st.markdown(f"#### 📋 Ringkasan & Laporan Aging Invoice ({filter_kontrak_pilih})")

    current_payment_records = muat_status_pembayaran()
    if filter_kontrak_pilih != "-- Semua Nomor Kontrak (ALL) --":
        current_payment_records = [p for p in current_payment_records if str(p.get("Nomor Kontrak", "")).strip() == str(filter_kontrak_pilih).strip()]

    if current_payment_records:
        hdr_cols = st.columns([1.1, 1.4, 1.3, 1.8, 0.9, 0.9, 0.6, 0.9, 0.9, 1.1, 1.0, 0.7, 0.7])
        headers_text = ["No. Kontrak", "No. Invoice", "No. Faktur Pajak", "Customer", "Tgl Inv", "Tgl Serah", "TOP", "Tgl JT", "Tgl Lunas", "Grand Total", "Status", "Edit", "Hapus"]
        for hc, ht in zip(hdr_cols, headers_text):
            with hc:
                st.markdown(f"<span style='font-size: 11px; font-weight: bold; color: #0f172a;'>{ht}</span>", unsafe_allow_html=True)
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

            cols_r = st.columns([1.1, 1.4, 1.3, 1.8, 0.9, 0.9, 0.6, 0.9, 0.9, 1.1, 1.0, 0.7, 0.7])
            with cols_r[0]:
                st.markdown(f"<small>{row_p.get('Nomor Kontrak', '-')}</small>", unsafe_allow_html=True)
            with cols_r[1]:
                st.markdown(f"**{inv_num_row}**", unsafe_allow_html=True)
            with cols_r[2]:
                st.markdown(f"<small>{faktur_pajak_row if faktur_pajak_row else '-'}</small>", unsafe_allow_html=True)
            with cols_r[3]:
                st.markdown(f"<small>{row_p.get('Customer', '-')}</small>", unsafe_allow_html=True)
            with cols_r[4]:
                st.markdown(f"<small>{str(row_p.get('Tanggal Invoice', ''))[:10]}</small>", unsafe_allow_html=True)
            with cols_r[5]:
                st.markdown(f"<small>{tgl_penyerahan_str}</small>", unsafe_allow_html=True)
            with cols_r[6]:
                st.markdown(f"<small>{durasi_info}</small>", unsafe_allow_html=True)
            with cols_r[7]:
                st.markdown(f"<small>{str(row_p.get('Tanggal Jatuh Tempo', ''))[:10]}</small>", unsafe_allow_html=True)
            with cols_r[8]:
                st.markdown(f"<small>{tgl_pelunasan_str}</small>", unsafe_allow_html=True)
            with cols_r[9]:
                gt_val = float(row_p.get('Grand Total', 0))
                st.markdown(f"<small style='white-space: nowrap;'>Rp {gt_val:,.2f}</small>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
            with cols_r[10]:
                st.markdown(f"<small>{row_p.get('Status Pembayaran', '-')}</small>", unsafe_allow_html=True)
            with cols_r[11]:
                if st.button("✏️", key=f"tbl_edit_{idx}_{inv_num_row}", help="Edit Data"):
                    st.session_state["active_invoice_selected"] = str(inv_num_row).strip()
                    st.rerun()
            with cols_r[12]:
                if st.button("🗑️", key=f"tbl_del_{idx}_{inv_num_row}", help="Hapus Data"):
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
    else:
        st.info("ℹ️ Belum ada data pemantauan pembayaran yang tersimpan untuk filter kontrak ini.")