import streamlit as st
import pandas as pd
from datetime import datetime, date

def bersih_angka(val):
    if val is None:
        return ""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    if s.lower() == "nan":
        return ""
    return s

def sort_pi_key(pi_str):
    try:
        parts = str(pi_str).split('/')
        if parts:
            digits = "".join([c for c in parts[0] if c.isdigit()])
            return int(digits) if digits else 0
    except:
        pass
    return 0

def parse_date_safely(val_str):
    if not val_str or str(val_str).strip().lower() == "nan":
        return date.today()
    val_cleaned = str(val_str).strip()
    formats = ["%d %b %Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%b %d, %Y", "%d %B %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(val_cleaned, fmt).date()
        except ValueError:
            continue
    try:
        return pd.to_datetime(val_cleaned).date()
    except:
        pass
    return date.today()

def tampilkan_modul_input(muat_data_invoice_func, simpan_data_invoice_func, menu_pilihan_sub):
    if menu_pilihan_sub == "Input Database & Invoice (31 Kolom)":
        st.markdown("""
            <div class="dashboard-card">
                <h4 style="margin-top:0; color:#065f46; font-size:15px;">🔍 Panggil Ulang Berdasarkan Nomor Kontrak & Nomor PI</h4>
            </div>
        """, unsafe_allow_html=True)

        saved_db_list = muat_data_invoice_func()

        if len(saved_db_list) > 0:
            list_kontrak_db = sorted(list(set(bersih_angka(data.get(1, data.get('Nomor Kontrak', '-'))) for data in saved_db_list if isinstance(data, dict) and bersih_angka(data.get(1, data.get('Nomor Kontrak', '-'))) != '')))
            opsi_kontrak_input = ["-- Buat Data Baru (Formulir Kosong) --"] + list_kontrak_db

            col_pk1, col_pk2, col_pk_btn = st.columns([2, 2.5, 1])
            with col_pk1:
                selected_kontrak_input = st.selectbox("Pilih Nomor Kontrak:", opsi_kontrak_input, key="input_filter_kontrak")

            if selected_kontrak_input == "-- Buat Data Baru (Formulir Kosong) --":
                with col_pk2:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    st.info("Formulir siap untuk data baru.")
                with col_pk_btn:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    if st.button("🔄 Panggil"):
                        st.session_state["edit_index"] = None
                        st.rerun()
            else:
                matched_pi_records_sorted = sorted(
                    [(i, d) for i, d in enumerate(saved_db_list) if isinstance(d, dict) and bersih_angka(d.get(1, d.get('Nomor Kontrak', '-'))) == selected_kontrak_input], 
                    key=lambda x: (sort_pi_key(x[1].get(0, x[1].get('Proforma Invoice No.', ''))), x[0]), 
                    reverse=True
                )
                
                opsi_pi_filtered = []
                index_mapping = {}
                for orig_idx, data in matched_pi_records_sorted:
                    pi_num = bersih_angka(data.get(0, data.get('Proforma Invoice No.', '-')))
                    label_pi = f"PI: {pi_num if pi_num else '-'} (Data {orig_idx+1})"
                    opsi_pi_filtered.append(label_pi)
                    index_mapping[label_pi] = orig_idx

                with col_pk2:
                    selected_pi_label = st.selectbox(f"Pilih Nomor PI untuk Kontrak [{selected_kontrak_input}]:", opsi_pi_filtered if opsi_pi_filtered else ["-- Tidak Ada PI --"], key="input_filter_pi")
                
                with col_pk_btn:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    if st.button("🔄 Panggil"):
                        if selected_pi_label != "-- Tidak Ada PI --" and selected_pi_label in index_mapping:
                            st.session_state["edit_index"] = index_mapping[selected_pi_label]
                        else:
                            st.session_state["edit_index"] = None
                        st.rerun()
        else:
            st.info("📌 Belum ada data database tersimpan di folder aman.")

        def_data = {}
        if st.session_state.get("edit_index") is not None and st.session_state["edit_index"] < len(saved_db_list):
            def_data = saved_db_list[st.session_state["edit_index"]]
        
        def get_val(idx_key, text_key):
            val = def_data.get(idx_key, def_data.get(text_key, ""))
            cleaned = bersih_angka(val)
            return cleaned if cleaned else ""

        with st.form("form_input_database"):
            col_no, col_item, col_input = st.columns([0.8, 3.5, 7])
            with col_no: st.markdown("**No**")
            with col_item: st.markdown("**Item**")
            with col_input: st.markdown("**Kolom Input Data (Bersih & Standar)**")
            st.markdown("---")

            def baris_input_bersih(no, label, default_val="", is_area=False):
                c1, c2, c3 = st.columns([0.8, 3.5, 7])
                with c1: c1.write(f"**{no}.**")
                with c2: c2.write(label)
                with c3:
                    if is_area:
                        return st.text_area(f"input_{no}", value=str(default_val), label_visibility="collapsed", height=75)
                    else:
                        return st.text_input(f"input_{no}", value=str(default_val), label_visibility="collapsed")

            def baris_input_tanggal(no, label, default_str=""):
                c1, c2, c3 = st.columns([0.8, 3.5, 7])
                with c1: c1.write(f"**{no}.**")
                with c2: c2.write(label)
                with c3:
                    d_val = parse_date_safely(default_str)
                    dt_res = st.date_input(f"input_{no}", value=d_val, label_visibility="collapsed")
                    return dt_res.strftime("%d %b %Y")

            val_1  = baris_input_bersih(1, "Nomor Kontrak", default_val=get_val(1, "Nomor Kontrak"))
            val_2  = baris_input_bersih(2, "Nomor Tender", default_val=get_val(2, "Nomor Tender"))
            val_3  = baris_input_bersih(3, "Judul Kontrak", default_val=get_val(7, "Judul Kontrak"), is_area=True)
            val_4  = baris_input_tanggal(4, "Tanggal Kontrak", default_str=get_val(4, "Tanggal Kontrak"))
            val_5  = baris_input_bersih(5, "Jangka Waktu Kontrak", default_val=get_val(5, "Jangka Waktu Kontrak"))
            val_6  = baris_input_bersih(6, "Proforma Invoice No.", default_val=get_val(0, "Proforma Invoice No."))
            val_7  = baris_input_tanggal(7, "Tanggal Performa Invoice", default_str=get_val(6, "Tanggal Performa Invoice"))
            val_8  = baris_input_bersih(8, "Nomor Purchase Order", default_val=get_val(8, "Nomor Purchase Order"))
            val_9  = baris_input_tanggal(9, "Tanggal Purchase Order", default_str=get_val(9, "Tanggal Purchase Order"))
            val_10 = baris_input_bersih(10, "Lingkup Pekerjaan", default_val=get_val(3, "Lingkup Pekerjaan"), is_area=True)
            val_11 = baris_input_bersih(11, "Pihak Pertama", default_val=get_val(10, "Pihak Pertama"))
            val_12 = baris_input_bersih(12, "Alamat Pihak Pertama", default_val=get_val(11, "Alamat Pihak Pertama"), is_area=True)
            
            c1, c2, c3 = st.columns([0.8, 3.5, 7])
            c1.write("**13.**"); c2.write("Diwakili Oleh")
            pilihan_p1 = ["Ronny Dwi Purnomo / Rafik Hidayat", "Rafik Hidayat / Ronny Dwi Purnomo", "Irwan / Budi Bernadi", "Budi Bernadi / Irwan"]
            def_p1 = get_val(12, "Diwakili Oleh")
            idx_p1 = pilihan_p1.index(def_p1) if def_p1 in pilihan_p1 else 0
            val_13 = c3.selectbox("Diwakili Oleh P1", pilihan_p1, index=idx_p1, label_visibility="collapsed")

            val_14 = baris_input_bersih(14, "Selaku", default_val=get_val(13, "Selaku"))
            val_15 = baris_input_bersih(15, "Pihak Kedua", default_val=get_val(14, "Pihak Kedua"))
            val_16 = baris_input_bersih(16, "Alamat Pihak Kedua", default_val=get_val(15, "Alamat Pihak Kedua"), is_area=True)
            val_17 = baris_input_bersih(17, "Diwakili Oleh (P2)", default_val=get_val(16, "Diwakili Oleh (P2)"))
            val_18 = baris_input_bersih(18, "Selaku (P2)", default_val=get_val(17, "Selaku (P2)"))
            val_19 = baris_input_bersih(19, "Periode Pekerjaan", default_val=get_val(18, "Periode Pekerjaan"))
            val_20 = baris_input_bersih(20, "Nomor WCC", default_val=get_val(19, "Nomor WCC"))
            val_21 = baris_input_tanggal(21, "Tanggal WCC", default_str=get_val(20, "Tanggal WCC"))
            val_22 = baris_input_bersih(22, "Nomor WO", default_val=get_val(21, "Nomor WO"))
            val_23 = baris_input_bersih(23, "Keterangan WO", default_val=get_val(22, "Keterangan WO"), is_area=True)
            val_24 = baris_input_bersih(24, "Nomor CTR", default_val=get_val(23, "Nomor CTR"))
            val_25 = baris_input_bersih(25, "Progress Pekerjaan", default_val=get_val(24, "Progress Pekerjaan"))
            val_26 = baris_input_bersih(26, "Prepared by Name", default_val=get_val(25, "Prepared by Name"))
            val_27 = baris_input_bersih(27, "Prepared by Title", default_val=get_val(26, "Prepared by Title"))

            c1, c2, c3 = st.columns([0.8, 3.5, 7])
            c1.write("**28.**"); c2.write("Approved by 1")
            pilihan_app1 = ["--- (Tidak Ada / Kosong) ---", "Imron Maulana / Moh Bazarul Aqhsa", "Moh Bazarul Aqhsa / Imron Maulana"]
            def_app1 = get_val(27, "Approved by 1")
            idx_app1 = pilihan_app1.index(def_app1) if def_app1 in pilihan_app1 else 0
            val_28 = c3.selectbox("Approved by 1", pilihan_app1, index=idx_app1, label_visibility="collapsed")

            val_29 = baris_input_bersih(29, "Approved by Title 1", default_val=get_val(28, "Approved by Title 1"))

            c1, c2, c3 = st.columns([0.8, 3.5, 7])
            c1.write("**30.**"); c2.write("Approved by 2")
            pilihan_app2 = ["--- (Tidak Ada / Kosong) ---", "Abidsar", "Imron Maulana", "Moh Bazarul Aqhsa"]
            def_app2 = get_val(29, "Approved by 2")
            idx_app2 = pilihan_app2.index(def_app2) if def_app2 in pilihan_app2 else 0
            val_30 = c3.selectbox("Approved by 2", pilihan_app2, index=idx_app2, label_visibility="collapsed")

            val_31 = baris_input_bersih(31, "Approved by Title 2", default_val=get_val(30, "Approved by Title 2"))

            st.markdown("---")
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1: submit_baru = st.form_submit_button("💾 Simpan Data Baru")
            with col_btn2: submit_save_as = st.form_submit_button("📥 Save As (Buat PI Baru)")
            with col_btn3: submit_update = st.form_submit_button("📝 Update Data Ini")

            if submit_baru or submit_save_as or submit_update:
                waktu_aksi = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S") if 'timedelta' in globals() else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data_terinput = {
                    0: bersih_angka(val_6), 1: bersih_angka(val_1), 2: bersih_angka(val_2), 3: val_10, 4: val_4, 5: val_5, 6: val_7, 7: val_3, 
                    8: bersih_angka(val_8), 9: val_9, 10: val_11, 11: val_12, 12: val_13, 13: val_14, 14: val_15, 
                    15: val_16, 16: val_17, 17: val_18, 18: val_19, 19: bersih_angka(val_20), 20: val_21, 21: bersih_angka(val_22), 
                    22: val_23, 23: bersih_angka(val_24), 24: val_25, 25: val_26, 26: val_27, 27: val_28, 28: val_29,
                    29: val_30, 30: val_31,
                    "Update Terakhir": waktu_aksi
                }
                current_data = muat_data_invoice_func()
                if submit_update and st.session_state.get("edit_index") is not None and st.session_state["edit_index"] < len(current_data):
                    current_data[st.session_state["edit_index"]] = data_terinput
                    simpan_data_invoice_func(current_data)
                    st.success("✨ Data berhasil diperbarui!")
                elif submit_save_as or submit_baru:
                    current_data.append(data_terinput)
                    simpan_data_invoice_func(current_data)
                    st.success("🎉 Data berhasil disimpan!")
                    st.session_state["edit_index"] = None

    elif menu_pilihan_sub == "Lihat Database Tersimpan":
        st.markdown("""
            <div class="dashboard-card">
                <h3 style="margin-top:0; color:#065f46; font-size:18px;">📂 Daftar Database Identifikasi Tersimpan</h3>
                <p style="font-size: 13px; color: #475569; margin-bottom: 0;">Kelola dan tampilkan rincian lengkap data tersimpan secara transparan.</p>
            </div>
        """, unsafe_allow_html=True)

        saved_records = muat_data_invoice_func()
        if not saved_records:
            st.info("ℹ️ Belum ada data database tersimpan di folder aman.")
        else:
            list_all_kontrak = ["-- Semua Kontrak (All Contracts) --"] + sorted(list(set(
                bersih_angka(rec.get(1, rec.get('Nomor Kontrak', '-'))) for rec in saved_records if bersih_angka(rec.get(1, rec.get('Nomor Kontrak', '-'))) != ''
            )))

            col_fdb1, col_fdb2 = st.columns(2)
            with col_fdb1:
                selected_filter_kontrak = st.selectbox("📌 Filter Berdasarkan Nomor Kontrak:", list_all_kontrak, key="db_filter_kontrak_v5")

            pi_filtered_candidates = [
                bersih_angka(rec.get(0, rec.get('Proforma Invoice No.', '-'))) 
                for rec in saved_records 
                if (selected_filter_kontrak == "-- Semua Kontrak (All Contracts) --" or bersih_angka(rec.get(1, rec.get('Nomor Kontrak', '-'))) == selected_filter_kontrak) 
                and bersih_angka(rec.get(0, rec.get('Proforma Invoice No.', '-'))) != ''
            ]

            list_all_pi = ["-- Semua PI (All PI) --"] + sorted(list(set(pi_filtered_candidates)), key=sort_pi_key, reverse=True)

            with col_fdb2:
                selected_filter_pi = st.selectbox("📄 Filter Berdasarkan Nomor PI:", list_all_pi, key="db_filter_pi_v5")

            st.markdown("---")

            filtered_records_list = []
            for original_idx, rec in enumerate(saved_records):
                c_kontrak = bersih_angka(rec.get(1, rec.get('Nomor Kontrak', '-')))
                c_pi = bersih_angka(rec.get(0, rec.get('Proforma Invoice No.', '-')))

                match_k = (selected_filter_kontrak == "-- Semua Kontrak (All Contracts) --") or (c_kontrak == selected_filter_kontrak)
                match_pi = (selected_filter_pi == "-- Semua PI (All PI) --") or (c_pi == selected_filter_pi)

                if match_k and match_pi:
                    filtered_records_list.append((original_idx, rec))

            if not filtered_records_list:
                st.warning("⚠️ Tidak ada data database yang cocok dengan filter yang dipilih.")
            else:
                st.info(f"Menampilkan {len(filtered_records_list)} data tersimpan secara transparan:")
                filtered_records_list_sorted = sorted(filtered_records_list, key=lambda x: x[0], reverse=True)

                for original_idx, rec in filtered_records_list_sorted:
                    pi_num = bersih_angka(rec.get(0, rec.get('Proforma Invoice No.', '-')))
                    kontrak_num = bersih_angka(rec.get(1, rec.get('Nomor Kontrak', '-')))
                    po_num = bersih_angka(rec.get(8, rec.get('Nomor Purchase Order', '-')))
                    wo_num = bersih_angka(rec.get(21, rec.get('Nomor WO', '-')))
                    ctr_num = bersih_angka(rec.get(23, rec.get('Nomor CTR', '-')))
                    judul_k = bersih_angka(rec.get(7, rec.get('Judul Kontrak', '-')))

                    with st.container():
                        st.markdown(f"""
                            <div style="background: #f8fafc; border: 1px solid #cbd5e1; padding: 12px 15px; border-radius: 6px; margin-bottom: 10px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                    <span style="font-weight: bold; color: #0f172a; font-size: 14px;">📄 PI No: {pi_num if pi_num else '-'}</span>
                                    <span style="background: #e2e8f0; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">Kontrak: {kontrak_num if kontrak_num else '-'}</span>
                                </div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; font-size: 12px; color: #334155; margin-bottom: 6px;">
                                    <div><b>Nomor PO:</b> {po_num if po_num else '-'}</div>
                                    <div><b>Nomor WO:</b> {wo_num if wo_num else '-'}</div>
                                    <div><b>Nomor CTR:</b> {ctr_num if ctr_num else '-'}</div>
                                </div>
                                <div style="font-size: 12px; color: #475569; border-top: 1px dashed #cbd5e1; padding-top: 6px;">
                                    <b>Judul / Lingkup:</b> {judul_k if judul_k else '-'}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("🗑️ Hapus Permanen Baris Ini", key=f"del_db_row_clean_{original_idx}"):
                            saved_records.pop(original_idx)
                            simpan_data_invoice_func(saved_records)
                            st.success("✅ Berhasil menghapus baris data database secara permanen!")
                            st.rerun()