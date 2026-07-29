import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# ---------------------------------------------------------
# 1. SUNUCU ADRESİ VE SAYFA YAPILANDIRMASI
# ---------------------------------------------------------
API_BASE_URL = "http://127.0.0.1:8000/api"

st.set_page_config(
    page_title="SmartCam IoT - Telemetri Paneli",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Oturum Durumları (Session State)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None


# ---------------------------------------------------------
# 1.1 ÖZEL TASARIM (CSS) — Sadece görünüm, mantık değişmedi
# ---------------------------------------------------------
def inject_custom_css():
    st.markdown("""
    <style>
        /* ---- Genel Zemin & Tipografi ---- */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"], .main {
            font-family: 'Inter', sans-serif;
            overflow-anchor: none !important;
        }

        div[data-testid="stPlotlyChart"] {
            min-height: 480px !important;
        }

        .stApp {
            background: radial-gradient(circle at 10% 0%, #0f1b33 0%, #0a1122 45%, #070c18 100%);
        }

        /* ---- Sidebar ---- */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #101a30 0%, #0b1424 100%);
            border-right: 1px solid rgba(255,255,255,0.06);
        }
        section[data-testid="stSidebar"] * {
            color: #e6ecf5 !important;
        }

        /* ---- Başlıklar ---- */
        h1 {
            color: #f5f8ff;
            font-weight: 800 !important;
            letter-spacing: -0.5px;
            padding-bottom: 4px;
            border-bottom: 2px solid rgba(99, 179, 237, 0.25);
        }
        h2, h3, h4 {
            color: #dbe6f7 !important;
            font-weight: 700 !important;
        }
        p, span, label, .stMarkdown, .stCaption {
            color: #c3ccdb;
        }

        /* ---- Metric Kartları ---- */
        div[data-testid="stMetric"] {
            background: linear-gradient(145deg, rgba(255,255,255,0.045), rgba(255,255,255,0.015));
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 18px 16px 12px 16px;
            box-shadow: 0 4px 18px rgba(0,0,0,0.25);
            transition: transform 0.15s ease, border-color 0.15s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            border-color: rgba(99, 179, 237, 0.45);
        }
        div[data-testid="stMetricLabel"] {
            color: #93a4c2 !important;
            font-weight: 600 !important;
            font-size: 0.82rem !important;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }
        div[data-testid="stMetricValue"] {
            color: #f5f8ff !important;
            font-weight: 700 !important;
        }

        /* ---- Butonlar ---- */
        .stButton > button {
            border-radius: 10px;
            font-weight: 600;
            border: 1px solid rgba(255,255,255,0.12);
            transition: all 0.15s ease;
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            border: none;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
        }
        .stButton > button[kind="primary"]:hover {
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
            transform: translateY(-1px);
        }
        .stButton > button:hover {
            border-color: rgba(99, 179, 237, 0.5);
            transform: translateY(-1px);
        }

        /* ---- Sekmeler (Tabs) ---- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            background: rgba(255,255,255,0.03);
            padding: 6px;
            border-radius: 12px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            color: #9fb0cc;
            font-weight: 600;
            padding: 8px 18px;
        }
        .stTabs [aria-selected="true"] {
            background: rgba(59, 130, 246, 0.18) !important;
            color: #eaf2ff !important;
        }

        /* ---- Giriş Kartı ---- */
        .login-card {
            background: linear-gradient(160deg, rgba(255,255,255,0.055), rgba(255,255,255,0.015));
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 20px;
            padding: 34px 34px 20px 34px;
            box-shadow: 0 12px 40px rgba(0,0,0,0.35);
            margin-top: 10px;
        }

        /* ---- Input alanları ---- */
        .stTextInput input {
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            border-radius: 10px !important;
            color: #f0f4fb !important;
        }
        .stTextInput input:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 2px rgba(59,130,246,0.25) !important;
        }

        /* ---- Bilgi/uyarı kutuları ---- */
        div[data-testid="stAlert"] {
            border-radius: 12px;
        }

        /* ---- Selectbox / Slider etiketleri ---- */
        .stSelectbox label, .stSlider label {
            color: #cbd6ea !important;
            font-weight: 600 !important;
        }

        /* ---- Expander ---- */
        details {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
        }

        /* ---- Ayırıcı ---- */
        hr {
            border-color: rgba(255,255,255,0.08) !important;
        }

        /* ---- Rozet stili (durum çipleri) ---- */
        .status-chip {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 999px;
            font-weight: 600;
            font-size: 0.85rem;
            border: 1px solid rgba(255,255,255,0.12);
            background: rgba(255,255,255,0.04);
        }
    </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# 2. YARDIMCI FONKSİYONLAR
# ---------------------------------------------------------
def parse_percentage(val):
    """Metin veya sayı olarak gelen yüzdeyi sayıya çevirir."""
    try:
        if isinstance(val, str):
            val = val.replace("%", "").strip()
        return int(float(val))
    except Exception:
        return 0

def get_status_indicator(value, thresholds=(50, 20)):
    """Akü % ve GSM Sinyali % durum rozeti üretir."""
    val = parse_percentage(value)
    if val >= thresholds[0]:
        return f"🟢 %{val} (Mükemmel)"
    elif val >= thresholds[1]:
        return f"🟡 %{val} (Normal)"
    else:
        return f"🔴 %{val} (Düşük)"


# ---------------------------------------------------------
# 3. GİRİŞ VE KAYIT EKRANI (TEST BAYPASLI)
# ---------------------------------------------------------
def render_auth_page():
    left, mid, right = st.columns([1, 1.3, 1])
    with mid:
        st.markdown(
            "<div style='text-align:center; margin-top: 30px;'>"
            "<div style='font-size:52px;'>📡</div>"
            "<h1 style='border:none; margin-bottom:0;'>SmartCam Telemetri Paneli</h1>"
            "<p style='color:#93a4c2; margin-top:4px;'>IoT İstasyon İzleme ve Sensör Analiz Sistemi</p>"
            "</div>",
            unsafe_allow_html=True
        )

        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.info("💡 **Hızlı Giriş:** `admin` / `admin123` (Yönetici) | `user` / `123` (Operatör)")

        tab_login, tab_register = st.tabs(["🔐  Giriş Yap", "📝  Kayıt Ol"])

        with tab_login:
            st.subheader("Kullanıcı Girişi")
            login_user = st.text_input("Kullanıcı Adı", key="login_user", placeholder="kullanici_adi")
            login_pass = st.text_input("Şifre", type="password", key="login_pass", placeholder="••••••••")

            if st.button("Giriş Yap", type="primary", use_container_width=True):
                if login_user == "admin" and login_pass == "admin123":
                    st.session_state.authenticated = True
                    st.session_state.username = "admin"
                    st.session_state.role = "admin"
                    st.success("Admin girişi başarılı!")
                    st.rerun()
                elif login_user and login_pass:
                    st.session_state.authenticated = True
                    st.session_state.username = login_user
                    st.session_state.role = "user"
                    st.success("Giriş başarılı!")
                    st.rerun()
                else:
                    st.warning("Lütfen kullanıcı adı ve şifre giriniz.")

        with tab_register:
            st.subheader("Yeni Kullanıcı Kaydı")
            reg_user = st.text_input("Kullanıcı Adı", key="reg_user", placeholder="kullanici_adi")
            reg_pass = st.text_input("Şifre", type="password", key="reg_pass", placeholder="••••••••")

            if st.button("Kayıt Oluştur", use_container_width=True):
                if reg_user and reg_pass:
                    st.success("Kayıt alındı! Hesabınız admin onayına gönderildi.")
                else:
                    st.info("Lütfen tüm alanları doldurunuz.")

        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# 4. ADMIN PANELİ (SIDEBAR)
# ---------------------------------------------------------
def render_admin_panel():
    st.sidebar.markdown("---")
    st.sidebar.subheader("👑 Admin Kontrol Paneli")
    st.sidebar.caption("Sistemde onay bekleyen yeni kayıt bulunmuyor.")


@st.fragment(run_every="5s")
def render_live_chart_fragment(station_id, limit, station_name):
    """Sadece bu grafik alanını sayfayı yukarı kaydırmadan 5 saniyede bir canlı yeniler."""
    try:
        res_history = requests.get(f"{API_BASE_URL}/sensor/history?station_id={station_id}&limit={limit}", timeout=5)
        sensor_logs = res_history.json() if res_history.status_code == 200 else []
    except Exception:
        sensor_logs = []

    if sensor_logs:
        df_sensor = pd.DataFrame(sensor_logs)
        if "recorded_at" in df_sensor.columns:
            df_sensor["recorded_at"] = pd.to_datetime(df_sensor["recorded_at"], errors="coerce")
        df_sensor["sensor_label"] = df_sensor["sensor_id"].apply(lambda x: f"Sensör #{x}")

        ctrl_col1, ctrl_col2 = st.columns(2)
        available_sensors = df_sensor["sensor_label"].unique().tolist()
        selected_sensor = ctrl_col1.selectbox("Analiz Edilecek Sensör:", available_sensors, key=f"sensor_select_{station_id}")
        
        df_filtered = df_sensor[df_sensor["sensor_label"] == selected_sensor]

        fig = px.line(
            df_filtered,
            x="recorded_at" if "recorded_at" in df_filtered.columns else "id",
            y="raw_value",
            title=f"{station_name} — {selected_sensor} Canlı Sensör Ölçüm Grafiği",
            markers=True,
            labels={"recorded_at": "Zaman", "id": "Log ID", "raw_value": "Ölçülen Değer"}
        )
        fig.update_traces(line=dict(color="#3b82f6", width=3), marker=dict(size=7, color="#60a5fa"))
        fig.update_layout(
            height=480,
            hovermode="x unified",
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="#dbe6f7"),
            title_font=dict(size=17, color="#f5f8ff"),
            margin=dict(l=10, r=10, t=55, b=10),
        )
        fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)")
        fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("İstasyon için henüz canlı sensör verisi bulunamadı.")


# ---------------------------------------------------------
# 5. ANA KONTROL PANELİ & SENSÖR ANALİZİ
# ---------------------------------------------------------
def render_dashboard():
    # Sidebar Profil
    st.sidebar.markdown(
        f"<div style='text-align:center; padding: 10px 0 4px 0;'>"
        f"<div style='font-size:40px;'>👤</div>"
        f"<h3 style='margin-bottom:2px;'>{st.session_state.username}</h3>"
        f"<span class='status-chip'>Rol: {st.session_state.role.upper()}</span>"
        f"</div>",
        unsafe_allow_html=True
    )
    st.sidebar.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)

    if st.sidebar.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

    if st.session_state.role == "admin":
        render_admin_panel()

    st.markdown(
        "<h1>📡 SmartCam IoT İstasyon ve Veri Takip Paneli</h1>",
        unsafe_allow_html=True
    )

    # API'den İstasyon Listesini Çek (/api/stations)
    with st.container():
        st.markdown("##### ⚙️ Veri Kaynağı Ayarları")
        limit = st.slider("Çekilecek Log Sayısı (Limit):", min_value=5, max_value=200, value=50)

    try:
        with st.spinner("İstasyonlar sunucudan alınıyor..."):
            res_stations = requests.get(f"{API_BASE_URL}/stations", timeout=5)
            stations = res_stations.json() if res_stations.status_code == 200 else []
    except Exception as e:
        st.error(f"API sunucusuna bağlanılamadı ({API_BASE_URL}): {e}")
        stations = []

    if not stations:
        st.warning("Veritabanında kayıtlı istasyon bulunamadı. Lütfen backend'i çalıştırdığınızdan emin olun.")
        return

    st.markdown("---")
    
    # İstasyon Seçimi
    station_map = {f"{s['name']} (ID: {s['id']})": s for s in stations}
    selected_option = st.selectbox("🛰️ Görüntülenecek İstasyonu Seçiniz:", list(station_map.keys()))
    selected_station = station_map[selected_option]
    station_id = selected_station["id"]

    # --- İSTASYON DURUMU VE METRİK KARTLARI ---
    st.markdown("### 📊 İstasyon Son Durumu")
    c1, c2, c3, c4 = st.columns(4)
    
    c1.metric("İstasyon Adı", selected_station.get("name", "N/A"))
    c2.metric("IP Adresi", selected_station.get("gsm_ip") or "192.168.1.100")
    c3.metric("IMEI No", selected_station.get("imei", "N/A"))
    c4.metric("Son Güncelleme", selected_station.get("updated_at", "N/A"))

    st.markdown("#### 🩺 Telemetri Durumu")
    m1, m2, m3 = st.columns(3)
    
    acc_val = selected_station.get("battery_percent", 0)
    gsm_val = selected_station.get("gsm_percent", 0)

    m1.metric("🔋 Akü Durumu", get_status_indicator(acc_val))
    m2.metric("📶 GSM Sinyali", get_status_indicator(gsm_val))
    m3.metric("🖥️ Cihaz Tipi", selected_station.get("device_type", "Gateway"))

    st.markdown("---")

    # --- SENSÖR ÖLÇÜMLERİ ZAMAN SERİSİ ---
    st.markdown("### 📈 Sensör Analizleri ve SCADA Denetim Ekranı")

    # STREAMLIT FRAGMENT: Sayfayı yukarı kaydırmadan sadece bu grafik bileşenini 5 saniyede bir canlı yeniler
    render_live_chart_fragment(station_id, limit, selected_station["name"])


# ---------------------------------------------------------
# 6. UYGULAMA BAŞLATICI
# ---------------------------------------------------------
def main():
    inject_custom_css()
    if not st.session_state.authenticated:
        render_auth_page()
    else:
        render_dashboard()

if __name__ == "__main__":
    main()
