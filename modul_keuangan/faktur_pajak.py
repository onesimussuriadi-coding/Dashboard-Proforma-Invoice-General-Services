import streamlit as st
import pandas as pd
import os
from datetime import datetime

def tampilkan_faktur_pajak(transaksi_list, menu_pilihan=None):
    st.markdown("#### 🌐 Tautan & Pencatatan Referensi e-Faktur Online (Coretax DJP)")

    DIR_DATABASE = "database_penyimpanan_aman"
    EXCEL_FAKTUR_PAJAK = os.path.join(DIR_DATABASE, "database_faktur_pajak_online.xlsx")

    def muat_invoice_resmi_dari_modul3():
        kemungkinan_file = [
            os.path.join(DIR_DATABASE, "database_invoice_resmi.xlsx"),
            os.path.join(DIR_DATABASE, "database_billing_tax.xlsx"),
            os.path.join(DIR_DATABASE, "database_invoice.xlsx")
        ]
        for file_path in kemungkinan_file:
            if os.path.exists(file_path):
                try:
                    df = pd.read_excel(file_path)
                    if df is not None and not df.empty:
                        return df.to_dict(orient="records")
                except:
                    pass
        return []

    def muat_faktur_tersimpan():
        if os.path.exists(EXCEL_FAKTUR_PAJAK):
            try:
                df = pd.read_excel(EXCEL_FAKTUR_PAJAK)
                if df is not None and not df.empty:
                    return df.to_dict(orient="records")
            except:
                pass
        return []

    def simpan_faktur_tersimpan(data_list):
        df_baru = pd.DataFrame(data_list)
        df_baru.to_excel(EXCEL_FAKTUR_PAJAK, index=False)

    invoice_resmi_list = muat_invoice_resmi_dari_modul3()
    db_faktur_list = muat_faktur_tersimpan()

    # Buat sub-menu pilihan di dalam modul faktur pajak agar bisa melihat daftar tersimpan
    sub_menu_faktur = st.radio(
        "Pilih Menu Faktur Pajak:",
        ["Input & Referensi Faktur Pajak", "📂 Lihat Daftar Referensi Faktur Pajak Tersimpan"],
        horizontal=True
    )

    st.markdown("---")

    if sub_menu_faktur == "📂 Lihat Daftar Referensi Faktur Pajak Tersimpan":
        st.markdown("##### 📁 Akumulasi Daftar Referensi Faktur Pajak yang Sudah Disimpan")
        st.info(f"📂 **Lokasi Penyimpanan File:** Folder `database_penyimpanan_aman/database_faktur_pajak_online.xlsx`")

        if not db_faktur_list:
            st.warning("⚠️ Belum ada catatan referensi faktur pajak yang tersimpan.")
        else:
            df_faktur = pd.DataFrame(db_faktur_list)
            st.dataframe(df_faktur, use_container_width=True)

            st.markdown("---")
            st.markdown("#### 🗑️ Hapus Catatan Referensi Faktur Pajak")
            
            pilihan_hapus_faktur = []
            for idx, item in enumerate(db_faktur_list):
                inv_no = str(item.get('Nomor Invoice', 'Tanpa Invoice'))
                nsfp_val = str(item.get('NSFP', 'Tanpa NSFP'))
                pilihan_hapus_faktur.append(f"Index {idx} | Invoice: {inv_no} | NSFP: {nsfp_val}")

            col_hf1, col_hf2 = st.columns([2, 1])
            with col_hf1:
                target_hapus_idx = st.selectbox(
                    "Pilih Catatan Faktur yang Ingin Dihapus:",
                    range(len(pilihan_hapus_faktur)),
                    format_func=lambda x: pilihan_hapus_faktur[x]
                )
            with col_hf2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("❌ Hapus Catatan Terpilih", use_container_width=True, type="primary"):
                    try:
                        db_faktur_list.pop(target_hapus_idx)
                        simpan_faktur_tersimpan(db_faktur_list)
                        st.success("✅ Berhasil menghapus catatan referensi faktur pajak secara permanen!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Gagal menghapus data: {e}")
        return

    # --- TAMPILAN UTAMA: INPUT & REFERENSI ---
    if not invoice_resmi_list:
        st.warning("⚠️ Belum ada Data Invoice Resmi yang tersimpan di Modul 3. Pastikan Anda telah menyimpan data invoice melalui menu 'Input Data Invoice Resmi' di Modul 3.")
        return

    # Tautan Resmi Portal Coretax DJP
    url_coretax_login = "https://coretaxdjp.pajak.go.id/identityproviderportal/account/login"

    st.markdown(f"""
        <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center;">
            <h4 style="margin: 0 0 8px 0; color: #166534;">🔗 Portal Resmi Coretax DJP</h4>
            <p style="margin: 0 0 12px 0; font-size: 13px; color: #15803d;">Klik tombol di bawah ini untuk langsung menuju halaman login sistem perpajakan Coretax.</p>
            <a href="{url_coretax_login}" target="_blank">
                <button style="background-color: #10b981; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 14px;">
                    🌐 Buka Login Coretax DJP
                </button>
            </a>
        </div>
    """, unsafe_allow_html=True)

    def sort_invoice_key(inv_str):
        try:
            parts = str(inv_str).split('/')
            if parts:
                digits = "".join([c for c in parts[0] if c.isdigit()])
                return int(digits) if digits else 0
        except:
            pass
        return 0

    sample_inv = invoice_resmi_list[0]
    k_key = "Nomor Kontrak" if "Nomor Kontrak" in sample_inv else ("Kontrak No." if "Kontrak No." in sample_inv else list(sample_inv.keys())[1])
    inv_key = "Nomor Invoice" if "Nomor Invoice" in sample_inv else ("Nomor Invoice Resmi" if "Nomor Invoice Resmi" in sample_inv else list(sample_inv.keys())[0])

    st.markdown("##### 📝 Pencatatan & Referensi Data Faktur Pajak")

    list_kontrak_tersedia = sorted(list(set([str(inv.get(k_key, "")) for inv in invoice_resmi_list if inv.get(k_key)])))

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_kontrak_fp = st.selectbox("Pilih Nomor Kontrak Referensi:", list_kontrak_tersedia if list_kontrak_tersedia else ["-- Tidak Ada Kontrak --"])
    
    invoice_filtered_kontrak = [inv for inv in invoice_resmi_list if str(inv.get(k_key, "")) == str(selected_kontrak_fp)]
    list_invoice_raw = [str(inv.get(inv_key, "")) for inv in invoice_filtered_kontrak if inv.get(inv_key)]
    list_invoice_tersedia = sorted(list(set(list_invoice_raw)), key=sort_invoice_key, reverse=True)

    with col_f2:
        selected_invoice_no = st.selectbox("Pilih Nomor Invoice Resmi:", list_invoice_tersedia if list_invoice_tersedia else ["-- Tidak Ada Invoice Resmi --"])

    saved_options = ["-- Buat Baru / Sesuai Invoice --"] + [f"Invoice: {f.get('Nomor Invoice')} | NSFP: {f.get('NSFP')}" for f in db_faktur_list]
    panggil_pilihan = st.selectbox("🔄 Panggil Ulang Catatan Faktur:", saved_options)

    matched_inv_data = next((inv for inv in invoice_filtered_kontrak if str(inv.get(inv_key)) == str(selected_invoice_no)), {})
    
    def_cust_name = matched_inv_data.get("Customer", matched_inv_data.get("Ditujukan Kepada", "JOB Pertamina - Medco E&P Tomori Sulawesi"))
    def_cust_npwp = matched_inv_data.get("NPWP Customer", matched_inv_data.get("NPWP", "002.796.802.3-081.000"))
    def_cust_addr = matched_inv_data.get("Alamat Customer", matched_inv_data.get("Alamat", "Bidakara Office Tower I 4Th Floor, Jl. Gatot Subroto"))

    total_invoice_value = 0.0
    for col_coba in ["Grand Total", "Total Tagihan", "Total Harga", "Total", "Jumlah", "Nilai Invoice"]:
        if col_coba in matched_inv_data:
            try:
                val_parsed = float(str(matched_inv_data.get(col_coba, 0)).replace(",", "").replace("Rp", "").strip())
                if val_parsed > 0:
                    total_invoice_value = val_parsed
                    break
            except:
                pass

    if total_invoice_value <= 0:
        for k, v in matched_inv_data.items():
            if any(kw in str(k).lower() for kw in ['total', 'grand', 'jumlah', 'nilai']):
                try:
                    val_parsed = float(str(v).replace(",", "").replace("Rp", "").strip())
                    if val_parsed > 0:
                        total_invoice_value = val_parsed
                        break
                except:
                    pass

    default_ket = matched_inv_data.get("Keterangan", "")
    if not default_ket:
        default_ket = f"Pembayaran tagihan berdasarkan Invoice No. {selected_invoice_no}"

    def_nsfp = "010.003-26.98765432"
    if panggil_pilihan != "-- Buat Baru / Sesuai Invoice --":
        matched_saved = next((f for f in db_faktur_list if f"Invoice: {f.get('Nomor Invoice')} | NSFP: {f.get('NSFP')}" == panggil_pilihan), None)
        if matched_saved:
            def_nsfp = matched_saved.get("NSFP", def_nsfp)
            default_ket = matched_saved.get("Keterangan", default_ket)
            if float(matched_saved.get("Nilai DPP", 0)) > 0:
                total_invoice_value = float(matched_saved.get("Nilai DPP", 0))
            if matched_saved.get("Customer Name"):
                def_cust_name = matched_saved.get("Customer Name")
            if matched_saved.get("Customer Address"):
                def_cust_addr = matched_saved.get("Customer Address")
            if matched_saved.get("Customer NPWP"):
                def_cust_npwp = matched_saved.get("Customer NPWP")

    st.markdown("---")
    st.markdown("##### 🏢 Referensi Data Customer (Penerima Jasa / Pembeli) - *Bisa disalin (copy-paste) manual ke Coretax*")

    col_cust1, col_cust2, col_cust3 = st.columns(3)
    with col_cust1:
        cust_name_input = st.text_input("Nama Customer:", value=str(def_cust_name))
    with col_cust2:
        cust_npwp_input = st.text_input("NPWP Customer:", value=str(def_cust_npwp))
    with col_cust3:
        cust_addr_input = st.text_input("Alamat Customer:", value=str(def_cust_addr))

    st.markdown("---")

    col_i1, col_i2 = st.columns(2)
    with col_i1:
        nsfp_input = st.text_input("Nomor Seri Faktur Pajak (NSFP):", value=def_nsfp)
        tanggal_fp = st.date_input("Tanggal Faktur Pajak:", value=datetime.today())
    with col_i2:
        formatted_dpp_default = f"{total_invoice_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        dpp_input_str = st.text_input("Nilai Total Invoice (DPP) - Bisa disalin:", value=formatted_dpp_default)
        
        try:
            clean_dpp = float(dpp_input_str.replace(".", "").replace(",", "."))
        except:
            clean_dpp = total_invoice_value

    keterangan_input = st.text_area("📝 Keterangan (Bersumber dari Invoice & Opsional untuk Diubah):", value=default_ket, height=90)

    st.markdown("---")

    if st.button("💾 Simpan Catatan Referensi Faktur Pajak", type="primary"):
        waktu_aksi = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        data_baru = {
            "Nomor Kontrak": selected_kontrak_fp,
            "Nomor Invoice": selected_invoice_no,
            "NSFP": nsfp_input,
            "Tanggal FP": tanggal_fp.strftime("%Y-%m-%d"),
            "Nilai DPP": clean_dpp,
            "Customer Name": cust_name_input,
            "Customer Address": cust_addr_input,
            "Customer NPWP": cust_npwp_input,
            "Keterangan": keterangan_input,
            "Update Terakhir": waktu_aksi
        }
        
        existing = [f for f in db_faktur_list if str(f.get("Nomor Invoice")) != str(selected_invoice_no)]
        existing.append(data_baru)
        simpan_faktur_tersimpan(existing)
        st.success(f"🎉 Berhasil menyimpan catatan referensi Faktur Pajak untuk Nomor Invoice [{selected_invoice_no}]!")