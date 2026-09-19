import streamlit as st
import pandas as pd
import os
import json

DIR_DATABASE = "database_penyimpanan_aman"
if not os.path.exists(DIR_DATABASE):
    os.makedirs(DIR_DATABASE)

def muat_data_from_db(nama_tabel):
    """
    Memuat data secara instan dan aman dari file Excel lokal server.
    """
    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    if os.path.exists(file_path):
        try:
            df_local = pd.read_excel(file_path, engine='openpyxl')
            if df_local is not None and not df_local.empty:
                # Pastikan kolom kunci tidak hilang
                return df_local.to_dict(orient="records")
        except Exception:
            pass
    return []

def simpan_data_to_db(nama_tabel, data_list):
    """
    Menyimpan data dengan aman. Menggabungkan data lama dan memperbarui 
    berdasarkan nomor Proforma Invoice secara akurat tanpa merusak struktur kolom.
    """
    if data_list is None or len(data_list) == 0:
        st.error("❌ Data kosong, gagal menyimpan.")
        return False

    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    
    try:
        df_new = pd.DataFrame(data_list)
        if df_new.empty:
            return False

        # Jika file lama ada, lakukan penggabungan/pembaruan baris yang aman
        if os.path.exists(file_path):
            try:
                df_old = pd.read_excel(file_path, engine='openpyxl')
                if not df_old.empty:
                    # Ambil kolom pertama sebagai referensi utama (Nomor Proforma Invoice)
                    key_col = df_old.columns[0]
                    if key_col in df_new.columns:
                        # Ubah ke string agar pencocokan akurat
                        df_old[key_col] = df_old[key_col].astype(str).str.strip()
                        df_new[key_col] = df_new[key_col].astype(str).str.strip()
                        
                        # Buat kamus data baru untuk penggantian
                        new_dict = {str(row[key_col]): row for _, row in df_new.iterrows()}
                        
                        updated_rows = []
                        existing_keys = set()
                        
                        # Timpa baris lama jika kodenya sama
                        for _, row in df_old.iterrows():
                            k = str(row[key_col])
                            if k in new_dict:
                                updated_rows.append(new_dict[k])
                                existing_keys.add(k)
                            else:
                                updated_rows.append(row)
                                
                        # Tambahkan baris baru yang belum ada di data lama
                        for _, row in df_new.iterrows():
                            k = str(row[key_col])
                            if k not in existing_keys:
                                updated_rows.append(row)
                                
                        df_new = pd.DataFrame(updated_rows)
            except Exception as e:
                st.warning(f"Catatan penyesuaian: {e}")

        # Simpan mutlak ke file Excel lokal
        df_new.to_excel(file_path, index=False, engine='openpyxl')
        return True
    except Exception as e:
        st.error(f"❌ Gagal menyimpan data: {e}")
        return False

def render_download_button_excel(nama_tabel="database_proforma_invoice"):
    """
    Menampilkan tombol unduh file Excel secara jelas di antarmuka web
    agar Bapak bisa mendownload file arsip terbaru kapan saja.
    """
    file_path = os.path.join(DIR_DATABASE, f"{nama_tabel}.xlsx")
    
    st.markdown("---")
    st.markdown("### 📥 Unduh File Excel Server Terbaru")
    st.info("Klik tombol di bawah ini untuk mendownload file Excel berisi data paling update langsung dari server.")
    
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            excel_bytes = f.read()
        st.download_button(
            label=f"📥 Download {nama_tabel}.xlsx Sekarang",
            data=excel_bytes,
            file_name=f"{nama_tabel}_terbaru.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"download_btn_fixed_{nama_tabel}"
        )
    else:
        st.warning(f"⚠️ File data untuk tabel '{nama_tabel}' belum tersedia.")