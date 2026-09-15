import streamlit as st
import pandas as pd
import os
import hashlib

DIR_DATABASE = "database_penyimpanan_aman"
EXCEL_USERS = os.path.join(DIR_DATABASE, "database_users_hak_akses.xlsx")

def hash_password(password):
    return hashlib.sha256(str(password).encode()).hexdigest()

def muat_database_users():
    if not os.path.exists(DIR_DATABASE):
        os.makedirs(DIR_DATABASE)
        
    if os.path.exists(EXCEL_USERS):
        try:
            df = pd.read_excel(EXCEL_USERS, engine='openpyxl')
            if df is not None and not df.empty:
                return df.to_dict(orient="records")
        except:
            pass
            
    # Default Users sesuai Rule Perusahaan PT Banggai Sentral Sulawesi
    default_users = [
        {
            "Username": "admin",
            "Password": hash_password("bss2026"),
            "Nama Lengkap": "Administrator Utama",
            "Role": "Super Admin",
            "Departemen": "IT & Manajemen"
        },
        {
            "Username": "finance",
            "Password": hash_password("finance2026"),
            "Nama Lengkap": "Staff Accounting & Finance",
            "Role": "Finance",
            "Departemen": "Keuangan"
        },
        {
            "Username": "manager",
            "Password": hash_password("manager2026"),
            "Nama Lengkap": "Project Manager",
            "Role": "Project Manager",
            "Departemen": "Manajemen Proyek"
        },
        {
            "Username": "projectsupport",
            "Password": hash_password("project2026"),
            "Nama Lengkap": "Project Support / Marketing",
            "Role": "Project Support",
            "Departemen": "Operasional & Marketing"
        },
        {
            "Username": "management",
            "Password": hash_password("viewer2026"),
            "Nama Lengkap": "Direksi & Manajemen",
            "Role": "Management",
            "Departemen": "Eksekutif"
        }
    ]
    df_default = pd.DataFrame(default_users)
    df_default.to_excel(EXCEL_USERS, index=False, sheet_name="Users")
    return default_users

def simpan_database_users(users_list):
    if not os.path.exists(DIR_DATABASE):
        os.makedirs(DIR_DATABASE)
    df = pd.DataFrame(users_list)
    df.to_excel(EXCEL_USERS, index=False, sheet_name="Users")
    st.session_state["db_users"] = users_list

def kelola_autentikasi_dan_hak_akses():
    if "db_users" not in st.session_state:
        st.session_state["db_users"] = muat_database_users()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = ""
    if "current_role" not in st.session_state:
        st.session_state["current_role"] = ""

    # Halaman Login Sistem
    if not st.session_state["logged_in"]:
        st.markdown("""
            <div style="max-width: 420px; margin: 40px auto; padding: 30px; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;">
                <div style="text-align: center; margin-bottom: 25px;">
                    <h3 style="color: #0f172a; margin: 0; font-size: 22px;">🔐 PT Banggai Sentral Sulawesi</h3>
                    <p style="color: #64748b; font-size: 13px; margin-top: 6px;">Sistem Terpadu Invoice, Tax & Financial Monitoring</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        col_l1, col_l2, col_l3 = st.columns([1, 2.2, 1])
        with col_l2:
            with st.form("form_login_system"):
                username_input = st.text_input("Username Pengguna", placeholder="Masukkan username...")
                password_input = st.text_input("Password", type="password", placeholder="Masukkan password...")
                submit_login = st.form_submit_button("🔑 Masuk ke Sistem", use_container_width=True, type="primary")

                if submit_login:
                    users_db = st.session_state["db_users"]
                    hashed_pw = hash_password(password_input)
                    
                    matched_user = next((u for u in users_db if str(u.get("Username")).strip().lower() == username_input.strip().lower() and str(u.get("Password")) == hashed_pw), None)
                    
                    if matched_user:
                        st.session_state["logged_in"] = True
                        st.session_state["current_user"] = matched_user.get("Username")
                        st.session_state["current_role"] = matched_user.get("Role")
                        st.session_state["nama_lengkap"] = matched_user.get("Nama Lengkap")
                        st.success(f"🎉 Selamat datang, {matched_user.get('Nama Lengkap')}! Memuat sistem...")
                        st.rerun()
                    else:
                        st.error("❌ Username atau Password salah! Silakan periksa kembali.")
        return False

    return True

def tampilkan_panel_sidebar_akun():
    username_aktif = st.session_state.get("current_user", "admin")
    role_aktif = st.session_state.get("current_role", "Super Admin")
    nama_aktif = st.session_state.get("nama_lengkap", "Administrator Utama")

    with st.expander("⚙️ Manajemen Akun & Hak Akses", expanded=True):
        st.markdown(f"""
            <div style="font-size: 13px; color: #1e293b; line-height: 1.5;">
                <p style="margin: 2px 0;">👤 <b>Login:</b> <span style="color: #0284c7; font-weight: bold;">{username_aktif}</span></p>
                <p style="margin: 2px 0;">🛡️ <b>Role:</b> <span style="background: #e2e8f0; padding: 2px 6px; border-radius: 4px; font-weight: bold; color: #0f172a;">{role_aktif}</span></p>
                <p style="margin: 2px 0; color: #64748b; font-size: 11px;">Nama: {nama_aktif}</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='margin: 8px 0;'>", unsafe_allow_html=True)

        if st.button("🔒 Keluar / Logout Sistem", use_container_width=True, type="secondary"):
            st.session_state["logged_in"] = False
            st.session_state["current_user"] = ""
            st.session_state["current_role"] = ""
            st.success("👋 Anda telah keluar dari sistem.")
            st.rerun()

    # Panel Admin Tambah User
    if role_aktif == "Super Admin":
        with st.expander("👥 Panel Kontrol Tambah/Edit User", expanded=False):
            with st.form("form_tambah_user_baru"):
                new_user = st.text_input("Username Baru")
                new_pass = st.text_input("Password Baru", type="password")
                new_nama = st.text_input("Nama Lengkap")
                new_role = st.selectbox("Pilih Role", ["Super Admin", "Finance", "Project Manager", "Project Support", "Management"])
                
                btn_simpan_user = st.form_submit_button("➕ Tambah User Baru")
                if btn_simpan_user:
                    if new_user and new_pass:
                        current_db = st.session_state["db_users"]
                        current_db.append({
                            "Username": new_user,
                            "Password": hash_password(new_pass),
                            "Nama Lengkap": new_nama if new_nama else new_user,
                            "Role": new_role,
                            "Departemen": "Umum"
                        })
                        simpan_database_users(current_db)
                        st.success(f"✅ User `{new_user}` dengan role `{new_role}` berhasil ditambahkan!")
                        st.rerun()
                    else:
                        st.error("⚠️ Username dan Password wajib diisi!")

def cek_izin_akses_modul(nomor_modul):
    """
    Aturan Hak Akses:
    - Super Admin: Akses Semua Modul (0, 1, 2, 3)
    - Finance: Hanya Modul 3
    - Project Manager: Modul 0, 1, 2
    - Project Support (Operasi Marketing): Modul 1, 2
    - Management (Viewer): Modul 1, 2, 3 (Read Only)
    """
    role = st.session_state.get("current_role", "Super Admin")
    
    if role == "Super Admin":
        return True, False # (Bisa Diakses, Bukan Read-Only Murni jika Admin)
    elif role == "Finance":
        return nomor_modul == 3, False
    elif role == "Project Manager":
        return nomor_modul in [0, 1, 2], False
    elif role == "Project Support":
        return nomor_modul in [1, 2], False
    elif role == "Management":
        # Manajemen bisa akses modul 1 sampai 3 dengan sifat Read-Only (True, True)
        is_allowed = nomor_modul in [1, 2, 3]
        return is_allowed, True 
    return False, False