import streamlit as st
import pandas as pd
import os
import glob
import base64
import sys
import re
from datetime import datetime, timedelta, date

# Menambahkan path untuk pemanggilan folder modul_dokumen
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import modul pendukung secara aman dengan penanganan error
try:
    from modul_dokumen.rincian_pekerjaan import tampilkan_rincian_pekerjaan
except ImportError:
    pass

try:
    from modul_dokumen.proforma_invoice import tampilkan_proforma_invoice
except ImportError:
    pass

try:
    from modul_dokumen.bamp import tampilkan_bamp
except ImportError:
    pass

try:
    from modul_dokumen.basp import tampilkan_basp
except ImportError:
    pass

try:
    from modul_dokumen.wcc import tampilkan_wcc
except ImportError:
    pass

try:
    from modul_dokumen.tkdn import tampilkan_tkdn
except ImportError:
    pass

try:
    from modul_dokumen.timesheet import tampilkan_timesheet
except ImportError:
    pass

try:
    from modul_dokumen.opname_pekerjaan import tampilkan_opname
except ImportError:
    pass

try:
    from modul_dokumen.bastb import tampilkan_bastb
except ImportError:
    pass

try:
    from modul_dokumen.arsip_pendukung import tampilkan_arsip_pendukung
except ImportError:
    pass

try:
    from modul_dokumen.paket_dokumen_lengkap import tampilkan_paket_lengkap
except ImportError:
    pass

try:
    from modul_dokumen.rekap_transaksi import tampilkan_rekap_transaksi
except ImportError:
    pass

try:
    from modul_keuangan.faktur_pajak import tampilkan_faktur_pajak
except ImportError:
    pass

try:
    from modul_keuangan.modul_billing_tax import tampilkan_billing_tax
except ImportError:
    pass

try:
    from modul_keamanan.autentikasi import form_login_sistem, render_panel_manajemen_akun
except ImportError:
    def form_login_sistem():
        return True
    def render_panel_manajemen_akun():
        pass

# Konfigurasi Halaman Streamlit
st.set_page_config(page_title="Dashboard Terintegrasi - PT. BANGGAI SENTRAL SULAWESI", layout="wide", initial_sidebar_state="expanded")

# --- FUNGSI UTAMA MODUL 3: PEMANTAUAN PEMBAYARAN & AGING INVOICE (DIAMANKAN MUTLAK) ---
def tampilkan_pemantauan_pembayaran():
    try:
        st.markdown("#### 📊 Modul Analisis Keuangan, Pemantauan Pembayaran & Aging Invoice")
        
        DIR_DATABASE = "database_penyimpanan_aman"
        if not os.path.exists(DIR_DATABASE):
            os.makedirs(DIR_DATABASE)
        
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
            try:
                semua_file = os.listdir(DIR_DATABASE)
                kemungkinan_file = [
                    os.path.join(DIR_DATABASE, f) for f in semua_file 
                    if f.endswith('.xlsx') and not f.startswith('~$')
                ]
                for file_path in kemungkinan_file:
                    try:
                        df = pd.read_excel(file_path)
                        if df is not None and not df.empty:
                            return df.to_dict(orient="records")
                    except:
                        pass
            except:
                pass
            return []

        invoice_list = muat_invoice_resmi()

        def ambil_grand_total_invoice_master(inv_no):
            for inv in invoice_list:
                found_no = str(inv.get("Nomor Invoice Resmi", inv.get("Nomor Invoice", ""))).strip()
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
            try:
                df_baru = pd.DataFrame(data_list)
                df_baru.to_excel(EXCEL_PAYMENT_STATUS, index=False)
                st.session_state["db_payment"] = data_list
            except Exception as e:
                st.error(f"Gagal menyimpan data ke file Excel: {e}")

        if "db_payment" not in st.session_state:
            st.session_state["db_payment"] = muat_status_pembayaran()

        payment_records = st.session_state["db_payment"]

        def ambil_tanggal_invoice(inv_data_obj):
            for k, v in inv_data_obj.items():
                if any(kata in str(k).lower() for kata in ["tgl", "tanggal", "date"]) and not any(kata in str(k).lower() for kata in ["penyerahan", "tempo", "lunas"]):
                    if pd.notnull(v) and str(v).strip() != "":
                        return str(v)[:10]
            return str(date.today())

        all_contracts = sorted(list(dict.fromkeys([str(inv.get("Kontrak No.", inv.get("Nomor Kontrak", "-"))).strip() for inv in invoice_list if inv.get("Kontrak No.") or inv.get("Nomor Kontrak")])))
        if not all_contracts and payment_records:
            all_contracts = sorted(list(dict.fromkeys([str(p.get("Nomor Kontrak", "-")).strip() for p in payment_records if p.get("Nomor Kontrak")])))
        
        if not all_contracts:
            all_contracts = ["-"]

        st.markdown("---")
        st.markdown("##### 🔍 Filter Tampilan & Rekapitulasi Berdasarkan Kontrak")
        opsi_filter_kontrak = ["-- Semua Nomor Kontrak (ALL) --"] + all_contracts
        filter_kontrak_pilih = st.selectbox("Pilih Nomor Kontrak untuk Filter Dashboard:", opsi_filter_kontrak, key="filter_kontrak_dashboard_mod3")

        if filter_kontrak_pilih != "-- Semua Nomor Kontrak (ALL) --":
            filtered_payment_records = [p for p in payment_records if str(p.get("Nomor Kontrak", "")).strip() == str(filter_kontrak_pilih).strip()]
            filtered_invoice_list = [inv for inv in invoice_list if str(inv.get("Kontrak No.", inv.get("Nomor Kontrak", "-"))).strip() == str(filter_kontrak_pilih).strip()]
        else:
            filtered_payment_records = payment_records
            filtered_invoice_list = invoice_list

        if payment_records:
            hari_ini = date.today()
            
            total_seluruh_tagihan = 0.0
            total_sudah_dibayar = 0.0

            jml_aman = 0; val_aman = 0.0
            jml_warning = 0; val_warning = 0.0
            jml_overdue = 0; val_overdue = 0.0
            jml_lunas = 0; val_lunas = 0.0

            for p in filtered_payment_records:
                g_total = float(p.get("Grand Total", 0.0))
                total_seluruh_tagihan += g_total
                status_byr = p.get("Status Pembayaran", "Belum Dibayar")

                if status_byr == "Lunas":
                    total_sudah_dibayar += g_total
                    jml_lunas += 1
                    val_lunas += g_total
                    continue
                elif status_byr == "Sebagian (DP / Termin)":
                    total_sudah_dibayar += (g_total * 0.5)

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
            persen_dibayar = (total_sudah_dibayar / total_seluruh_tagihan * 100) if total_seluruh_tagihan > 0 else 0.0
            persen_sisa = (sisa_belum_terbayar / total_seluruh_tagihan * 100) if total_seluruh_tagihan > 0 else 0.0

            def fmt_rp(val):
                return f"Rp {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            st.markdown("---")
            st.markdown(f"##### 💰 Rekapitulasi Saldo Keuangan & Tagihan ({filter_kontrak_pilih})")
            c_fin1, c_fin2, c_fin3 = st.columns(3)
            with c_fin1:
                st.markdown(f"""
                    <div style="background-color: #1e293b; color: white; padding: 18px; border-radius: 8px; text-align: center; border-left: 5px solid #38bdf8;">
                        <p style="margin: 0; font-size: 13px; color: #94a3b8; font-weight: 600;">TOTAL SELURUH TAGIHAN</p>
                        <h3 style="margin: 6px 0 0 0; font-size: 20px; color: #ffffff;">{fmt_rp(total_seluruh_tagihan)}</h3>
                        <p style="margin: 4px 0 0 0; font-size: 11px; color: #38bdf8;">100.00% dari Total Portofolio</p>
                    </div>
                """, unsafe_allow_html=True)
            with c_fin2:
                st.markdown(f"""
                    <div style="background-color: #1e293b; color: white; padding: 18px; border-radius: 8px; text-align: center; border-left: 5px solid #10b981;">
                        <p style="margin: 0; font-size: 13px; color: #94a3b8; font-weight: 600;">TOTAL SUDAH DIBAYARKAN</p>
                        <h3 style="margin: 6px 0 0 0; font-size: 20px; color: #34d399;">{fmt_rp(total_sudah_dibayar)}</h3>
                        <p style="margin: 4px 0 0 0; font-size: 11px; color: #34d399;">{persen_dibayar:.2f}% (Rasio Realisasi)</p>
                    </div>
                """, unsafe_allow_html=True)
            with c_fin3:
                st.markdown(f"""
                    <div style="background-color: #1e293b; color: white; padding: 18px; border-radius: 8px; text-align: center; border-left: 5px solid #f59e0b;">
                        <p style="margin: 0; font-size: 13px; color: #94a3b8; font-weight: 600;">SISA SALDO BELUM TERBAYAR</p>
                        <h3 style="margin: 6px 0 0 0; font-size: 20px; color: #fbbf24;">{fmt_rp(sisa_belum_terbayar)}</h3>
                        <p style="margin: 4px 0 0 0; font-size: 11px; color: #fbbf24;">{persen_sisa:.2f}% (Outstanding Piutang)</p>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("##### 📑 Rincian Akumulasi Tagihan per Nomor Kontrak")
            
            summary_contract_map = {}
            for p in payment_records:
                c_no = str(p.get("Nomor Kontrak", "-")).strip()
                gt = float(p.get("Grand Total", 0.0))
                st_byr = p.get("Status Pembayaran", "Belum Dibayar")
                
                if c_no not in summary_contract_map:
                    summary_contract_map[c_no] = {"tagihan": 0.0, "terbayar": 0.0, "jml_inv": 0, "lunas": 0}
                
                summary_contract_map[c_no]["tagihan"] += gt
                summary_contract_map[c_no]["jml_inv"] += 1
                if st_byr == "Lunas":
                    summary_contract_map[c_no]["terbayar"] += gt
                    summary_contract_map[c_no]["lunas"] += 1
                elif st_byr == "Sebagian (DP / Termin)":
                    summary_contract_map[c_no]["terbayar"] += (gt * 0.5)

            rh_cols = st.columns([1.5, 1.0, 1.5, 1.5, 1.5, 1.2, 1.0])
            r_headers = ["Nomor Kontrak", "Jml Dok", "Total Tagihan (Rp)", "Sudah Dibayar (Rp)", "Sisa Piutang (Rp)", "Realisasi (%)", "Status"]
            for rh, rht in zip(rh_cols, r_headers):
                with rh:
                    st.markdown(f"<span style='font-size: 11px; font-weight: bold; color: #0f172a;'>{rht}</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 4px 0; border-top: 2px solid #cbd5e1;'>", unsafe_allow_html=True)

            tot_sum_tagihan = 0.0
            tot_sum_terbayar = 0.0
            tot_sum_piutang = 0.0
            tot_jml_dok = 0

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

                rc_cols = st.columns([1.5, 1.0, 1.5, 1.5, 1.5, 1.2, 1.0])
                with rc_cols[0]:
                    st.markdown(f"**{c_key}**", unsafe_allow_html=True)
                with rc_cols[1]:
                    st.markdown(f"<small>{c_val['jml_inv']} Dok</small>", unsafe_allow_html=True)
                with rc_cols[2]:
                    st.markdown(f"<small>{fmt_rp(t_tag)}</small>", unsafe_allow_html=True)
                with rc_cols[3]:
                    st.markdown(f"<small>{fmt_rp(t_byr)}</small>", unsafe_allow_html=True)
                with rc_cols[4]:
                    st.markdown(f"<small>{fmt_rp(t_piu)}</small>", unsafe_allow_html=True)
                with rc_cols[5]:
                    st.markdown(f"<small><b>{pct_real:.2f}%</b></small>", unsafe_allow_html=True)
                with rc_cols[6]:
                    st.markdown(f"<small>{st_teks}</small>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 2px 0; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

            tot_pct_overall = (tot_sum_terbayar / tot_sum_tagihan * 100) if tot_sum_tagihan > 0 else 0.0
            tot_cols = st.columns([1.5, 1.0, 1.5, 1.5, 1.5, 1.2, 1.0])
            with tot_cols[0]:
                st.markdown("**TOTAL KESELURUHAN**", unsafe_allow_html=True)
            with tot_cols[1]:
                st.markdown(f"**{tot_jml_dok} Dok**", unsafe_allow_html=True)
            with tot_cols[2]:
                st.markdown(f"**{fmt_rp(tot_sum_tagihan)}**", unsafe_allow_html=True)
            with tot_cols[3]:
                st.markdown(f"**{fmt_rp(tot_sum_terbayar)}**", unsafe_allow_html=True)
            with tot_cols[4]:
                st.markdown(f"**{fmt_rp(tot_sum_piutang)}**", unsafe_allow_html=True)
            with tot_cols[5]:
                st.markdown(f"**{tot_pct_overall:.2f}%**", unsafe_allow_html=True)
            with tot_cols[6]:
                st.markdown("**100%**", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 4px 0; border-top: 2px solid #0f172a;'>", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("##### 📈 Grafik Analisis Komparasi Keuangan & Persentase Kinerja Penagihan")
            
            col_g1, col_g2 = st.columns([2, 1])
            with col_g1:
                df_grafik = pd.DataFrame({
                    "Kategori Keuangan": ["Total Tagihan", "Sudah Dibayar", "Sisa Saldo (Piutang)"],
                    "Nominal (Rp)": [total_seluruh_tagihan, total_sudah_dibayar, sisa_belum_terbayar]
                }).set_index("Kategori Keuangan")
                st.bar_chart(df_grafik, color="#38bdf8")
                
            with col_g2:
                st.markdown(f"""
                    <div style="background-color: #0f172a; color: #f8fafc; padding: 16px; border-radius: 8px; font-size: 13px;">
                        <p style="font-weight: bold; color: #38bdf8; margin-bottom: 8px;">💡 Ringkasan Analisis Eksekutif:</p>
                        <ul style="padding-left: 18px; margin: 0; color: #cbd5e1;">
                            <li><b>Efektivitas Penagihan:</b> <code>{persen_dibayar:.2f}%</code></li>
                            <li><b>Rasio Piutang Tertahan:</b> <code>{persen_sisa:.2f}%</code></li>
                            <li><b>Total Dokumen Lunas:</b> <code>{jml_lunas} Dokumen</code></li>
                            <li><b>Total Dokumen Overdue:</b> <code>{jml_overdue} Dokumen</code></li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("##### 🚨 Indikator Peringatan & Aging Status Pembayaran (Sistem Notifikasi)")
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
        st.markdown("##### 📝 Form Input & Pembaruan Status Pembayaran (Berdasarkan Kontrak)")

        col_fc1, col_fc2 = st.columns([1.5, 2.5])
        with col_fc1:
            form_kontrak_pilih = st.selectbox("1️⃣ Pilih Nomor Kontrak:", all_contracts, key="form_input_kontrak_sel_mod3")
        
        inv_list_filtered_contract = [inv for inv in invoice_list if str(inv.get("Kontrak No.", inv.get("Nomor Kontrak", "-"))).strip() == str(form_kontrak_pilih).strip()]
        
        sample_inv = invoice_list[0] if invoice_list else {}
        inv_key = "Nomor Invoice Resmi" if "Nomor Invoice Resmi" in sample_inv else ("Nomor Invoice" if "Nomor Invoice" in sample_inv else (list(sample_inv.keys())[0] if sample_inv else "Nomor Invoice"))

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
            pilihan_panggil_bayar = st.selectbox("2️⃣ Panggil Ulang Data Pemantauan Tersimpan (Kontrak Terpilih):", opsi_panggil_bayar, key="select_panggil_bayar_mod3")
            if st.button("📥 Panggil untuk Diedit", key="btn_panggil_edit_mod3", use_container_width=True):
                if pilihan_panggil_bayar != "-- Pilih Data Tersimpan untuk Diedit / Panggil Ulang --":
                    st.session_state["active_invoice_selected"] = str(pilihan_panggil_bayar).strip()
                    st.success(f"📋 Memuat data pemantauan Invoice `{pilihan_panggil_bayar}`")
                    st.rerun()

        default_select_idx = 0
        if active_edit_inv in list_inv_aktif:
            default_select_idx = list_inv_aktif.index(active_edit_inv)

        if not list_inv_aktif:
            selected_inv = st.text_input("3️⃣ Ketik Nomor Invoice Aktif:", value=active_edit_inv, key="txt_inv_aktif_mod3")
        else:
            selected_inv = st.selectbox("3️⃣ Pilih Nomor Invoice Aktif:", list_inv_aktif, index=default_select_idx if default_select_idx < len(list_inv_aktif) else 0, key="dropdown_master_invoice_aktif_mod3")

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
        status_pembayaran = st.selectbox("Status Pembayaran:", status_opsi, index=idx_st, key="select_status_pembayaran_live_mod3")

        # --- FORM INPUT & UPDATE ---
        with st.form("form_update_pembayaran_mod3"):
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
                if not str(selected_inv).strip():
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
                        "Nomor Invoice": str(selected_inv).strip(),
                        "Nomor Faktur Pajak": str(nomor_faktur_pajak).strip(),
                        "Customer": inv_data.get("Customer", existing_pay.get("Customer", "-")),
                        "Tanggal Invoice": tgl_invoice_bawaan,
                        "Tanggal Penyerahan": tgl_penyerahan.strftime("%Y-%m-%d"),
                        "TOP Hari": int(top_hari),
                        "Tanggal Jatuh Tempo": tgl_jatuh_tempo.strftime("%Y-%m-%d"),
                        "Tanggal Pelunasan": str_tgl_pelunasan_final,
                        "Durasi Riil Hari": int(durasi_riil_hari),
                        "Grand Total": float(grand_total_otomatis),
                        "Status Pembayaran": status_pembayaran,
                        "Catatan": str(catatan_bayar),
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
                    st.markdown(f"<small>Rp {gt_val:,.2f}</small>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
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
            st.info("ℹ️ Belum ada data pemantauan pembayaran yang tersimpan untuk filter kontrak ini. Silakan gunakan form di atas untuk menambah atau memperbarui data.")
    except Exception as e:
        st.error(f"⚠️ Terjadi kendala saat memuat modul pemantauan pembayaran: {e}")


# --- STRUKTUR UTAMA APLIKASI & NAVIGASI ---
if form_login_sistem():
    try:
        render_panel_manajemen_akun()
    except Exception:
        pass

    user_role = st.session_state.get('current_role', 'Staff')

    st.markdown("""
        <style>
        .stApp { background-color: #f8fafc; color: #0f172a; }
        label, .stSelectbox label, .stTextInput label, .stNumberInput label, .stDateInput label, .stTextArea label {
            color: #0f172a !important; font-weight: 600 !important; font-size: 13px !important;
        }
        div[data-baseweb="base-input"], div[data-baseweb="textarea"], div[data-baseweb="select"] {
            background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; color: #000000 !important;
        }
        input, textarea { background-color: #ffffff !important; color: #000000 !important; }
        .company-header-centered {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #ffffff; padding: 18px 25px; border-radius: 10px; text-align: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-bottom: 3px solid #10b981; margin-bottom: 25px;
        }
        .stButton>button { width: 100%; border-radius: 6px; font-weight: 600; background-color: #10b981; color: white; }
        .stButton>button:hover { background-color: #059669; color: white; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="company-header-centered">
            <h2 style="margin:0; font-size: 24px; font-weight: 700; color: #ffffff;">PT. BANGGAI SENTRAL SULAWESI</h2>
            <p style="margin:4px 0 0 0; font-size: 13px; color: #34d399; font-weight: 500;">General Contractor and Suppliers | Dashboard Terintegrasi Utama</p>
        </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("### 🗂️ Navigasi Dashboard Utama")
    waktu_wita = datetime.utcnow() + timedelta(hours=8)
    current_time_str = waktu_wita.strftime("%d %b %Y, %H:%M:%S")
    st.sidebar.markdown(f"🕒 **Waktu Sistem (WITA):**<br>`{current_time_str}`", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    if user_role == "Staff Timesheet":
        modul_pilihan = st.sidebar.selectbox("Pilih Modul:", ["Timesheet Peralatan"], key="modul_staff_timesheet")
    elif user_role == "Finance / Invoice":
        modul_pilihan = st.sidebar.selectbox("Pilih Modul Utama:", [
            "💰 Modul 3: Invoice & Tax Management",
            "📁 Arsip Dokumen Customer & Pendukung"
        ], key="modul_finance_inv")
    elif user_role == "Staf Marketing / Operasional":
        modul_pilihan = st.sidebar.selectbox("Pilih Modul Utama:", [
            "📁 Modul 1: Database & Master Kontrak",
            "📄 Modul 2: Invoice & Dokumen Turunan",
            "📁 Arsip Dokumen Customer & Pendukung"
        ], key="modul_marketing_ops")
    else: 
        modul_pilihan = st.sidebar.selectbox("Pilih Modul Utama:", [
            "📁 Modul 0: Master Referensi Harga & Pekerjaan",
            "📁 Modul 1: Database & Master Kontrak",
            "📄 Modul 2: Invoice & Dokumen Turunan",
            "💰 Modul 3: Invoice & Tax Management",
            "📁 Arsip Dokumen Customer & Pendukung"
        ], key="modul_utama_all")

    st.sidebar.markdown("---")

    if modul_pilihan == "Timesheet Peralatan":
        menu = "Timesheet"
    elif modul_pilihan == "📁 Modul 0: Master Referensi Harga & Pekerjaan":
        menu = st.sidebar.radio("Pilih Menu:", [
            "Input & Kelola Master Referensi",
            "Lihat Daftar Master Referensi Tersimpan"
        ], key="menu_mod0")
    elif modul_pilihan == "📁 Modul 1: Database & Master Kontrak":
        menu = st.sidebar.radio("Pilih Menu:", [
            "Input Database & Invoice (31 Kolom)",
            "Lihat Database Tersimpan"
        ], key="menu_mod1")
    elif modul_pilihan == "💰 Modul 3: Invoice & Tax Management":
        menu = st.sidebar.radio("Pilih Menu:", [
            "Input Data Invoice Resmi",
            "Input & Cetak Faktur Pajak",
            "Pemantauan Proses Pembayaran",
            "Pratinjau, Cetak & Download PDF Invoice",
            "Lihat Daftar Invoice & Pajak Tersimpan"
        ], key="menu_mod3")
    elif modul_pilihan == "📁 Arsip Dokumen Customer & Pendukung":
        menu = "Arsip Dokumen Customer & Pendukung"
    else:
        menu = st.sidebar.radio("Pilih Menu:", [
            "Input & Proses Rincian Pekerjaan",
            "Pratinjau, Cetak & Download PDF Dokumen",
            "Lihat Akumulasi Riwayat Transaksi",
            "Lihat Master Rekap Transaksi"
        ], key="menu_mod_lain")

    st.sidebar.markdown("---")
    st.sidebar.success("📂 **Status Sistem:** Penyimpanan Lokal Folder Aman Aktif")

    if st.sidebar.button("🔄 Sinkronisasi cPanel Sekarang", key="btn_sync_cpanel"):
        st.sidebar.info("ℹ️ Mode penyimpanan mandiri lokal aktif. Data tersimpan aman dan instan di folder lokal.")

    if st.sidebar.button("🔒 Keluar / Logout Sistem", key="btn_logout_sys"):
        st.session_state.logged_in = False
        st.rerun()

    # --- ROUTING EKSEKUSI MODUL SECARA TEPAT DAN AMAN ---
    if modul_pilihan == "💰 Modul 3: Invoice & Tax Management":
        transaksi_list = []
        if menu == "Input & Cetak Faktur Pajak":
            if 'tampilkan_faktur_pajak' in globals():
                tampilkan_faktur_pajak(transaksi_list, menu)
            else:
                st.info("Modul Faktur Pajak sedang dimuat.")
        elif menu == "Pemantauan Proses Pembayaran":
            tampilkan_pemantauan_pembayaran()
        elif menu == "Input Data Invoice Resmi":
            if 'tampilkan_billing_tax' in globals():
                tampilkan_billing_tax(transaksi_list, menu)
            else:
                st.info("Modul Billing & Tax sedang dimuat.")
        elif menu == "Pratinjau, Cetak & Download PDF Invoice":
            if 'tampilkan_billing_tax' in globals():
                tampilkan_billing_tax(transaksi_list, menu)
            else:
                st.info("Modul Billing & Tax sedang dimuat.")
        elif menu == "Lihat Daftar Invoice & Pajak Tersimpan":
            if 'tampilkan_billing_tax' in globals():
                tampilkan_billing_tax(transaksi_list, menu)
            else:
                st.info("Modul Billing & Tax sedang dimuat.")
        else:
            tampilkan_pemantauan_pembayaran()
            
    elif modul_pilihan == "📁 Arsip Dokumen Customer & Pendukung":
        if 'tampilkan_arsip_pendukung' in globals():
            tampilkan_arsip_pendukung()
        else:
            st.info("Arsip Pendukung sedang dimuat.")