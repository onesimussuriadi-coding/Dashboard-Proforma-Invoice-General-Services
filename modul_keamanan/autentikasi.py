import streamlit as st
import pandas as pd
import os

DIR_DATABASE = "database_penyimpanan_aman"
if not os.path.exists(DIR_DATABASE):
    os.makedirs(DIR_DATABASE)

EXCEL_PENGGUNA = os.path.join(DIR_DATABASE, "database_pengguna.xlsx")

def muat_data_pengguna():
    default_users = [
        {"Username": "admin", "Password": "bss2026", "Role": "Manajer Operasional"},
        {"Username": "staff_timesheet", "Password": "ts2026", "Role": "Staff Timesheet"}
    ]
    if os.path.exists(EXCEL_PENGGUNA):
        try:
            df = pd.read_excel(EXCEL_PENGGUNA)
            if df is not None and not df.empty:
                return df.to_dict(orient="records")
        except Exception:
            pass
    return default_users

def simpan_data_pengguna(data_list):
    df_baru = pd.DataFrame(data_list)
    df_baru.to_excel(EXCEL_PENGGUNA, index=False)

def form_login_sistem():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = ""
    if 'current_role' not in st.session_state:
        st.session_state.current_role = ""

    if not st.session_state.logged_in:
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            st.markdown("""
                <div style="padding: 25px 25px 10px 25px; background: #ffffff; border-radius: 12px 12px 0 0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-top: 5px solid #065f46; text-align: center;">
                    <h3 style="color: #065f46; margin: 0; font-size: 20px;">🔐 PT BSS - Internal Corporate Login</h3>
                    <p style="font-size: 12px; color: #475569; margin-top: 5px;">Sistem Pengendalian Berjenjang Terbatas</p>
                </div>
            """, unsafe_allow_html=True)
            
            with st.form("login_form_secure"):
                username_input = st.text_input("Username Korporat")
                password_input = st.text_input("Password Akses", type="password")
                submit_btn = st.form_submit_button("Masuk ke Sistem", use_container_width=True)
                
                if submit_btn:
                    daftar_user = muat_data_pengguna()
                    login_sukses = False
                    role_user = ""
                    for user in daftar_user:
                        if str(user.get("Username")).strip().lower() == username_input.strip().lower() and str(user.get("Password")) == password_input:
                            login_sukses = True
                            role_user = str(user.get("Role", "Staff"))
                            break
                    
                    if login_sukses:
                        st.session_state.logged_in = True
                        st.session_state.current_user = username_input.strip()
                        st.session_state.current_role = role_user
                        st.success("Login Berhasil! Memuat hak akses...")
                        st.rerun()
                    else:
                        st.error("⚠️ Username atau Password salah.")
        return False
    return True

def render_panel_manajemen_akun():
    st.sidebar.markdown("---")
    with st.sidebar.expander("⚙️ Manajemen Akun & Hak Akses"):
        st.markdown(f"👤 **Login:** `{st.session_state.get('current_user')}`")
        st.markdown(f"🛡️ **Role:** `{st.session_state.get('current_role')}`")
        
        if st.session_state.get('current_role') in ["Manajer Operasional", "Administrator"]:
            st.markdown("---")
            
            # Dibungkus dalam expander agar bisa dibuka-tutup secara rapi
            with st.expander("📂 Lihat & Kelola Akun Terdaftar"):
                daftar_user = muat_data_pengguna()
                if daftar_user:
                    for idx, u in enumerate(daftar_user):
                        c_info, c_del = st.columns([3, 1])
                        c_info.markdown(f"<small><b>{u.get('Username')}</b><br><i>{u.get('Role')}</i></small>", unsafe_allow_html=True)
                        with c_del:
                            if u.get('Username') != "admin":
                                if st.button("🗑️", key=f"del_user_{idx}"):
                                    daftar_user.pop(idx)
                                    simpan_data_pengguna(daftar_user)
                                    st.success("Akun dihapus!")
                                    st.rerun()
                            else:
                                st.markdown("<small><i>Utama</i></small>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("**Tambah Akun Baru:**")
            with st.form("form_tambah_user_secure"):
                new_user = st.text_input("Username Baru")
                new_pass = st.text_input("Password Baru", type="password")
                new_role = st.selectbox("Hak Akses (Role)", [
                    "Manajer Operasional", 
                    "Finance / Invoice", 
                    "Staff Timesheet"
                ])
                btn_tambah = st.form_submit_button("➕ Daftarkan Akun")
                
                if btn_tambah:
                    if not new_user or not new_pass:
                        st.error("⚠️ Username & Password wajib diisi!")
                    else:
                        existing_users = muat_data_pengguna()
                        if any(str(u.get("Username")).strip().lower() == new_user.strip().lower() for u in existing_users):
                            st.error("⚠️ Username sudah terdaftar!")
                        else:
                            existing_users.append({
                                "Username": new_user.strip(),
                                "Password": new_pass.strip(),
                                "Role": new_role
                            })
                            simpan_data_pengguna(existing_users)
                            st.success(f"🎉 Akun {new_user} berhasil dibuat!")
                            st.rerun()
        
        st.markdown("---")
        if st.sidebar.button("🔒 Keluar / Logout Sistem", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.current_user = ""
            st.session_state.current_role = ""
            st.rerun()