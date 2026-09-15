import streamlit as st
import hashlib
import os
import pandas as pd

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Direktori penyimpanan aman yang dikelola oleh Super Admin
DIR_DATABASE = "database_penyimpanan_aman"
EXCEL_USERS = os.path.join(DIR_DATABASE, "database_users.xlsx")

def muat_database_users_dinamis():
    """Membaca data akun secara murni dinamis dari database Excel yang dikelola Super Admin."""
    if os.path.exists(EXCEL_USERS):
        try:
            df = pd.read_excel(EXCEL_USERS, engine='openpyxl')
            if df is not None and not df.empty:
                return df.to_dict(orient="records")
        except Exception:
            pass
    
    # Fallback darurat jika file database belum ada sama sekali (hanya 1 akun super admin awal)
    return [
        {
            "Username": "admin",
            "Password": hash_password("admin2026"),
            "Nama Lengkap": "Administrator Utama",
            "Role": "Super Admin",
            "Departemen": "IT & System Control"
        }
    ]

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
                # Memuat akun secara dinamis langsung dari database kelolaan Super Admin
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