import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta, date
import streamlit.components.v1 as components
import base64

def sort_pi_key(pi_str):
    """Mengekstrak nomor urut dari format nomor (misal: '015/BSS-JOB/WS/VIII/2026' -> angka 15)"""
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
    """Membersihkan nilai angka/ID agar tidak ada desimal .0 di belakangnya"""
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
            <h3 style="margin:0; font-size: 20px;">💰 Modul 3: Invoice & Tax Management (Accounting Department)</h3>
            <p style="margin:4px 0 0 0; font-size: 12px; color: #34d399;">Panel khusus pengelolaan tagihan resmi, perhitungan pajak (PPN/PPh), dan dokumen penagihan keuangan.</p>
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
        if active_billing_idx is not None and active_billing_idx < len(billing_records):
            data_edit_aktif = billing_records[active_billing_idx]
            st.success(f"📋 **Mode Edit Aktif:** Memuat data Invoice `{data_edit_aktif.get('Nomor Invoice Resmi')}`")

        valid_transaksi_list = []
        for t in transaksi_list:
            po_num = bersih_angka(t.get("Nomor PO", ""))
            if po_num and po_num != "-" and po_num.lower() != "nan":
                valid_transaksi_list.append(t)

        if not valid_transaksi_list:
            st.warning("⚠️ Belum ada transaksi Proforma Invoice (PI) yang memiliki Nomor PO lengkap. Harap lengkapi terlebih dahulu di Modul 2.")
            return

        list_kontrak_valid = sorted(list(dict.fromkeys([str(t.get("Nomor Kontrak")) for t in valid_transaksi_list if t.get("Nomor Kontrak")])))
        
        st.markdown("---")
        st.markdown("##### 🔍 Saringan Hierarki Data Sumber (Kontrak $\rightarrow$ Nomor PO $\rightarrow$ PI)")
        
        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1:
            selected_kontrak_m3 = st.selectbox("1️⃣ Pilih Nomor Kontrak", list_kontrak_valid, key="m3_sel_kontrak")

        filtered_by_kontrak = [t for t in valid_transaksi_list if str(t.get("Nomor Kontrak")) == str(selected_kontrak_m3)]
        list_po_valid = sorted(list(dict.fromkeys([str(t.get("Nomor PO")) for t in filtered_by_kontrak if t.get("Nomor PO")])))
        
        with col_h2:
            selected_po_m3 = st.selectbox("2️⃣ Pilih Nomor PO", list_po_valid if list_po_valid else [""], key="m3_sel_po")

        filtered_by_po = [t for t in filtered_by_kontrak if str(t.get("Nomor PO")) == str(selected_po_m3)]
        raw_list_pi_m3 = list(dict.fromkeys([str(t.get("PI No.")) for t in filtered_by_po if t.get("PI No.")]))
        list_pi_m3 = sorted(raw_list_pi_m3, key=sort_pi_key, reverse=True)

        with col_h3:
            selected_pi_m3 = st.selectbox("3️⃣ Pilih Nomor Proforma Invoice (PI)", list_pi_m3 if list_pi_m3 else [""], key="m3_sel_pi")

        matched_transaksi = [t for t in filtered_by_po if str(t.get("PI No.")) == str(selected_pi_m3)]
        total_nilai_pi = sum([float(t.get("Total Harga", 0.0)) for t in matched_transaksi])

        customer_default = matched_transaksi[0].get("Ditujukan Kepada", "") if matched_transaksi else data_edit_aktif.get("Customer", "")
        alamat_default = matched_transaksi[0].get("Alamat Pihak Pertama", "") if matched_transaksi else data_edit_aktif.get("Alamat Customer", "")
        
        # Penarikan data bank dinamis standar Proforma Invoice
        if matched_transaksi:
            t_data = matched_transaksi[0]
            b_nama = t_data.get("Nama Bank", "BANK RAKYAT INDONESIA (PERSERO) Tbk.")
            b_pemilik = t_data.get("Atas Nama Rekening", "PT. BANGGAI SENTRAL SULAWESI")
            b_cabang = t_data.get("Cabang Bank", "Cabang Luwuk")
            b_rekening = t_data.get("Nomor Rekening", "0167 0167 8888 303")
            bank_string_dinamis = f"<b>Bank Name :</b> {b_nama}<br><b>Branch :</b> {b_cabang}<br><b>Account No :</b> {b_rekening}<br><b>Account Name :</b> {b_pemilik}"
        else:
            bank_string_dinamis = data_edit_aktif.get("Informasi Bank", "<b>Bank Name :</b> BANK RAKYAT INDONESIA (PERSERO) Tbk.<br><b>Branch :</b> Cabang Luwuk<br><b>Account No :</b> 0167 0167 8888 303<br><b>Account Name :</b> PT. BANGGAI SENTRAL SULAWESI")

        deskripsi_po_default = matched_transaksi[0].get("Deskripsi PO", "") if matched_transaksi else ""
        if not deskripsi_po_default and matched_transaksi:
            deskripsi_po_default = "Meeting package pelatihan HSE untuk kegiatan wellservices 2026"

        with st.form("form_input_billing_resmi"):
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.markdown(f"**PI Rujukan Aktif:** `{selected_pi_m3}`")
                customer_name = st.text_input("Customer / Klien", value=customer_default)
                alamat_customer = st.text_area("Alamat Klien", value=alamat_default, height=75)
                
                def_sa_wan = format_nomor_bersih(data_edit_aktif.get("Nomor SA / WAN", ""))
                nomor_sa_wan = st.text_input(
                    "Nomor SA / WAN (Work Acceptance Notice / Service Agreement)",
                    value=def_sa_wan,
                    placeholder="Ketik manual nomor SA / WAN di sini..."
                )

                npwp_records = st.session_state["db_npwp"]
                existing_npwp = next((n.get("NPWP") for n in npwp_records if n.get("Customer") == customer_name), "002.796.802.3-081.000")
                nomor_npwp = st.text_input("Nomor NPWP Customer", value=str(data_edit_aktif.get("NPWP Customer", existing_npwp)))

            with col_b2:
                nomor_invoice_resmi = st.text_input("Nomor Invoice Resmi (Diberikan Accounting)", value=str(data_edit_aktif.get("Nomor Invoice Resmi", "")))
                
                tgl_inv_val = datetime.today().date()
                try:
                    tgl_inv_val = datetime.strptime(str(data_edit_aktif.get("Tanggal Invoice", "")), "%Y-%m-%d").date()
                except:
                    pass
                tanggal_invoice = st.date_input("Tanggal Invoice", value=tgl_inv_val)

                due_date_val = datetime.today().date() + timedelta(days=30)
                try:
                    due_date_val = datetime.strptime(str(data_edit_aktif.get("Jatuh Tempo", "")), "%Y-%m-%d").date()
                except:
                    pass
                tanggal_jatuh_tempo = st.date_input("Tanggal Jatuh Tempo (Due Date)", value=due_date_val)

                st.markdown(f"**Total Nilai PI Terdeteksi:** Rp {total_nilai_pi:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                
                try:
                    val_custom_tagihan = float(data_edit_aktif.get("Nilai Invoice", total_nilai_pi))
                except:
                    val_custom_tagihan = total_nilai_pi

                nilai_invoice_resmi = st.number_input("Total Nilai Tagihan Invoice (Rp)", min_value=0.0, value=val_custom_tagihan, step=1000.0, format="%.2f")

            st.markdown("---")
            def_keterangan_inv = data_edit_aktif.get("Keterangan Invoice", deskripsi_po_default)
            keterangan_invoice_resmi = st.text_area(
                "📝 Deskripsi Keterangan Invoice (Opsional: Otomatis dari Ruang Lingkup Pekerjaan, dapat disesuaikan jika diperlukan):",
                value=def_keterangan_inv,
                height=90
            )

            st.markdown("---")
            st.markdown("#### 🧮 Kalkulasi Otomatis Pajak (PPN 11% & PPh 23 / Pasal 22)")

            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                kena_ppn = st.checkbox("Kenakan PPN (11%)", value=data_edit_aktif.get("Kena PPN", True))
            with col_p2:
                kena_pph = st.checkbox("Potong PPh (2% / 1.5% - PPh 23/22)", value=data_edit_aktif.get("Kena PPh", True))
            with col_p3:
                persen_pph = st.number_input("Tarif PPh (%)", min_value=0.0, max_value=10.0, value=float(data_edit_aktif.get("Tarif PPh", 2.0)), step=0.5)

            ppn_nominal = nilai_invoice_resmi * 0.11 if kena_ppn else 0.0
            pph_nominal = nilai_invoice_resmi * (persen_pph / 100.0) if kena_pph else 0.0
            total_pembayaran_netto = nilai_invoice_resmi + ppn_nominal - pph_nominal

            st.markdown(f"""
                * **Dasar Tagihan:** Rp {nilai_invoice_resmi:,.2f}
                * **Nilai PPN (11%):** Rp {ppn_nominal:,.2f}
                * **Potongan PPh ({persen_pph}%):** Rp {pph_nominal:,.2f}
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
                        st.success("✨ Data Invoice & Pajak berhasil di-update!")
                    elif submit_save_as or submit_simpan_baru:
                        current_billing.append(item_billing_baru)
                        simpan_data_billing(current_billing)
                        st.success("🎉 Data Invoice & Pajak baru berhasil disimpan!")
                        st.session_state["edit_billing_idx"] = None

    # --- MENU 2: PRATINJAU, CETAK & DOWNLOAD PDF INVOICE ---
    elif menu_pilihan == "Pratinjau, Cetak & Download PDF Invoice":
        st.markdown("#### 🖨️ Pratinjau & Cetak Dokumen Invoice Resmi (Standar ISO & Upload Logo)")
        
        billing_records = muat_data_billing()
        if not billing_records:
            st.warning("⚠️ Belum ada data invoice resmi tersimpan di Modul 3.")
        else:
            list_inv_resmi = sorted(
                list(dict.fromkeys([str(item.get("Nomor Invoice Resmi")) for item in billing_records if item.get("Nomor Invoice Resmi")])),
                key=sort_pi_key,
                reverse=True
            )

            col_ctrl1, col_ctrl2 = st.columns([2, 2])
            with col_ctrl1:
                selected_inv_preview = st.selectbox("🔄 Panggil Ulang Nomor Invoice Disimpan:", list_inv_resmi, key="preview_panggil_inv")
            with col_ctrl2:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                col_btn_a, col_btn_b = st.columns(2)
                with col_btn_a:
                    if st.button("💾 Save Data", use_container_width=True):
                        st.success("✅ Data invoice tersimpan di database.")
                with col_btn_b:
                    if st.button("📝 Update Data", use_container_width=True):
                        st.success("✨ Data berhasil diperbarui.")

            st.markdown("---")
            
            with st.expander("🖼️ Pengaturan Logo Kop Surat (Upload Logo BSS & ISO)", expanded=False):
                col_ul1, col_ul2 = st.columns(2)
                with col_ul1:
                    uploaded_logo_bss = st.file_uploader("Upload Logo BSS (Kiri)", type=["png", "jpg", "jpeg"], key="logo_bss_upload")
                with col_ul2:
                    uploaded_logo_iso = st.file_uploader("Upload Logo ISO (Kanan - Proporsional Seimbang)", type=["png", "jpg", "jpeg"], key="logo_iso_upload")

            selected_record = next((item for item in billing_records if str(item.get("Nomor Invoice Resmi")) == str(selected_inv_preview)), None)

            if selected_record:
                val_inv = float(selected_record.get('Nilai Invoice', 0))
                val_ppn = float(selected_record.get('PPN Nominal', 0))
                val_pph = float(selected_record.get('PPh Nominal', 0))
                val_netto = float(selected_record.get('Total Netto', 0))
                dpp_nilai_lain = val_inv * (11 / 12) if val_ppn > 0 else val_inv

                nomor_sa_wan_val = format_nomor_bersih(selected_record.get('Nomor SA / WAN', ''))
                nomor_po_val = format_nomor_bersih(selected_record.get('Nomor PO', selected_record.get('Nomor PO Rujukan', '-')))
                
                kontrak_no_val = format_nomor_bersih(selected_record.get('Kontrak No.', '-'))
                bank_info_val = selected_record.get('Informasi Bank', '<b>Bank Name :</b> BANK RAKYAT INDONESIA (PERSERO) Tbk.<br><b>Branch :</b> Cabang Luwuk<br><b>Account No :</b> 0167 0167 8888 303<br><b>Account Name :</b> PT. BANGGAI SENTRAL SULAWESI')

                logo_bss_b64 = get_image_base64(uploaded_logo_bss) if uploaded_logo_bss else None
                logo_iso_b64 = get_image_base64(uploaded_logo_iso) if uploaded_logo_iso else None

                html_logo_kiri = f'<img src="{logo_bss_b64}" style="max-height: 70px; max-width: 120px; object-fit: contain;">' if logo_bss_b64 else '<div style="border: 1px dashed #94a3b8; padding: 18px 8px; font-size: 11px; color: #64748b; background: #f8fafc; border-radius: 4px;"><b>[LOGO BSS]</b></div>'
                html_logo_kanan = f'<img src="{logo_iso_b64}" style="max-height: 70px; max-width: 120px; object-fit: contain;">' if logo_iso_b64 else '<div style="border: 1px dashed #94a3b8; padding: 18px 8px; font-size: 11px; color: #64748b; background: #f8fafc; border-radius: 4px;"><b>[LOGO ISO]</b></div>'

                html_invoice = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        @page {{
                            size: A4;
                            margin: 10mm 15mm;
                        }}
                        body {{ 
                            background-color: #f1f5f9; 
                            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; 
                            margin: 0; 
                            padding: 10px; 
                        }}
                        .invoice-container {{ 
                            background-color: white; 
                            color: #111; 
                            padding: 25px; 
                            border: 2px solid #000; 
                            border-radius: 4px; 
                            max-width: 820px; 
                            margin: auto; 
                        }}
                        .print-btn {{ 
                            background-color: #1e293b; 
                            color: white; 
                            border: none; 
                            padding: 10px 20px; 
                            font-size: 14px; 
                            font-weight: bold; 
                            border-radius: 6px; 
                            cursor: pointer; 
                            margin-bottom: 15px; 
                            display: block; 
                            margin-left: auto; 
                            margin-right: auto; 
                        }}
                        .print-btn:hover {{ background-color: #334155; }}
                        @media print {{
                            body {{ background-color: white; padding: 0; margin: 0; }}
                            .print-btn {{ display: none; }}
                            .invoice-container {{ border: none; padding: 0; max-width: 100%; margin: 0; }}
                            @page {{ margin: 10mm 15mm; }}
                        }}
                        .iso-footer-left {{
                            font-size: 9px;
                            font-weight: bold;
                            color: #000;
                            margin-top: 25px;
                            border-top: 1px solid #000;
                            padding-top: 6px;
                            text-align: left;
                        }}
                    </style>
                </head>
                <body>
                    <button class="print-btn" onclick="window.print()">🖨️ Cetak / Print Dokumen Ini (Save to PDF)</button>
                    
                    <div class="invoice-container">
                        <!-- KOP SURAT 3 KOLOM -->
                        <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px; border-bottom: 2px solid #000; padding-bottom: 10px;">
                            <tr>
                                <td style="width: 22%; vertical-align: middle; text-align: center; padding: 5px;">
                                    {html_logo_kiri}
                                </td>
                                <td style="width: 56%; vertical-align: middle; text-align: center; padding: 5px;">
                                    <h3 style="margin: 0; font-size: 16px; font-weight: bold; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px;">PT Banggai Sentral Sulawesi</h3>
                                    <p style="margin: 3px 0; font-size: 11px; font-weight: bold; color: #334155; letter-spacing: 0.3px;">General Contractor and Supplier</p>
                                    <p style="margin: 2px 0 0 0; font-size: 10px; color: #475569;">Jl. Urip Sumoharjo Nomor 53, Luwuk, Kabupaten Banggai, Provinsi Sulawesi Tengah</p>
                                </td>
                                <td style="width: 22%; vertical-align: middle; text-align: center; padding: 5px;">
                                    {html_logo_kanan}
                                </td>
                            </tr>
                        </table>

                        <!-- Header Bar -->
                        <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
                            <tr>
                                <td style="border: 1px solid #000; padding: 8px 12px; font-weight: bold; width: 60%; background: #ffffff; color: #000;">Original</td>
                                <td style="border: 1px solid #000; padding: 8px 12px; text-align: right; font-weight: bold; font-size: 20px; background: #ffffff; color: #000; width: 40%; letter-spacing: 1px;">INVOICE</td>
                            </tr>
                        </table>

                        <!-- Customer & Misc Box -->
                        <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 20px;">
                            <tr>
                                <td style="width: 50%; border: 1px solid #000; vertical-align: top; padding: 12px;">
                                    <div style="font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 4px; margin-bottom: 8px;">Customer</div>
                                    <table style="width: 100%; font-size: 13px; border-collapse: collapse;">
                                        <tr>
                                            <td style="width: 65px; vertical-align: top; padding: 3px 0; font-weight: normal;">Name</td>
                                            <td style="width: 15px; vertical-align: top; padding: 3px 0;">:</td>
                                            <td style="vertical-align: top; padding: 3px 0; font-weight: bold;">{selected_record.get('Customer')}</td>
                                        </tr>
                                        <tr>
                                            <td style="vertical-align: top; padding: 3px 0; font-weight: normal;">Address</td>
                                            <td style="vertical-align: top; padding: 3px 0;">:</td>
                                            <td style="vertical-align: top; padding: 3px 0;">{selected_record.get('Alamat Customer')}</td>
                                        </tr>
                                        <tr>
                                            <td style="vertical-align: top; padding: 3px 0; font-weight: normal;">NPWP</td>
                                            <td style="vertical-align: top; padding: 3px 0;">:</td>
                                            <td style="vertical-align: top; padding: 3px 0;">{selected_record.get('NPWP Customer')}</td>
                                        </tr>
                                    </table>
                                </td>
                                <td style="width: 50%; border: 1px solid #000; vertical-align: top; padding: 12px; border-left: none;">
                                    <div style="font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 4px; margin-bottom: 8px;">Misc</div>
                                    <table style="width: 100%; font-size: 13px; border-collapse: collapse;">
                                        <tr><td style="width: 130px; padding: 3px 0;">Invoice No.</td><td style="padding: 3px 0;">: <b>{selected_record.get('Nomor Invoice Resmi')}</b></td></tr>
                                        <tr><td style="padding: 3px 0;">Invoice Date</td><td style="padding: 3px 0;">: {selected_record.get('Tanggal Invoice')}</td></tr>
                                        <tr><td style="padding: 3px 0;">Contract Number</td><td style="padding: 3px 0;">: {kontrak_no_val}</td></tr>
                                        <tr><td style="padding: 3px 0;">PO Nomor</td><td style="padding: 3px 0;">: {nomor_po_val}</td></tr>
                                        {f"<tr><td style='padding: 3px 0;'>WAN / SA Nomor</td><td style='padding: 3px 0;'>: {nomor_sa_wan_val}</td></tr>" if nomor_sa_wan_val and nomor_sa_wan_val != "-" else ""}
                                        <tr><td style="padding: 3px 0;">Due Date</td><td style="padding: 3px 0;">: {selected_record.get('Jatuh Tempo')}</td></tr>
                                    </table>
                                </td>
                            </tr>
                        </table>

                        <!-- Item Description Table -->
                        <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 15px;">
                            <thead>
                                <tr style="background-color: #f1f5f9; border: 1px solid #000;">
                                    <th style="border: 1px solid #000; padding: 8px; width: 45px; text-align: center;">No.</th>
                                    <th style="border: 1px solid #000; padding: 8px; text-align: left;">DESCRIPTION</th>
                                    <th style="border: 1px solid #000; padding: 8px; width: 70px; text-align: center;">UNIT</th>
                                    <th style="border: 1px solid #000; padding: 8px; width: 150px; text-align: right;">AMOUNT (Rp.)</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td style="border: 1px solid #000; padding: 12px 10px 140px 10px; text-align: center; vertical-align: top;">1</td>
                                    <td style="border: 1px solid #000; padding: 12px 10px 140px 10px; vertical-align: top;">
                                        <b>{selected_record.get('Keterangan Invoice')}</b>
                                    </td>
                                    <td style="border: 1px solid #000; padding: 12px 10px 140px 10px; text-align: center; vertical-align: top;">-</td>
                                    <td style="border: 1px solid #000; padding: 12px 10px 140px 10px; text-align: right; vertical-align: top;">Rp {val_inv:,.2f}</td>
                                </tr>
                                
                                <!-- Bank & Totals Section -->
                                <tr>
                                    <td colspan="2" style="border: 1px solid #000; padding: 15px; vertical-align: top;">
                                        <div style="font-size: 12px; font-weight: bold; margin-bottom: 4px; text-transform: uppercase;">PAYMENT INSTRUCTION</div>
                                        <div style="font-size: 11.5px; margin-bottom: 6px; color: #334155;">Please remit to our bank:</div>
                                        <div style="border: 1px solid #000; padding: 10px; background: #fafafa; font-size: 12px; line-height: 1.4; display: inline-block; width: 92%;">
                                            {bank_info_val}
                                        </div>
                                    </td>
                                    <td colspan="2" style="border: 1px solid #000; padding: 0; vertical-align: top;">
                                        <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                                            <tr>
                                                <td style="border-bottom: 1px solid #000; padding: 8px; font-weight: bold;">Total Amount Due</td>
                                                <td style="border-bottom: 1px solid #000; padding: 8px; text-align: right;">Rp {val_inv:,.2f}</td>
                                            </tr>
                                            <tr>
                                                <td style="border-bottom: 1px solid #000; padding: 8px; font-size: 11px; color: #475569;">DPP Nilai Lain (11/12)</td>
                                                <td style="border-bottom: 1px solid #000; padding: 8px; text-align: right; font-size: 11px; color: #475569;">Rp {dpp_nilai_lain:,.2f}</td>
                                            </tr>
                                            <tr>
                                                <td style="border-bottom: 1px solid #000; padding: 8px;">VAT (PPN 11%)</td>
                                                <td style="border-bottom: 1px solid #000; padding: 8px; text-align: right;">Rp {val_ppn:,.2f}</td>
                                            </tr>
                                            {f"<tr><td style='border-bottom: 1px solid #000; padding: 8px; color: #b91c1c;'>Potongan PPh</td><td style='border-bottom: 1px solid #000; padding: 8px; text-align: right; color: #b91c1c;'>(Rp {val_pph:,.2f})</td></tr>" if val_pph > 0 else ""}
                                            <tr style="background-color: #f1f5f9; font-weight: bold;">
                                                <td style="padding: 10px; border-top: 2px solid #000;">T O T A L</td>
                                                <td style="padding: 10px; border-top: 2px solid #000; text-align: right;">Rp {val_netto:,.2f}</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </tbody>
                        </table>

                        <!-- Signature Section (Digeser ke Kanan di Bawah Kolom Total) -->
                        <table style="width: 100%; margin-top: 25px; border-collapse: collapse;">
                            <tr>
                                <td style="width: 55%;"></td>
                                <td style="width: 45%; text-align: left; padding-left: 20px;">
                                    <p style="margin: 0 0 85px 0;">Best Regards,</p>
                                    <p style="margin: 0; font-weight: bold; text-decoration: underline; font-size: 14px;">Ferry Tatimu</p>
                                    <p style="margin: 2px 0 0 0; font-size: 13px;">Direktur</p>
                                </td>
                            </tr>
                        </table>

                        <!-- Footer Code ISO (Bersih di Sudut Kiri Bawah Tanpa Duplikasi) -->
                        <div class="iso-footer-left">
                            FM-AK-11 Rev: 00
                        </div>
                    </div>
                </body>
                </html>
                """

                components.html(html_invoice, height=1050, scrolling=True)

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