import streamlit as st
import pandas as pd
from datetime import datetime, date

def tampilkan_modul_2_rincian(
    saved_db, 
    master_ref_data, 
    bersih_angka_func, 
    sort_pi_key_func, 
    muat_data_transaksi_func, 
    simpan_data_transaksi_func, 
    muat_master_bank_func, 
    simpan_master_bank_func
):
    current_role_user = str(st.session_state.get("current_role", "")).strip().lower()
    is_management = current_role_user in ["management", "direksi"]

    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📝 Lembar Kerja & Pemrosesan Rincian Pekerjaan</h3>
        </div>
    """, unsafe_allow_html=True)

    if not saved_db:
        st.warning("⚠️ Belum ada data di Database Modul 1. Harap lakukan input data kontrak & PI terlebih dahulu.")
        return
    if not master_ref_data:
        st.warning("⚠️ Belum ada data di Master Referensi Harga (Modul 0).")
        return

    existing_tx_list = muat_data_transaksi_func()
    list_kontrak = list(set([bersih_angka_func(item.get(1, item.get("Nomor Kontrak", ""))) for item in saved_db if item.get(1) or item.get("Nomor Kontrak")]))
    
    raw_list_pi = list(dict.fromkeys([bersih_angka_func(item.get(0, item.get("Proforma Invoice No.", ""))) for item in saved_db if item.get(0) or item.get("Proforma Invoice No.")]))
    list_pi = sorted(raw_list_pi, key=sort_pi_key_func, reverse=True)

    col1, col2 = st.columns(2)
    with col1:
        forced_k = st.session_state.get("forced_kontrak", None)
        default_kontrak_val = forced_k if forced_k in list_kontrak else (list_kontrak[0] if list_kontrak else "")
        idx_k = list_kontrak.index(default_kontrak_val) if default_kontrak_val in list_kontrak else 0
        selected_kontrak = st.selectbox("Nomor Kontrak", list_kontrak if list_kontrak else [""], index=idx_k, key="main_sel_kontrak")
        
        search_pi_keyword = st.text_input("🔍 Cari Nomor PI (Ketik sebagian untuk mencari spesifik):", "").strip().lower()
        
        filtered_pi_raw = [bersih_angka_func(item.get(0, item.get("Proforma Invoice No.", ""))) for item in saved_db if bersih_angka_func(item.get(1, item.get("Nomor Kontrak"))) == str(selected_kontrak)]
        if not filtered_pi_raw:
            filtered_pi = list_pi
        else:
            filtered_pi = sorted(list(dict.fromkeys(filtered_pi_raw)), key=sort_pi_key_func, reverse=True)

        if search_pi_keyword:
            filtered_pi = [pi for pi in filtered_pi if search_pi_keyword in pi.lower()]
            if not filtered_pi:
                st.warning("⚠️ Tidak ada nomor PI yang cocok dengan kata kunci.")
                filtered_pi = [""]

        forced_pi_val = st.session_state.get("forced_pi", None)
        default_pi_val = forced_pi_val if forced_pi_val in filtered_pi else (filtered_pi[0] if filtered_pi else "")
        idx_pi = filtered_pi.index(default_pi_val) if default_pi_val in filtered_pi else 0
        
        c_pi, c_btn = st.columns([2.5, 1])
        with c_pi:
            selected_pi = st.selectbox("Nomor Proforma Invoice (PI)", filtered_pi if filtered_pi else [""], index=idx_pi, key="main_sel_pi")
        with c_btn:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("📥 Panggil Data", use_container_width=True, type="primary"):
                keys_to_clear = [k for k in st.session_state.keys() if any(k.startswith(prefix) for prefix in ["kat_", "spek_", "spek_manual_", "qty_", "unit_", "tm_", "ts_", "hs_prov_", "ket_"])]
                for k in keys_to_clear:
                    del st.session_state[k]

                pi_target = str(selected_pi).strip()
                st.session_state["loaded_pi_target"] = pi_target
                st.session_state["forced_kontrak"] = selected_kontrak
                st.session_state["forced_pi"] = pi_target
                
                matched_tx_items = [t for t in existing_tx_list if bersih_angka_func(t.get("PI No.")) == pi_target]
                if matched_tx_items:
                    st.session_state["num_rows"] = len(matched_tx_items)
                else:
                    st.session_state["num_rows"] = 1
                st.rerun()

    loaded_tx_items = []
    active_pi_load = st.session_state.get("loaded_pi_target", None)
    if active_pi_load and active_pi_load == str(selected_pi).strip():
        loaded_tx_items = [t for t in existing_tx_list if bersih_angka_func(t.get("PI No.")) == str(active_pi_load).strip()]
        if loaded_tx_items:
            st.info(f"📋 **Mode Tinjau Rincian:** Data PI `{active_pi_load}` terpanggil aktif ({len(loaded_tx_items)} baris item).")

    matched_record = next((item for item in saved_db if bersih_angka_func(item.get(1, item.get("Nomor Kontrak"))) == str(selected_kontrak) and bersih_angka_func(item.get(0, item.get("Proforma Invoice No."))) == str(selected_pi)), saved_db[0] if saved_db else {})

    nama_kontrak = bersih_angka_func(matched_record.get(7, matched_record.get("Judul Kontrak", "")))
    nomor_tender = bersih_angka_func(matched_record.get(2, matched_record.get("Nomor Tender", "")))
    tanggal_pi = bersih_angka_func(matched_record.get(6, matched_record.get("Tanggal Performa Invoice", "")))
    ditujukan_kepada = bersih_angka_func(matched_record.get(10, matched_record.get("Pihak Pertama", "")))
    alamat_pihak_pertama = bersih_angka_func(matched_record.get(11, matched_record.get("Alamat Pihak Pertama", "")))
    jangka_waktu = bersih_angka_func(matched_record.get(5, matched_record.get("Jangka Waktu Kontrak", "")))
    
    nomor_po_default_m1 = bersih_angka_func(matched_record.get(8, matched_record.get("Nomor Purchase Order", "-")))
    nomor_wo_default_m1 = bersih_angka_func(matched_record.get(21, matched_record.get("Nomor WO", "-")))
    tanggal_po_default_m1 = bersih_angka_func(matched_record.get(9, matched_record.get("Tanggal Purchase Order", "")))
    desc_po_default_m1 = bersih_angka_func(matched_record.get(3, matched_record.get("Lingkup Pekerjaan", "")))

    with col2:
        raw_po_num = nomor_po_default_m1 if (nomor_po_default_m1 and nomor_po_default_m1 != "-") else (loaded_tx_items[0].get("Nomor PO", "") if loaded_tx_items else "")
        def_po_num = bersih_angka_func(raw_po_num)
        
        raw_wan_num = loaded_tx_items[0].get("Nomor WAN / SA", "") if loaded_tx_items else ""
        def_wan_num = bersih_angka_func(raw_wan_num)

        raw_po_date = tanggal_po_default_m1 if tanggal_po_default_m1 else (loaded_tx_items[0].get("Tanggal PO", "") if loaded_tx_items else "")
        def_po_date = bersih_angka_func(raw_po_date)

        nomor_po = st.text_input("Nomor PO", def_po_num if def_po_num else "-", disabled=is_management)
        
        raw_wo_num = nomor_wo_default_m1 if (nomor_wo_default_m1 and nomor_wo_default_m1 != "-") else (loaded_tx_items[0].get("Nomor WO", "") if loaded_tx_items else "")
        nomor_wo = st.text_input("Nomor WO", bersih_angka_func(raw_wo_num) if raw_wo_num else "-", disabled=is_management)

        nomor_wan_sa = st.text_input("Nomor WAN / SA (Work Authorization Notice / Service Agreement)", def_wan_num if def_wan_num else "-", disabled=is_management)
        tanggal_po = st.text_input("Tanggal PO", def_po_date if def_po_date else "-", disabled=is_management)
        mata_uang = st.text_input("Mata Uang", "IDR", disabled=is_management)

    with col1:
        def_desc_po = desc_po_default_m1 if desc_po_default_m1 else (bersih_angka_func(loaded_tx_items[0].get("Deskripsi PO", "")) if loaded_tx_items else "")
        desc_po = st.text_area("Lingkup Pekerjaan", def_desc_po, height=130, disabled=is_management)

    st.markdown("---")
    
    opsi_jenis_bastp = [
        "Pekerjaan Jasa",
        "Pekerjaan Barang / Material",
        "Pekerjaan Gabungan (Barang & Jasa)"
    ]
    
    def_jenis_bastp = loaded_tx_items[0].get("Jenis BASTP", opsi_jenis_bastp[1]) if loaded_tx_items else opsi_jenis_bastp[1]
    idx_bastp = opsi_jenis_bastp.index(def_jenis_bastp) if def_jenis_bastp in opsi_jenis_bastp else 1
    
    jenis_bastp_pilih = st.selectbox(
        "Pilih Jenis BASTP untuk Dokumen Turunan:",
        opsi_jenis_bastp,
        index=idx_bastp,
        key="input_jenis_bastp_select",
        disabled=is_management
    )
    
    st.markdown("---")
    bank_records = muat_master_bank_func()
    bank_names_list = [b.get("Bank Name") for b in bank_records] + ["➕ Tambah Rekening Bank Baru..."]
    
    def_b_name = loaded_tx_items[0].get("Bank Name", bank_records[0].get("Bank Name")) if loaded_tx_items else bank_records[0].get("Bank Name")
    idx_b = bank_names_list.index(def_b_name) if def_b_name in bank_names_list else 0

    c_bank1, c_bank2 = st.columns(2)
    with c_bank1:
        pilih_bank_dropdown = st.selectbox("Pilih Rekening Bank Tujuan", bank_names_list, index=idx_b, disabled=is_management)
        
        if not is_management and pilih_bank_dropdown == "➕ Tambah Rekening Bank Baru...":
            new_b_name = st.text_input("Nama Bank Baru (Contoh: BANK MANDIRI)")
            new_b_branch = st.text_input("Cabang Bank Baru", value="Cabang Luwuk")
            new_b_acc_no = st.text_input("Nomor Rekening Baru")
            new_b_acc_name = st.text_input("Atas Nama Rekening Baru", value="PT. BANGGAI SENTRAL SULAWESI")
            new_b_attn = st.text_input("Attn. Departemen", value="Accounts Payable - Finance Department")
            
            if st.button("💾 Simpan Rekening Bank Baru"):
                if new_b_name and new_b_acc_no:
                    bank_records.append({
                        "Bank Name": new_b_name.upper(),
                        "Bank Branch": new_b_branch,
                        "Account No": new_b_acc_no,
                        "Account Name": new_b_acc_name,
                        "Attn": new_b_attn
                    })
                    if simpan_master_bank_func(bank_records):
                        st.success("✅ Rekening bank baru berhasil disimpan!")
                    st.rerun()
                else:
                    st.error("⚠️ Nama Bank dan Nomor Rekening wajib diisi!")
            
            bank_name = def_b_name
            bank_branch = loaded_tx_items[0].get("Bank Branch", "Cabang Luwuk") if loaded_tx_items else "Cabang Luwuk"
            bank_acc_no = bersih_angka_func(loaded_tx_items[0].get("Account No", "")) if loaded_tx_items else ""
            bank_acc_name = loaded_tx_items[0].get("Account Name", "PT. BANGGAI SENTRAL SULAWESI") if loaded_tx_items else "PT. BANGGAI SENTRAL SULAWESI"
            attn_to = loaded_tx_items[0].get("Attn", "Accounts Payable - Finance Department") if loaded_tx_items else "Accounts Payable - Finance Department"
        else:
            bank_name = pilih_bank_dropdown
            selected_bank_obj = next((b for b in bank_records if b.get("Bank Name") == bank_name), bank_records[0])
            bank_branch = bersih_angka_func(selected_bank_obj.get("Bank Branch", "Cabang Luwuk"))
            bank_acc_no = bersih_angka_func(selected_bank_obj.get("Account No", ""))
            bank_acc_name = bersih_angka_func(selected_bank_obj.get("Account Name", "PT. BANGGAI SENTRAL SULAWESI"))
            attn_to = bersih_angka_func(selected_bank_obj.get("Attn", "Accounts Payable - Finance Department"))

            st.text_input("Cabang Bank", value=bank_branch if bank_branch else "-", disabled=True)
            st.text_input("Nomor Rekening", value=bank_acc_no if bank_acc_no else "-", disabled=True)

    with c_bank2:
        st.text_input("Atas Nama Rekening", value=bank_acc_name if bank_acc_name else "-", disabled=True)
        attn_to = st.text_input("Attn. (Penerima Invoice)", value=attn_to if attn_to else "-", disabled=is_management)
        try:
            def_percent = float(loaded_tx_items[0].get("Percent", 100.0) or 100.0) if loaded_tx_items else 100.0
        except:
            def_percent = 100.0
        persen_val = st.number_input("Persentase Tagihan (%)", min_value=1.0, max_value=100.0, value=def_percent, disabled=is_management)

    st.markdown("---")
    
    if is_management:
        st.info("🔒 **Mode Direksi (Read-Only):** Rincian item pekerjaan dan kontrol perhitungan ditampilkan dalam mode baca saja (Read-Only).")

    df_ref = pd.DataFrame(master_ref_data)
    df_ref["Nomor Kontrak Clean"] = df_ref["Nomor Kontrak"].astype(str).str.strip()
    df_ref["Kategori Clean"] = df_ref["Kategori"].astype(str).str.strip().str.upper()
    
    if "Uraian Pekerjaan" in df_ref.columns:
        df_ref["Uraian Clean"] = df_ref["Uraian Pekerjaan"].astype(str).str.strip()
    elif "Deskripsi Pekerjaan" in df_ref.columns:
        df_ref["Uraian Clean"] = df_ref["Deskripsi Pekerjaan"].astype(str).str.strip()
    else:
        df_ref["Uraian Clean"] = ""

    df_ref_kontrak = df_ref[df_ref["Nomor Kontrak Clean"] == str(selected_kontrak).strip()]
    if df_ref_kontrak.empty:
        df_ref_kontrak = df_ref 

    base_list_kat = sorted(df_ref_kontrak["Kategori Clean"].dropna().unique().tolist())
    if "PROFESSIONAL SUM" not in base_list_kat and "PROVISIONAL SUM" not in base_list_kat:
        base_list_kat.append("PROVISIONAL SUM")
    if "ESTIMATED SUM" not in base_list_kat:
        base_list_kat.append("ESTIMATED SUM")

    if "num_rows" not in st.session_state:
        st.session_state.num_rows = len(loaded_tx_items) if loaded_tx_items else 1

    items_data_input = []
    
    for i in range(st.session_state.num_rows):
        default_item_data = loaded_tx_items[i] if loaded_tx_items and i < len(loaded_tx_items) else {}
        
        # PERBAIKAN KATEGORI & URAIAN DARI DATA TERSIMPAN JIKA ADA
        def_kat_item = str(default_item_data.get("Kategori", "")).strip().upper()
        list_kat = list(base_list_kat)
        if def_kat_item and def_kat_item not in list_kat:
            list_kat.insert(0, def_kat_item)
        elif def_kat_item in list_kat:
            list_kat.remove(def_kat_item)
            list_kat.insert(0, def_kat_item)

        c_k1, c_k2 = st.columns(2)
        with c_k1:
            idx_kat = 0 if list_kat else 0
            if def_kat_item in list_kat:
                idx_kat = list_kat.index(def_kat_item)
            kat_pilih = st.selectbox(f"Kategori Pekerjaan {i+1}", list_kat if list_kat else ["-"], index=idx_kat, key=f"kat_{i}", disabled=is_management)
        
        kat_lower = str(kat_pilih).lower()
        is_provisional = "provisional" in kat_lower or "professional" in kat_lower
        is_estimated_sum = "estimated" in kat_lower or "estimasi" in kat_lower

        with c_k2:
            if is_provisional:
                current_desc_val = str(default_item_data.get("Deskripsi Pekerjaan", default_item_data.get("Uraian Pekerjaan", "")))
                if not current_desc_val or "fogging" in current_desc_val.lower() or "provisional sum (" in current_desc_val.lower() or "add cost" in current_desc_val.lower():
                    default_desc_final = "At Cost + Fee 15%"
                else:
                    default_desc_final = current_desc_val

                spek_pilih = st.text_input(f"Uraian Pekerjaan / Spesifikasi {i+1} (Manual)", value=default_desc_final, key=f"spek_manual_{i}", disabled=is_management)
            else:
                df_f_kat = df_ref_kontrak[df_ref_kontrak["Kategori Clean"] == str(kat_pilih).strip().upper()]
                if df_f_kat.empty:
                    df_f_kat = df_ref[df_ref["Kategori Clean"] == str(kat_pilih).strip().upper()]
                    
                raw_list_spek = sorted(df_f_kat["Uraian Clean"].dropna().unique().tolist()) if not df_f_kat.empty else ["- (Tidak ada data uraian)"]
                
                def_spek_item = str(default_item_data.get("Deskripsi Pekerjaan", default_item_data.get("Uraian Pekerjaan", "")))
                
                spek_display_map = {}
                spek_options_formatted = []

                for orig_text in raw_list_spek:
                    if "BBM & " in orig_text:
                        parts = orig_text.split("BBM & ")
                        unique_part = parts[-1].strip() if len(parts) > 1 else orig_text
                        display_text = f"⭐ [{unique_part}] — ({orig_text})"
                    else:
                        display_text = orig_text
                    
                    spek_display_map[display_text] = orig_text
                    spek_options_formatted.append(display_text)

                idx_spek = 0
                if def_spek_item in raw_list_spek and str(default_item_data.get("Kategori", "")).strip().upper() == str(kat_pilih).strip().upper():
                    for disp, orig in spek_display_map.items():
                        if orig == def_spek_item:
                            try:
                                idx_spek = spek_options_formatted.index(disp)
                            except:
                                idx_spek = 0
                            break

                selected_display_spek = st.selectbox(f"Uraian Pekerjaan / Spesifikasi {i+1}", spek_options_formatted if spek_options_formatted else ["-"], index=idx_spek, key=f"spek_{i}", disabled=is_management)
                spek_pilih = spek_display_map.get(selected_display_spek, selected_display_spek)

        hs_otomatis = 0.0
        unit_otomatis = "Month"
        if not is_provisional:
            df_f_kat = df_ref_kontrak[df_ref_kontrak["Kategori Clean"] == str(kat_pilih).strip().upper()]
            if df_f_kat.empty:
                df_f_kat = df_ref[df_ref["Kategori Clean"] == str(kat_pilih).strip().upper()]

            if not df_f_kat.empty and spek_pilih != "- (Tidak ada data uraian)":
                m_row = df_f_kat[df_f_kat["Uraian Clean"] == str(spek_pilih).strip()]
                if m_row.empty:
                    m_row = df_f_kat[df_f_kat["Uraian Clean"].str.lower() == str(spek_pilih).strip().lower()]

                if not m_row.empty:
                    row_m = m_row.iloc[0]
                    try:
                        hs_otomatis = float(row_m.get("Harga Satuan", 0.0) or 0.0)
                    except:
                        hs_otomatis = 0.0
                    unit_otomatis = str(row_m.get("Unit", "Month"))

        c_item1, c_item2, c_item3, c_item4 = st.columns([1, 1, 1, 1])
        with c_item1:
            try:
                def_qty = float(default_item_data.get("Qty", 1.0) or 1.0)
            except:
                def_qty = 1.0
            q_val = st.number_input(f"Qty {i+1}", value=def_qty, key=f"qty_{i}", disabled=is_management)
        with c_item2:
            default_u_opts = ["Month", "Day", "Ls", "Unit", "Trip", "Jam", "EA", "AU", "Kg", "Pallet", "Ltr"]
            existing_u_from_master = df_ref["Unit"].dropna().astype(str).unique().tolist() if "Unit" in df_ref.columns else []
            u_opts = sorted(list(set(default_u_opts + existing_u_from_master)))
            
            def_unit = str(default_item_data.get("Unit", unit_otomatis if not is_provisional else "AU"))
            if def_unit not in u_opts and def_unit:
                u_opts.insert(0, def_unit)
            idx_u = u_opts.index(def_unit) if def_unit in u_opts else 0
            u_val = st.selectbox(f"Unit {i+1}", u_opts, index=idx_u, key=f"unit_{i}", disabled=is_management)

        with c_item3:
            # PULL TANGGAL MULAI TERSIMPAN (TIDAK MERESET KE HARI INI)
            def_tm_str = str(default_item_data.get("Tanggal Mulai", ""))
            try:
                # Coba parse berbagai format tanggal (mendukung string bersih atau format lama dengan waktu)
                clean_tm_str = def_tm_str.split()[0] if def_tm_str else ""
                def_tm = datetime.strptime(clean_tm_str, "%Y-%m-%d").date()
            except:
                try:
                    def_tm = datetime.strptime(clean_tm_str, "%d %b %Y").date()
                except:
                    def_tm = date.today()
            tm_val = st.date_input(f"Tanggal Mulai {i+1}", value=def_tm, key=f"tm_{i}", disabled=is_management)

        with c_item4:
            # PULL TANGGAL SELESAI TERSIMPAN (TIDAK MERESET KE HARI INI)
            def_ts_str = str(default_item_data.get("Tanggal Selesai", ""))
            try:
                clean_ts_str = def_ts_str.split()[0] if def_ts_str else ""
                def_ts = datetime.strptime(clean_ts_str, "%Y-%m-%d").date()
            except:
                try:
                    def_ts = datetime.strptime(clean_ts_str, "%d %b %Y").date()
                except:
                    def_ts = date.today()
            ts_val = st.date_input(f"Tanggal Selesai {i+1}", value=def_ts, key=f"ts_{i}", disabled=is_management)

        if is_provisional:
            try:
                def_harga_manual = float(default_item_data.get("Harga Satuan", 0.0) or 0.0)
            except:
                def_harga_manual = 0.0
            hs_manual = st.number_input(f"Harga At Cost / Nilai Dasar {i+1} (Rp)", min_value=0.0, value=def_harga_manual, step=1000.0, format="%.2f", key=f"hs_prov_{i}", disabled=is_management)
            hs_final = hs_manual
        else:
            # AMBIL HARGA DARI DATA TERSIMPAN JIKA KATEGORI & SPESIFIKASI SAMA, ATAU DARI MASTER
            try:
                def_saved_hs = float(default_item_data.get("Harga Satuan", 0.0) or 0.0)
            except:
                def_saved_hs = 0.0
            
            if def_saved_hs > 0 and str(default_item_data.get("Deskripsi Pekerjaan", "")).strip() == str(spek_pilih).strip():
                hs_final = def_saved_hs
            else:
                hs_final = hs_otomatis

        formatted_hs = f"Rp {hs_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        if is_provisional:
            calc_total = (q_val * hs_final * 1.15) * (persen_val / 100.0)
        elif is_estimated_sum:
            calc_total = (q_val * hs_final * 0.9) * (persen_val / 100.0)
        else:
            calc_total = q_val * hs_final * (persen_val / 100.0)

        formatted_total = f"Rp {calc_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        col_info1, col_info2 = st.columns(2)
        with col_info1:
            if is_provisional:
                st.markdown(f"💰 **Nilai Dasar At Cost:** `{formatted_hs}`")
            else:
                st.markdown(f"💰 **Harga Satuan (Modul 0):** `{formatted_hs}`")
        with col_info2:
            if is_estimated_sum:
                st.markdown(f"📊 **Estimasi Total Harga (Diskon 10%):** `{formatted_total}`")
            elif is_provisional:
                st.markdown(f"📊 **Estimasi Total (At Cost + Fee 15%):** `{formatted_total}`")
            else:
                st.markdown(f"📊 **Estimasi Total Harga:** `{formatted_total}`")

        def_ket = str(default_item_data.get("Keterangan", ""))
        ket_val = st.text_input(f"Keterangan Tambahan {i+1}", value=def_ket, key=f"ket_{i}", disabled=is_management)
        st.markdown("---")

        items_data_input.append({
            "kategori": kat_pilih,
            "deskripsi": spek_pilih,
            "qty": q_val,
            "unit": u_val,
            # FORMAT TANGGAL DISIMPAN MURNI TANPA JAM (YYYY-MM-DD)
            "tgl_mulai": tm_val.strftime("%Y-%m-%d"),
            "tgl_selesai": ts_val.strftime("%Y-%m-%d"),
            "harga_satuan": hs_final,
            "keterangan": ket_val,
            "is_provisional": is_provisional,
            "is_estimated_sum": is_estimated_sum
        })

    grand_total_preview = 0
    for item_prev in items_data_input:
        if item_prev.get("is_provisional"):
            sub_prov = item_prev["qty"] * item_prev["harga_satuan"]
            grand_total_preview += (sub_prov * 1.15) * (persen_val / 100.0)
        elif item_prev.get("is_estimated_sum"):
            sub_est = item_prev["qty"] * item_prev["harga_satuan"] * 0.9
            grand_total_preview += sub_est * (persen_val / 100.0)
        else:
            grand_total_preview += (item_prev["qty"] * item_prev["harga_satuan"]) * (persen_val / 100.0)

    formatted_grand_total = f"Rp {grand_total_preview:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    st.markdown("---")
    st.markdown(f"### 🧮 **Grand Total Keseluruhan (Kontrol Input):** `{formatted_grand_total}`")
    st.markdown("---")

    with st.form("form_aksi_simpan_rincian"):
        if not is_management:
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                submit_tambah_baris = st.form_submit_button("➕ Tambah Baris Pekerjaan")
            with col_m2:
                submit_kurang_baris = st.form_submit_button("➖ Kurangi Baris Terakhir")

            st.markdown("---")
            col_btn_save, col_btn_dist = st.columns(2)
            with col_btn_save:
                submit_simpan_sementara = st.form_submit_button("💾 Simpan / Update Data Sementara", type="secondary")
            with col_btn_dist:
                submit_proses_distribusi = st.form_submit_button("🚀 Proses & Distribusikan Data ke Dokumen Turunan", type="primary")
        else:
            submit_tambah_baris, submit_kurang_baris, submit_simpan_sementara, submit_proses_distribusi = False, False, False, False
            st.info("ℹ️ Tombol manajemen baris, penyimpanan, dan distribusi data dinonaktifkan untuk akun Direksi.")

        if submit_tambah_baris:
            st.session_state.num_rows += 1
            st.rerun()

        if submit_kurang_baris and st.session_state.num_rows > 1:
            st.session_state.num_rows -= 1
            st.rerun()

        if submit_simpan_sementara:
            waktu_aksi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            existing_tx = muat_data_transaksi_func()
            pi_target_simpan = str(selected_pi).strip()
            
            existing_tx = [t for t in existing_tx if bersih_angka_func(t.get("PI No.")) != pi_target_simpan]

            prov_items = [it for it in items_data_input if it.get("is_provisional")]
            subtotal_prov = sum([it["qty"] * it["harga_satuan"] for it in prov_items])
            total_prov_with_fee = subtotal_prov * 1.15 

            for item in items_data_input:
                if item.get("is_provisional"):
                    if len(prov_items) > 0 and item == prov_items[0]:
                        total_harga = total_prov_with_fee * (persen_val / 100.0)
                    else:
                        total_harga = 0.0 
                elif item.get("is_estimated_sum"):
                    total_harga = (item["qty"] * item["harga_satuan"] * 0.9) * (persen_val / 100.0)
                else:
                    total_harga = (item["qty"] * item["harga_satuan"]) * (persen_val / 100.0)

                data_transaksi = {
                    "Nomor Kontrak": selected_kontrak,
                    "Nama Kontrak": nama_kontrak,
                    "Nomor Tender": nomor_tender,
                    "PI No.": selected_pi,
                    "Tanggal PI": tanggal_pi,
                    "Ditujukan Kepada": ditujukan_kepada,
                    "Alamat Pihak Pertama": alamat_pihak_pertama,
                    "Jangka Waktu Kontrak": jangka_waktu,
                    "Nomor PO": nomor_po,
                    "Nomor WO": nomor_wo,
                    "Nomor WAN / SA": nomor_wan_sa,
                    "Deskripsi PO": desc_po,
                    "Tanggal PO": tanggal_po,
                    "Mata Uang": mata_uang,
                    "Jenis BASTP": jenis_bastp_pilih, 
                    "Kategori": item["kategori"],
                    "Deskripsi Pekerjaan": item["deskripsi"],
                    "Qty": item["qty"],
                    "Unit": item["unit"],
                    "Percent": persen_val,
                    "Tanggal Mulai": item["tgl_mulai"],
                    "Tanggal Selesai": item["tgl_selesai"],
                    "Harga Satuan": item["harga_satuan"],
                    "Total Harga": total_harga,
                    "Bank Name": bank_name,
                    "Bank Branch": bank_branch,
                    "Account No": bank_acc_no,
                    "Account Name": bank_acc_name,
                    "Attn": attn_to,
                    "Keterangan": item["keterangan"],
                    "Update Terakhir": waktu_aksi
                }
                existing_tx.append(data_transaksi)

            if simpan_data_transaksi_func(existing_tx):
                st.success(f"💾 Berhasil menyimpan data sementara secara permanen ke file lokal Excel untuk PI [{pi_target_simpan}]!")
            st.rerun()

        if submit_proses_distribusi:
            waktu_aksi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            existing_tx = muat_data_transaksi_func()
            pi_baru = str(selected_pi).strip()
            
            existing_tx = [t for t in existing_tx if bersih_angka_func(t.get("PI No.")) != pi_baru]

            prov_items = [it for it in items_data_input if it.get("is_provisional")]
            subtotal_prov = sum([it["qty"] * it["harga_satuan"] for it in prov_items])
            total_prov_with_fee = subtotal_prov * 1.15

            for item in items_data_input:
                if item.get("is_provisional"):
                    if len(prov_items) > 0 and item == prov_items[0]:
                        total_harga = total_prov_with_fee * (persen_val / 100.0)
                    else:
                        total_harga = 0.0
                elif item.get("is_estimated_sum"):
                    total_harga = (item["qty"] * item["harga_satuan"] * 0.9) * (persen_val / 100.0)
                else:
                    total_harga = (item["qty"] * item["harga_satuan"]) * (persen_val / 100.0)

                data_transaksi = {
                    "Nomor Kontrak": selected_kontrak,
                    "Nama Kontrak": nama_kontrak,
                    "Nomor Tender": nomor_tender,
                    "PI No.": selected_pi,
                    "Tanggal PI": tanggal_pi,
                    "Ditujukan Kepada": ditujukan_kepada,
                    "Alamat Pihak Pertama": alamat_pihak_pertama,
                    "Jangka Waktu Kontrak": jangka_waktu,
                    "Nomor PO": nomor_po,
                    "Nomor WO": nomor_wo,
                    "Nomor WAN / SA": nomor_wan_sa,
                    "Deskripsi PO": desc_po,
                    "Tanggal PO": tanggal_po,
                    "Mata Uang": mata_uang,
                    "Jenis BASTP": jenis_bastp_pilih, 
                    "Kategori": item["kategori"],
                    "Deskripsi Pekerjaan": item["deskripsi"],
                    "Qty": item["qty"],
                    "Unit": item["unit"],
                    "Percent": persen_val,
                    "Tanggal Mulai": item["tgl_mulai"],
                    "Tanggal Selesai": item["tgl_selesai"],
                    "Harga Satuan": item["harga_satuan"],
                    "Total Harga": total_harga,
                    "Bank Name": bank_name,
                    "Bank Branch": bank_branch,
                    "Account No": bank_acc_no,
                    "Account Name": bank_acc_name,
                    "Attn": attn_to,
                    "Keterangan": item["keterangan"],
                    "Update Terakhir": waktu_aksi
                }
                existing_tx.append(data_transaksi)

            if simpan_data_transaksi_func(existing_tx):
                st.session_state.num_rows = 1
                st.success(f"🎉 Berhasil mendistribusikan data secara permanen ke file lokal Excel untuk Proforma Invoice [{pi_baru}]!")
            st.rerun()