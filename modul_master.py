import streamlit as st
import pandas as pd
import base64

def tampilkan_master_referensi_tersimpan(master_data_list):
    st.markdown("""
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 15px 20px; border-radius: 8px; margin-bottom: 20px;">
            <h3 style="margin:0; color:#34d399; font-size:18px;">📂 Daftar Master Referensi Harga & Pekerjaan Tersimpan (Dengan Tombol Edit & Hapus per Baris)</h3>
            <p style="margin:4px 0 0 0; font-size: 12px; color: #cbd5e1;">Panel kontrol lengkap: Filter Kontrak, Filter Kategori, Tabel Text-Wrap, serta Tombol Cetak & Save PDF.</p>
        </div>
    """, unsafe_allow_html=True)

    if not master_data_list:
        st.info("ℹ️ Belum ada data master referensi harga yang tersimpan.")
        return

    # Konversi ke DataFrame Pandas
    df_master = pd.DataFrame(master_data_list)

    # Deteksi nama kolom secara dinamis
    kolom_kontrak = next((col for col in ['Nomor Kontrak', 'No Kontrak', 'Kontrak'] if col in df_master.columns), None)
    kolom_kategori = next((col for col in ['Kategori', 'Kategori Pekerjaan', 'Jenis Pekerjaan'] if col in df_master.columns), None)

    # --- PANEL FILTER KONTRAK & KATEGORI ---
    st.markdown("#### 🔍 Filter & Pemilihan Data Master")
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        if kolom_kontrak:
            list_kontrak = ["-- Semua Kontrak --"] + list(df_master[kolom_kontrak].dropna().astype(str).unique())
            selected_kontrak = st.selectbox("📌 Pilih Nomor Kontrak:", list_kontrak, key="filter_kontrak_master_v3")
        else:
            selected_kontrak = "-- Semua Kontrak --"

    with col_f2:
        if kolom_kategori:
            list_kategori = ["-- Semua Kategori --"] + list(df_master[kolom_kategori].dropna().astype(str).unique())
            selected_kategori = st.selectbox("🏷️ Pilih Kategori Pekerjaan:", list_kategori, key="filter_kategori_master_v3")
        else:
            selected_kategori = "-- Semua Kategori --"

    # Terapkan Filter
    df_filtered = df_master.copy()
    if kolom_kontrak and selected_kontrak != "-- Semua Kontrak --":
        df_filtered = df_filtered[df_filtered[kolom_kontrak].astype(str) == selected_kontrak]
    if kolom_kategori and selected_kategori != "-- Semua Kategori --":
        df_filtered = df_filtered[df_filtered[kolom_kategori].astype(str) == selected_kategori]

    st.markdown("---")

    # --- TABEL HTML DENGAN TEXT-WRAP AGAR PROPORSIONAL ---
    th_html = "".join([f"<th style='border: 1px solid #cbd5e1; padding: 8px; background-color: #1e293b; color: white; font-size: 11px; text-align: left;'>{col}</th>" for col in df_filtered.columns])
    
    tr_html = ""
    for _, row in df_filtered.iterrows():
        tr_html += "<tr>"
        for col_name, val in row.items():
            val_str = str(val) if pd.notna(val) else ""
            c_lower = str(col_name).lower()
            
            if 'kategori' in c_lower:
                tr_html += f"<td style='border: 1px solid #cbd5e1; padding: 8px; font-size: 11px; width: 25%; word-wrap: break-word; white-space: normal;'>{val_str}</td>"
            elif 'uraian' in c_lower or 'deskripsi' in c_lower or 'pekerjaan' in c_lower:
                tr_html += f"<td style='border: 1px solid #cbd5e1; padding: 8px; font-size: 11px; width: 45%; word-wrap: break-word; white-space: normal;'>{val_str}</td>"
            elif 'no' in c_lower and len(c_lower) <= 3:
                tr_html += f"<td style='border: 1px solid #cbd5e1; padding: 8px; font-size: 11px; width: 8%; text-align: center;'>{val_str}</td>"
            else:
                tr_html += f"<td style='border: 1px solid #cbd5e1; padding: 8px; font-size: 11px; word-wrap: break-word; white-space: normal;'>{val_str}</td>"
        tr_html += "</tr>"

    tabel_html_wrapper = f"""
    <div style="width: 100%; overflow-x: auto; margin-bottom: 20px;">
        <table style="width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; table-layout: fixed;">
            <thead>
                <tr>{th_html}</tr>
            </thead>
            <tbody>
                {tr_html}
            </tbody>
        </table>
    </div>
    """
    st.markdown(tabel_html_wrapper, unsafe_allow_html=True)

    # --- HTML DOKUMEN UNTUK CETAK & PDF ---
    print_html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Master Referensi Harga - PT BSS</title>
        <style>
            @page {{ size: A4 landscape; margin: 10mm; }}
            body {{ font-family: Arial, sans-serif; font-size: 11px; color: #000; padding: 10px; background: #fff; }}
            .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 8px; margin-bottom: 15px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; table-layout: fixed; }}
            th, td {{ border: 1px solid #000; padding: 6px; font-size: 10px; word-wrap: break-word; white-space: normal; text-align: left; }}
            th {{ background-color: #f1f5f9; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2 style="margin: 0; font-size: 16px; text-transform: uppercase;">PT. BANGGAI SENTRAL SULAWESI</h2>
            <p style="margin: 3px 0 0 0; font-size: 11px; font-weight: bold;">Master Referensi Harga & Pekerjaan</p>
            <p style="margin: 2px 0 0 0; font-size: 10px; color: #333;">Kontrak: {selected_kontrak} | Kategori: {selected_kategori}</p>
        </div>
        <table>
            <thead>
                <tr>{th_html}</tr>
            </thead>
            <tbody>
                {tr_html}
            </tbody>
        </table>
    </body>
    </html>
    """

    # --- TOMBOL AKSI UTAMA (CETAK & SAVE PDF) ---
    st.markdown("---")
    st.markdown("#### 🖨️ Tombol Aksi Dokumen Master Referensi")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        b64_print = base64.b64encode(print_html_content.encode("utf-8")).decode()
        print_script = f"""
            <script>
                function printMaster() {{
                    var win = window.open('about:blank', '_blank');
                    win.document.open();
                    win.document.write(atob("{b64_print}"));
                    win.document.close();
                    win.focus();
                    setTimeout(function(){{ win.print(); }}, 500);
                }}
            </script>
            <button onclick="printMaster()" style="width: 100%; background-color: #10b981; color: white; padding: 14px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                🖨️ Cetak / Print Dokumen
            </button>
        """
        st.components.v1.html(print_script, height=65)

    with col_btn2:
        download_link = f'<a href="data:text/html;base64,{b64_print}" download="Master_Referensi_Kontrak_{str(selected_kontrak).replace("/", "-")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 14px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">📥 Save as PDF / Download HTML</button></a>'
        st.markdown(download_link, unsafe_allow_html=True)