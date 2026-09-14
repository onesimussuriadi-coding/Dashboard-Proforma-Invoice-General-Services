# modul_input/modul_1_database.py
import streamlit as st
import pandas as pd
from datetime import datetime, date

def tampilkan_modul_1_database(menu, saved_db_list, bersih_angka_func, parse_date_func, sort_pi_key_func, simpan_data_invoice_func, muat_data_invoice_func):
    
    # ==========================================
    # MENU 1: INPUT DATABASE & INVOICE (31 KOLOM)
    # ==========================================
    if menu == "Input Database & Invoice (31 Kolom)":
        st.markdown("""
            <div class="dashboard-card">
                <h4 style="margin-top:0; color:#065f46; font-size:15px;">🔍 Panggil Ulang Berdasarkan Nomor Kontrak & Nomor PI</h4>
            </div>
        """, unsafe_allow_html=True)

        if len(saved_db_list) > 0:
            list_kontrak_db = sorted(list(set(bersih_angka_func(data.get(1, data.get('Nomor Kontrak', '-'))) for data in saved_db_list if isinstance(data, dict) and bersih_angka_func(data.get(1, data.get('Nomor Kontrak', '-'))) != '')))
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
                    [(i, d) for i, d in enumerate(saved_db_list) if isinstance(d, dict) and bersih_angka_func(d.get(1, d.get('Nomor Kontrak', '-'))) == selected_kontrak_input], 
                    key=lambda x: (sort_pi_key_func(x[1].get(0, x[1].get('Proforma Invoice No.', ''))), x[0]), 
                    reverse=True
                )
                
                opsi_pi_filtered = []
                index_mapping = {}
                for orig_idx, data in matched_pi_records_sorted:
                    pi_num = bersih_angka_func(data.get(0, data.get('Proforma Invoice No.', '-')))
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
        if st.session_state.get("edit_index") is not None and st.session_state["edit_index"] < len(st.session_state.get("db_tersimpan", [])):
            def_data = st.session_state["db_tersimpan"][st.session_state["edit_index"]]
        
        def get_val(idx_key, text_key):
            val = def_data.get(idx_key, def_data.get(text_key, def_data.get(str(idx_key), "")))
            cleaned = bersih_angka_func(val)
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
                    d_val = parse_date_func(default_str)
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
            c1.write("**13.**")
            c2.write("Diwakili Oleh")
            pilihan_p1 = [
                "Ronny Dwi Purnomo / Rafik Hidayat",
                "Rafik Hidayat / Ronny Dwi Purnomo",
                "Irwan / Budi Bernadi",
                "Budi Bernadi / Irwan",
                "Aldito Fauzi Roe / Aryanto Yoga",
                "Aryanto Yoga / Aldito Fauzi Roe",
            ]
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
            c1.write("**28.**")
            c2.write("Approved by 1")
            pilihan_app1 = [
                "--- (Tidak Ada / Kosong) ---",
                "Imron Maulana / Moh Bazarul Aqhsa",
                "Moh Bazarul Aqhsa / Imron Maulana",
                "Irwan / Budi Bernadi",
                "Budi Bernadi / Irwan",
                "Aldito Fauzi Roe / Aryanto Yoga",
                "Aryanto Yoga / Aldito Fauzi Roe"
            ]
            def_app1 = get_val(27, "Approved by 1")
            idx_app1 = pilihan_app1.index(def_app1) if def_app1 in pilihan_app1 else 0
            val_28 = c3.selectbox("Approved by 1", pilihan_app1, index=idx_app1, label_visibility="collapsed")

            val_29 = baris_input_bersih(29, "Approved by Title 1", default_val=get_val(28, "Approved by Title 1"))

            c1, c2, c3 = st.columns([0.8, 3.5, 7])
            c1.write("**30.**")
            c2.write("Approved by 2")
            pilihan_app2 = [
                "--- (Tidak Ada / Kosong) ---",
                "Abidsar",
                "Imron Maulana",
                "Moh Bazarul Aqhsa"
            ]
            def_app2 = get_val(29, "Approved by 2")
            idx_app2 = pilihan_app2.index(def_app2) if def_app2 in pilihan_app2 else 0
            val_30 = c3.selectbox("Approved by 2", pilihan_app2, index=idx_app2, label_visibility="collapsed")

            val_31 = baris_input_bersih(31, "Approved by Title 2", default_val=get_val(30, "Approved by Title 2"))

            st.markdown("---")
            
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                submit_baru = st.form_submit_button("💾 Simpan Data Baru")
            with col_btn2:
                submit_save_as = st.form_submit_button("📥 Save As (Buat PI Baru)")
            with col_btn3:
                submit_update = st.form_submit_button("📝 Update Data Ini")
            
            if submit_baru or submit_save_as or submit_update:
                waktu_aksi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data_terinput = {
                    0: bersih_angka_func(val_6), 1: bersih_angka_func(val_1), 2: bersih_angka_func(val_2), 3: val_10, 4: val_4, 5: val_5, 6: val_7, 7: val_3, 
                    8: bersih_angka_func(val_8), 9: val_9, 10: val_11, 11: val_12, 12: val_13, 13: val_14, 14: val_15, 
                    15: val_16, 16: val_17, 17: val_18, 18: val_19, 19: bersih_angka_func(val_20), 20: val_21, 21: bersih_angka_func(val_22), 
                    22: val_23, 23: bersih_angka_func(val_24), 24: val_25, 25: val_26, 26: val_27, 27: val_28, 28: val_29,
                    29: val_30, 30: val_31,
                    "Update Terakhir": waktu_aksi
                }
                current_data = muat_data_invoice_func()
                if submit_update:
                    if st.session_state.get("edit_index") is not None and st.session_state["edit_index"] < len(current_data):
                        current_data[st.session_state["edit_index"]] = data_terinput
                        if simpan_data_invoice_func(current_data):
                            st.success("✨ Data berhasil diperbarui secara permanen ke file lokal Excel!")
                elif submit_save_as or submit_baru:
                    current_data.append(data_terinput)
                    if simpan_data_invoice_func(current_data):
                        st.success("🎉 Data berhasil disimpan secara permanen ke file lokal Excel!")
                        st.session_state["edit_index"] = None
                st.rerun()

    # ==========================================
    # MENU 2: LIHAT DATABASE TERSIMPAN (RAPI & PADAT)
    # ==========================================
    elif menu == "Lihat Database Tersimpan":
        st.markdown("""
            <div class="dashboard-card">
                <h3 style="margin-top:0; color:#065f46; font-size:18px;">📂 Ringkasan Database Kontrak & Proforma Invoice</h3>
            </div>
        """, unsafe_allow_html=True)

        records = muat_data_invoice_func()
        if not records:
            st.info("ℹ️ Belum ada data database tersimpan di folder aman.")
            return

        # Ekstrak data terstruktur untuk filter & tabel
        summary_list = []
        for orig_idx, d in enumerate(records):
            if isinstance(d, dict):
                k_no = bersih_angka_func(d.get(1, d.get("Nomor Kontrak", "-")))
                pi_no = bersih_angka_func(d.get(0, d.get("Proforma Invoice No.", "-")))
                po_no = bersih_angka_func(d.get(8, d.get("Nomor Purchase Order", "-")))
                wo_no = bersih_angka_func(d.get(21, d.get("Nomor WO", "-")))
                ctr_no = bersih_angka_func(d.get(23, d.get("Nomor CTR", "-")))
                tgl_pi = bersih_angka_func(d.get(6, d.get("Tanggal Performa Invoice", "-")))
                upd_time = bersih_angka_func(d.get("Update Terakhir", "-"))

                summary_list.append({
                    "Index": orig_idx,
                    "Nomor Kontrak": k_no if k_no else "-",
                    "Nomor PI": pi_no if pi_no else "-",
                    "Nomor PO": po_no if po_no else "-",
                    "Nomor WO": wo_no if wo_no else "-",
                    "Nomor CTR": ctr_no if ctr_no else "-",
                    "Tanggal PI": tgl_pi if tgl_pi else "-",
                    "Update Terakhir": upd_time if upd_time else "-"
                })

        df_sum = pd.DataFrame(summary_list)

        # Dropdown Filter Kontrak & PI
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            list_kontrak_opt = ["-- Semua Nomor Kontrak --"] + sorted(list(df_sum["Nomor Kontrak"].unique()))
            sel_kontrak = st.selectbox("📌 Filter Nomor Kontrak:", list_kontrak_opt, key="db_view_kontrak")

        df_filtered = df_sum.copy()
        if sel_kontrak != "-- Semua Nomor Kontrak --":
            df_filtered = df_filtered[df_filtered["Nomor Kontrak"] == sel_kontrak]

        with col_f2:
            list_pi_opt = ["-- Semua Nomor PI --"] + sorted(list(df_filtered["Nomor PI"].unique()), key=sort_pi_key_func, reverse=True)
            sel_pi = st.selectbox("🧾 Filter Nomor PI:", list_pi_opt, key="db_view_pi")

        if sel_pi != "-- Semua Nomor PI --":
            df_filtered = df_filtered[df_filtered["Nomor PI"] == sel_pi]

        st.markdown(f"**Menampilkan {len(df_filtered)} dari total {len(df_sum)} data tersimpan:**")
        st.markdown("---")

        # HTML Table padat, bersih, dan rapi
        table_rows = ""
        for idx, row in df_filtered.iterrows():
            orig_i = row["Index"]
            table_rows += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 8px 10px; text-align: center; font-weight: bold; color: #475569; font-size: 13px;">#{orig_i+1}</td>
                <td style="padding: 8px 10px; font-weight: bold; color: #0f172a; font-size: 13px;">{row['Nomor Kontrak']}</td>
                <td style="padding: 8px 10px; color: #0284c7; font-weight: 600; font-size: 13px;">{row['Nomor PI']}</td>
                <td style="padding: 8px 10px; color: #334155; font-size: 13px;">{row['Nomor PO']}</td>
                <td style="padding: 8px 10px; color: #334155; font-size: 13px;">{row['Nomor WO']}</td>
                <td style="padding: 8px 10px; color: #334155; font-size: 13px;">{row['Nomor CTR']}</td>
                <td style="padding: 8px 10px; text-align: center; color: #64748b; font-size: 12px;">{row['Tanggal PI']}</td>
            </tr>
            """

        table_html = f"""
        <div style="overflow-x: auto; border: 1px solid #cbd5e1; border-radius: 8px; background-color: #ffffff;">
            <table style="width: 100%; border-collapse: collapse; text-align: left; font-family: sans-serif;">
                <thead>
                    <tr style="background-color: #1e293b; color: #ffffff; font-size: 13px;">
                        <th style="padding: 10px; text-align: center; width: 50px;">No</th>
                        <th style="padding: 10px;">Nomor Kontrak</th>
                        <th style="padding: 10px;">Nomor PI</th>
                        <th style="padding: 10px;">Nomor PO</th>
                        <th style="padding: 10px;">Nomor WO</th>
                        <th style="padding: 10px;">Nomor CTR</th>
                        <th style="padding: 10px; text-align: center;">Tanggal PI</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        """
        st.components.v1.html(table_html, height=450, scrolling=True)