import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
import io

def get_mysql_connection():
    """
    Membuat koneksi langsung ke server Cloud MySQL menggunakan 
    konfigurasi secrets Streamlit yang andal dan aman.
    """
    try:
        db_conf = st.secrets["database"]
        conn = mysql.connector.connect(
            host=db_conf["host"],
            user=db_conf["user"],
            password=db_conf["password"],
            database=db_conf["database"],
            port=db_conf.get("port", 3306)
        )
        return conn
    except Exception as e:
        return None

def muat_data_from_db(nama_tabel):
    """
    Memuat seluruh data secara real-time langsung dari tabel MySQL pusat
    dengan struktur baris kamus standar yang kompatibel dengan seluruh modul.
    """
    conn = get_mysql_connection()
    if conn is not None:
        try:
            query = f"SELECT * FROM `{nama_tabel}`"
            df_sql = pd.read_sql(query, conn)
            conn.close()
            if df_sql is not None and not df_sql.empty:
                records = []
                for _, row in df_sql.iterrows():
                    rec_dict = {}
                    for i, col_name in enumerate(df_sql.columns):
                        # Menyimpan dengan kunci indeks angka dan juga nama kolom asli
                        val = str(row[col_name]) if pd.notnull(row[col_name]) and str(row[col_name]).lower() != "nan" else ""
                        rec_dict[i] = val
                        rec_dict[str(i)] = val
                        rec_dict[col_name] = val
                    records.append(rec_dict)
                return records
        except Error as e:
            if conn and conn.is_connected():
                conn.close()
    return []

def simpan_data_to_db(nama_tabel, data_list):
    """
    Menyimpan atau memperbarui data secara permanen ke tabel MySQL pusat
    menggunakan pemetaan `COL 1` hingga `COL 31`.
    """
    if data_list is None or len(data_list) == 0:
        st.error("❌ Data kosong, gagal menyimpan ke database.")
        return False

    conn = get_mysql_connection()
    if conn is None:
        st.error("❌ Gagal terhubung ke server database MySQL.")
        return False

    try:
        cursor = conn.cursor()
        
        for item in data_list:
            val_map = {}
            for idx in range(1, 32):
                val = ""
                if isinstance(item, dict):
                    val = item.get(idx - 1, item.get(str(idx - 1), ""))
                    if not val:
                        mapping_keys = [
                            "Proforma Invoice No.", "Nomor Kontrak", "Nomor Tender", "Lingkup Pekerjaan",
                            "Tanggal Kontrak", "Jangka Waktu Kontrak", "Tanggal Performa Invoice", "Judul Kontrak",
                            "Nomor Purchase Order", "Tanggal Purchase Order", "Pihak Pertama", "Alamat Pihak Pertama",
                            "Diwakili Oleh", "Selaku", "Pihak Kedua", "Alamat Pihak Kedua", "Diwakili Oleh (P2)",
                            "Selaku (P2)", "Periode Pekerjaan", "Nomor WCC", "Tanggal WCC", "Nomor WO",
                            "Keterangan WO", "Nomor CTR", "Progress Pekerjaan", "Prepared by Name",
                            "Prepared by Title", "Approved by 1", "Approved by Title 1", "Approved by 2", "Approved by Title 2"
                        ]
                        if (idx - 1) < len(mapping_keys):
                            val = item.get(mapping_keys[idx - 1], "")
                
                val_map[f"COL {idx}"] = str(val) if val is not None and str(val).strip().lower() != "nan" else ""

            cols = [f"`COL {i}`" for i in range(1, 32)]
            placeholders = ", ".join(["%s"] * 31)
            columns_str = ", ".join(cols)
            vals = tuple(val_map[f"COL {i}"] for i in range(1, 32))

            updates = ", ".join([f"`COL {i}` = VALUES(`COL {i}`)" for i in range(2, 32)])
            
            query = f"""
                INSERT INTO `{nama_tabel}` ({columns_str}) 
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE {updates}
            """
            
            cursor.execute(query, vals)

        conn.commit()
        cursor.close()
        conn.close()
        return True

    except Error as e:
        st.error(f"❌ Gagal menyimpan data ke MySQL: {e}")
        if conn.is_connected():
            conn.close()
        return False

def render_pilihan_panggil_ulang(nama_tabel="database_proforma_invoice"):
    """
    Merender widget interaktif untuk fitur panggil ulang berdasarkan 
    Nomor Kontrak dan Nomor Proforma Invoice di antarmuka aplikasi.
    """
    data = muat_data_from_db(nama_tabel)
    if not data:
        st.info("📌 Belum ada data database yang tersimpan atau gagal terhubung ke server.")
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

def render_download_button_excel(nama_tabel="database_proforma_invoice"):
    data = muat_data_from_db(nama_tabel)
    if data:
        df_export = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, header=False)
        excel_bytes = output.getvalue()

        st.markdown("---")
        st.markdown("### 📥 Unduh Data Tabel MySQL Terbaru")
        st.download_button(
            label=f"📥 Download {nama_tabel}.xlsx",
            data=excel_bytes,
            file_name=f"{nama_tabel}_mysql_terbaru.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"download_btn_mysql_{nama_tabel}"
        )