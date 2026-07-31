import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, time

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
# 1.1 ÖZEL TASARIM (CSS)
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
        .stButton > button, .stFormSubmitButton > button {
            border-radius: 10px;
            font-weight: 600;
            border: 1px solid rgba(255,255,255,0.12);
            transition: all 0.15s ease;
            width: 100% !important;
        }
        .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            border: none;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
        }
        .stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
            transform: translateY(-1px);
        }
        .stButton > button:hover, .stFormSubmitButton > button:hover {
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
# 3. GİRİŞ VE KAYIT EKRANI
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

        tab_login, tab_register = st.tabs(["🔐  Giriş Yap", "📝  Kayıt Ol"])

        with tab_login:
            with st.form("login_form", clear_on_submit=False):
                st.subheader("Kullanıcı Girişi")
                login_user = st.text_input("Kullanıcı Adı / E-Posta / Telefon / Ad Soyad", key="login_user", placeholder="kullanıcı adı, e-posta veya telefon")
                login_pass = st.text_input("Şifre", type="password", key="login_pass", placeholder="••••••••")
                
                submitted = st.form_submit_button("Giriş Yap", type="primary")

                if submitted:
                    if not login_user or not login_pass:
                        st.warning("Lütfen kullanıcı bilgisi ve şifre alanlarını doldurunuz.")
                    else:
                        try:
                            res = requests.post(
                                f"{API_BASE_URL}/auth/login",
                                json={"username": login_user, "password": login_pass},
                                timeout=5
                            )
                            if res.status_code == 200:
                                data = res.json()
                                st.session_state.authenticated = True
                                st.session_state.username = data.get("username", login_user)
                                st.session_state.role = data.get("role", "user")
                                st.success("Giriş başarılı!")
                                st.rerun()
                            elif res.status_code == 403:
                                st.error("❌ Hesabınız henüz yönetici tarafından onaylanmamış.")
                            else:
                                st.error("❌ Hatalı kullanıcı adı veya şifre!")
                        except requests.exceptions.ConnectionError:
                            st.error("❌ API sunucusuna bağlanılamadı! Lütfen backend'in çalıştığından emin olun.")
                        except Exception as e:
                            st.error(f"Giriş sırasında bir hata oluştu: {e}")

        with tab_register:
            with st.form("register_form", clear_on_submit=False):
                st.subheader("Yeni Kullanıcı Kaydı")
                reg_fullname = st.text_input("Ad Soyad", key="reg_fullname", placeholder="Ahmet Yılmaz")
                reg_user = st.text_input("Kullanıcı Adı", key="reg_user", placeholder="kullanici_adi")
                
                col_em, col_ph = st.columns(2)
                with col_em:
                    reg_email = st.text_input("E-Posta Adresi", key="reg_email", placeholder="ornek@email.com")
                with col_ph:
                    reg_phone = st.text_input("Telefon Numarası", key="reg_phone", placeholder="0555 123 4567")

                reg_pass = st.text_input("Şifre", type="password", key="reg_pass", placeholder="En az 6 karakter, harf ve rakam (Örn: Xk9#mP2)")
                reg_pass_confirm = st.text_input("Şifre Tekrar", type="password", key="reg_pass_confirm", placeholder="••••••••")
                
                with st.expander("📄 KVKK Aydınlatma Metni"):
                    st.caption(
                        "SmartCam Telemetri Sistemi kapsamında kişisel verileriniz (Ad Soyad, E-Posta, Telefon) "
                        "6698 sayılı KVKK gereğince yalnızca sistem erişim yetkilendirmesi, onay süreçleri ve güvenlik "
                        "doğrulaması amacıyla işlenmektedir. Verileriniz 3. şahıslarla paylaşılmaz."
                    )

                reg_kvkk = st.checkbox("KVKK Aydınlatma Metni'ni okudum ve kabul ediyorum.", key="reg_kvkk")
                
                st.caption("⚠️ Şifre 'ad123' gibi basit olmamalı; en az 6 karakter, harf ve rakam içermelidir.")
                reg_submitted = st.form_submit_button("Kayıt Başvurusu Yap", type="primary")

                if reg_submitted:
                    if not (reg_fullname and reg_user and reg_email and reg_phone and reg_pass and reg_pass_confirm):
                        st.warning("⚠️ Lütfen tüm alanları eksiksiz doldurunuz.")
                    elif reg_pass != reg_pass_confirm:
                        st.error("❌ Şifreler birbiriyle eşleşmiyor!")
                    elif not reg_kvkk:
                        st.warning("⚠️ Kayıt oluşturabilmek için KVKK Aydınlatma Metni'ni kabul etmelisiniz.")
                    else:
                        try:
                            res = requests.post(
                                f"{API_BASE_URL}/auth/register",
                                json={
                                    "username": reg_user,
                                    "password": reg_pass,
                                    "full_name": reg_fullname,
                                    "email": reg_email,
                                    "phone": reg_phone,
                                    "kvkk_approved": reg_kvkk
                                },
                                timeout=5
                            )
                            if res.status_code in [200, 201]:
                                st.success("✅ Kayıt başvurunuz alındı! Hesabınız Admin onayına gönderildi.")
                            else:
                                err_msg = res.json().get("detail", "Kayıt oluşturulamadı.")
                                st.error(f"❌ {err_msg}")
                        except requests.exceptions.ConnectionError:
                            st.error("❌ API sunucusuna bağlanılamadı!")
                        except Exception as e:
                            st.error(f"Kayıt sırasında bir hata oluştu: {e}")

        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# 4. ADMIN PANELİ (SIDEBAR)
# ---------------------------------------------------------
def render_admin_panel():
    st.sidebar.markdown("---")
    st.sidebar.subheader("👑 Onay Bekleyen Kullanıcılar")
    
    try:
        res = requests.get(f"{API_BASE_URL}/admin/pending-users", timeout=5)
        if res.status_code == 200:
            pending_users = res.json()
            
            if not pending_users:
                st.sidebar.caption("Onay bekleyen kullanıcı bulunmuyor.")
            else:
                for user in pending_users:
                    u_id = user.get("id") or user.get("user_id")
                    u_name = user.get("username") or user.get("name") or f"Kullanıcı #{u_id}"
                    full_name = user.get("full_name") or ""
                    email = user.get("email") or ""
                    phone = user.get("phone") or ""
                    
                    st.sidebar.markdown(f"**👤 {u_name}** ({full_name}) `ID: {u_id}`")
                    if email or phone:
                        st.sidebar.caption(f"📧 {email} | 📞 {phone}")

                    col_btn1, col_btn2 = st.sidebar.columns(2)
                    
                    if col_btn1.button("✅ Onayla", key=f"app_{u_id}", use_container_width=True):
                        requests.post(
                            f"{API_BASE_URL}/admin/approve-user",
                            json={"user_id": u_id, "action": "approve"}
                        )
                        st.toast(f"{u_name} ({full_name}) başarıyla onaylandı!", icon="✅")
                        st.rerun()
                        
                    if col_btn2.button("❌ Reddet", key=f"rej_{u_id}", use_container_width=True):
                        requests.post(
                            f"{API_BASE_URL}/admin/approve-user",
                            json={"user_id": u_id, "action": "reject"}
                        )
                        st.toast(f"{u_name} reddedildi!", icon="❌")
                        st.rerun()
                    st.sidebar.markdown("---")
        else:
            st.sidebar.caption("Onay listesi sunucudan alınamadı.")
    except Exception:
        st.sidebar.error("Backend bağlantısı sağlanamadı.")


# ---------------------------------------------------------
# 4.1 CANLI GRAFİK ALANI
# ---------------------------------------------------------
def render_live_chart_section(station_id, limit, station_name):
    """Grafik ve filtreleri oluşturur. Filtre açıksa fragment yenilemesi tamamen devre dışı kalır."""
    
    use_date_filter = st.toggle(
        "🕒 Tarih/Saat Aralık Filtresi Uygula", 
        value=False, 
        key=f"toggle_filter_{station_id}"
    )

    refresh_interval = None if use_date_filter else "5s"

    @st.fragment(run_every=refresh_interval)
    def _draw_chart(is_filtered):
        start_dt = None
        end_dt = None

        if is_filtered:
            d_col1, t_col1, d_col2, t_col2 = st.columns(4)
            with d_col1:
                start_date = st.date_input("Başlangıç Tarihi", key=f"start_date_{station_id}")
            with t_col1:
                start_time = st.time_input("Başlangıç Saati", value=time(0, 0), key=f"start_time_{station_id}")
            with d_col2:
                end_date = st.date_input("Bitiş Tarihi", key=f"end_date_{station_id}")
            with t_col2:
                end_time = st.time_input("Bitiş Saati", value=time(23, 59), key=f"end_time_{station_id}")

            start_dt = datetime.combine(start_date, start_time)
            end_dt = datetime.combine(end_date, end_time)

        try:
            url = f"{API_BASE_URL}/sensor/history?station_id={station_id}&limit={limit}"
            if is_filtered and start_dt and end_dt:
                url += f"&start_time={start_dt.isoformat()}&end_time={end_dt.isoformat()}"
                
            res_history = requests.get(url, timeout=5)
            sensor_logs = res_history.json() if res_history.status_code == 200 else []
        except Exception:
            sensor_logs = []

        if sensor_logs:
            df_sensor = pd.DataFrame(sensor_logs)
            if "recorded_at" in df_sensor.columns:
                df_sensor["recorded_at"] = pd.to_datetime(df_sensor["recorded_at"], errors="coerce")
            df_sensor["sensor_label"] = df_sensor["sensor_id"].apply(lambda x: f"Sensör #{x}")

            ctrl_col1, _ = st.columns(2)
            available_sensors = df_sensor["sensor_label"].unique().tolist()
            selected_sensor = ctrl_col1.selectbox(
                "Analiz Edilecek Sensör:", 
                available_sensors, 
                key=f"sensor_select_{station_id}"
            )
            
            df_filtered = df_sensor[df_sensor["sensor_label"] == selected_sensor]

            if is_filtered and start_dt and end_dt and "recorded_at" in df_filtered.columns:
                df_filtered = df_filtered[
                    (df_filtered["recorded_at"] >= start_dt) & 
                    (df_filtered["recorded_at"] <= end_dt)
                ]

            chart_title = f"{station_name} — {selected_sensor} Canlı Sensör Ölçüm Grafiği"
            if is_filtered:
                chart_title = f"{station_name} — {selected_sensor} Tarih Aralığı Ölçümleri"

            fig = px.line(
                df_filtered,
                x="recorded_at" if "recorded_at" in df_filtered.columns else "id",
                y="raw_value",
                title=chart_title,
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
            st.info("Seçilen istasyon veya tarih aralığı için henüz sensör verisi bulunamadı.")

    _draw_chart(use_date_filter)


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

    render_live_chart_section(station_id, limit, selected_station["name"])


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
