import streamlit as st
import hashlib
import os
import pandas as pd

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

DIR_DATABASE = "database_penyimpanan_aman"
EXCEL_USERS = os.path.join(DIR_DATABASE, "database_users.xlsx")

def muat_database_users_dinamis():
    """Membaca data akun secara murni dinamis dari database Excel yang dikelola Super Admin."""
    if not os.path.exists(DIR_DATABASE):
        os.makedirs(DIR_DATABASE)
        
    if os.path.exists(EXCEL_USERS):
        try:
            df = pd.read_excel(EXCEL_USERS, engine='openpyxl')
            if df is not None and not df.empty:
                return df.to_dict(orient="records")
        except Exception:
            pass
    
    # Fallback inisialisasi awal jika file excel belum ada
    default_users = [
        {
            "Username": "admin",
            "Password": hash_password("admin2026"),
            "Nama Lengkap": "Administrator Utama",
            "Role": "Super Admin",
            "Departemen": "IT & System Control"
        },
        {
            "Username": "prayogo@ptbss.id",
            "Password": hash_password("management2026"),
            "Nama Lengkap": "Prayogo",
            "Role": "Management",
            "Departemen": "Manajemen & Direksi"
        }
    ]
    
    # Simpan default ke file excel agar langsung terbentuk
    try:
        df_init = pd.DataFrame(default_users)
        df_init.to_excel(EXCEL_USERS, index=False)
    except:
        pass
        
    return default_users

def render_autentikasi():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        st.markdown("""
            <div style="max-width: 400px; margin: 50px auto; padding: 25px; background: #1e293b; border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="text-align: center; margin-bottom: 20px;">🔐 Login Sistem PT BSS</h3>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("form_login"):
            username_input = st.text_input("Username / Email")
            password_input = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Masuk Sistem", use_container_width=True)

            if submit_login:
                users = muat_database_users_dinamis()
                hashed_pw = hash_password(password_input)
                
                user_match = next((u for u in users if str(u.get("Username", "")).strip().lower() == username_input.strip().lower() and str(u.get("Password", "")) == hashed_pw), None)
                
                if user_match:
                    st.session_state["logged_in"] = True
                    st.session_state["current_user"] = user_match.get("Username")
                    st.session_state["current_role"] = user_match.get("Role")
                    st.session_state["nama_lengkap"] = user_match.get("Nama Lengkap")
                    st.success("✅ Login berhasil! Memuat sistem...")
                    st.rerun()
                else:
                    st.error("❌ Username atau Password salah!")
        return False
    
    return True

def render_panel_manajemen_akun():
    st.markdown("#### 👥 Panel Manajemen Akun & Kredensial Pengguna")
    st.info("💡 Menu ini digunakan oleh Super Admin untuk menambah, melihat, atau menghapus akun pengguna secara dinamis.")

    if not os.path.exists(DIR_DATABASE):
        os.makedirs(DIR_DATABASE)

    users = muat_database_users_dinamis()
    df_users = pd.DataFrame(users)

    if not df_users.empty:
        df_display = df_users.copy()
        if "Password" in df_display.columns:
            df_display["Password"] = "******** (Protected)"
        st.markdown("##### 📋 Daftar Akun Aktif dalam Sistem")
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("##### ➕ Tambah Akun Pengguna Baru")

    with st.form("form_tambah_akun_baru"):
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            new_username = st.text_input("Username / Email (contoh: nama@ptbss.id)")
            new_password = st.text_input("Password / Sandi Awal", type="password")
            new_nama = st.text_input("Nama Lengkap & Jabatan")
        with col_u2:
            new_role = st.selectbox("Hak Akses (Role)", ["Project Support", "Admin Support", "Management", "Super Admin"])
            new_dept = st.text_input("Departemen / Unit Kerja")

        submit_tambah = st.form_submit_button("💾 Simpan Akun Baru", use_container_width=True)

        if submit_tambah:
            if not new_username or not new_password or not new_nama:
                st.error("⚠️ Username, Password, dan Nama Lengkap wajib diisi!")
            else:
                if any(str(u.get("Username", "")).strip().lower() == new_username.strip().lower() for u in users):
                    st.error(f"⚠️ Username `{new_username}` sudah terdaftar dalam sistem!")
                else:
                    new_user_entry = {
                        "Username": new_username.strip(),
                        "Password": hash_password(new_password),
                        "Nama Lengkap": new_nama.strip(),
                        "Role": new_role,
                        "Departemen": new_dept.strip() if new_dept else "Umum"
                    }
                    users.append(new_user_entry)
                    
                    df_save = pd.DataFrame(users)
                    df_save.to_excel(EXCEL_USERS, index=False)
                    st.success(f"🎉 Akun baru untuk `{new_username}` dengan role `{new_role}` berhasil ditambahkan!")
                    st.rerun()

    if len(users) > 1:
        st.markdown("---")
        st.markdown("##### 🗑️ Hapus Akun Pengguna")
        list_username_tersedia = [u.get("Username") for u in users if u.get("Username") != "admin"]
        
        col_d1, col_d2 = st.columns([2, 1])
        with col_d1:
            target_hapus_user = st.selectbox("Pilih Username yang Ingin Dihapus:", list_username_tersedia)
        with col_d2:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("❌ Hapus Akun Ini", type="primary", use_container_width=True):
                updated_users = [u for u in users if u.get("Username") != target_hapus_user]
                df_save = pd.DataFrame(updated_users)
                df_save.to_excel(EXCEL_USERS, index=False)
                st.success(f"🗑️ Akun `{target_hapus_user}` berhasil dihapus dari sistem!")
                st.rerun()

# --- ALIAS FUNGSI UNTUK KOMPATIBILITAS DI APP.PY ---
def form_login_sistem():
    return render_autentikasi()