import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta, date
import streamlit.components.v1 as components
import base64

# Import modul kuitansi
try:
    from modul_keuangan.modul_kuitansi import tampilkan_kuitansi
except ImportError:
    try:
        from modul_kuitansi import tampilkan_kuitansi
    except ImportError as e:
        def tampilkan_kuitansi(transaksi_list):
            st.error(f"Gagal memuat modul kuitansi: {e}")

def sort_pi_key(pi_str):
    try:
        parts = str(pi_str).split('/')
        if parts:
            digits = "".join([c for c in parts[0] if c.isdigit()])
            return int(digits) if digits else 0
    except:
        pass
    return 0

def bersih_angka(val):
    if val is None:
        return ""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    if s.lower() == "nan":
        return ""
    return s

def format_nomor_bersih(val):
    if val is None:
        return ""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    if s.lower() == "nan" or s == "-":
        return "-"
    return s

def get_image_base64(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        encoded = base64.b64encode(bytes_data).decode()
        file_type = uploaded_file.type.split("/")[-1]
        return f"data:image/{file_type};base64,{encoded}"
    return None

def tampilkan_billing_tax(transaksi_list, menu_pilihan):
    st.markdown("""
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 15px 20px; border-radius: 8px; margin-bottom: 20px;">
            <h3 style="margin:0; font-size: 20px;">💰 Modul 3: Invoice, Tax & Kuitansi Management (Accounting Department)</h3>
            <p style="margin:4px 0 0 0; font-size: 12px; color: #34d399;">Panel khusus pengelolaan tagihan resmi, perhitungan pajak (PPN & PPh berbasis Management Fee), dan pencetakan dokumen keuangan terpusat.</p>
        </div>
    """, unsafe_allow_html=True)

    DIR_DATABASE = "database_penyimpanan_aman"
    EXCEL_BILLING = os.path.join(DIR_DATABASE, "database_billing_tax.xlsx")
    EXCEL_NPWP = os.path.join(DIR_DATABASE, "database_npwp_customer.xlsx")

    def muat_data_billing():
        if os.path.exists(EXCEL_BILLING):
            try:
                df = pd.read_excel(EXCEL_BILLING)
                if df is not None and not df.empty:
                    df = df.dropna(how='all')
                    return df.to_dict(orient="records")
            except:
                pass
        return []

    def simpan_data_billing(data_list):
        df_baru = pd.DataFrame(data_list)
        df_baru.to_excel(EXCEL_BILLING, index=False)
        st.session_state["db_billing"] = data_list

    def muat_database_npwp():
        if os.path.exists(EXCEL_NPWP):
            try:
                df = pd.read_excel(EXCEL_NPWP)
                if df is not None and not df.empty:
                    return df.to_dict(orient="records")
            except:
                pass
        return [
            {"Customer": "JOB Pertamina - Medco E&P Tomori Sulawesi", "NPWP": "002.796.802.3-081.000"}
        ]

    def simpan_database_npwp(data_list):
        df_baru = pd.DataFrame(data_list)
        df_baru.to_excel(EXCEL_NPWP, index=False)
        st.session_state["db_npwp"] = data_list

    if "db_billing" not in st.session_state:
        st.session_state["db_billing"] = muat_data_billing()

    if "db_npwp" not in st.session_state:
        st.session_state["db_npwp"] = muat_database_npwp()

    # --- MENU 1: INPUT DATA INVOICE RESMI ---
    if menu_pilihan == "Input Data Invoice Resmi":
        st.markdown("#### 📝 Lembar Input & Manajemen Invoice Resmi")

        billing_records = st.session_state["db_billing"]
        
        list_invoice_tersimpan = sorted(
            list(dict.fromkeys([str(item.get("Nomor Invoice Resmi", "")) for item in billing_records if item.get("Nomor Invoice Resmi")])),
            key=sort_pi_key,
            reverse=True
        )

        opsi_panggil_invoice = ["-- Buat Invoice Baru (Formulir Kosong) --"] + list_invoice_tersimpan

        col_pi1, col_pi2, col_pi_btn = st.columns([2.5, 2, 1])
        with col_pi1:
            pilihan_inv_panggil = st.selectbox("🔄 Panggil Ulang Berdasarkan Nomor Invoice Resmi:", opsi_panggil_invoice, key="select_panggil_inv_resmi")
        with col_pi2:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            st.info("Pilih nomor invoice untuk edit / save as.")
        with col_pi_btn:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("📥 Panggil", key="btn_panggil_inv_resmi"):
                if pilihan_inv_panggil == "-- Buat Invoice Baru (Formulir Kosong) --":
                    st.session_state["edit_billing_idx"] = None
                else:
                    for idx, item in enumerate(billing_records):
                        if str(item.get("Nomor Invoice Resmi")) == pilihan_inv_panggil:
                            st.session_state["edit_billing_idx"] = idx
                            break
                st.rerun()

        data_edit_aktif = {}
        active_billing_idx = st.session_state.get("edit_billing_idx", None)
        is_mode_edit = False
        if active_billing_idx is not None and active_billing_idx < len(billing_records):
            data_edit_aktif = billing_records[active_billing_idx]
            is_mode_edit = True
            st.success(f"📋 **Mode Edit Aktif (Data Tersimpan Modul 3):** Memuat data Invoice `{data_edit_aktif.get('Nomor Invoice Resmi')}`")

        target_kontrak_val = data_edit_aktif.get("Kontrak No.", "") if is_mode_edit else ""
        target_po_val = data_edit_aktif.get("Nomor PO", "") if is_mode_edit else ""
        target_pi_val = data_edit_aktif.get("PI No.", "") if is_mode_edit else ""

        valid_transaksi_list = []
        for t in transaksi_list:
            po_num = bersih_angka(t.get("Nomor PO", ""))
            if po_num and po_num != "-" and po_num.lower() != "nan":
                valid_transaksi_list.append(t)

        if not valid_transaksi_list and not is_mode_edit:
            st.warning("⚠️ Belum ada transaksi Proforma Invoice (PI) di Modul 2. Harap lengkapi terlebih dahulu.")
            return

        list_kontrak_valid = sorted(list(dict.fromkeys([str(t.get("Nomor Kontrak")) for t in valid_transaksi_list if t.get("Nomor Kontrak")])))
        if is_mode_edit and target_kontrak_val and target_kontrak_val not in list_kontrak_valid:
            list_kontrak_valid.append(target_kontrak_val)

        idx_kontrak_def = 0
        if str(target_kontrak_val) in list_kontrak_valid:
            idx_kontrak_def = list_kontrak_valid.index(str(target_kontrak_val))

        st.markdown("---")
        st.markdown("##### 🔍 Saringan Hierarki Data Sumber (Kontrak $\rightarrow$ Nomor PO $\rightarrow$ PI)")
        
        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1:
            selected_kontrak_m3 = st.selectbox("1️⃣ Pilih Nomor Kontrak", list_kontrak_valid if list_kontrak_valid else [target_kontrak_val], index=idx_kontrak_def, key="m3_sel_kontrak")

        filtered_by_kontrak = [t for t in valid_transaksi_list if str(t.get("Nomor Kontrak")) == str(selected_kontrak_m3)]
        list_po_valid = sorted(list(dict.fromkeys([str(t.get("Nomor PO")) for t in filtered_by_kontrak if t.get("Nomor PO")])))
        if is_mode_edit and target_po_val and target_po_val not in list_po_valid:
            list_po_valid.append(target_po_val)

        idx_po_def = 0
        if str(target_po_val) in list_po_valid:
            idx_po_def = list_po_valid.index(str(target_po_val))

        with col_h2:
            selected_po_m3 = st.selectbox("2️⃣ Pilih Nomor PO", list_po_valid if list_po_valid else [target_po_val], index=idx_po_def if list_po_valid else 0, key="m3_sel_po")

        filtered_by_po = [t for t in filtered_by_kontrak if str(t.get("Nomor PO")) == str(selected_po_m3)]
        raw_list_pi_m3 = list(dict.fromkeys([str(t.get("PI No.")) for t in filtered_by_po if t.get("PI No.")]))
        list_pi_m3 = sorted(raw_list_pi_m3, key=sort_pi_key, reverse=True)
        if is_mode_edit and target_pi_val and target_pi_val not in list_pi_m3:
            list_pi_m3.append(target_pi_val)

        idx_pi_def = 0
        if str(target_pi_val) in list_pi_m3:
            idx_pi_def = list_pi_m3.index(str(target_pi_val))

        with col_h3:
            selected_pi_m3 = st.selectbox("3️⃣ Pilih Nomor Proforma Invoice (PI)", list_pi_m3 if list_pi_m3 else [target_pi_val], index=idx_pi_def if list_pi_m3 else 0, key="m3_sel_pi")

        matched_transaksi = [t for t in filtered_by_po if str(t.get("PI No.")) == str(selected_pi_m3)]
        
        total_nilai_pi_modul2 = sum([float(str(t.get("Total Harga", 0)).replace("Rp", "").replace(".", "").replace(",", ".").strip() or 0) for t in matched_transaksi])

        if is_mode_edit:
            customer_default = data_edit_aktif.get("Customer", "")
            alamat_default = data_edit_aktif.get("Alamat Customer", "")
            bank_string_dinamis = data_edit_aktif.get("Informasi Bank", "<b>Bank Name :</b> BANK RAKYAT INDONESIA (PERSERO) Tbk.<br><b>Branch :</b> Cabang Luwuk<br><b>Account No :</b> 0167 0167 8888 303<br><b>Account Name :</b> PT. BANGGAI SENTRAL SULAWESI")
            deskripsi_default = data_edit_aktif.get("Keterangan Invoice", "")
            nilai_default_tagihan = float(data_edit_aktif.get("Nilai Invoice", 0.0))
            
            is_prof_sum_default = bool(data_edit_aktif.get("Gunakan Professional Sum", False))
            add_cost_default = float(data_edit_aktif.get("Add Cost", 0.0) or 0.0)
            mgmt_fee_default = float(data_edit_aktif.get("Management Fee", 0.0) or 0.0)
        else:
            customer_default = matched_transaksi[0].get("Ditujukan Kepada", "") if matched_transaksi else ""
            alamat_default = matched_transaksi[0].get("Alamat Pihak Pertama", "") if matched_transaksi else ""
            if matched_transaksi:
                t_data = matched_transaksi[0]
                b_nama = t_data.get("Nama Bank", "BANK RAKYAT INDONESIA (PERSERO) Tbk.")
                b_pemilik = t_data.get("Atas Nama Rekening", "PT. BANGGAI SENTRAL SULAWESI")
                b_cabang = t_data.get("Cabang Bank", "Cabang Luwuk")
                b_rekening = t_data.get("Nomor Rekening", "0167 0167 8888 303")
                bank_string_dinamis = f"<b>Bank Name :</b> {b_nama}<br><b>Branch :</b> {b_cabang}<br><b>Account No :</b> {b_rekening}<br><b>Account Name :</b> {b_pemilik}"
            else:
                bank_string_dinamis = "<b>Bank Name :</b> BANK RAKYAT INDONESIA (PERSERO) Tbk.<br><b>Branch :</b> Cabang Luwuk<br><b>Account No :</b> 0167 0167 8888 303<br><b>Account Name :</b> PT. BANGGAI SENTRAL SULAWESI"
            
            deskripsi_default = matched_transaksi[0].get("Deskripsi PO", "") if matched_transaksi else ""
            nilai_default_tagihan = total_nilai_pi_modul2
            
            is_prof_sum_default = False
            if matched_transaksi and any("professional" in str(t.get("Kategori", "")).lower() or "provisional" in str(t.get("Kategori", "")).lower() or "professional" in str(t.get("Deskripsi Pekerjaan", "")).lower() for t in matched_transaksi):
                is_prof_sum_default = True
            
            if is_prof_sum_default:
                add_cost_default = nilai_default_tagihan / 1.15
                mgmt_fee_default = nilai_default_tagihan - add_cost_default
            else:
                add_cost_default = 0.0
                mgmt_fee_default = 0.0

        with st.form("form_input_billing_resmi"):
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.markdown(f"**PI Rujukan Aktif:** `{selected_pi_m3}`")
                customer_name = st.text_input("Customer / Klien", value=customer_default)
                alamat_customer = st.text_area("Alamat Klien", value=alamat_default, height=75)
                
                def_sa_wan = format_nomor_bersih(data_edit_aktif.get("Nomor SA / WAN", "")) if is_mode_edit else ""
                nomor_sa_wan = st.text_input(
                    "Nomor SA / WAN (Work Acceptance Notice / Service Agreement)",
                    value=def_sa_wan,
                    placeholder="Ketik manual nomor SA / WAN di sini..."
                )

                npwp_records = st.session_state["db_npwp"]
                existing_npwp = next((n.get("NPWP") for n in npwp_records if n.get("Customer") == customer_name), "002.796.802.3-081.000")
                saved_npwp = str(data_edit_aktif.get("NPWP Customer", existing_npwp)) if is_mode_edit else existing_npwp
                nomor_npwp = st.text_input("Nomor NPWP Customer", value=saved_npwp)

            with col_b2:
                nomor_invoice_resmi = st.text_input("Nomor Invoice Resmi (Diberikan Accounting)", value=str(data_edit_aktif.get("Nomor Invoice Resmi", "")) if is_mode_edit else "")
                
                tgl_inv_val = datetime.today().date()
                if is_mode_edit and data_edit_aktif.get("Tanggal Invoice"):
                    try:
                        tgl_inv_val = datetime.strptime(str(data_edit_aktif.get("Tanggal Invoice")), "%Y-%m-%d").date()
                    except:
                        pass
                tanggal_invoice = st.date_input("Tanggal Invoice", value=tgl_inv_val)

                due_date_val = datetime.today().date() + timedelta(days=30)
                if is_mode_edit and data_edit_aktif.get("Jatuh Tempo"):
                    try:
                        due_date_val = datetime.strptime(str(data_edit_aktif.get("Jatuh Tempo")), "%Y-%m-%d").date()
                    except:
                        pass
                tanggal_jatuh_tempo = st.date_input("Tanggal Jatuh Tempo (Due Date)", value=due_date_val)

                st.markdown(f"**Nilai Acuan Aktif (Modul 2):** Rp {nilai_default_tagihan:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                
                nilai_invoice_resmi = st.number_input("Total Nilai Tagihan Invoice (Rp)", min_value=0.0, value=float(nilai_default_tagihan), step=1000.0, format="%.2f")

            st.markdown("---")
            st.markdown("#### 💼 Pengaturan Khusus Professional Sum (Add Cost & Management Fee)")
            
            gunakan_prof_sum = st.checkbox("Pisahkan rincian baris menjadi Professional Sum (Add Cost & Management Fee 15%)", value=is_prof_sum_default)
            
            input_add_cost = 0.0
            input_mgmt_fee = 0.0
            if gunakan_prof_sum:
                def_ac = add_cost_default if add_cost_default > 0 else (nilai_invoice_resmi / 1.15)
                def_mf = mgmt_fee_default if mgmt_fee_default > 0 else (nilai_invoice_resmi - def_ac)

                col_ps1, col_ps2 = st.columns(2)
                with col_ps1:
                    input_add_cost = st.number_input("Nilai Add Cost (Murni, Rp)", min_value=0.0, value=float(def_ac), step=1000.0, format="%.2f")
                with col_ps2:
                    input_mgmt_fee = st.number_input("Nilai Management / Handling Fee 15% (Rp)", min_value=0.0, value=float(def_mf), step=1000.0, format="%.2f")
                
                subtotal_ps = input_add_cost + input_mgmt_fee
                st.info(f"💡 **Simulasi Perhitungan:** Add Cost (Rp {input_add_cost:,.2f}) + Management Fee 15% (Rp {input_mgmt_fee:,.2f}) = **Rp {subtotal_ps:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
                
                if abs(subtotal_ps - nilai_invoice_resmi) > 1.0:
                    st.warning(f"⚠️ Catatan: Jumlah Add Cost + Management Fee (Rp {subtotal_ps:,.2f}) berbeda dengan Total Tagihan Utama (Rp {nilai_invoice_resmi:,.2f}).")

            st.markdown("---")
            keterangan_invoice_resmi = st.text_area(
                "📝 Deskripsi Keterangan Invoice Utama:",
                value=deskripsi_default,
                height=90
            )

            st.markdown("---")
            st.markdown("#### 🧮 Kalkulasi Otomatis Pajak (PPN 11% & PPh Berbasis Management Fee)")

            def_kena_ppn = bool(data_edit_aktif.get("Kena PPN", True)) if is_mode_edit else True
            def_kena_pph = bool(data_edit_aktif.get("Kena PPh", True)) if is_mode_edit else True
            def_tarif_pph = float(data_edit_aktif.get("Tarif PPh", 2.0)) if is_mode_edit else 2.0

            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                kena_ppn = st.checkbox("Kenakan PPN (11%)", value=def_kena_ppn)
            with col_p2:
                kena_pph = st.checkbox("Potong PPh (2% / 1.5% - PPh 23/22)", value=def_kena_pph)
            with col_p3:
                persen_pph = st.number_input("Tarif PPh (%)", min_value=0.0, max_value=10.0, value=def_tarif_pph, step=0.5)

            # Perhitungan PPN dari Total Tagihan
            ppn_nominal = nilai_invoice_resmi * 0.11 if kena_ppn else 0.0

            # KETENTUAN PAJAK PRESISI: Jika Professional Sum aktif, PPh dihitung dari Management Fee. Jika tidak, dari total nilai invoice.
            base_pph = input_mgmt_fee if gunakan_prof_sum else nilai_invoice_resmi
            pph_nominal = base_pph * (persen_pph / 100.0) if kena_pph else 0.0

            total_pembayaran_netto = nilai_invoice_resmi + ppn_nominal - pph_nominal

            st.markdown(f"""
                * **Dasar Tagihan Invoice:** Rp {nilai_invoice_resmi:,.2f}
                * **Dasar Pengenaan PPh (Management Fee):** Rp {base_pph:,.2f}
                * **Nilai PPN (11%):** Rp {ppn_nominal:,.2f}
                * **Potongan PPh ({persen_pph}% dari Management Fee):** Rp {pph_nominal:,.2f}
                * **Total Netto Diterima:** **Rp {total_pembayaran_netto:,.2f}**
            """.replace(",", "X").replace(".", ",").replace("X", "."))

            st.markdown("---")
            
            col_bt1, col_bt2, col_bt3 = st.columns(3)
            with col_bt1:
                submit_simpan_baru = st.form_submit_button("💾 Simpan Data Baru")
            with col_bt2:
                submit_save_as = st.form_submit_button("📥 Save As (Buat Invoice Baru)")
            with col_bt3:
                submit_update = st.form_submit_button("📝 Update Data Ini")

            if submit_simpan_baru or submit_save_as or submit_update:
                if not nomor_invoice_resmi:
                    st.error("⚠️ Nomor Invoice Resmi wajib diisi oleh Tim Accounting!")
                elif not selected_pi_m3:
                    st.error("⚠️ Silakan pilih Nomor Proforma Invoice (PI) rujukan terlebih dahulu!")
                else:
                    waktu_aksi = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
                    item_billing_baru = {
                        "Nomor Invoice Resmi": nomor_invoice_resmi,
                        "Kontrak No.": selected_kontrak_m3,
                        "Nomor PO": selected_po_m3,
                        "Nomor SA / WAN": format_nomor_bersih(nomor_sa_wan),
                        "PI No.": selected_pi_m3,
                        "Customer": customer_name,
                        "Alamat Customer": alamat_customer,
                        "NPWP Customer": nomor_npwp,
                        "Tanggal Invoice": str(tanggal_invoice),
                        "Jatuh Tempo": str(tanggal_jatuh_tempo),
                        "Keterangan Invoice": keterangan_invoice_resmi,
                        "Informasi Bank": bank_string_dinamis,
                        "Nilai Invoice": nilai_invoice_resmi,
                        "Gunakan Professional Sum": 1 if gunakan_prof_sum else 0,
                        "Add Cost": input_add_cost if gunakan_prof_sum else 0.0,
                        "Management Fee": input_mgmt_fee if gunakan_prof_sum else 0.0,
                        "PPN Nominal": ppn_nominal,
                        "PPh Nominal": pph_nominal,
                        "Total Netto": total_pembayaran_netto,
                        "Kena PPN": kena_ppn,
                        "Kena PPh": kena_pph,
                        "Tarif PPh": persen_pph,
                        "Update Terakhir": waktu_aksi
                    }

                    current_billing = muat_data_billing()
                    if submit_update and active_billing_idx is not None and active_billing_idx < len(current_billing):
                        current_billing[active_billing_idx] = item_billing_baru
                        simpan_data_billing(current_billing)
                        st.success("✨ Data Invoice & Pajak berhasil di-update dengan perhitungan PPh berbasis Management Fee!")
                    elif submit_save_as or submit_simpan_baru:
                        current_billing.append(item_billing_baru)
                        simpan_data_billing(current_billing)
                        st.success("🎉 Data Invoice & Pajak baru berhasil disimpan!")
                        st.session_state["edit_billing_idx"] = None

    # --- MENU 2: PRATINJAU, CETAK & DOWNLOAD PDF INVOICE ---
    elif menu_pilihan == "Pratinjau, Cetak & Download PDF Invoice":
        st.markdown("#### 🖨️ Pratinjau, Cetak & Download Dokumen Keuangan Resmi")
        
        billing_records = muat_data_billing()
        if not billing_records:
            st.warning("⚠️ Belum ada data invoice resmi tersimpan di Modul 3.")
        else:
            list_inv_resmi = sorted(
                list(dict.fromkeys([str(item.get("Nomor Invoice Resmi")) for item in billing_records if item.get("Nomor Invoice Resmi")])),
                key=sort_pi_key,
                reverse=True
            )

            col_sel_jenis, col_ctrl1 = st.columns([1.5, 2.5])
            with col_sel_jenis:
                jenis_dok_terpilih = st.selectbox(
                    "📄 Pilih Jenis Dokumen:", 
                    ["Invoice & Tax Billing", "Kuitansi Pembayaran"],
                    key="select_jenis_dokumen_m3"
                )
            with col_ctrl1:
                selected_inv_preview = st.selectbox("🔄 Panggil Ulang Nomor Invoice Disimpan:", list_inv_resmi, key="preview_panggil_inv")

            st.markdown("---")

            if jenis_dok_terpilih == "Kuitansi Pembayaran":
                st.markdown("##### 🧾 Pratinjau Kuitansi Berdasarkan Invoice Terpilih")
                selected_record_kuitansi = next((item for item in billing_records if str(item.get("Nomor Invoice Resmi")) == str(selected_inv_preview)), None)
                
                if selected_record_kuitansi:
                    pi_rujukan = selected_record_kuitansi.get("PI No.")
                    matched_tx_kuitansi = [t for t in transaksi_list if str(t.get("PI No.")) == str(pi_rujukan)]
                    if matched_tx_kuitansi:
                        tampilkan_kuitansi(matched_tx_kuitansi)
                    else:
                        tampilkan_kuitansi(transaksi_list)
                else:
                    tampilkan_kuitansi(transaksi_list)

            else:
                with st.expander("🖼️ Pengaturan Logo Kop Surat & Tanda Tangan Direktur", expanded=False):
                    col_ul1, col_ul2, col_ul3 = st.columns(3)
                    with col_ul1:
                        uploaded_logo_bss = st.file_uploader("Upload Logo BSS (Kiri)", type=["png", "jpg", "jpeg"], key="logo_bss_upload")
                    with col_ul2:
                        uploaded_logo_iso = st.file_uploader("Upload Logo ISO (Kanan)", type=["png", "jpg", "jpeg"], key="logo_iso_upload")
                    with col_ul3:
                        uploaded_ttd_dir = st.file_uploader("Upload TTD Direktur (Ferry Tatimu)", type=["png", "jpg", "jpeg"], key="ttd_direktur_upload")

                selected_record = next((item for item in billing_records if str(item.get("Nomor Invoice Resmi")) == str(selected_inv_preview)), None)

                if selected_record:
                    val_inv = float(selected_record.get('Nilai Invoice', 0) or 0)
                    val_ppn = float(selected_record.get('PPN Nominal', 0) or 0)
                    val_pph = float(selected_record.get('PPh Nominal', 0) or 0)
                    val_netto = float(selected_record.get('Total Netto', 0) or 0)
                    dpp_nilai_lain = val_inv * (11 / 12) if val_ppn > 0 else val_inv

                    # DETEKSI ROBUST Professional Sum (bisa berupa boolean True, angka 1, atau string '1'/'true')
                    raw_prof_sum = selected_record.get('Gunakan Professional Sum', False)
                    is_prof_sum_akt = False
                    if str(raw_prof_sum).lower() in ['true', '1', 'yes', '1.0']:
                        is_prof_sum_akt = True
                    
                    val_add_cost = float(selected_record.get('Add Cost', 0) or 0)
                    val_mgmt_fee = float(selected_record.get('Management Fee', 0) or 0)

                    nomor_sa_wan_val = format_nomor_bersih(selected_record.get('Nomor SA / WAN', ''))
                    nomor_po_val = format_nomor_bersih(selected_record.get('Nomor PO', selected_record.get('Nomor PO Rujukan', '-')))
                    
                    kontrak_no_val = format_nomor_bersih(selected_record.get('Kontrak No.', '-'))
                    bank_info_val = selected_record.get('Informasi Bank', '<b>Bank Name :</b> BANK RAKYAT INDONESIA (PERSERO) Tbk.<br><b>Branch :</b> Cabang Luwuk<br><b>Account No :</b> 0167 0167 8888 303<br><b>Account Name :</b> PT. BANGGAI SENTRAL SULAWESI')

                    logo_bss_b64 = get_image_base64(uploaded_logo_bss) if uploaded_logo_bss else None
                    logo_iso_b64 = get_image_base64(uploaded_logo_iso) if uploaded_logo_iso else None
                    ttd_dir_b64 = get_image_base64(uploaded_ttd_dir) if uploaded_ttd_dir else None

                    html_logo_kiri = f'<img src="{logo_bss_b64}" style="max-height: 70px; max-width: 130px; object-fit: contain;">' if logo_bss_b64 else ''
                    html_logo_kanan = f'<img src="{logo_iso_b64}" style="max-height: 75px; max-width: 210px; object-fit: contain;">' if logo_iso_b64 else ''
                    
                    html_ttd_direktur = f'<img src="{ttd_dir_b64}" style="max-height: 75px; max-width: 160px; object-fit: contain; display: block; margin: 0 auto;">' if ttd_dir_b64 else '<div style="height: 65px;"></div>'

                    tanggal_cetak_str = datetime.today().strftime("%m/%d/%Y, %I:%M %p")
                    deskripsi_keterangan_inv = str(selected_record.get('Keterangan Invoice', ''))

                    # KONDISIONAL KETAT TABEL ITEM: Jika Professional Sum aktif, cetak 2 baris terpisah (Add Cost & Management Fee) secara presisi!
                    if is_prof_sum_akt:
                        tabel_item_html = f"""
                        <tr>
                            <td style="border: 1px solid #000; padding: 8px; text-align: center; vertical-align: top;">1</td>
                            <td style="border: 1px solid #000; padding: 8px; vertical-align: top;"><b>Add Cost:</b><br>{deskripsi_keterangan_inv}</td>
                            <td style="border: 1px solid #000; padding: 8px; text-align: center; vertical-align: top;">-</td>
                            <td style="border: 1px solid #000; padding: 8px; text-align: right; vertical-align: top;">-</td>
                            <td style="border: 1px solid #000; padding: 8px; text-align: right; vertical-align: top;">Rp {val_add_cost:,.2f}</td>
                        </tr>
                        <tr>
                            <td style="border: 1px solid #000; padding: 8px; text-align: center; vertical-align: top;">2</td>
                            <td style="border: 1px solid #000; padding: 8px; vertical-align: top;"><b>Management Fee / Handling Fee (15%):</b><br>Layanan manajemen & pengelolaan operasional terkait</td>
                            <td style="border: 1px solid #000; padding: 8px; text-align: center; vertical-align: top;">-</td>
                            <td style="border: 1px solid #000; padding: 8px; text-align: right; vertical-align: top;">-</td>
                            <td style="border: 1px solid #000; padding: 8px; text-align: right; vertical-align: top;">Rp {val_mgmt_fee:,.2f}</td>
                        </tr>
                        """
                    else:
                        tabel_item_html = f"""
                        <tr>
                            <td style="border: 1px solid #000; padding: 10px 8px 145px 8px; text-align: center; vertical-align: top;">1</td>
                            <td style="border: 1px solid #000; padding: 10px 8px 145px 8px; vertical-align: top;"><b>{deskripsi_keterangan_inv}</b></td>
                            <td style="border: 1px solid #000; padding: 10px 8px 145px 8px; text-align: center; vertical-align: top;">-</td>
                            <td style="border: 1px solid #000; padding: 10px 8px 145px 8px; text-align: right; vertical-align: top;">-</td>
                            <td style="border: 1px solid #000; padding: 10px 8px 145px 8px; text-align: right; vertical-align: top;">Rp {val_inv:,.2f}</td>
                        </tr>
                        """

                    html_invoice = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title></title>
                        <style>
                            @page {{ 
                                size: A4; 
                                margin: 6mm; 
                            }}
                            @media print {{
                                html, body {{
                                    width: 210mm;
                                    height: 297mm;
                                    margin: 0 !important;
                                    padding: 6mm !important;
                                    background: #fff !important;
                                    -webkit-print-color-adjust: exact;
                                }}
                                @page {{
                                    margin: 0;
                                }}
                            }}
                            body {{ 
                                font-family: Arial, sans-serif; 
                                background-color: #ffffff; 
                                color: #000000; 
                                padding: 6mm; 
                                margin: 0; 
                                font-size: 11px; 
                                line-height: 1.3; 
                            }}
                            .invoice-container {{ 
                                background-color: white; 
                                color: #111; 
                                padding: 10px; 
                                border: 2px solid #000; 
                                border-radius: 4px; 
                                max-width: 820px; 
                                margin: auto; 
                                min-height: 275mm;
                                display: flex;
                                flex-direction: column;
                                justify-content: space-between;
                            }}
                            .invoice-content-body {{
                                flex-grow: 1;
                            }}
                            .footer-wrapper {{
                                margin-top: auto;
                                border-top: 1px solid #000;
                                padding-top: 6mm;
                            }}
                            .footer-container {{
                                display: flex;
                                justify-content: space-between;
                                align-items: center;
                                font-size: 10.5px;
                                color: #000;
                                font-weight: bold;
                            }}
                            .company-footer {{
                                text-align: center;
                                font-size: 8.5px;
                                color: #475569;
                                margin-top: 4px;
                                line-height: 1.3;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="invoice-container">
                            <div class="invoice-content-body">
                                <table style="width: 100%; border-collapse: collapse; margin-bottom: 12px; border-bottom: 2px solid #000; padding-bottom: 8px;">
                                    <tr>
                                        <td style="width: 20%; vertical-align: middle; text-align: center; padding: 5px;">{html_logo_kiri}</td>
                                        <td style="width: 52%; vertical-align: middle; text-align: center; padding: 5px;">
                                            <h3 style="margin: 0; font-size: 15px; font-weight: bold; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px;">PT Banggai Sentral Sulawesi</h3>
                                            <p style="margin: 2px 0; font-size: 10.5px; font-weight: bold; color: #334155; letter-spacing: 0.3px;">General Contractor and Supplier</p>
                                            <p style="margin: 2px 0 0 0; font-size: 9.5px; color: #475569;">Jl. Urip Sumoharjo Nomor 53, Luwuk, Kabupaten Banggai, Provinsi Sulawesi Tengah</p>
                                        </td>
                                        <td style="width: 28%; vertical-align: middle; text-align: center; padding: 5px;">{html_logo_kanan}</td>
                                    </tr>
                                </table>

                                <table style="width: 100%; border-collapse: collapse; margin-bottom: 0;">
                                    <tr>
                                        <td style="border: 1px solid #000; border-bottom: none; padding: 8px 12px; font-weight: bold; width: 50%; background: #ffffff; color: #000;">Original</td>
                                        <td style="border: 1px solid #000; border-bottom: none; border-left: none; padding: 8px 12px; text-align: right; font-weight: bold; font-size: 20px; background: #ffffff; color: #000; width: 50%; letter-spacing: 1px;">INVOICE</td>
                                    </tr>
                                </table>

                                <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 15px;">
                                    <tr>
                                        <td style="width: 50%; border: 1px solid #000; vertical-align: top; padding: 10px;">
                                            <div style="font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 4px; margin-bottom: 6px;">Customer</div>
                                            <table style="width: 100%; font-size: 12px; border-collapse: collapse;">
                                                <tr><td style="width: 65px; vertical-align: top; padding: 2px 0;">Name</td><td style="width: 15px; vertical-align: top; padding: 2px 0;">:</td><td style="vertical-align: top; padding: 2px 0; font-weight: bold;">{selected_record.get('Customer')}</td></tr>
                                                <tr><td style="vertical-align: top; padding: 2px 0;">Address</td><td style="vertical-align: top; padding: 2px 0;">:</td><td style="vertical-align: top; padding: 2px 0;">{selected_record.get('Alamat Customer')}</td></tr>
                                                <tr><td style="vertical-align: top; padding: 2px 0;">NPWP</td><td style="vertical-align: top; padding: 2px 0;">:</td><td style="vertical-align: top; padding: 2px 0;">{selected_record.get('NPWP Customer')}</td></tr>
                                            </table>
                                        </td>
                                        <td style="width: 50%; border: 1px solid #000; vertical-align: top; padding: 10px; border-left: none;">
                                            <div style="font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 4px; margin-bottom: 6px;">Misc</div>
                                            <table style="width: 100%; font-size: 12px; border-collapse: collapse;">
                                                <tr><td style="width: 130px; padding: 2px 0;">Invoice No.</td><td style="padding: 2px 0;">: <b>{selected_record.get('Nomor Invoice Resmi')}</b></td></tr>
                                                <tr><td style="padding: 2px 0;">Invoice Date</td><td style="padding: 2px 0;">: {selected_record.get('Tanggal Invoice')}</td></tr>
                                                <tr><td style="padding: 2px 0;">Contract Number</td><td style="padding: 2px 0;">: {kontrak_no_val}</td></tr>
                                                <tr><td style="padding: 2px 0;">PO Nomor</td><td style="padding: 2px 0;">: {nomor_po_val}</td></tr>
                                                {f"<tr><td style='padding: 2px 0;'>WAN / SA Nomor</td><td style='padding: 2px 0;'>: {nomor_sa_wan_val}</td></tr>" if nomor_sa_wan_val and nomor_sa_wan_val != "-" else ""}
                                                <tr><td style="padding: 2px 0;">Due Date</td><td style="padding: 2px 0;">: {selected_record.get('Jatuh Tempo')}</td></tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>

                                <!-- TABEL UTAMA -->
                                <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 12px;">
                                    <thead>
                                        <tr style="background-color: #f1f5f9; border: 1px solid #000;">
                                            <th style="border: 1px solid #000; padding: 6px; width: 45px; text-align: center;">No.</th>
                                            <th style="border: 1px solid #000; padding: 6px; text-align: left;">DESCRIPTION</th>
                                            <th style="border: 1px solid #000; padding: 6px; width: 70px; text-align: center;">UNIT</th>
                                            <th style="border: 1px solid #000; padding: 6px; width: 110px; text-align: right;">UNIT PRICE (Rp.)</th>
                                            <th style="border: 1px solid #000; padding: 6px; width: 130px; text-align: right;">AMOUNT (Rp.)</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {tabel_item_html}
                                        <tr>
                                            <td colspan="3" style="border: 1px solid #000; padding: 12px; vertical-align: top;">
                                                <div style="font-size: 11px; font-weight: bold; margin-bottom: 3px; text-transform: uppercase;">PAYMENT INSTRUCTION</div>
                                                <div style="font-size: 10.5px; margin-bottom: 5px; color: #334155;">Please remit to our bank:</div>
                                                <div style="border: 1px solid #000; padding: 8px; background: #fafafa; font-size: 11px; line-height: 1.3; display: inline-block; width: 94%;">{bank_info_val}</div>
                                            </td>
                                            <td colspan="2" style="border: 1px solid #000; padding: 0; vertical-align: top;">
                                                <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                                                    <tr><td style="border-bottom: 1px solid #000; padding: 6px; font-weight: bold;">Total Amount Due</td><td style="border-bottom: 1px solid #000; padding: 6px; text-align: right;">Rp {val_inv:,.2f}</td></tr>
                                                    <tr><td style="border-bottom: 1px solid #000; padding: 6px; font-size: 10px; color: #475569;">DPP Nilai Lain (11/12)</td><td style="border-bottom: 1px solid #000; padding: 6px; text-align: right; font-size: 10px; color: #475569;">Rp {dpp_nilai_lain:,.2f}</td></tr>
                                                    <tr><td style="border-bottom: 1px solid #000; padding: 6px;">VAT (PPN 11%)</td><td style="border-bottom: 1px solid #000; padding: 6px; text-align: right;">Rp {val_ppn:,.2f}</td></tr>
                                                    {f"<tr><td style='border-bottom: 1px solid #000; padding: 6px; color: #b91c1c;'>Potongan PPh</td><td style='border-bottom: 1px solid #000; padding: 6px; text-align: right; color: #b91c1c;'>(Rp {val_pph:,.2f})</td></tr>" if val_pph > 0 else ""}
                                                    <tr style="background-color: #f1f5f9; font-weight: bold;">
                                                        <td style="padding: 8px; border-top: 2px solid #000;">T O T A L</td>
                                                        <td style="padding: 8px; border-top: 2px solid #000; text-align: right;">Rp {val_netto:,.2f}</td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>

                                <!-- TANDA TANGAN -->
                                <table style="width: 100%; margin-top: 50px; border-collapse: collapse;">
                                    <tr>
                                        <td style="width: 63%;"></td>
                                        <td style="width: 37%; text-align: left; padding-left: 35px;">
                                            <p style="margin: 0 0 5px 0;">Best Regards,</p>
                                            <div style="text-align: center; width: 160px; margin: 8px 0;">
                                                {html_ttd_direktur}
                                            </div>
                                            <p style="margin: 5px 0 0 0; font-weight: bold; text-decoration: underline; font-size: 13px;">Ferry Tatimu</p>
                                            <p style="margin: 2px 0 0 0; font-size: 12px;">Direktur</p>
                                        </td>
                                    </tr>
                                </table>
                            </div>

                            <div class="footer-wrapper">
                                <div class="footer-container">
                                    <div>FM-AK-11 Rev: 00</div>
                                    <div>{tanggal_cetak_str}</div>
                                </div>
                                <div class="company-footer">
                                    Head Office: Jl. Urip Sumoharjo 53, Luwuk 94715, Phone: 0461-21025, 21185, 21307, Fax: 0461-325241, email: Luwuk@ptbss.com<br>
                                    Representative Office: Jl. Nginden Intan Tengah Blok F1-47, Surabaya 60118, Phone : 031-5925721
                                </div>
                            </div>
                        </div>
                    </body>
                    </html>
                    """

                    st.markdown('<div class="document-preview">', unsafe_allow_html=True)
                    st.components.v1.html(html_invoice, height=580, scrolling=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    col_save_pratinjau, col_btn1, col_btn2 = st.columns([1.5, 1, 1])
                    with col_save_pratinjau:
                        if st.button("💾 Simpan Perubahan Pratinjau (Save)", use_container_width=True, type="primary"):
                            waktu_aksi = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
                            selected_record["Update Terakhir"] = waktu_aksi
                            
                            current_billing = muat_data_billing()
                            for i, item in enumerate(current_billing):
                                if str(item.get("Nomor Invoice Resmi")) == str(selected_record.get("Nomor Invoice Resmi")):
                                    current_billing[i] = selected_record
                                    break
                            simpan_data_billing(current_billing)
                            st.success(f"✅ Berhasil menyimpan perubahan terakhir untuk Invoice [{selected_record.get('Nomor Invoice Resmi')}]!")

                    with col_btn1:
                        b64_html = base64.b64encode(html_invoice.encode()).decode()
                        print_script = f"""
                            <script>
                                function printDoc() {{
                                    var win = window.open('about:blank', '_blank');
                                    win.document.open();
                                    win.document.write(atob("{b64_html}"));
                                    win.document.close();
                                    win.focus();
                                    setTimeout(function(){{ win.print(); }}, 500);
                                }}
                            </script>
                            <button onclick="printDoc()" style="width: 100%; background-color: #10b981; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
                                🖨️ Cetak / Print
                            </button>
                        """
                        st.components.v1.html(print_script, height=50)

                    with col_btn2:
                        b64_pdf = base64.b64encode(html_invoice.encode()).decode()
                        download_link = f'<a href="data:text/html;base64,{b64_pdf}" download="Invoice_{str(selected_record.get("Nomor Invoice Resmi", "")).replace("/", "-")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download</button></a>'
                        st.markdown(download_link, unsafe_allow_html=True)

    # --- MENU 3: LIHAT DAFTAR INVOICE & PAJAK TERSIMPAN ---
    elif menu_pilihan == "Lihat Daftar Invoice & Pajak Tersimpan":
        st.markdown("#### 📂 Akumulasi Daftar Invoice & Pajak Tersimpan")
        
        billing_records = muat_data_billing()
        if billing_records:
            df_bill = pd.DataFrame(billing_records)
            st.dataframe(df_bill, use_container_width=True)
            
            st.markdown("---")
            st.markdown("#### 🗑️ Hapus Data Invoice Tersimpan")
            pilihan_hapus_inv = [f"{item.get('Nomor Invoice Resmi')} (Customer: {item.get('Customer')})" for item in billing_records]
            
            col_dh1, col_dh2 = st.columns([2, 1])
            with col_dh1:
                target_del_idx = st.selectbox("Pilih Invoice yang Ingin Dihapus:", range(len(pilihan_hapus_inv)), format_func=lambda x: pilihan_hapus_inv[x])
            with col_dh2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("❌ Hapus Invoice Terpilih", use_container_width=True, type="primary"):
                    try:
                        billing_records.pop(target_del_idx)
                        simpan_data_billing(billing_records)
                        st.success("✅ Berhasil menghapus data invoice resmi!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Gagal menghapus: {e}")
        else:
            st.info("Belum ada data invoice tersimpan.")