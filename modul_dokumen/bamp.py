import streamlit as st
import base64

def tampilkan_bamp(transaksi_list):
    st.markdown("""
        <div class="dashboard-card">
            <h3 style="margin-top:0; color:#065f46; font-size:18px;">📄 Berita Acara Mulai Pekerjaan (BAMP)</h3>
        </div>
    """, unsafe_allow_html=True)

    if not transaksi_list:
        st.warning("⚠️ Belum ada data transaksi.")
        return

    # Pemilihan transaksi
    pilihan_tx = [f"PI: {t['PI No.']} | PO: {t['Nomor PO']}" for t in transaksi_list]
    selected_idx = st.selectbox("Pilih Data Transaksi:", range(len(pilihan_tx)), format_func=lambda x: pilihan_tx[x])
    t = transaksi_list[selected_idx]

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; padding: 30px; font-size: 11px; }}
            .title {{ text-align: center; font-weight: bold; font-size: 14px; text-decoration: underline; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; }}
            td {{ padding: 3px; vertical-align: top; }}
            .data-table {{ border: 1px solid #000; margin-top: 15px; }}
            .data-table th, .data-table td {{ border: 1px solid #000; padding: 6px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="title">BERITA ACARA MULAI PEKERJAAN (BAMP)</div>
        <p>Pada hari ini, tanggal <b>{t['Tanggal Mulai']}</b>, bertanda tangan di bawah ini:</p>
        
        <table style="width: 100%; border: none;">
            <tr><td style="width: 5%;">01.</td><td style="width: 45%;"><b>PIHAK PERTAMA</b></td><td style="width: 50%;"><b>PIHAK KEDUA</b></td></tr>
            <tr><td></td><td>Nama Perusahaan: {t.get('Pihak Pertama', 'JOB Pertamina - Medco E&P Tomori Sulawesi')}</td><td>Nama Perusahaan: PT Banggai Sentral Sulawesi</td></tr>
            <tr><td></td><td>Alamat: {t.get('Alamat Pihak Pertama', 'Bidakara Office Tower...')}</td><td>Alamat: Jl. Urip Sumorharjo No. 53, Luwuk</td></tr>
            <tr><td></td><td>Diwakili oleh: {t.get('Perwakilan Pihak Pertama', 'Ronny Dwi Purnomo')}</td><td>Diwakili oleh: {t.get('Perwakilan Pihak Kedua', 'Ir. Ferry Tatimu')}</td></tr>
            <tr><td></td><td>Jabatan: {t.get('Jabatan Pihak Pertama', 'Maintenance Support Supervisor')}</td><td>Jabatan: {t.get('Jabatan Pihak Kedua', 'Direktur')}</td></tr>
        </table>

        <p><b>DASAR PELAKSANAAN PEKERJAAN</b></p>
        <table style="width: 100%;">
            <tr><td style="width: 200px;">Nomor Kontrak</td><td>: {t['Nomor Kontrak']}</td></tr>
            <tr><td>Tanggal Kontrak</td><td>: {t.get('Tanggal Kontrak', '-')}</td></tr>
            <tr><td>Nomor PO</td><td>: {t['Nomor PO']}</td></tr>
            <tr><td>Tanggal PO</td><td>: {t['Tanggal PO']}</td></tr>
        </table>

        <p>Dengan ini PIHAK KEDUA memulai melaksanakan pekerjaan: <i>{t['Deskripsi PO']}</i></p>

        <table class="data-table">
            <tr><th>NO</th><th>URAIAN</th><th>JUMLAH</th><th>SATUAN</th><th>CATATAN</th></tr>
            <tr><td>1</td><td>{t['Deskripsi Pekerjaan']}</td><td>{t['Qty']}</td><td>{t['Unit']}</td><td>-</td></tr>
        </table>

        <p>Demikian Berita Acara ini dibuat untuk dipergunakan sebagaimana mestinya.</p>
        
        <table style="width: 100%; margin-top: 40px;">
            <tr><td style="text-align: center;">PIHAK PERTAMA</td><td style="text-align: center;">PIHAK KEDUA</td></tr>
            <tr><td style="height: 60px;"></td><td></td></tr>
            <tr><td style="text-align: center;"><u>{t.get('Perwakilan Pihak Pertama', '')}</u></td><td style="text-align: center;"><u>{t.get('Perwakilan Pihak Kedua', '')}</u></td></tr>
        </table>
    </body>
    </html>
    """

    st.components.v1.html(html_content, height=600, scrolling=True)
    
    # Tombol Aksi
    b64_html = base64.b64encode(html_content.encode()).decode()
    st.markdown(f'<a href="data:text/html;base64,{b64_html}" download="BAMP_{t["Nomor PO"]}.html"><button>📥 Download BAMP</button></a>', unsafe_allow_html=True)