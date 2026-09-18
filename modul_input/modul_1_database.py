import streamlit as st
import pandas as pd
from datetime import datetime, date

def tampilkan_modul_1_database(menu, saved_db_list, bersih_angka_func, parse_date_func, sort_pi_key_func, simpan_data_invoice_func, muat_data_invoice_func):
    current_role_user = str(st.session_state.get("current_role", "")).strip().lower()
    is_management = current_role_user in ["management", "direksi"]

    query_params = st.query_params
    if "delete_db_idx" in query_params:
        if is_management:
            st.error("❌ Akses Ditolak! Akun Direksi berada dalam mode Read-Only dan tidak diizinkan menghapus data.")
            st.query_params.clear()
            st.rerun()
        else:
            try:
                del_idx = int(query_params["delete_db_idx"])
                all_db = muat_data_invoice_func()
                if 0 <= del_idx < len(all_db):
                    deleted_pi = bersih_angka_func(all_db[del_idx].get(0, all_db[del_idx].get('Proforma Invoice No.', '-')))
                    all_db.pop(del_idx)
                    if simpan_data_invoice_func(all_db):
                        st.success(f"🗑️ Berhasil menghapus data PI [{deleted_pi}] secara permanen!")
                    st.query_params.clear()
                    st.rerun()
            except Exception as e:
                st.error(f"Gagal menghapus data: {e}")

    if menu == "Input Database & Invoice (31 Kolom)":
        st.markdown("""
            <div style="background-color: #ffffff; border: 1px solid #cbd5e1; padding: 15px 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 20px;">
                <h4 style="margin:0; color:#0f172a; font-size:15px; font-weight:700;">🔍 Panggil Ulang Berdasarkan Nomor Kontrak & Nomor PI</h4>
            </div>
        """, unsafe_allow_html=True)

        if is_management:
            st.info("🔒 **Mode Direksi (Read-Only):** Formulir 31 kolom ditampilkan dalam mode baca saja (Read-Only). Anda dapat meninjau seluruh parameter kontrak dan PI secara lengkap.")

        if len(saved_db_list) > 0:
            list_kontrak_db = sorted(list(set(bersih_angka_func(data.get(1, data.get('Nomor Kontrak', '-'))) for data in saved_db_list if isinstance(data, dict) and bersih_angka_func(data.get(1, data.get('Nomor Kontrak', '-'))) != '')))
            opsi_kontrak_input = ["-- Buat Data Baru (Formulir Kosong) --"] + list_kontrak_db

            col_pk1, col_pk2, col_pk_btn = st.columns([2, 2.5, 1])
            with col_pk1:
                selected_kontrak_input = st.selectbox("Pilih Nomor Kontrak:", opsi_kontrak_input, key="input_filter_kontrak")

            if selected_kontrak_input == "-- Buat Data Baru (Formulir Kosong) --":
                with col_pk2:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    st.info("💡 Formulir siap untuk ditinjau / data baru.")
                with col_pk_btn:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    if st.button("🔄 Panggil"):
                        st.session_state["edit_index"] = None
                        st.session_state["active_pi_key"] = None
                        st.rerun()
            else:
                matched_pi_records_sorted = sorted(
                    [(i, d) for i, d in enumerate(saved_db_list) if isinstance(d, dict) and bersih_angka_func(d.get(1, d.get('Nomor Kontrak', '-'))) == selected_kontrak_input], 
                    key=lambda x: (sort_pi_key_func(x[1].get(0, x[1].get('Proforma Invoice No.', ''))), x[0]), 
                    reverse=True
                )
                
                opsi_pi_filtered = []
                index_mapping = {}
                pi_mapping = {}
                for orig_idx, data in matched_pi_records_sorted:
                    pi_num = bersih_angka_func(data.get(0, data.get('Proforma Invoice No.', '-')))
                    label_pi = f"PI: {pi_num if pi_num else '-'} (Data #{orig_idx+1})"
                    opsi_pi_filtered.append(label_pi)
                    index_mapping[label_pi] = orig_idx
                    pi_mapping[label_pi] = pi_num

                with col_pk2:
                    selected_pi_label = st.selectbox(f"Pilih Nomor PI [{selected_kontrak_input}]:", opsi_pi_filtered if opsi_pi_filtered else ["-- Tidak Ada PI --"], key="input_filter_pi")
                
                with col_pk_btn:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    if st.button("🔄 Panggil Data", use_container_width=True, type="primary"):
                        if selected_pi_label != "-- Tidak Ada PI --" and selected_pi_label in index_mapping:
                            st.session_state["edit_index"] = index_mapping[selected_pi_label]
                            st.session_state["active_pi_key"] = pi_mapping[selected_pi_label]
                        else:
                            st.session_state["edit_index"] = None
                            st.session_state["active_pi_key"] = None
                        st.rerun()
        else:
            st.info("📌 Belum ada data database tersimpan di folder aman.")

        # --- MEKANISME PENGUNCIAN DATA BERBASIS STATE & NOMOR PI ---
        def_data = {}
        edit_idx = st.session_state.get("edit_index")
        
        if edit_idx is not None and edit_idx < len(st.session_state.get("db_tersimpan", [])):
            def_data = st.session_state["db_tersimpan"][edit_idx]
            current_pi_val = bersih_angka_func(def_data.get(0, def_data.get('Proforma Invoice No.', '-')))
            st.session_state["active_pi_key"] = current_pi_val
            st.warning(f"📝 **Mode Tinjau Data:** Menampilkan Data Baris #{edit_idx+1} — PI No: `{current_pi_val}`")
        
        # Simpan nilai inputan sementara di session berdasarkan PI aktif agar tidak hilang saat refresh kode
        active_pi = st.session_state.get("active_pi_key", "default_form")
        storage_state_key = f"form_cache_{active_pi}".replace("/", "_")
        
        if storage_state_key not in st.session_state:
            st.session_state[storage_state_key] = def_data

        cached_data = st.session_state[storage_state_key]

        def get_val(idx_key, text_key):
            val = cached_data.get(idx_key, cached_data.get(text_key, cached_data.get(str(idx_key), "")))
            cleaned = bersih_angka_func(val)
            return cleaned if cleaned else ""

        with st.form("form_input_database"):
            col_no, col_item, col_input = st.columns([0.8, 3.5, 7])
            with col_no: st.markdown("**No**")
            with col_item: st.markdown("**Item Parameter**")
            with col_input: st.markdown("**Kolom Input Data (Bersih & Standar)**")
            st.markdown("---")

            def baris_input_bersih(no, label, default_val="", is_area=False):
                c1, c2, c3 = st.columns([0.8, 3.5, 7])
                with c1: c1.write(f"**{no}.**")
                with c2: c2.write(label)
                with c3:
                    if is_area:
                        return st.text_area(f"input_{no}", value=str(default_val), label_visibility="collapsed", height=75, disabled=is_management)
                    else:
                        return st.text_input(f"input_{no}", value=str(default_val), label_visibility="collapsed", disabled=is_management)

            def baris_input_tanggal(no, label, default_str=""):
                c1, c2, c3 = st.columns([0.8, 3.5, 7])
                with c1: c1.write(f"**{no}.**")
                with c2: c2.write(label)
                with c3:
                    d_val = parse_date_func(default_str)
                    dt_res = st.date_input(f"input_{no}", value=d_val, label_visibility="collapsed", disabled=is_management)
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
            val_13 = c3.selectbox("Diwakili Oleh P1", pilihan_p1, index=idx_p1, label_visibility="collapsed", disabled=is_management)

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
            val_28 = c3.selectbox("Approved by 1", pilihan_app1, index=idx_app1, label_visibility="collapsed", disabled=is_management)

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
            val_30 = c3.selectbox("Approved by 2", pilihan_app2, index=idx_app2, label_visibility="collapsed", disabled=is_management)

            val_31 = baris_input_bersih(31, "Approved by Title 2", default_val=get_val(30, "Approved by Title 2"))

            st.markdown("---")
            
            if not is_management:
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    submit_baru = st.form_submit_button("💾 Simpan Data Baru")
                with col_btn2:
                    submit_save_as = st.form_submit_button("📥 Save As (Buat PI Baru)")
                with col_btn3:
                    submit_update = st.form_submit_button("📝 Update Data Ini")
            else:
                submit_baru, submit_save_as, submit_update = False, False, False
                st.info("ℹ️ Tombol aksi simpan dan pembaruan data dinonaktifkan untuk akun Direksi.")
            
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
                
                # Perbarui cache session agar data langsung sinkron
                st.session_state[storage_state_key] = data_terinput
                
                current_data = muat_data_invoice_func()
                if submit_update:
                    if st.session_state.get("edit_index") is not None and st.session_state["edit_index"] < len(current_data):
                        current_data[st.session_state["edit_index"]] = data_terinput
                        if simpan_data_invoice_func(current_data):
                            st.success("✨ Data berhasil diperbarui secara permanen ke file lokal & database!")
                elif submit_save_as or submit_baru:
                    current_data.append(data_terinput)
                    if simpan_data_invoice_func(current_data):
                        st.success("🎉 Data berhasil disimpan secara permanen ke file lokal & database!")
                        st.session_state["edit_index"] = None
                        st.session_state["active_pi_key"] = None
                st.rerun()

    elif menu == "Lihat Database Tersimpan":
        # Bagian menu lihat database tetap berjalan normal seperti semula
        st.markdown("""
            <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 12px 18px; border-radius: 6px; margin-bottom: 15px; border-left: 4px solid #0284c7;">
                <h4 style="margin:0; color:#0f172a; font-size:15px; font-weight:700;">📂 Database Grid — Kontrak & Proforma Invoice</h4>
                <p style="margin:2px 0 0 0; color:#64748b; font-size:12px;">Tampilan data padat terstruktur dengan kisi-kisi tabel presisi.</p>
            </div>
        """, unsafe_allow_html=True)

        records = muat_data_invoice_func()
        if not records:
            st.info("ℹ️ Belum ada data database tersimpan di folder aman.")
            return

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

        st.markdown(f"<span style='font-size: 13px; color: #475569;'>Menampilkan <b>{len(df_filtered)}</b> dari total <b>{len(df_sum)}</b> baris data tersimpan:</span>", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

        table_rows = ""
        for idx, row in df_filtered.iterrows():
            orig_i = row["Index"]
            bg_color = "#ffffff" if idx % 2 == 0 else "#f8fafc"
            
            table_rows += f"""
            <tr style="background-color: {bg_color}; transition: background 0.15s;" onmouseover="this.style.backgroundColor='#f1f5f9';" onmouseout="this.style.backgroundColor='{bg_color}';">
                <td style="border: 1px solid #cbd5e1; padding: 6px 10px; text-align: center; font-weight: bold; color: #475569; font-size: 12px;">{orig_i+1}</td>
                <td style="border: 1px solid #cbd5e1; padding: 6px 10px; font-weight: 600; color: #0f172a; font-size: 12px; font-family: monospace;">{row['Nomor Kontrak']}</td>
                <td style="border: 1px solid #cbd5e1; padding: 6px 10px; color: #0284c7; font-weight: 700; font-size: 12px; font-family: monospace;">{row['Nomor PI']}</td>
                <td style="border: 1px solid #cbd5e1; padding: 6px 10px; color: #334155; font-size: 12px; font-family: monospace;">{row['Nomor PO']}</td>
                <td style="border: 1px solid #cbd5e1; padding: 6px 10px; color: #334155; font-size: 12px; font-family: monospace;">{row['Nomor WO']}</td>
                <td style="border: 1px solid #cbd5e1; padding: 6px 10px; color: #334155; font-size: 12px; font-family: monospace;">{row['Nomor CTR']}</td>
                <td style="border: 1px solid #cbd5e1; padding: 6px 10px; text-align: center; color: #475569; font-size: 12px;">{row['Tanggal PI']}</td>
            """
            
            if not is_management:
                table_rows += f"""
                <td style="border: 1px solid #cbd5e1; padding: 4px 8px; text-align: center; white-space: nowrap;">
                    <a href="?delete_db_idx={orig_i}" target="_self" style="text-decoration: none;" onclick="return confirm('Apakah Anda yakin ingin menghapus PI {row['Nomor PI']} ini secara permanen?');">
                        <button style="background-color: #ef4444; color: white; border: none; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; cursor: pointer;">🗑️ Hapus</button>
                    </a>
                </td>
                """
            
            table_rows += "</tr>"

        action_header_html = '<th style="border: 1px solid #cbd5e1; padding: 8px 10px; text-align: center; width: 80px;">Aksi</th>' if not is_management else ''

        table_html = f"""
        <div style="overflow-x: auto; border: 1px solid #cbd5e1; border-radius: 4px; background-color: #ffffff;">
            <table style="width: 100%; border-collapse: collapse; text-align: left; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
                <thead>
                    <tr style="background-color: #e2e8f0; color: #1e293b; font-size: 12px; font-weight: bold;">
                        <th style="border: 1px solid #cbd5e1; padding: 8px 10px; text-align: center; width: 45px;">No</th>
                        <th style="border: 1px solid #cbd5e1; padding: 8px 10px;">Nomor Kontrak</th>
                        <th style="border: 1px solid #cbd5e1; padding: 8px 10px;">Nomor PI</th>
                        <th style="border: 1px solid #cbd5e1; padding: 8px 10px;">Nomor PO</th>
                        <th style="border: 1px solid #cbd5e1; padding: 8px 10px;">Nomor WO</th>
                        <th style="border: 1px solid #cbd5e1; padding: 8px 10px;">Nomor CTR</th>
                        <th style="border: 1px solid #cbd5e1; padding: 8px 10px; text-align: center;">Tanggal PI</th>
                        {action_header_html}
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        """
        st.components.v1.html(table_html, height=520, scrolling=True)