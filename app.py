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
        .stApp { background-color: #0b1120; color: #f8fafc; }
        
        /* Sidebar Dark Mode */
        section[data-testid="stSidebar"] {
            background-color: #0f172a !important;
            border-right: 1px solid rgba(255,255,255,0.1) !important;
        }
        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3, 
        section[data-testid="stSidebar"] p, 
        section[data-testid="stSidebar"] span {
            color: #f8fafc !important;
        }
        
        /* Metin & Etiket Parlaklığı (High Contrast) */
        label, p, span, .stMarkdown, .stCaption, div[class*="stWidgetLabel"] p {
            color: #e2e8f0 !important;
            font-weight: 600 !important;
        }
        
        /* Metric Kart Parlaklıkları */
        div[data-testid="stMetric"] {
            background: linear-gradient(145deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 16px; padding: 18px 16px;
        }
        div[data-testid="stMetricLabel"] p {
            color: #cbd5e1 !important;
            font-weight: 700 !important;
            font-size: 0.9rem !important;
        }
        div[data-testid="stMetricValue"] {
            color: #ffffff !important;
            font-weight: 800 !important;
        }

        /* Sekmeler (Tabs) Minimal & Kırmızı Alt Çizgi Stili */
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
            background: transparent !important;
            padding: 4px 0px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .stTabs [data-baseweb="tab"] {
            background-color: transparent !important;
            background: transparent !important;
            border: none !important;
            color: #94a3b8 !important;
            font-weight: 500 !important;
            padding: 10px 8px;
        }
        .stTabs [data-baseweb="tab"] p, .stTabs [data-baseweb="tab"] span {
            color: #94a3b8 !important;
            font-weight: 500 !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: transparent !important;
            background: transparent !important;
            border: none !important;
        }
        .stTabs [aria-selected="true"] p, .stTabs [aria-selected="true"] span {
            color: #ef4444 !important;
            font-weight: 900 !important;
            font-size: 1.05rem !important;
        }
        .stTabs [data-baseweb="tab-border-highlight"], div[data-baseweb="tab-highlight"] {
            background-color: #ef4444 !important;
            height: 3px !important;
        }

        .status-chip {
            display: inline-block; padding: 6px 14px; border-radius: 999px;
            font-weight: 600; font-size: 0.85rem; background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.18);
            color: #38bdf8 !important;
        }

        /* ---- Input ve Selectbox Alanları ---- */
        .stTextInput input, .stNumberInput input, div[data-baseweb="input"] input, div[data-baseweb="select"] {
            background-color: #1e293b !important;
            border: 1px solid rgba(255,255,255,0.25) !important;
            border-radius: 10px !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            font-weight: 600 !important;
        }
        div[data-baseweb="select"] div {
            color: #ffffff !important;
            background-color: #1e293b !important;
        }
        div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
            background-color: #1e293b !important;
            color: #ffffff !important;
        }
        li[role="option"] {
            color: #ffffff !important;
            background-color: #1e293b !important;
        }
        li[role="option"]:hover {
            background-color: #334155 !important;
        }
        .stTextInput input:focus, .stNumberInput input:focus, div[data-baseweb="input"] input:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 2px rgba(59,130,246,0.35) !important;
            background-color: #1e293b !important;
        }

        /* ---- Buton Özelleştirmeleri (Örn: Çıkış Yap & Form Butonları) ---- */
        .stButton button, section[data-testid="stSidebar"] button {
            background-color: #1e293b !important;
            color: #f8fafc !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            transition: all 0.2s ease-in-out !important;
        }
        .stButton button p, section[data-testid="stSidebar"] button p, 
        section[data-testid="stSidebar"] button span {
            color: #f8fafc !important;
            font-weight: 700 !important;
        }
        .stButton button:hover, section[data-testid="stSidebar"] button:hover {
            background-color: #2563eb !important;
            color: #ffffff !important;
            border-color: #3b82f6 !important;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.45) !important;
        }
        .stButton button:hover p, section[data-testid="stSidebar"] button:hover p,
        section[data-testid="stSidebar"] button:hover span {
            color: #ffffff !important;
        }
        input:-webkit-autofill,
        input:-webkit-autofill:hover, 
        input:-webkit-autofill:focus {
            -webkit-text-fill-color: #ffffff !important;
            -webkit-box-shadow: 0 0 0px 1000px #1e293b inset !important;
            transition: background-color 5000s ease-in-out 0s;
        }
        
        /* B-Tree Kart Tasarımları */
        .btree-root-card {
            background: linear-gradient(135deg, #1e1b4b, #312e81);
            border: 1px solid #6366f1;
            padding: 16px; border-radius: 12px; margin-bottom: 16px;
        }
        .btree-station-card {
            background: #1e293b;
            border-left: 4px solid #3b82f6;
            padding: 12px 16px; margin: 8px 0; border-radius: 8px;
        }
        .btree-sensor-badge {
            display: inline-block; background: #0f172a; border: 1px solid #10b981;
            color: #34d399; padding: 6px 12px; border-radius: 8px; margin: 4px; font-size: 0.9rem;
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
    if st.sidebar.button("Çıkış Yap", use_container_width=True):
        st.session_state.authenticated = False
        st.query_params.clear()
        st.components.v1.html("<script>window.parent.localStorage.removeItem('smartcam_user_session');</script>", height=0)
        st.rerun()

    st.markdown("<h1>📡 SmartCam Telemetri ve Sensör İzleme Paneli</h1>", unsafe_allow_html=True)

    # Sekmeler: Admin vs Normal Kullanıcı
    is_admin = (st.session_state.role == "admin")
    
    if is_admin:
        tabs_list = ["📊 Canlı Telemetri & Hiyerarşi", "🌳 3 Katmanlı B-Tree İndeksi", "👑 Admin Yönetim Paneli"]
    else:
        tabs_list = ["📊 Canlı Telemetri & Hiyerarşi", "📩 İstasyon / Sensör Ekleme Talebi"]

    dash_tabs = st.tabs(tabs_list)

    # --- TAB 1: TELEMETRİ İZLEME (HERKESE AÇIK) ---
    with dash_tabs[0]:
        try:
            stations = requests.get(f"{API_BASE_URL}/stations", timeout=5).json()
        except Exception: stations = []

        st_opts = ["-- Lütfen Bir İstasyon Seçiniz --"] + [s["name"] for s in stations]
        st_map = {s["name"]: s for s in stations}
        sel_st_str = st.selectbox("1️⃣ Adım: İzlemek İstediğiniz İstasyon:", st_opts)

        if sel_st_str != "-- Lütfen Bir İstasyon Seçiniz --":
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
                    
                    # Zoom/Seçim revizyon anahtarı
                    ver_key = f"zoom_ver_{sel_st['id']}_{sel_sn['id']}"
                    if ver_key not in st.session_state:
                        st.session_state[ver_key] = 0

                    # Grafiğin üstüne başlık ve Türkçe "Grafiği Sıfırla" butonu koyuyoruz
                    c_title, c_rst = st.columns([4, 1.2])
                    with c_title:
                        st.markdown(f"#### 📈 {sel_st['name']} — {sel_sn['label']} Ölçüm Grafiği")
                    with c_rst:
                        if st.button("🔄 Grafiği Sıfırla", key=f"reset_btn_{sel_st['id']}_{sel_sn['id']}", help="Yakınlaştırmayı sıfırlar ve tam boyuta döner"):
                            st.session_state[ver_key] += 1
                            st.rerun()

                    fig = px.line(df, x="recorded_at", y="raw_value")
                    
                    # 📌 uirevision ve yatay-only (X ekseni) zoom kısıtlaması
                    fig.update_layout(
                        uirevision=f"sensor_{sel_st['id']}_{sel_sn['id']}_{st.session_state[ver_key]}",
                        xaxis=dict(title="Zaman (recorded_at)", fixedrange=False),
                        yaxis=dict(title=f"Ölçüm ({sel_sn['default_unit']})", fixedrange=True),
                        margin=dict(l=10, r=10, t=10, b=10)
                    )
                    
                    st.plotly_chart(
                        fig, 
                        use_container_width=True, 
                        key=f"telemetry_chart_{sel_st['id']}_{sel_sn['id']}"
                    )
                else:
                    st.info("ℹ️ Bu sensöre ait henüz ölçüm verisi yok.")

    # --- TAB 2 (ADMİN İÇİN B-TREE, USER İÇİN İSTEK FORMU) ---
    if is_admin:
        # --- ADMİN: 3-KATMANLI B-TREE İNDEKSİ ---
        with dash_tabs[1]:
            st.subheader("🌳 SmartCam 3-Katmanlı B-Tree Ağaç Yapısı")
            st.caption("Veriler Hiyerarşik Ağaç Yapısı (Katman 1: Root -> Katman 2: İstasyonlar -> Katman 3: Sensörler) ile indekslenmiştir.")
            try:
                btree_res = requests.get(f"{API_BASE_URL}/stations/btree", timeout=5).json()
                
                root_name = btree_res.get("data", {}).get("name", "SmartCam IoT Ana Sistem")
                st.markdown(f"""
                <div class="btree-root-card">
                    <h3 style="margin:0; color:#a5b4fc;">🌐 Katman 1 (Root Düğüm): {root_name}</h3>
                    <span style="color:#cbd5e1; font-size:0.9rem;">Sistem İndeks Ana Kökü — Tüm İstasyonlar Bu Düğüme Bağlıdır</span>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("#### 📡 Katman 2: İstasyon Düğümleri (Internal B-Tree Nodes)")
                stations_nodes = btree_res.get("children", [])
                
                if stations_nodes:
                    for st_node in stations_nodes:
                        st_data = st_node.get("data", {})
                        st_key = st_node.get("key", "")
                        sensors_nodes = st_node.get("children", [])
                        
                        with st.expander(f"📡 {st_data.get('name')} [{st_key}] — {len(sensors_nodes)} Bağlı Sensör", expanded=True):
                            st.write(f"**IP Adresi:** `{st_data.get('gsm_ip')}` | **IMEI:** `{st_data.get('imei')}`")
                            
                            st.markdown("##### 🔌 Katman 3: Sensör ve Veri Yaprak Düğümleri (Leaf Data Nodes):")
                            if sensors_nodes:
                                badge_html = ""
                                for sn_node in sensors_nodes:
                                    sn_data = sn_node.get("data", {})
                                    badge_html += f'<div class="btree-sensor-badge">🔌 {sn_data.get("label")} <b>({sn_data.get("unit")})</b></div>'
                                st.markdown(badge_html, unsafe_allow_html=True)
                            else:
                                st.info("Bu istasyona bağlı yaprak sensör bulunamadı.")
                else:
                    st.info("Ağaçta henüz kayıtlı istasyon düğümü yok.")

                st.divider()
                with st.expander("📄 Geliştiriciler İçin Ham B-Tree JSON Çıktısı"):
                    st.json(btree_res)

            except Exception as e:
                st.error(f"B-Tree indeksi yüklenemedi: {e}")

        # --- ADMİN: YÖNETİM PANELİ ---
        with dash_tabs[2]:
            st.subheader("👑 Admin Yönetim & İstasyon / Kullanıcı İşlemleri")
            
            sub_t1, sub_t2, sub_t3, sub_t4 = st.tabs(["⏳ Bekleyen Üyelik Başvuruları", "📩 Bekleyen Cihaz/Sensör Talepleri", "➕ İstasyon Ekle", "🔌 Sensör Ekle"])

            # 1. Bekleyen Kullanıcılar
            with sub_t1:
                try:
                    p_res = requests.get(f"{API_BASE_URL}/auth/pending-users", timeout=5)
                    if p_res.status_code == 200:
                        pending_users = p_res.json()
                        if pending_users:
                            for u in pending_users:
                                with st.expander(f"👤 {u.get('full_name')} (@{u.get('username')})"):
                                    st.write(f"**E-Posta:** {u.get('email')}")
                                    st.write(f"**Telefon:** {u.get('phone')}")
                                    ca, cr = st.columns(2)
                                    if ca.button("✅ Onayla", key=f"app_{u.get('id')}"):
                                        requests.post(f"{API_BASE_URL}/auth/user-action", json={"user_id": u.get("id"), "action": "approve"})
                                        st.success(f"{u.get('username')} onaylandı!")
                                        st.rerun()
                                    if cr.button("❌ Reddet", key=f"rej_{u.get('id')}"):
                                        requests.post(f"{API_BASE_URL}/auth/user-action", json={"user_id": u.get("id"), "action": "reject"})
                                        st.warning(f"{u.get('username')} reddedildi.")
                                        st.rerun()
                        else:
                            st.success("✅ Onay bekleyen yeni kullanıcı başvurusu yok.")
                except Exception as e:
                    st.error(f"Başvurular çekilemedi: {e}")

            # 2. Bekleyen Cihaz/Sensör Talepleri
            with sub_t2:
                try:
                    req_res = requests.get(f"{API_BASE_URL}/stations/requests/pending", timeout=5)
                    if req_res.status_code == 200:
                        p_reqs = req_res.json()
                        if p_reqs:
                            for r_item in p_reqs:
                                with st.expander(f"📩 {r_item.get('title')} (Talep Eden: @{r_item.get('user_username')})"):
                                    st.write(f"**Tip:** `{r_item.get('request_type').upper()}`")
                                    st.write(f"**Detaylar:** `{r_item.get('details')}`")
                                    ca, cr = st.columns(2)
                                    if ca.button("✅ Onayla ve Ekle", key=f"app_req_{r_item.get('id')}"):
                                        requests.post(f"{API_BASE_URL}/stations/requests/action", json={"request_id": r_item.get("id"), "action": "approve"})
                                        st.success("Talep onaylandı ve eklendi!")
                                        st.rerun()
                                    if cr.button("❌ Reddet", key=f"rej_req_{r_item.get('id')}"):
                                        requests.post(f"{API_BASE_URL}/stations/requests/action", json={"request_id": r_item.get("id"), "action": "reject"})
                                        st.warning("Talep reddedildi.")
                                        st.rerun()
                        else:
                            st.success("✅ Bekleyen cihaz/sensör talebi yok.")
                except Exception as e:
                    st.error(f"Talepler yüklenemedi: {e}")

            # 3. Doğrudan İstasyon Ekle
            with sub_t3:
                with st.form("new_station_form"):
                    st_name = st.text_input("İstasyon Adı", placeholder="Örn: İstasyon-3 (Güney Havzası)")
                    st_ip = st.text_input("GSM IP Adresi", placeholder="Örn: 192.168.1.105")
                    st_imei = st.text_input("IMEI Numarası", placeholder="Örn: 864920049281005")
                    if st.form_submit_button("➕ İstasyonu Kaydet", type="primary"):
                        if st_name:
                            try:
                                r = requests.post(f"{API_BASE_URL}/stations", json={"name": st_name, "gsm_ip": st_ip, "imei": st_imei}, timeout=5)
                                if r.status_code == 200:
                                    st.success(f"✅ [{st_name}] istasyonu başarıyla eklendi!")
                                    st.rerun()
                                else: st.error("İstasyon eklenemedi.")
                            except Exception as e: st.error(f"Hata: {e}")
                        else: st.warning("İstasyon adı zorunludur.")

            # 4. Doğrudan Sensör Ekle
            with sub_t4:
                try:
                    all_st = requests.get(f"{API_BASE_URL}/stations", timeout=5).json()
                except Exception: all_st = []

                if all_st:
                    with st.form("new_sensor_form"):
                        target_st_name = st.selectbox("Sensörün Ekleneceği İstasyon", [s["name"] for s in all_st])
                        target_st_id = next((s["id"] for s in all_st if s["name"] == target_st_name), None)
                        sn_label = st.text_input("Sensör Adı / Etiketi", placeholder="Örn: PH Değeri")
                        sn_type = st.selectbox("Sensör Tipi", ["temp", "humidity", "pressure", "wind_speed", "rainfall", "ph", "generic"])
                        sn_unit = st.text_input("Ölçüm Birimi", placeholder="Örn: pH, °C, bar")
                        
                        if st.form_submit_button("➕ Sensörü Kaydet", type="primary"):
                            if target_st_id and sn_label and sn_unit:
                                try:
                                    r = requests.post(f"{API_BASE_URL}/stations/{target_st_id}/sensors", json={
                                        "label": sn_label, "sensor_type": sn_type, "default_unit": sn_unit
                                    }, timeout=5)
                                    if r.status_code == 200:
                                        st.success(f"✅ Sensör [{target_st_name}] istasyonuna eklendi!")
                                        st.rerun()
                                    else: st.error("Sensör eklenemedi.")
                                except Exception as e: st.error(f"Hata: {e}")
                            else: st.warning("Tüm alanları doldurunuz.")
                else:
                    st.info("Sensör ekleyebilmek için önce en az 1 istasyon tanımlanmalıdır.")

    else:
        # --- STANDART KULLANICI (USER): İSTASYON / SENSÖR EKLEME TALEBİ PANELİ ---
        with dash_tabs[1]:
            st.subheader("📩 Yeni İstasyon veya Sensör Ekleme Talebi Gönder")
            st.caption("Gönderdiğiniz talepler Admin onayına sunulacak ve onaylandığında sisteme eklenecektir.")
            
            req_type_choice = st.radio("Talep Türü Seçiniz:", ["📡 İstasyon Ekleme Talebi", "🔌 Sensör Ekleme Talebi"])
            
            if req_type_choice == "📡 İstasyon Ekleme Talebi":
                with st.form("user_req_station_form"):
                    u_st_name = st.text_input("Talep Edilen İstasyon Adı", placeholder="Örn: İstasyon-4 (Kuzey Barajı)")
                    u_st_ip = st.text_input("GSM IP Adresi (İsteğe Bağlı)", placeholder="192.168.1.110")
                    u_st_imei = st.text_input("IMEI No (İsteğe Bağlı)", placeholder="864920049281099")
                    if st.form_submit_button("📩 Talebi Admin'e Gönder", type="primary"):
                        if u_st_name:
                            try:
                                r = requests.post(f"{API_BASE_URL}/stations/requests", json={
                                    "username": st.session_state.username,
                                    "request_type": "station",
                                    "title": f"Yeni İstasyon Talebi: {u_st_name}",
                                    "details": {"name": u_st_name, "gsm_ip": u_st_ip, "imei": u_st_imei}
                                }, timeout=5)
                                if r.status_code == 200:
                                    st.success("✅ İstasyon ekleme talebiniz Admin onayına başarıyla iletildi!")
                                else: st.error("Talep iletilemedi.")
                            except Exception as e: st.error(f"Hata: {e}")
                        else: st.warning("İstasyon adı girmek zorunludur.")
            
            else:
                try:
                    all_st_user = requests.get(f"{API_BASE_URL}/stations", timeout=5).json()
                except Exception: all_st_user = []

                if all_st_user:
                    with st.form("user_req_sensor_form"):
                        u_st_target = st.selectbox("Sensörün Ekleneceği İstasyonu Seçiniz", [s["name"] for s in all_st_user])
                        u_st_target_id = next((s["id"] for s in all_st_user if s["name"] == u_st_target), None)
                        u_sn_label = st.text_input("Sensör Adı / Etiketi", placeholder="Örn: Su Debisi")
                        u_sn_type = st.selectbox("Sensör Tipi", ["temp", "humidity", "pressure", "wind_speed", "rainfall", "ph", "generic"])
                        u_sn_unit = st.text_input("Ölçüm Birimi", placeholder="Örn: L/s, m3/h")
                        
                        if st.form_submit_button("📩 Talebi Admin'e Gönder", type="primary"):
                            if u_st_target_id and u_sn_label and u_sn_unit:
                                try:
                                    r = requests.post(f"{API_BASE_URL}/stations/requests", json={
                                        "username": st.session_state.username,
                                        "request_type": "sensor",
                                        "title": f"Yeni Sensör Talebi ({u_st_target}): {u_sn_label}",
                                        "details": {"station_id": u_st_target_id, "label": u_sn_label, "sensor_type": u_sn_type, "default_unit": u_sn_unit}
                                    }, timeout=5)
                                    if r.status_code == 200:
                                        st.success("✅ Sensör ekleme talebiniz Admin onayına başarıyla iletildi!")
                                    else: st.error("Talep iletilemedi.")
                                except Exception as e: st.error(f"Hata: {e}")
                            else: st.warning("Lütfen tüm alanları doldurunuz.")
                else:
                    st.info("Sensör talebi yapabilmek için sistemde en az 1 istasyon bulunmalıdır.")

def main():
    inject_custom_css()
    check_persistent_session()
    if not st.session_state.authenticated: render_auth_page()
    else: render_dashboard()

if __name__ == "__main__":
    main()
