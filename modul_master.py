import streamlit as st
import pandas as pd

def tampilkan_database_tersimpan():
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📂 Daftar Database Identifikasi Tersimpan (Folder Aman)</h3>
        </div>
    """, unsafe_allow_html=True)

    # Memuat data database induk dari folder aman
    try:
        db_data = muat_data_invoice()
    except:
        db_data = []

    if not db_data:
        st.info("ℹ️ Belum ada data tersimpan di dalam database.")
        return

    # Konversi ke DataFrame Pandas untuk ditampilkan ke layar
    df = pd.DataFrame(db_data)

    # Menampilkan tabel data yang tersimpan
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🗑️ Pengelolaan Data: Hapus Baris yang Salah / Duplikat")

    # Membuat daftar opsi pilihan baris berdasarkan Proforma Invoice No. atau Index
    pilihan_hapus = []
    for idx, item in enumerate(db_data):
        pi_val = str(item.get('Proforma Invoice No.') or item.get('PI No.') or 'Tanpa Nomor PI')
        kontrak_val = str(item.get('Nomor Kontrak') or 'Tanpa Kontrak')
        pilihan_hapus.append(f"Index {idx} | PI: {pi_val} | Kontrak: {kontrak_val}")

    col_h1, col_h2 = st.columns([2, 1])
    with col_h1:
        target_hapus_idx = st.selectbox(
            "Pilih Baris Data yang Ingin Dihapus Secara Permanen:",
            range(len(pilihan_hapus)),
            format_func=lambda x: pilihan_hapus[x],
            key="select_row_to_delete"
        )
    with col_h2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("❌ Hapus Baris Terpilih", use_container_width=True, type="primary"):
            try:
                # Mengambil dan membuang baris yang dipilih dari list database
                deleted_item = db_data.pop(target_hapus_idx)
                
                # Menyimpan kembali database yang telah diperbarui ke penyimpanan sistem (folder aman)
                simpan_data_invoice(db_data)
                
                pi_terhapus = deleted_item.get('Proforma Invoice No.') or deleted_item.get('PI No.') or 'Baris Kosong'
                st.success(f"✅ Berhasil menghapus data (PI: {pi_terhapus}) secara permanen!")
                
                # Memuat ulang halaman agar tabel langsung memperbarui tampilannya
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Terjadi kesalahan saat menghapus data: {e}")