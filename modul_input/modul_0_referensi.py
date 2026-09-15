import streamlit as st
import pandas as pd
from datetime import datetime

def tampilkan_modul_0_referensi(menu, muat_master_referensi_func, simpan_master_referensi_func, muat_data_invoice_func, bersih_angka_func):
    # Identifikasi role user aktif untuk pengamanan Read-Only Mutlak Direksi
    current_role_user = str(st.session_state.get("current_role", "")).strip().lower()
    is_management = current_role_user in ["management", "direksi"]

    query_params = st.query_params
    
    # Cegah aksi hapus jika user adalah management
    if "delete_master_idx" in query_params:
        if is_management:
            st.error("❌ Akses Ditolak! Akun Direksi berada dalam mode Read-Only dan tidak diizinkan menghapus data.")
            st.query_params.clear()
            st.rerun()
        else:
            try:
                del_idx = int(query_params["delete_master_idx"])
                all_m = muat_master_referensi_func()
                if 0 <= del_idx < len(all_m):
                    all_m.pop(del_idx)
                    if simpan_master_referensi_func(all_m):
                        st.success("✅ Berhasil menghapus baris master referensi secara permanen!")
                    st.query_params.clear()
                    st.rerun()
            except:
                pass

    # Cegah aksi edit jika user adalah management
    if "edit_master_idx" in query_params:
        if is_management:
            st.warning("⚠️ Akun Direksi berada dalam mode Read-Only (Hanya Lihat).")
            st.query_params.clear()
            st.rerun()
        else:
            try:
                ed_idx = int(query_params["edit_master_idx"])
                all_m = muat_master_referensi_func()
                if 0 <= ed_idx < len(all_m):
                    st.session_state["edit_master_index"] = ed_idx
                    st.query_params.clear()
                    st.rerun()
            except:
                pass

    if menu == "Input & Kelola Master Referensi":
        st.markdown("""
            <div class="dashboard-card">
                <h3 style="margin-top:0; color:#065f46; font-size:18px;">📌 Input & Panggil Kembali Master Referensi Harga Tetap</h3>
            </div>
        """, unsafe_allow_html=True)

        # PENGAMANAN MUTLAK DIREKSI: Jika Management, blokir form input & edit total
        if is_management:
            st.info("🔒 **Mode Direksi (Read-Only):** Formulir input dan pengelolaan master referensi dikunci. Anda dapat melihat daftar referensi pada menu penelusuran.")
            return

        master_data_live = muat_master_referensi_func()
        opsi_panggil_uraian = ["-- Buat Data Referensi Baru --"] + [f"{str(m.get('Uraian Pekerjaan', m.get('Deskripsi Pekerjaan', '')))[:60]}... (Kontrak: {str(m.get('Nomor Kontrak',''))})" for m in master_data_live]
        
        col_p_ref, col_b_ref = st.columns([3, 1])
        with col_p_ref:
            pilihan_panggil_uraian = st.selectbox("Panggil Ulang Berdasarkan Uraian Pekerjaan:", opsi_panggil_uraian)
        with col_b_ref:
            if st.button("🔄 Panggil Data Ini"):
                if pilihan_panggil_uraian == "-- Buat Data Referensi Baru --":
                    st.session_state["edit_master_index"] = None
                else:
                    for idx, m in enumerate(master_data_live):
                        prefix_Str = f"{str(m.get('Uraian Pekerjaan', m.get('Deskripsi Pekerjaan', '')))[:60]}... (Kontrak: {str(m.get('Nomor Kontrak',''))})"
                        if prefix_Str == pilihan_panggil_uraian:
                            st.session_state["edit_master_index"] = idx
                            break
                st.rerun()

        def_ref = {}
        if st.session_state.get("edit_master_index") is not None and st.session_state["edit_master_index"] < len(master_data_live):
            def_ref = master_data_live[st.session_state["edit_master_index"]]
            st.info("📋 **Mode Edit Aktif:** Anda sedang mengubah data referensi yang dipanggil.")

        saved_db = muat_data_invoice_func()
        
        kontrak_from_invoice = [str(item.get(1, item.get("Nomor Kontrak", ""))) for item in saved_db if item.get(1) or item.get("Nomor Kontrak")]
        kontrak_from_master = [str(m.get("Nomor Kontrak", "")) for m in master_data_live if m.get("Nomor Kontrak")]
        combined_kontrak_list = sorted(list(set(kontrak_from_invoice + kontrak_from_master))) + ["-- Ketik Nomor Kontrak Baru --"]

        default_kat_list = ["MONTHLY BASIS", "ON-CALL BASIS", "JASA MOBILISASI", "PROFESSIONAL SUM", "PROVISIONAL SUM", "ESTIMATED SUM", "LAINNYA"]
        existing_kat_from_db = list(set([str(m.get("Kategori")).strip().upper() for m in master_data_live if m.get("Kategori")]))
        combined_kat_list = sorted(list(set(default_kat_list + existing_kat_from_db))) + ["-- Ketik Kategori Baru --"]

        default_unit_list = ["Month", "Day", "Ls", "Unit", "Trip", "Jam", "EA", "AU"]
        existing_unit_from_db = list(set([str(m.get("Unit")) for m in master_data_live if m.get("Unit")]))
        combined_unit_list = sorted(list(set(default_unit_list + existing_unit_from_db))) + ["-- Ketik Satuan Baru --"]

        with st.form("form_master_referensi"):
            col1, col2 = st.columns(2)
            with col1:
                def_kontrak_val = str(def_ref.get("Nomor Kontrak", combined_kontrak_list[0] if combined_kontrak_list else ""))
                idx_kontrak_ref = combined_kontrak_list.index(def_kontrak_val) if def_kontrak_val in combined_kontrak_list else 0
                kontrak_pilih = st.selectbox("Nomor Kontrak Rujukan", combined_kontrak_list, index=idx_kontrak_ref)
                
                kontrak_manual = st.text_input("✍️ Ketik Nomor Kontrak Baru (Jika memilih opsi 'Kontrak Baru' di atas):")
                
                def_kat_val = str(def_ref.get("Kategori", combined_kat_list[0])).strip().upper()
                idx_kat_ref = combined_kat_list.index(def_kat_val) if def_kat_val in combined_kat_list else 0
                kategori_pilih = st.selectbox("Kategori Pekerjaan", combined_kat_list, index=idx_kat_ref)
                
                kategori_manual = st.text_input("✍️ Ketik Nama Kategori Baru (Jika memilih 'Kategori Baru' di atas):")

                def_unit_val = str(def_ref.get("Unit", combined_unit_list[0]))
                idx_unit_ref = combined_unit_list.index(def_unit_val) if def_unit_val in combined_unit_list else 0
                unit_pilih = st.selectbox("Satuan Unit", combined_unit_list, index=idx_unit_ref)
                
                unit_manual = st.text_input("✍️ Ketik Nama Satuan Baru (Jika memilih 'Satuan Baru' di atas, misal: m3, EA, AU):")

            with col2:
                val_uraian_def = str(def_ref.get("Uraian Pekerjaan", def_ref.get("Deskripsi Pekerjaan", "")))
                uraian_ref = st.text_area("Uraian Pekerjaan / Spesifikasi Alat", value=val_uraian_def, height=105)
                try:
                    val_hs_num = float(def_ref.get("Harga Satuan", 0.0) or 0.0)
                except:
                    val_hs_num = 0.0
                harga_satuan_ref = st.number_input("Harga Satuan Tetap (Rp)", min_value=0.0, value=val_hs_num, step=1000.0, format="%.2f")

            st.markdown("---")
            col_sb1, col_sb2 = st.columns(2)
            with col_sb1:
                submit_master_baru = st.form_submit_button("💾 Simpan Master Baru")
            with col_sb2:
                submit_master_update = st.form_submit_button("📝 Update Data Dipanggil / Save As")

            if submit_master_baru or submit_master_update:
                if kontrak_pilih == "-- Ketik Nomor Kontrak Baru --":
                    final_kontrak = kontrak_manual.strip()
                else:
                    final_kontrak = kontrak_pilih

                if kategori_pilih == "-- Ketik Kategori Baru --":
                    final_kategori = kategori_manual.strip()
                else:
                    final_kategori = kategori_pilih

                if unit_pilih == "-- Ketik Satuan Baru --":
                    final_unit = unit_manual.strip()
                else:
                    final_unit = unit_pilih

                if not final_kontrak or not uraian_ref or not final_kategori or not final_unit:
                    st.error("⚠️ Nomor Kontrak, Kategori, Satuan, dan Uraian Pekerjaan tidak boleh kosong!")
                else:
                    master_data = muat_master_referensi_func()
                    item_baru = {
                        "Nomor Kontrak": final_kontrak,
                        "Kategori": final_kategori.upper(),
                        "Uraian Pekerjaan": uraian_ref,
                        "Unit": final_unit,
                        "Harga Satuan": harga_satuan_ref,
                        "Update Terakhir": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    if submit_master_update and st.session_state.get("edit_master_index") is not None and st.session_state["edit_master_index"] < len(master_data):
                        master_data[st.session_state["edit_master_index"]] = item_baru
                        if simpan_master_referensi_func(master_data):
                            st.success("✨ Data Master Referensi berhasil di-update!")
                    else:
                        master_data.append(item_baru)
                        if simpan_master_referensi_func(master_data):
                            st.success("🎉 Data Master Referensi baru berhasil disimpan ke file lokal!")
                    
                    st.session_state["edit_master_index"] = None
                    st.rerun()

    elif menu == "Lihat Daftar Master Referensi Tersimpan":
        st.markdown("""
            <div class="dashboard-card">
                <h3 style="margin-top:0; color:#065f46; font-size:18px;">📂 Daftar Master Referensi Harga & Pekerjaan Tersimpan</h3>
            </div>
        """, unsafe_allow_html=True)

        master_records = muat_master_referensi_func()
        if not master_records:
            st.info("ℹ️ Belum ada data master referensi harga tersimpan di folder aman.")
        else:
            df_master = pd.DataFrame(master_records)

            col_f1, col_f2 = st.columns(2)
            with col_f1:
                kolom_kontrak = next((col for col in ['Nomor Kontrak', 'No Kontrak', 'Kontrak'] if col in df_master.columns), None)
                if kolom_kontrak:
                    list_kontrak = ["-- Semua Kontrak --"] + list(df_master[kolom_kontrak].dropna().astype(str).unique())
                    selected_kontrak = st.selectbox("📌 Filter Berdasarkan Nomor Kontrak:", list_kontrak, key="filter_kontrak_master_v3")
                else:
                    selected_kontrak = "-- Semua Kontrak --"

            with col_f2:
                kolom_kategori = next((col for col in ['Kategori', 'Kategori Pekerjaan', 'Jenis Pekerjaan'] if col in df_master.columns), None)
                if kolom_kategori:
                    list_kategori = ["-- Semua Kategori --"] + list(df_master[kolom_kategori].dropna().astype(str).unique())
                    selected_kategori = st.selectbox("🏷️ Filter Berdasarkan Kategori Pekerjaan:", list_kategori, key="filter_kategori_master_v3")
                else:
                    selected_kategori = "-- Semua Kategori --"

            df_filtered = df_master.copy()
            if kolom_kontrak and selected_kontrak != "-- Semua Kontrak --":
                df_filtered = df_filtered[df_filtered[kolom_kontrak].astype(str) == selected_kontrak]
            if kolom_kategori and selected_kategori != "-- Semua Kategori --":
                df_filtered = df_filtered[df_filtered[kolom_kategori].astype(str) == selected_kategori]

            st.markdown("---")

            headers_html = "<th style='border: 1px solid #cbd5e1; padding: 10px; background-color: #1e293b; color: white; font-size: 13px; text-align: center; width: 45px;'>No</th>"
            for col in df_filtered.columns:
                c_lower = str(col).lower()
                if 'kontrak' in c_lower:
                    w_style = "width: 110px; text-align: left;"
                elif 'kategori' in c_lower:
                    w_style = "width: 130px; text-align: left;"
                elif 'uraian' in c_lower or 'deskripsi' in c_lower or 'pekerjaan' in c_lower:
                    w_style = "text-align: left;"
                elif 'unit' in c_lower:
                    w_style = "width: 55px; text-align: center;"
                elif 'harga' in c_lower or 'satuan' in c_lower:
                    w_style = "width: 115px; text-align: right;"
                elif 'update' in c_lower:
                    w_style = "width: 135px; text-align: center;"
                else:
                    w_style = "text-align: left;"
                headers_html += f"<th style='border: 1px solid #cbd5e1; padding: 10px; background-color: #1e293b; color: white; font-size: 13px; {w_style}'>{col}</th>"
            
            # Kolom Aksi HANYA MUNCUL JIKA BUKAN MANAGEMENT
            if not is_management:
                headers_html += "<th class='no-print' style='border: 1px solid #cbd5e1; padding: 10px; background-color: #1e293b; color: white; font-size: 13px; text-align: center; width: 120px;'>Aksi</th>"

            html_table_rows = ""
            for original_idx, row in df_filtered.iterrows():
                html_table_rows += "<tr>"
                html_table_rows += f"<td style='border: 1px solid #cbd5e1; padding: 10px; text-align: center; font-size: 13px;'>{original_idx+1}</td>"
                
                for col_name, val in row.items():
                    val_clean = bersih_angka_func(val)
                    c_lower = str(col_name).lower()
                    
                    if any(k in c_lower for k in ['harga', 'satuan', 'total', 'nominal', 'nilai']):
                        try:
                            num_val = float(val)
                            val_str = f"{num_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        except:
                            val_str = val_clean
                        cell_align = "text-align: right; white-space: nowrap;"
                    elif any(k in c_lower for k in ['unit']):
                        val_str = val_clean if val_clean else "-"
                        cell_align = "text-align: center; white-space: nowrap;"
                    elif any(k in c_lower for k in ['update']):
                        val_str = val_clean if val_clean else "-"
                        cell_align = "text-align: center; white-space: nowrap; font-size: 11px;"
                    elif any(k in c_lower for k in ['uraian', 'deskripsi', 'pekerjaan']):
                        val_str = val_clean if val_clean else "-"
                        cell_align = "text-align: left; word-wrap: break-word; white-space: normal; line-height: 1.4; min-width: 180px;"
                    else:
                        val_str = val_clean if val_clean else "-"
                        cell_align = "text-align: left; white-space: nowrap;"
                    
                    html_table_rows += f"<td style='border: 1px solid #cbd5e1; padding: 10px; font-size: 13px; {cell_align}'>{val_str}</td>"
                
                # Sembunyikan tombol Edit & Hapus jika user adalah Management/Direksi
                if not is_management:
                    action_buttons = f"""
                        <td class='no-print' style='border: 1px solid #cbd5e1; padding: 8px; text-align: center; white-space: nowrap;'>
                            <a href='?edit_master_idx={original_idx}' target='_self' style='text-decoration: none;'>
                                <button style='background-color: #3b82f6; color: white; border: none; padding: 4px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; cursor: pointer; margin-right: 2px;'>✏️ Edit</button>
                            </a>
                            <a href='?delete_master_idx={original_idx}' target='_self' style='text-decoration: none;'>
                                <button style='background-color: #ef4444; color: white; border: none; padding: 4px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; cursor: pointer;'>🗑️ Hapus</button>
                            </a>
                        </td>
                    """
                    html_table_rows += action_buttons
                
                html_table_rows += "</tr>"

            full_interactive_table_html = f"""
            <div style="max-height: 550px; overflow-y: auto; border: 1px solid #cbd5e1; border-radius: 8px; margin-bottom: 20px;">
                <table style="width: 100%; border-collapse: collapse; background-color: #ffffff; color: #0f172a;">
                    <thead>
                        <tr>{headers_html}</tr>
                    </thead>
                    <tbody>
                        {html_table_rows}
                    </tbody>
                </table>
            </div>
            """
            st.components.v1.html(full_interactive_table_html, height=500, scrolling=True)