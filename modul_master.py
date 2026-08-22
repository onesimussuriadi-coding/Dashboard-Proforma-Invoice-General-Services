import streamlit as st
import pandas as pd
import base64

def tampilkan_master_referensi_tersimpan(master_data_list):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📂 Daftar Master Referensi Harga & Pekerjaan Tersimpan</h3>
        </div>
    """, unsafe_allow_html=True)

    if not master_data_list:
        st.info("ℹ️ Belum ada data master referensi harga yang tersimpan.")
        return

    # Konversi ke DataFrame Pandas
    df_master = pd.DataFrame(master_data_list)

    # Ambil daftar Nomor Kontrak unik untuk filter
    kolom_kontrak = None
    for col in ['Nomor Kontrak', 'No Kontrak', 'Kontrak']:
        if col in df_master.columns:
            kolom_kontrak = col
            break

    if kolom_kontrak:
        list_kontrak = ["-- Semua Kontrak --"] + list(df_master[kolom_kontrak].dropna().unique())
        selected_kontrak = st.selectbox("🔍 Filter Berdasarkan Nomor Kontrak:", list_kontrak, key="filter_kontrak_master")

        if selected_kontrak != "-- Semua Kontrak --":
            df_filtered = df_master[df_master[kolom_kontrak] == selected_kontrak]
        else:
            df_filtered = df_master
    else:
        df_filtered = df_master
        selected_kontrak = "-- Semua Kontrak --"

    # Menampilkan tabel data yang sudah difilter
    st.dataframe(df_filtered, use_container_width=True)

    # --- FITUR PREVIEW & CETAK (PRINT) ---
    st.markdown("---")
    st.markdown("#### 🖨️ Pratinjau & Cetak Dokumen Master Referensi")

    # Membuat HTML sederhana untuk preview & print tabel yang difilter
    html_table_rows = ""
    for _, row in df_filtered.iterrows():
        html_table_rows += "<tr>"
        for val in row:
            html_table_rows += f"<td style='border: 1px solid #333; padding: 6px; font-size: 10px;'>{val}</td>"
        html_table_rows += "</tr>"

    headers_html = "".join([f"<th style='border: 1px solid #333; padding: 6px; background-color: #f1f5f9; font-size: 10px;'>{col}</th>" for col in df_filtered.columns])

    print_html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Master Referensi Harga - PT BSS</title>
        <style>
            @page {{ size: A4 landscape; margin: 10mm; }}
            body {{ font-family: Arial, sans-serif; font-size: 11px; color: #000; padding: 10px; }}
            .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 8px; margin-bottom: 15px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2 style="margin: 0; font-size: 14px;">PT. BANGGAI SENTRAL SULAWESI</h2>
            <p style="margin: 2px 0; font-size: 10px;">Master Referensi Harga & Pekerjaan - Filter Kontrak: {selected_kontrak}</p>
        </div>
        <table>
            <tr>{headers_html}</tr>
            {html_table_rows}
        </table>
    </body>
    </html>
    """

    # Tampilkan Preview kecil di Streamlit
    with st.expander("👁️ Klik Disini untuk Melihat Pratinjau Dokumen Cetak"):
        st.components.v1.html(print_html_content, height=350, scrolling=True)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        b64_print = base64.b64encode(print_html_content.encode()).decode()
        print_script = f"""
            <script>
                function printMaster() {{
                    var win = window.open('about:blank', '_blank');
                    win.document.write(atob("{b64_print}"));
                    win.document.close();
                    win.focus();
                    setTimeout(function(){{ win.print(); }}, 500);
                }}
            </script>
            <button onclick="printMaster()" style="width: 100%; background-color: #10b981; color: white; padding: 10px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
                🖨️ Cetak / Print Master Referensi
            </button>
        """
        st.components.v1.html(print_script, height=50)

    with col_btn2:
        download_link = f'<a href="data:text/html;base64,{b64_print}" download="Master_Referensi_{str(selected_kontrak).replace("/", "-")}.html" style="text-decoration: none;"><button style="width: 100%; background-color: #3b82f6; color: white; padding: 10px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">📥 Download File HTML</button></a>'
        st.markdown(download_link, unsafe_allow_html=True)