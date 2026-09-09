import streamlit as st
import os
import pandas as pd
import glob
from datetime import datetime
import base64

def tampilkan_arsip_pendukung():
    st.markdown("""
        <div class="dashboard-card" style="padding: 12px 20px; margin-bottom: 10px;">
            <h3 style="margin:0; color:#065f46; font-size:16px;">📁 Arsip Dokumen Penunjang & Customer (Kamar Berdasarkan Kontrak)</h3>
            <p style="margin:2px 0 0 0; font-size:11px; color:#4b5563;">Modul terpusat untuk mengunggah, mengelola, dan menelusuri dokumen penagihan berdasarkan Nomor Kontrak dan Kamar Kategori.</p>
        </div>
    """, unsafe_allow_html=True)

    DIR_ARJEP = os.path.join("database_penyimpanan_aman", "arsip_dokumen_customer")
    if not os.path.exists(DIR_ARJEP):
        os.makedirs(DIR_ARJEP)

    # Kamar dokumen (Kamar Arsip Lama / Unsorted dihapus agar file lama tidak menumpuk/mengganggu)
    kamar_dokumen = {
        "PO (Purchase Order) Customer": "01_Purchase_Order",
        "Proforma Invoice (PI)": "02_Proforma_Invoice",
        "CTR": "03_CTR",
        "WO (Work Order)": "04_WO",
        "WAN (Work Authorization Notice)": "05_WAN_SA",
        "Timesheet / Daily Report": "06_Timesheet",
        "Surat Jalan / Manifest": "07_Surat_Jalan",
        "Berita Acara Lapangan / Checklist": "08_Berita_Acara",
        "Korespondensi / Lainnya": "09_Korespondensi"
    }

    for nama_kamar, folder_name in kamar_dokumen.items():
        kamar_path = os.path.join(DIR_ARJEP, folder_name)
        if not os.path.exists(kamar_path):
            os.makedirs(kamar_path)

    meta_file_path = os.path.join(DIR_ARJEP, "metadata_arsip.xlsx")
    columns_meta = ["ID", "Tanggal Upload", "Nomor Kontrak", "Nomor PI / PO / Ref", "Kategori Dokumen", "Nama File Asli", "Path File", "Keterangan"]
    
    if os.path.exists(meta_file_path):
        try:
            df_arsip = pd.read_excel(meta_file_path)
            for col in columns_meta:
                if col not in df_arsip.columns:
                    df_arsip[col] = "-"
        except:
            df_arsip = pd.DataFrame(columns=columns_meta)
    else:
        df_arsip = pd.DataFrame(columns=columns_meta)

    # Bersihkan metadata dari data yang tidak memiliki nomor kontrak atau referensi yang valid (nan / -)
    if not df_arsip.empty:
        df_arsip = df_arsip[
            (df_arsip['Nomor Kontrak'].astype(str).str.strip().str.lower() != 'nan') &
            (df_arsip['Nomor Kontrak'].astype(str).str.strip() != '-') &
            (df_arsip['Nomor Kontrak'].astype(str).str.strip() != '') &
            (df_arsip['Nomor PI / PO / Ref'].astype(str).str.strip().str.lower() != 'nan') &
            (df_arsip['Nomor PI / PO / Ref'].astype(str).str.strip() != '-') &
            (df_arsip['Nomor PI / PO / Ref'].astype(str).str.strip() != '')
        ]
        df_arsip.to_excel(meta_file_path, index=False)

    kontrak_koleksi = []
    if not df_arsip.empty and 'Nomor Kontrak' in df_arsip.columns:
        kontrak_koleksi.extend(df_arsip['Nomor Kontrak'].dropna().astype(str).tolist())

    list_kontrak_unik = sorted(list(set([str(k).strip() for k in kontrak_koleksi if str(k).strip() and str(k).strip().lower() not in ["nan", "-", ""]])))
    opsi_dropdown_kontrak = ["-- Pilih atau Ketik Nomor Kontrak Baru --"] + list_kontrak_unik + ["➕ [Ketik Nomor Kontrak Manual Baru...]"]

    tab_upload, tab_list = st.tabs(["📤 Upload Dokumen Baru ke Kamar", "🗂️ Daftar & Telusuri Berdasarkan Kamar"])

    with tab_upload:
        st.markdown("#### Form Upload Dokumen dengan Identifikasi Kontrak")
        with st.form("form_upload_arsip_kamar", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                pilihan_kontrak_cb = st.selectbox("Pilih Nomor Kontrak Rujukan *", opsi_dropdown_kontrak)
                input_kontrak_manual = st.text_input("✍️ Masukkan Nomor Kontrak Baru (Jika memilih opsi '[Ketik Manual]' di atas):", placeholder="Contoh: 7201250141")
                
                pi_po_ref = st.text_input("Nomor Referensi (PI / PO / CTR / WO) *", placeholder="Contoh: PI-010, PO-4500011581, CTR-05")
                
                kategori_dok = st.selectbox("Pilih Kamar / Kategori Dokumen", list(kamar_dokumen.keys()))
            with col2:
                keterangan_dok = st.text_area("Keterangan Tambahan / Detail Dokumen", placeholder="Catatan singkat mengenai dokumen ini...")
                uploaded_file = st.file_uploader("Pilih Berkas (PDF, Gambar, Word, Excel, ZIP)", type=["pdf", "png", "jpg", "jpeg", "docx", "xlsx", "zip"])

            submit_upload = st.form_submit_button("💾 Simpan & Masukkan ke Kamar", use_container_width=True)

            if submit_upload:
                if pilihan_kontrak_cb == "➕ [Ketik Nomor Kontrak Manual Baru...]":
                    final_nomor_kontrak = input_kontrak_manual.strip()
                elif pilihan_kontrak_cb != "-- Pilih atau Ketik Nomor Kontrak Baru --":
                    final_nomor_kontrak = pilihan_kontrak_cb
                else:
                    final_nomor_kontrak = ""

                if uploaded_file is not None and final_nomor_kontrak and pi_po_ref.strip():
                    try:
                        target_folder_name = kamar_dokumen[kategori_dok]
                        target_dir = os.path.join(DIR_ARJEP, target_folder_name)
                        
                        original_filename = uploaded_file.name.replace(' ', '_')
                        target_path = os.path.join(target_dir, original_filename)
                        
                        counter = 1
                        base_name, ext = os.path.splitext(original_filename)
                        while os.path.exists(target_path):
                            target_path = os.path.join(target_dir, f"{base_name}_{counter}{ext}")
                            counter += 1

                        with open(target_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        final_saved_filename = os.path.basename(target_path)

                        new_id = len(df_arsip) + 1 if not df_arsip.empty else 1
                        new_row = {
                            "ID": new_id,
                            "Tanggal Upload": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Nomor Kontrak": final_nomor_kontrak,
                            "Nomor PI / PO / Ref": pi_po_ref.strip(),
                            "Kategori Dokumen": kategori_dok,
                            "Nama File Asli": final_saved_filename,
                            "Path File": target_path,
                            "Keterangan": keterangan_dok if keterangan_dok else "-"
                        }

                        df_arsip = pd.concat([df_arsip, pd.DataFrame([new_row])], ignore_index=True)
                        df_arsip.to_excel(meta_file_path, index=False)

                        st.success(f"✅ Berkas [{final_saved_filename}] berhasil diunggah ke kamar **[{kategori_dok}]** dengan Kontrak **[{final_nomor_kontrak}]**!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal mengunggah file: {e}")
                else:
                    st.warning("⚠️ Pastikan Nomor Kontrak, Nomor Referensi, dan Berkas File telah diisi dengan benar!")

    with tab_list:
        st.markdown("#### Penelusuran Berdasarkan Kamar Dokumen & Kontrak")
        
        if list_kontrak_unik:
            selected_global_kontrak = st.selectbox(
                "📌 Pilih Nomor Kontrak untuk Menyaring Dokumen:",
                ["-- Semua Nomor Kontrak --"] + list_kontrak_unik,
                key="global_filter_nomor_kontrak"
            )
        else:
            selected_global_kontrak = "-- Semua Nomor Kontrak --"

        st.markdown("---")

        tab_kamar_list = st.tabs(list(kamar_dokumen.keys()))

        for idx, (nama_kamar, folder_name) in enumerate(kamar_dokumen.items()):
            with tab_kamar_list[idx]:
                st.markdown(f"##### 📁 Kamar: {nama_kamar}")
                
                kamar_path = os.path.join(DIR_ARJEP, folder_name)
                files_in_kamar = glob.glob(os.path.join(kamar_path, "*.*"))

                if not files_in_kamar:
                    st.info(f"ℹ️ Belum ada dokumen di kamar {nama_kamar}.")
                else:
                    ada_data_ditampilkan = False
                    for file_path in sorted(files_in_kamar, key=os.path.getmtime, reverse=True):
                        file_name = os.path.basename(file_path)
                        
                        matched_meta = df_arsip[df_arsip['Path File'].astype(str).str.endswith(file_name)] if not df_arsip.empty else pd.DataFrame()
                        
                        # HANYA TAMPILKAN JIKA DATA METADATA LENGKAP (ADA NOMOR KONTRAK & REFERENSI VALID)
                        if matched_meta.empty:
                            continue
                        
                        row_meta = matched_meta.iloc[0]
                        kontrak_val = str(row_meta.get('Nomor Kontrak', '-'))
                        pi_po_val = str(row_meta.get('Nomor PI / PO / Ref', '-'))
                        ket_val = str(row_meta.get('Keterangan', '-'))

                        if not kontrak_val or kontrak_val in ["-", "nan", "NaN"] or not pi_po_val or pi_po_val in ["-", "nan", "NaN"]:
                            continue

                        if selected_global_kontrak != "-- Semua Nomor Kontrak --" and kontrak_val != selected_global_kontrak:
                            continue

                        ada_data_ditampilkan = True
                        
                        clean_ket = f" — {ket_val}" if ket_val and ket_val != "-" else ""
                        display_label = f"📄 Kontrak [{kontrak_val}] — Ref [{pi_po_val}]{clean_ket}"
                        
                        with st.expander(display_label):
                            col_info, col_act = st.columns([3, 1])
                            with col_info:
                                st.markdown(f"""
<div style="line-height: 1.6; font-size: 13px; margin-bottom: -10px;">
• <b>Nomor Kontrak:</b> {kontrak_val}<br>
• <b>Nomor Referensi (PI / PO / CTR / WO):</b> {pi_po_val}<br>
• <b>Keterangan:</b> {ket_val}
</div>
""", unsafe_allow_html=True)
                            with col_act:
                                if os.path.exists(file_path):
                                    with open(file_path, "rb") as f:
                                        file_bytes = f.read()
                                    
                                    st.download_button(
                                        label="📥 Download",
                                        data=file_bytes,
                                        file_name=file_name,
                                        key=f"dl_kamar_{folder_name}_{file_name}",
                                        use_container_width=True
                                    )

                                    if st.button("🗑️ Hapus", key=f"del_kamar_{folder_name}_{file_name}", use_container_width=True):
                                        try:
                                            os.remove(file_path)
                                        except:
                                            pass
                                        
                                        if not df_arsip.empty and 'Path File' in df_arsip.columns:
                                            df_arsip = df_arsip[~df_arsip['Path File'].astype(str).str.endswith(file_name)]
                                            df_arsip.to_excel(meta_file_path, index=False)
                                        
                                        st.warning(f"Arsip {file_name} berhasil dihapus.")
                                        st.rerun()
                        st.markdown("<div style='margin: -15px 0;'></div>", unsafe_allow_html=True)
                    
                    if not ada_data_ditampilkan:
                        st.info(f"ℹ️ Tidak ada dokumen valid untuk Nomor Kontrak **[{selected_global_kontrak}]** di kamar {nama_kamar}.")