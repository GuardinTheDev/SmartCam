import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time as pytime
from datetime import datetime, time

API_BASE_URL = "http://127.0.0.1:8000/api"

st.set_page_config(
    page_title="SmartCam IoT - Katmanlı Telemetri Paneli",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS TASARIM ---
def inject_custom_css():
    st.markdown("""
    <style>
        .stApp { background-color: #0b1120; color: #e2e8f0; }
        div[data-testid="stMetric"] {
            background: linear-gradient(145deg, rgba(255,255,255,0.045), rgba(255,255,255,0.015));
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px; padding: 18px 16px;
        }
        .status-chip {
            display: inline-block; padding: 6px 14px; border-radius: 999px;
            font-weight: 600; font-size: 0.85rem; background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.12);
        }
        /* ---- Input alanları ---- */
        .stTextInput input, .stNumberInput input, div[data-baseweb="input"] input {
            background-color: #1e293b !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
            border-radius: 10px !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            font-weight: 500 !important;
        }
        .stTextInput input:focus, .stNumberInput input:focus, div[data-baseweb="input"] input:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 2px rgba(59,130,246,0.35) !important;
            background-color: #1e293b !important;
        }
        input:-webkit-autofill,
        input:-webkit-autofill:hover, 
        input:-webkit-autofill:focus {
            -webkit-text-fill-color: #ffffff !important;
            -webkit-box-shadow: 0 0 0px 1000px #1e293b inset !important;
            transition: background-color 5000s ease-in-out 0s;
        }
    </style>
    """, unsafe_allow_html=True)

def parse_percentage(val):
    try:
        return int(float(str(val).replace("%", "").strip()))
    except Exception:
        return 0

def get_status_indicator(value, thresholds=(50, 20)):
    val = parse_percentage(value)
    if val >= thresholds[0]: return f"🟢 %{val} (Mükemmel)"
    elif val >= thresholds[1]: return f"🟡 %{val} (Normal)"
    else: return f"🔴 %{val} (Düşük)"

def format_relative_time(dt_input):
    if not dt_input or dt_input == "N/A": return "Az önce"
    try:
        clean_str = str(dt_input).replace("Z", "").replace("T", " ")
        dt_obj = datetime.fromisoformat(clean_str)
        diff = datetime.now() - dt_obj
        sec = int(diff.total_seconds())
        if sec < 60: return "Az önce"
        m = sec // 60
        h = m // 60
        d = h // 24
        mo = d // 30
        if m < 60: return f"{m} dakika önce"
        elif h < 24: return f"{h} saat önce"
        elif d < 30: return f"{d} gün önce"
        elif mo < 12: return f"{mo} ay önce"
        else: return dt_obj.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return str(dt_input)

def check_persistent_session():
    current_time = pytime.time()
    if "authenticated" not in st.session_state: st.session_state.authenticated = False
    if "username" not in st.session_state: st.session_state.username = None
    if "role" not in st.session_state: st.session_state.role = None

    if not st.session_state.authenticated:
        q_user = st.query_params.get("session_user")
        q_role = st.query_params.get("session_role")
        q_exp = st.query_params.get("session_exp")
        if q_user and q_role and q_exp:
            try:
                if current_time < float(q_exp):
                    st.session_state.authenticated = True
                    st.session_state.username = q_user
                    st.session_state.role = q_role
                else: st.query_params.clear()
            except Exception: st.query_params.clear()

    st.components.v1.html("""
        <script>
        (function() {
            const p = window.parent;
            const s = p.localStorage.getItem('smartcam_user_session');
            if (s) {
                try {
                    const d = JSON.parse(s);
                    if (d.expires_at > Date.now()) {
                        const url = new URL(p.location.href);
                        if (!url.searchParams.has('session_user')) {
                            url.searchParams.set('session_user', d.username);
                            url.searchParams.set('session_role', d.role);
                            url.searchParams.set('session_exp', (d.expires_at / 1000).toString());
                            p.location.href = url.href;
                        }
                    } else { p.localStorage.removeItem('smartcam_user_session'); }
                } catch(e) {}
            }
        })();
        </script>
    """, height=0)

# --- GİRİŞ & KAYIT EKRANI ---
def render_auth_page():
    st.components.v1.html("""
        <script>
        const p = window.parent.document;
        if (!window.keyboardNavInjected) {
            window.keyboardNavInjected = true;
            p.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === 'ArrowDown') {
                    const act = p.activeElement;
                    if (act && act.tagName === 'INPUT') {
                        const inps = Array.from(p.querySelectorAll('input:not([type="hidden"]):not([type="checkbox"])'));
                        const idx = inps.indexOf(act);
                        if (idx > -1 && idx < inps.length - 1) {
                            if (e.key === 'ArrowDown' || (e.key === 'Enter' && act.type !== 'password')) {
                                e.preventDefault(); e.stopPropagation(); inps[idx + 1].focus();
                            }
                        }
                    }
                }
            }, true);
        }
        </script>
    """, height=0)

    _, mid, _ = st.columns([1, 1.3, 1])
    with mid:
        st.markdown("<div style='text-align:center;'>📡 <h1>SmartCam Telemetri Paneli</h1></div>", unsafe_allow_html=True)
        t_login, t_reg = st.tabs(["🔐 Giriş Yap", "📝 Kayıt Ol"])

        with t_login:
            with st.form("login_form"):
                u = st.text_input("Kullanıcı Adı / E-Posta / Telefon", key="login_user")
                p = st.text_input("Şifre", type="password", key="login_pass")
                if st.form_submit_button("Giriş Yap", type="primary"):
                    if u and p:
                        try:
                            r = requests.post(f"{API_BASE_URL}/auth/login", json={"username": u, "password": p}, timeout=5)
                            if r.status_code == 200:
                                data = r.json()
                                exp = pytime.time() + 3600
                                st.session_state.authenticated = True
                                st.session_state.username = data.get("username", u)
                                st.session_state.role = data.get("role", "user")
                                st.query_params["session_user"] = st.session_state.username
                                st.query_params["session_role"] = st.session_state.role
                                st.query_params["session_exp"] = str(exp)
                                st.components.v1.html(f"""
                                    <script>window.parent.localStorage.setItem('smartcam_user_session', JSON.stringify({{
                                        username: "{st.session_state.username}", role: "{st.session_state.role}", expires_at: {int(exp * 1000)}
                                    }}));</script>
                                """, height=0)
                                st.success("Giriş başarılı!")
                                st.rerun()
                            elif r.status_code == 403: st.error("❌ Hesabınız onay bekliyor veya reddedilmiş.")
                            else: st.error("❌ Hatalı kullanıcı adı veya şifre!")
                        except Exception as e: st.error(f"Bağlantı hatası: {e}")

        with t_reg:
            with st.form("register_form"):
                fn = st.text_input("Ad Soyad", key="rf_name")
                un = st.text_input("Kullanıcı Adı", key="rf_user")
                em = st.text_input("E-Posta", key="rf_em")
                ph = st.text_input("Telefon", key="rf_ph")
                pw = st.text_input("Şifre", type="password", key="rf_pass")
                pwc = st.text_input("Şifre Tekrar", type="password", key="rf_pass_c")
                kvkk = st.checkbox("KVKK Aydınlatma Metni'ni okudum ve kabul ediyorum.", key="rf_kvkk")
                if st.form_submit_button("Kayıt Başvurusu Yap", type="primary"):
                    if fn and un and em and ph and pw and pwc:
                        if pw != pwc: st.error("❌ Şifreler eşleşmiyor!")
                        elif not kvkk: st.warning("⚠️ KVKK metnini kabul etmelisiniz.")
                        else:
                            try:
                                r = requests.post(f"{API_BASE_URL}/auth/register", json={
                                    "username": un, "password": pw, "full_name": fn, "email": em, "phone": ph, "kvkk_approved": kvkk
                                }, timeout=5)
                                if r.status_code in [200, 201]: st.success("✅ Kayıt başarılı, admin onayına gönderildi!")
                                else: st.error(f"❌ {r.json().get('detail', 'Kayıt başarısız')}")
                            except Exception as e: st.error(f"Hata: {e}")

# --- DASHBOARD & SEÇİM ---
def render_dashboard():
    st.sidebar.markdown(f"<div style='text-align:center;'>👤 <h3>{st.session_state.username}</h3><span class='status-chip'>Rol: {st.session_state.role.upper()}</span></div>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.authenticated = False
        st.query_params.clear()
        st.components.v1.html("<script>window.parent.localStorage.removeItem('smartcam_user_session');</script>", height=0)
        st.rerun()

    st.markdown("<h1>📡 SmartCam Telemetri ve Sensör İzleme Paneli</h1>", unsafe_allow_html=True)
    
    try:
        stations = requests.get(f"{API_BASE_URL}/stations", timeout=5).json()
    except Exception: stations = []

    st_opts = ["-- Lütfen Bir İstasyon Seçiniz --"] + [s["name"] for s in stations]
    st_map = {s["name"]: s for s in stations}
    sel_st_str = st.selectbox("1️⃣ Adım: İzlemek İstediğiniz İstasyon:", st_opts)

    if sel_st_str == "-- Lütfen Bir İstasyon Seçiniz --":
        st.info("👈 Lütfen yukarıdan bir istasyon seçiniz.")
        return

    sel_st = st_map[sel_st_str]
    st.markdown(f"### 📊 [{sel_st['name']}] Genel Durum")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("İstasyon Adı", sel_st.get("name"))
    c2.metric("IP Adresi", sel_st.get("gsm_ip"))
    c3.metric("IMEI No", sel_st.get("imei"))
    c4.metric("Son Güncelleme", format_relative_time(sel_st.get("updated_at")))

    # Sensör Seçimi
    try:
        sensors = requests.get(f"{API_BASE_URL}/stations/{sel_st['id']}/sensors", timeout=5).json()
    except Exception: sensors = []

    sn_opts = ["-- Lütfen Bir Sensör Seçiniz --"] + [f"{s['label']} ({s['default_unit']})" for s in sensors]
    sn_map = {f"{s['label']} ({s['default_unit']})": s for s in sensors}
    sel_sn_str = st.selectbox("2️⃣ Adım: Analiz Edilecek Sensör:", sn_opts)

    if sel_sn_str != "-- Lütfen Bir Sensör Seçiniz --":
        sel_sn = sn_map[sel_sn_str]
        try:
            logs = requests.get(f"{API_BASE_URL}/sensor/history?station_id={sel_st['id']}&sensor_id={sel_sn['id']}&limit=50", timeout=5).json()
        except Exception: logs = []
        
        if logs:
            df = pd.DataFrame(logs)
            st.metric(f"⚡ Canlı {sel_sn['label']} Değeri ({format_relative_time(logs[0].get('recorded_at'))})", f"{logs[0].get('raw_value')} {sel_sn['default_unit']}")
            fig = px.line(df, x="recorded_at", y="raw_value", title=f"{sel_st['name']} — {sel_sn['label']} Ölçüm Grafiği")
            st.plotly_chart(fig, use_container_width=True)

def main():
    inject_custom_css()
    check_persistent_session()
    if not st.session_state.authenticated: render_auth_page()
    else: render_dashboard()

if __name__ == "__main__": main()
