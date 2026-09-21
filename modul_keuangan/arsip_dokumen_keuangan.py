import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

def tampilkan_arsip_dokumen_keuangan(billing_records, is_management):
    st.markdown("#### 📁 Manajemen Arsip Dokumen Pendukung Keuangan Terpusat")
    st.markdown("Unggah dan kelola arsip file terkait penagihan seperti **Invoice Resmi, Faktur Pajak, SSP PPN, SSP PPh, Bukti Potong (Bupot)**, dan dokumen pendukung pembayaran lainnya secara terstruktur.")

    DIR_DATABASE = "database_penyimpanan_aman"
    if not os.path.exists(DIR_DATABASE):
        os.makedirs(DIR_DATABASE)

    EXCEL_ARSIP_PAJAK = os.path.join(DIR_DATABASE, "database_arsip_dokumen_pajak.xlsx")
    DIR_ARSIP_FILES = os.path.join(DIR_DATABASE, "arsip_billing_files")
    if not os.path.exists(DIR_ARSIP_FILES):
        os.makedirs(DIR_ARSIP_FILES)

    def muat_arsip_pajak():
        if os.path.exists(EXCEL_ARSIP_PAJAK):
            try:
                df = pd.read_excel(EXCEL_ARSIP_PAJAK, engine='openpyxl')
                if df is not None and not df.empty:
                    return df.dropna(how='all').to_dict(orient="records")
            except:
                pass
        return []

    def simpan_arsip_pajak(data_list):
        if is_management:
            return
        df_baru = pd.DataFrame(data_list)
        try:
            with pd.ExcelWriter(EXCEL_ARSIP_PAJAK, engine='openpyxl') as writer:
                df_baru.to_excel(writer, index=False, sheet_name="Arsip_Dokumen_Pajak")
        except Exception as e:
            st.error(f"⚠️ Error saat menyimpan Arsip Pajak: {e}")
        st.session_state["db_arsip_pajak"] = data_list

    if "db_arsip_pajak" not in st.session_state:
        st.session_state["db_arsip_pajak"] = muat_arsip_pajak()

    arsip_records = st.session_state["db_arsip_pajak"]

    if not billing_records:
        st.warning("⚠️ Belum ada data Invoice Resmi tersimpan. Silakan buat/simpan invoice terlebih dahulu di menu 'Input Data Invoice Resmi'.")
        return

    def sort_pi_key(pi_str):
        try:
            parts = str(pi_str).split('/')
            if parts:
                digits = "".join([c for c in parts[0] if c.isdigit()])
                return int(digits) if digits else 0
        except:
            pass
        return 0

    list_inv_arsip = sorted(
        list(dict.fromkeys([str(item.get("Nomor Invoice Resmi")) for item in billing_records if item.get("Nomor Invoice Resmi")])),
        key=sort_pi_key,
        reverse=True
    )

    with st.form("form_upload_arsip_keuangan", clear_on_submit=True):
        col_ar1, col_ar2 = st.columns(2)
        with col_ar1:
            selected_inv_arsip = st.selectbox("Pilih Nomor Invoice Resmi Terkait:", list_inv_arsip)
            matched_inv_info = next((i for i in billing_records if str(i.get("Nomor Invoice Resmi")) == str(selected_inv_arsip)), {})
            
            klien_terikat = matched_inv_info.get("Customer", "-")
            kontrak_terikat = matched_inv_info.get("Kontrak No.", "-")
            
            st.markdown(f"**Klien Terikat:** `{klien_terikat}`")
            st.markdown(f"**Kontrak Terikat:** `{kontrak_terikat}`")

            jenis_dokumen_arsip = st.selectbox("Jenis Dokumen Pendukung:", [
                "Invoice Resmi (Signed/Stamped)",
                "Faktur Pajak (e-Faktur)",
                "SSP PPN (Surat Setoran Pajak PPN)",
                "SSP PPh (Surat Setoran Pajak PPh)",
                "Bukti Potong PPh (Bupot 23/22)",
                "Berita Acara / Dokumen Pendukung Lainnya"
            ])

        with col_ar2:
            keterangan_arsip = st.text_area("Keterangan / Catatan Dokumen:", placeholder="Contoh: Faktur pajak masa Juni 2026 lengkap dengan NTPN.")
            file_dokumen_upload = st.file_uploader("Upload File Dokumen (PDF / Gambar / Excel / Word):", type=["pdf", "png", "jpg", "jpeg", "xlsx", "xls", "docx", "doc"])

        st.markdown("<br>", unsafe_allow_html=True)
        submit_upload_arsip = st.form_submit_button("📤 Unggah & Simpan ke Arsip Keuangan", use_container_width=True, type="primary")

        if submit_upload_arsip:
            if is_management:
                st.error("⚠️ Akses ditolak: Akun Direksi berada dalam mode Read-Only.")
            elif not file_dokumen_upload:
                st.error("⚠️ Silakan pilih file dokumen yang akan di-upload!")
            else:
                nama_file_asli = file_dokumen_upload.name
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_nama_file = f"{timestamp_str}_{nama_file_asli.replace(' ', '_')}"
                path_simpan_lokal = os.path.join(DIR_ARSIP_FILES, safe_nama_file)

                try:
                    with open(path_simpan_lokal, "wb") as f:
                        f.write(file_dokumen_upload.getbuffer())

                    waktu_upload = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
                    item_arsip_baru = {
                        "Nomor Invoice Resmi": selected_inv_arsip,
                        "Customer": klien_terikat,
                        "Kontrak No.": kontrak_terikat,
                        "Jenis Dokumen": jenis_dokumen_arsip,
                        "Nama File": nama_file_asli,
                        "Path File": path_simpan_lokal,
                        "Keterangan": keterangan_arsip,
                        "Tanggal Upload": waktu_upload
                    }

                    arsip_records.append(item_arsip_baru)
                    simpan_arsip_pajak(arsip_records)
                    st.success(f"✅ Dokumen `{nama_file_asli}` berhasil diunggah dan diarsipkan untuk Invoice `{selected_inv_arsip}`!")
                    st.rerun()
                except Exception as e:
                    st.error(f"⚠️ Gagal mengunggah file: {e}")

    st.markdown("---")
    st.markdown("##### 📚 Daftar Arsip Dokumen Pendukung Tersimpan")

    if arsip_records:
        df_arsip = pd.DataFrame(arsip_records)
        
        filter_inv_tampil = st.selectbox("🔍 Saring Berdasarkan Nomor Invoice:", ["-- Tampilkan Semua Invoice --"] + list_inv_arsip)
        if filter_inv_tampil != "-- Tampilkan Semua Invoice --":
            df_arsip_tampil = df_arsip[df_arsip["Nomor Invoice Resmi"] == filter_inv_tampil]
        else:
            df_arsip_tampil = df_arsip

        if not df_arsip_tampil.empty:
            for idx, row in df_arsip_tampil.iterrows():
                with st.container():
                    col_info, col_act1, col_act2 = st.columns([3, 1, 1])
                    with col_info:
                        st.markdown(f"**📂 [{row.get('Jenis Dokumen')}]** — `{row.get('Nama File')}`")
                        st.markdown(f"<span style='font-size: 11.5px; color: #475569;'>Invoice: <b>{row.get('Nomor Invoice Resmi')}</b> | Klien: {row.get('Customer')} | Upload: {row.get('Tanggal Upload')}</span>", unsafe_allow_html=True)
                        if row.get('Keterangan'):
                            st.markdown(f"<span style='font-size: 11px; color: #334155;'>Catatan: {row.get('Keterangan')}</span>", unsafe_allow_html=True)
                    
                    path_file_lokal = row.get("Path File")
                    with col_act1:
                        if path_file_lokal and os.path.exists(path_file_lokal):
                            with open(path_file_lokal, "rb") as file_down:
                                st.download_button(
                                    label="📥 Download",
                                    data=file_down,
                                    file_name=row.get("Nama File"),
                                    key=f"dl_arsip_k euclidean_{idx}",
                                    use_container_width=True
                                )
                        else:
                            st.warning("File tidak ditemukan di server.")

                    with col_act2:
                        if not is_management:
                            if st.button("❌ Hapus", key=f"del_arsip_keu_{idx}", use_container_width=True):
                                try:
                                    if path_file_lokal and os.path.exists(path_file_lokal):
                                        os.remove(path_file_lokal)
                                    arsip_records = [ar for i, ar in enumerate(arsip_records) if i != idx]
                                    simpan_arsip_pajak(arsip_records)
                                    st.success("✅ Arsip berhasil dihapus!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Gagal hapus: {e}")
                        else:
                            st.info("Locked")
                    st.markdown("---")
        else:
            st.info("Tidak ada arsip dokumen untuk nomor invoice tersebut.")
    else:
        st.info("Belum ada arsip dokumen pendukung keuangan yang diunggah.")