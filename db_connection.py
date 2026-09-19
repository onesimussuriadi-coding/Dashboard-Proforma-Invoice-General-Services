import streamlit as st
import pandas as pd
import os
import json

# --- PENYESUAIAN DIREKTORI KE GOOGLE DRIVE LOKAL ---
# Ganti path di bawah ini sesuai dengan direktori folder "database_penyimpanan_aman" 
# yang ada di dalam folder Google Drive di komputer Anda (contoh menggunakan path Windows/Mac standar).
# Jika folder proyek berada di Google Drive Desktop (Drive G atau C), arahkan langsung ke sana:
DIR_DATABASE = "database_penyimpanan_aman"  # Atau ubah misal: r"G:/My Drive/Dashboard Proforma Invoice/database_penyimpanan_aman"

if not os.path.exists(DIR_DATABASE):
    try:
        os.makedirs(DIR_DATABASE)
    except Exception:
        pass

def muat_data_from_db(nama_tabel):
    """
    Memuat data secara instan dan aman dari file Excel lokal yang 
    tersinkronisasi langsung dengan Google Drive.
    """
    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    if os.path.exists(file_path):
        try:
            df_local = pd.read_excel(file_path, engine='openpyxl')
            if df_local is not None and not df_local.empty:
                return df_local.to_dict(orient="records")
        except Exception:
            pass
    return []

def simpan_data_to_db(nama_tabel, data_list):
    """
    [REAL-TIME & PERMANEN KE GOOGLE DRIVE] Menyimpan data secara mutlak ke file Excel 
    di folder penyimpanan aman yang tersinkronisasi ke Google Drive. Menggabungkan data lama 
    dan memperbarui baris berdasarkan Proforma Invoice secara akurat.
    """
    if data_list is None or len(data_list) == 0:
        st.error("❌ Data kosong, gagal menyimpan.")
        return False

    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    
    try:
        df_new = pd.DataFrame(data_list)
        if df_new.empty:
            return False

        # Jika file arsip lama ada, gabungkan & perbarui dengan data baru
        if os.path.exists(file_path):
            try:
                df_old = pd.read_excel(file_path, engine='openpyxl')
                if not df_old.empty:
                    key_col = df_old.columns[0]
                    if key_col in df_new.columns:
                        df_old[key_col] = df_old[key_col].astype(str).str.strip()
                        df_new[key_col] = df_new[key_col].astype(str).str.strip()
                        
                        new_dict = {str(row[key_col]): row for _, row in df_new.iterrows()}
                        updated_rows = []
                        existing_keys = set()
                        
                        # Pertahankan data lama, timpa jika ada pembaruan (update)
                        for _, row in df_old.iterrows():
                            k = str(row[key_col])
                            if k in new_dict:
                                updated_rows.append(new_dict[k])
                                existing_keys.add(k)
                            else:
                                updated_rows.append(row)
                                
                        # Tambahkan data baru yang belum ada
                        for _, row in df_new.iterrows():
                            k = str(row[key_col])
                            if k not in existing_keys:
                                updated_rows.append(row)
                                
                        df_new = pd.DataFrame(updated_rows)
            except Exception as e:
                st.warning(f"Catatan penyesuaian: {e}")

        # Simpan secara permanen ke file Excel di folder Google Drive
        df_new.to_excel(file_path, index=False, engine='openpyxl')
        return True
    except Exception as e:
        st.error(f"❌ Gagal menyimpan data ke Google Drive: {e}")
        return False

def render_download_button_excel(nama_tabel="database_proforma_invoice"):
    """
    Menampilkan tombol unduh file Excel langsung dari folder penyimpanan aman 
    yang tersinkronisasi dengan Google Drive.
    """
    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    
    st.markdown("---")
    st.markdown("### 📥 Unduh Arsip File Excel (Google Drive Terkini)")
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                excel_bytes = f.read()
            st.download_button(
                label=f"📥 Download File {nama_tabel}.xlsx",
                data=excel_bytes,
                file_name=f"{nama_tabel}_terbaru.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"download_btn_gdrive_{nama_tabel}"
            )
        except Exception as e:
            st.error(f"❌ Gagal membaca file: {e}")
    else:
        st.warning(f"⚠️ File data untuk tabel '{nama_tabel}' belum tersedia.")

def render_pilihan_panggil_ulang(nama_tabel="database_proforma_invoice"):
    """
    Merender widget interaktif untuk fitur panggil ulang berdasarkan 
    Nomor Kontrak dan Nomor Proforma Invoice di antarmuka aplikasi.
    """
    data = muat_data_from_db(nama_tabel)
    if not data:
        st.info("📌 Belum ada data database tersimpan. Silakan impor atau masukkan data terlebih dahulu.")
        return None

    st.markdown("### 🔍 Panggil Ulang Berdasarkan Nomor Kontrak & Nomor PI")
    
    list_kontrak = sorted(list(set([str(item.get("Nomor Kontrak", item.get(1, ""))) for item in data if item.get("Nomor Kontrak", item.get(1, "")) ])))
    
    selected_kontrak = st.selectbox("Pilih Nomor Kontrak:", ["-- Pilih Nomor Kontrak --"] + list_kontrak, key="select_panggil_kontrak")
    
    selected_record = None
    if selected_kontrak != "-- Pilih Nomor Kontrak --":
        filtered_data = [item for item in data if str(item.get("Nomor Kontrak", item.get(1, ""))) == selected_kontrak]
        list_pi = [str(item.get("Proforma Invoice No.", item.get(0, ""))) for item in filtered_data]
        
        selected_pi = st.selectbox("Pilih Proforma Invoice (PI) No.:", ["-- Pilih Nomor PI --"] + list_pi, key="select_panggil_pi")
        
        if selected_pi != "-- Pilih Nomor PI --":
            match_list = [item for item in filtered_data if str(item.get("Proforma Invoice No.", item.get(0, ""))) == selected_pi]
            if match_list:
                selected_record = match_list[0]
                st.success(f"✅ Data berhasil dipanggil ulang untuk Kontrak: {selected_kontrak} | PI: {selected_pi}")

    return selected_record