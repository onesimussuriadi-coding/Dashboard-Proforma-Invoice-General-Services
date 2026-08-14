import streamlit as st
import pandas as pd

# Konfigurasi Halaman Dashboard dengan Layout Wide
st.set_page_config(page_title="Dashboard Proforma Invoice & Kontrak", layout="wide")

st.title("📊 Dashboard Performa Invoice & Kontrak")
st.markdown("---")

# Inisialisasi Session State
if "db_tersimpan" not in st.session_state:
    st.session_state["db_tersimpan"] = []
if "edit_index" not in st.session_state:
    st.session_state["edit_index"] = None  # Untuk menandai data mana yang sedang diedit

# Sidebar untuk Navigasi Menu
menu = st.sidebar.selectbox("Pilih Menu", ["Input Database & Invoice", "Lihat Database Tersimpan", "Master Kontrak"])

if menu == "Master Kontrak":
    st.subheader("📁 Data Master Kontrak (Source of Truth)")
    st.write("Daftar template item pekerjaan yang tersimpan dalam sistem.")
    
    data_master = {
        "Contract No.": ["", "", ""],
        "Tender No": ["", "", ""],
        "Contract Title": [""] * 3,
        "Kode Item": ["001", "002", "003"],
        "Deskripsi": ["", "", ""],
        "Satuan": ["", "", ""],
        "Harga Satuan (IDR)": [0, 0, 0]
    }
    df_master = pd.DataFrame(data_master)
    st.dataframe(df_master, use_container_width=True)

elif menu == "Input Database & Invoice":
    st.subheader("📝 Input & Edit Database Identifikasi")
    
    # --- FITUR PANGGIL ULANG ---
    st.markdown("#### 🔍 Panggil Ulang Data Tersimpan (Untuk Diedit/Koreksi)")
    if len(st.session_state["db_tersimpan"]) > 0:
        opsi_panggil = ["-- Formulir Kosong (Buat Data Baru) --"]
        for i, data in enumerate(st.session_state["db_tersimpan"]):
            opsi_panggil.append(f"Data {i+1} | PI: {data.get('Proforma Invoice No.', '-')} | Kontrak: {data.get('Contract No.', '-')}")
        
        # Pilihan Data & Tombol Panggil
        col_pilih, col_btn_panggil = st.columns([3, 1])
        with col_pilih:
            pilihan_edit = st.selectbox("Pilih data yang ingin diedit atau dikoreksi:", opsi_panggil, label_visibility="collapsed")
        with col_btn_panggil:
            if st.button("🔄 Panggil Ulang Data"):
                if pilihan_edit == "-- Formulir Kosong (Buat Data Baru) --":
                    st.session_state["edit_index"] = None
                else:
                    # Mengambil index asli dari teks pilihan
                    idx_str = pilihan_edit.split(" ")[1] # Mendapatkan angka "1", "2", dst.
                    st.session_state["edit_index"] = int(idx_str) - 1
                st.rerun() # Refresh halaman agar form terisi data yang dipanggil
    else:
        st.info("Belum ada data yang tersimpan. Silakan simpan data pertama Anda di bawah.")

    # Menyiapkan data default untuk form jika dalam mode "Edit"
    def_data = {}
    if st.session_state["edit_index"] is not None and st.session_state["edit_index"] < len(st.session_state["db_tersimpan"]):
        def_data = st.session_state["db_tersimpan"][st.session_state["edit_index"]]
        st.warning(f"⚠️ **MODE EDIT AKTIF:** Anda sedang mengoreksi Data ke-{st.session_state['edit_index'] + 1}. Jika sudah selesai diedit, pastikan klik tombol **'Simpan Kembali (Update)'** di paling bawah.")
    
    def get_val(key):
        return def_data.get(key, "")

    st.markdown("---")

    # Membuat Form Input Interaktif
    with st.form("form_input_database"):
        
        # Header Tabel
        col_no, col_item, col_colon, col_input = st.columns([0.5, 3, 0.2, 8.5])
        with col_no: st.markdown("**No**")
        with col_item: st.markdown("**Item**")
        with col_colon: st.markdown("**:**")
        with col_input: st.markdown("**Input (Kolom Luas / Text Area & Text Input)**")
        st.markdown("---")

        def baris_input_teks(no, label, val="", is_area=False):
            c1, c2, c3, c4 = st.columns([0.5, 3, 0.2, 8.5])
            with c1: st.write(str(no))
            with c2: st.write(label)
            with c3: st.write(":")
            with c4:
                if is_area:
                    return st.text_area(f"input_{no}", value=val, label_visibility="collapsed", height=70)
                else:
                    return st.text_input(f"input_{no}", value=val, label_visibility="collapsed")

        # 26 Item Form (Sekarang akan terisi otomatis jika tombol 'Panggil Ulang' diklik)
        val_1 = baris_input_teks(1, "Contract No.", val=get_val("Contract No."))
        val_2 = baris_input_teks(2, "Tender No", val=get_val("Tender No"))
        val_3 = baris_input_teks(3, "Contract Title", val=get_val("Contract Title"), is_area=True)
        val_4 = baris_input_teks(4, "Tanggal Contract", val=get_val("Tanggal Contract"))
        val_5 = baris_input_teks(5, "Contract Period", val=get_val("Contract Period"))
        val_6 = baris_input_teks(6, "Proforma Invoice No.", val=get_val("Proforma Invoice No."))
        val_7 = baris_input_teks(7, "Tanggal Performa Invoice", val=get_val("Tanggal PI"))
        val_8 = baris_input_teks(8, "No PO", val=get_val("No PO"))
        val_9 = baris_input_teks(9, "Tanggal PO", val=get_val("Tanggal PO"))
        val_10 = baris_input_teks(10, "Keterangan PO", val=get_val("Keterangan PO"), is_area=True)
        val_11 = baris_input_teks(11, "Pihak Pertama", val=get_val("Pihak Pertama"))
        val_12 = baris_input_teks(12, "Alamat Pihak Pertama", val=get_val("Alamat Pihak Pertama"), is_area=True)
        val_13 = baris_input_teks(13, "Diwakili Oleh", val=get_val("Diwakili Oleh (P1)"))
        val_14 = baris_input_teks(14, "Selaku", val=get_val("Selaku (P1)"))
        val_15 = baris_input_teks(15, "Pihak Kedua", val=get_val("Pihak Kedua"))
        val_16 = baris_input_teks(16, "Alamat Pihak Kedua", val=get_val("Alamat Pihak Kedua"), is_area=True)
        val_17 = baris_input_teks(17, "Diwakili Oleh", val=get_val("Diwakili Oleh (P2)"))
        val_18 = baris_input_teks(18, "Selaku", val=get_val("Selaku (P2)"))
        val_19 = baris_input_teks(19, "Period", val=get_val("Period"))
        val_20 = baris_input_teks(20, "Certificate No. (Cover WCC No.)", val=get_val("Certificate No."))
        val_21 = baris_input_teks(21, "WCC Date", val=get_val("WCC Date"))
        val_22 = baris_input_teks(22, "WO No.", val=get_val("WO No."))
        val_23 = baris_input_teks(23, "WO Title", val=get_val("WO Title"), is_area=True)
        val_24 = baris_input_teks(24, "CTR No.", val=get_val("CTR No."))
        val_25 = baris_input_teks(25, "Prepared by Name", val=get_val("Prepared by Name"))
        val_26 = baris_input_teks(26, "Prepared by Title", val=get_val("Prepared by Title"))

        st.markdown("---")
        
        # Dua Tombol Aksi di Bawah Form
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submit_baru = st.form_submit_button("💾 Simpan Sebagai Data Baru")
        with col_btn2:
            submit_update = st.form_submit_button("📝 Simpan Kembali (Update Data Terpilih)")
        
        # Logika Penyimpanan
        if submit_baru or submit_update:
            data_terinput = {
                "Contract No.": val_1, "Tender No": val_2, "Contract Title": val_3, 
                "Tanggal Contract": val_4, "Contract Period": val_5, 
                "Proforma Invoice No.": val_6, "Tanggal PI": val_7, 
                "No PO": val_8, "Tanggal PO": val_9, "Keterangan PO": val_10,
                "Pihak Pertama": val_11, "Alamat Pihak Pertama": val_12, 
                "Diwakili Oleh (P1)": val_13, "Selaku (P1)": val_14,
                "Pihak Kedua": val_15, "Alamat Pihak Kedua": val_16, 
                "Diwakili Oleh (P2)": val_17, "Selaku (P2)": val_18,
                "Period": val_19, "Certificate No.": val_20, "WCC Date": val_21, 
                "WO No.": val_22, "WO Title": val_23, "CTR No.": val_24, 
                "Prepared by Name": val_25, "Prepared by Title": val_26
            }

            if submit_update:
                if st.session_state["edit_index"] is not None:
                    # Menimpa (Update) data yang lama dengan data baru yang sudah diedit
                    st.session_state["db_tersimpan"][st.session_state["edit_index"]] = data_terinput
                    st.success("Perubahan data berhasil disimpan kembali (diupdate)!")
                else:
                    st.error("Gagal mengupdate: Anda belum memanggil data apapun! Silakan klik 'Simpan Sebagai Data Baru'.")
            elif submit_baru:
                # Menambah data sebagai daftar baru
                st.session_state["db_tersimpan"].append(data_terinput)
                st.success("Data berhasil ditambahkan sebagai entri baru!")
                st.session_state["edit_index"] = None # Matikan mode edit setelah simpan baru

elif menu == "Lihat Database Tersimpan":
    st.subheader("📂 Daftar Database Identifikasi Tersimpan")
    st.write("Semua data yang berhasil disimpan atau diupdate akan muncul di sini.")
    
    if len(st.session_state["db_tersimpan"]) > 0:
        df_saved = pd.DataFrame(st.session_state["db_tersimpan"])
        st.dataframe(df_saved, use_container_width=True)
    else:
        st.info("Belum ada data yang tersimpan. Silakan isi form terlebih dahulu.")