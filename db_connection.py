import streamlit as st
import pandas as pd
import os
import json
import io

DIR_DATABASE = "database_penyimpanan_aman"
if not os.path.exists(DIR_DATABASE):
    os.makedirs(DIR_DATABASE)
LOCAL_BACKUP_FILE = os.path.join(DIR_DATABASE, "backup_database_invoice.json")

def get_mysql_connection():
    """Dinonaktifkan sementara agar aplikasi berjalan instan tanpa kendala jaringan luar."""
    return None

def muat_data_from_db(nama_tabel="database_proforma_invoice"):
    """
    Memuat data dari file lokal dengan pemetaan ganda (indeks angka & nama kolom teks)
    agar kompatibel penuh dengan seluruh pemanggilan di app.py tanpa ada yang hilang.
    """
    local_data = []
    if os.path.exists(LOCAL_BACKUP_FILE):
        try:
            with open(LOCAL_BACKUP_FILE, "r", encoding="utf-8") as f:
                local_data = json.load(f)
        except Exception:
            local_data = []

    # Daftar nama kolom teks sesuai header standar tabel
    mapping_keys = [
        "Proforma Invoice No.", "Nomor Kontrak", "Nomor Tender", "Lingkup Pekerjaan",
        "Tanggal Kontrak", "Jangka Waktu Kontrak", "Tanggal Performa Invoice", "Judul Kontrak",
        "Nomor Purchase Order", "Tanggal Purchase Order", "Pihak Pertama", "Alamat Pihak Pertama",
        "Diwakili Oleh", "Selaku", "Pihak Kedua", "Alamat Pihak Kedua", "Diwakili Oleh (P2)",
        "Selaku (P2)", "Periode Pekerjaan", "Nomor WCC", "Tanggal WCC", "Nomor WO",
        "Keterangan WO", "Nomor CTR", "Progress Pekerjaan", "Prepared by Name",
        "Prepared by Title", "Approved by 1", "Approved by Title 1", "Approved by 2", "Approved by Title 2"
    ]

    # Lakukan normalisasi agar setiap baris memiliki kunci ganda (indeks & nama teks)
    formatted_data = []
    for item in local_data:
        new_item = {}
        if isinstance(item, dict):
            for i, key_name in enumerate(mapping_keys):
                # Ambil nilai dari berbagai kemungkinan format key yang lama
                val = item.get(i, item.get(str(i), item.get(key_name, "")))
                # Simpan dalam semua format agar app.py pasti menemukannya
                new_item[i] = val
                new_item[str(i)] = val
                new_item[key_name] = val
        formatted_data.append(new_item)

    return formatted_data

def simpan_data_to_db(nama_tabel, data_list):
    """
    Menyimpan data secara permanen dan aman ke penyimpanan lokal aplikasi.
    """
    if data_list is None:
        st.error("❌ Data kosong, gagal menyimpan.")
        return False

    try:
        with open(LOCAL_BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(data_list, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"❌ Gagal menyimpan data: {e}")
        return False

def render_download_button_excel(nama_tabel="database_proforma_invoice"):
    data = muat_data_from_db(nama_tabel)
    if data:
        df_export = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, header=False)
        excel_bytes = output.getvalue()

        st.markdown("---")
        st.markdown("### 📥 Unduh Data Tabel Terbaru")
        st.download_button(
            label=f"📥 Download {nama_tabel}.xlsx",
            data=excel_bytes,
            file_name=f"{nama_tabel}_terbaru.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"download_btn_local_{nama_tabel}"
        )