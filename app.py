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
_DEFAULT_STATE = {
    "authenticated": False,
    "username": None,
    "role": None,
    "user_id": None,
    "page": "istasyonlar",
    "selected_station_id": None,
    "selected_user_id": None,
}
for _key, _val in _DEFAULT_STATE.items():
    if _key not in st.session_state:
        st.session_state[_key] = _val

# -----------------------------------------------------------------
# Menüler (ilerde yeni menü eklemek için sadece bu listeye ekleme
# yapmak yeterli olur — sidebar otomatik olarak günceller)
# -----------------------------------------------------------------
MENU_ITEMS = [
    {"key": "istasyonlar", "label": "🛰️  İstasyonlar", "roles": None},
    {"key": "hesaplar", "label": "👥  Hesaplar", "roles": ["admin"]},
]


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

        /* ---- Sidebar navigasyon butonları (SOLA YASLI) ---- */
        section[data-testid="stSidebar"] .stButton > button {
            text-align: left !important;
            justify-content: flex-start !important;
            background: transparent;
            border: 1px solid transparent;
            padding-left: 14px !important;
        }
        section[data-testid="stSidebar"] .stButton > button p {
            text-align: left !important;
        }
        section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
            background: rgba(255,255,255,0.05);
            border-color: rgba(255,255,255,0.1);
        }
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: rgba(59, 130, 246, 0.18) !important;
            box-shadow: none;
            border: 1px solid rgba(99, 179, 237, 0.4);
            color: #eaf2ff !important;
        }

        /* ---- Üst bar kullanıcı popover butonu ---- */
        div[data-testid="stPopover"] > div > button {
            border-radius: 999px !important;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.12) !important;
            font-weight: 600;
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
        .stTextInput input, .stNumberInput input {
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            border-radius: 10px !important;
            color: #f0f4fb !important;
        }
        .stTextInput input:focus, .stNumberInput input:focus {
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

        /* ---- Konteynerli kartlar ---- */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 14px !important;
            border-color: rgba(255,255,255,0.08) !important;
            background: rgba(255,255,255,0.02);
        }

        /* ---- Tablolar (dataframe) ---- */
        div[data-testid="stDataFrame"] {
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.08);
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

        /* ---- Cihaz/İstasyon Listesi Tablosu ---- */
        .device-table-card {
            background: linear-gradient(160deg, rgba(255,255,255,0.035), rgba(255,255,255,0.01));
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 4px 18px;
            margin-bottom: 14px;
        }
        .device-table-header {
            display: flex;
            padding: 12px 4px 10px 4px;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        .device-table-header span {
            color: #7c8aa8 !important;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        div[data-testid="stHorizontalBlock"].device-row-block {
            border-bottom: 1px solid rgba(255,255,255,0.06);
            padding-top: 10px;
            padding-bottom: 10px;
            align-items: center;
        }
        .dev-name {
            color: #f0f4fb !important;
            font-weight: 700;
            font-size: 0.95rem;
            margin-bottom: 2px;
        }
        .dev-sub {
            color: #7c8aa8 !important;
            font-size: 0.78rem;
        }
        .cat-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 0.76rem;
            font-weight: 600;
            white-space: nowrap;
        }
        .conn-wrap { display: flex; flex-direction: column; gap: 2px; margin-top: 6px; }
        .conn-status { font-size: 0.8rem; font-weight: 600; white-space: nowrap; }
        .conn-ip { font-size: 0.76rem; color: #7c8aa8 !important; white-space: nowrap; }
        .metric-col-wrap { margin-top: 9px; }
        .bar-wrap { display: flex; align-items: center; gap: 10px; white-space: nowrap; }
        .bar-track {
            width: 46px;
            height: 7px;
            background: rgba(255,255,255,0.08);
            border-radius: 4px;
            overflow: hidden;
            flex-shrink: 0;
        }
        .bar-fill { height: 100%; border-radius: 4px; }
        .bar-pct { font-size: 0.78rem; color: #c3ccdb !important; font-weight: 600; min-width: 32px; }
        .sensor-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            border-radius: 8px;
            background: rgba(59,130,246,0.14);
            border: 1px solid rgba(99,179,237,0.3);
            color: #93c5fd !important;
            font-weight: 700;
            font-size: 0.82rem;
        }
        .user-avatar {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 34px;
            height: 34px;
            border-radius: 999px;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            color: #ffffff !important;
            font-weight: 700;
            font-size: 0.85rem;
            flex-shrink: 0;
        }
        .user-row-wrap { display: flex; align-items: center; gap: 10px; }
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


def get_user_status_chip(status_value):
    mapping = {
        "approved": "🟢 Onaylı",
        "pending": "🟡 Onay Bekliyor",
        "rejected": "🔴 Reddedildi",
    }
    return mapping.get(status_value, status_value or "-")


def go_to(page, **kwargs):
    """Sayfa yönlendirme yardımcısı."""
    st.session_state.page = page
    for k, v in kwargs.items():
        st.session_state[k] = v
    st.rerun()


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

        tab_login, tab_register = st.tabs(["🔐   Giriş Yap", "📝   Kayıt Ol"])

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
                                st.session_state.user_id = data.get("user_id")
                                st.session_state.page = "istasyonlar"
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
# 4. ÜST BAR (Logo + sağ üstte kullanıcı dropdown'ı)
# ---------------------------------------------------------
def render_top_bar():
    col_logo, col_spacer, col_user = st.columns([4, 4, 1.6])

    with col_logo:
        st.markdown(
            "<h2 style='margin-bottom:0;'>📡 SmartCam Telemetri Paneli</h2>",
            unsafe_allow_html=True
        )

    with col_user:
        with st.popover(f"👤 {st.session_state.username}", use_container_width=True):
            st.markdown(f"**{st.session_state.username}**")
            st.caption(f"Rol: {st.session_state.role.upper() if st.session_state.role else '-'}")
            st.markdown("---")
            if st.button("🙍 Hesap Detayım", key="topbar_profile_btn", use_container_width=True):
                go_to("hesap_detay", selected_user_id=st.session_state.user_id)
            if st.button("🚪 Çıkış Yap", key="topbar_logout_btn", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.username = None
                st.session_state.role = None
                st.session_state.user_id = None
                st.session_state.page = "istasyonlar"
                st.rerun()

    st.markdown("<hr style='margin-top:4px;'>", unsafe_allow_html=True)


# ---------------------------------------------------------
# 5. SOL MENÜ (Genişleyebilir navigasyon — SOLA YASLI)
# ---------------------------------------------------------
def render_sidebar():
    st.sidebar.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown("#### Menü")

    for item in MENU_ITEMS:
        if item["roles"] and st.session_state.role not in item["roles"]:
            continue
        is_active = st.session_state.page.startswith(item["key"])
        if st.sidebar.button(
            item["label"],
            key=f"nav_{item['key']}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            go_to(item["key"], selected_station_id=None, selected_user_id=None)

    st.sidebar.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# 6. İSTASYONLAR — LİSTE (TABLO) VE DETAY
# ---------------------------------------------------------
def render_add_station_form():
    try:
        res_cat = requests.get(f"{API_BASE_URL}/station-categories", timeout=5)
        categories = res_cat.json() if res_cat.status_code == 200 else []
    except Exception:
        categories = []

    cat_map = {cat["name"]: cat["id"] for cat in categories} if categories else {"Akarsu": 1, "Baraj": 2, "Gateway": 3, "Yeraltı Suyu": 4}

    with st.form("add_station_form", clear_on_submit=True):
        st.subheader("Yeni İstasyon Tanımlama")
        st_name = st.text_input("İstasyon Adı", placeholder="Örn: Kuşadası Barajı Ana İstasyon")

        col_st1, col_st2 = st.columns(2)
        with col_st1:
            st_category = st.selectbox("İstasyon Kategorisi", list(cat_map.keys()))
        with col_st2:
            st_device_type = st.selectbox("Cihaz Tipi", ["Gateway", "IoT Node", "ESP32-S3", "RTU", "SmartCam"])

        col_st3, col_st4 = st.columns(2)
        with col_st3:
            st_phone = st.text_input("GSM Telefon No (Opsiyonel)", placeholder="0555 000 0000")
        with col_st4:
            st_imei = st.text_input("IMEI Numarası (Opsiyonel - Boşsa otomatik üretilir)", placeholder="15 haneli IMEI")

        st_submitted = st.form_submit_button("🛰️ İstasyonu Kaydet ve Oluştur", type="primary")

        if st_submitted:
            if not st_name.strip():
                st.warning("⚠️ Lütfen geçerli bir istasyon adı giriniz.")
            else:
                try:
                    payload = {
                        "category_id": cat_map[st_category],
                        "name": st_name.strip(),
                        "imei": st_imei.strip() if st_imei.strip() else None,
                        "phone_number": st_phone.strip(),
                        "device_type": st_device_type
                    }
                    res = requests.post(f"{API_BASE_URL}/stations", json=payload, timeout=5)
                    if res.status_code == 200:
                        data = res.json()
                        st.success(f"✅ {data['message']}")
                        st.info(
                            f"🔑 **Oluşturulan İstasyon ID:** `{data['station_id']}`\n\n"
                            f"🔒 **Güvenlik Kodu (securityCode):** `{data['generated_security_code']}`\n\n"
                            f"📱 **IMEI No:** `{data.get('imei', 'Otomatik Atandı')}`"
                        )
                        st.rerun()
                    else:
                        st.error(f"❌ Hata: {res.json().get('detail', 'İstasyon oluşturulamadı.')}")
                except Exception as e:
                    st.error(f"İstasyon eklenirken sunucu hatası oluştu: {e}")


def render_add_sensor_form(station_id, station_name):
    with st.form(f"add_sensor_form_{station_id}", clear_on_submit=True):
        st.subheader(f"'{station_name}' İstasyonuna Yeni Sensör Ekle")

        col_sn1, col_sn2 = st.columns(2)
        with col_sn1:
            sn_label = st.text_input("Sensör Adı / Etiketi", placeholder="Örn: Ortam Sıcaklığı, Su Seviyesi")
        with col_sn2:
            sn_id = st.number_input("Sensör Kanal ID'si (Opsiyonel)", min_value=0, max_value=999, value=0, help="Sahadan gönderilen sensorData['ID'] ile eşleşir. 0 bırakılırsa otomatik atanır.")

        col_sn3, col_sn4 = st.columns(2)
        with col_sn3:
            sn_unit = st.text_input("Ölçüm Birimi", placeholder="Örn: °C, %, cm, bar, m³/s")
        with col_sn4:
            sn_default_val = st.number_input("Başlangıç (Varsayılan) Değeri", value=0.0, step=0.1)

        sn_submitted = st.form_submit_button("🌡️ Sensörü İstasyona Tanımla", type="primary")

        if sn_submitted:
            if not sn_label.strip() or not sn_unit.strip():
                st.warning("⚠️ Lütfen sensör adı ve ölçüm birimini doldurunuz.")
            else:
                try:
                    payload = {
                        "station_id": station_id,
                        "label": sn_label.strip(),
                        "id": int(sn_id) if sn_id > 0 else None,
                        "default_unit": sn_unit.strip(),
                        "default_value": float(sn_default_val)
                    }
                    res = requests.post(f"{API_BASE_URL}/sensors", json=payload, timeout=5)
                    if res.status_code == 200:
                        data = res.json()
                        st.success(f"✅ {data['message']}")
                        st.info(f"⚡ **Sensör Kanal ID'si:** `{data.get('sensor_id')}` (Cihaz JSON paketinde `sensorData['{data.get('sensor_id')}']` olarak gönderilmelidir)")
                        st.rerun()
                    else:
                        st.error(f"❌ Hata: {res.json().get('detail', 'Sensör eklenemedi.')}")
                except Exception as e:
                    st.error(f"Sensör eklenirken sunucu hatası oluştu: {e}")


ROLE_COLORS = {
    "admin": ("rgba(236,72,153,0.16)", "#f9a8d4"),
    "user": ("rgba(59,130,246,0.16)", "#93c5fd"),
}
STATUS_COLORS = {
    "approved": ("rgba(34,197,94,0.16)", "#4ade80", "🟢 Onaylı"),
    "pending": ("rgba(234,179,8,0.16)", "#facc15", "🟡 Onay Bekliyor"),
    "rejected": ("rgba(239,68,68,0.16)", "#f87171", "🔴 Reddedildi"),
}


def _user_avatar_html(name):
    initial = (name or "?").strip()[0].upper() if name and name.strip() else "?"
    return f"<div class='user-avatar'>{initial}</div>"


def render_pending_user_approvals():
    try:
        res = requests.get(f"{API_BASE_URL}/admin/pending-users", timeout=5)
        pending_users = res.json() if res.status_code == 200 else []
    except Exception:
        st.error("Kullanıcı listesi alınırken API sunucusuna bağlanılamadı.")
        return

    if not pending_users:
        st.info("ℹ️ Şu anda onay bekleyen kullanıcı bulunmuyor.")
        return

    col_weights = [2.3, 2.1, 1.3, 0.7, 0.7]
    h1, h2, h3, h4, h5 = st.columns(col_weights)
    h1.markdown("<span>KULLANICI</span>", unsafe_allow_html=True)
    h2.markdown("<span>İLETİŞİM</span>", unsafe_allow_html=True)
    h3.markdown("<span>BAŞVURU TARİHİ</span>", unsafe_allow_html=True)
    h4.markdown("<span></span>", unsafe_allow_html=True)
    h5.markdown("<span></span>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:4px 0 10px 0;'>", unsafe_allow_html=True)

    for u in pending_users:
        u_id = u.get("id") or u.get("user_id")
        u_name = u.get("username") or u.get("name") or f"Kullanıcı #{u_id}"
        full_name = u.get("full_name") or ""

        c1, c2, c3, c4, c5 = st.columns(col_weights)
        with c1:
            st.markdown(
                f"<div class='user-row-wrap'>{_user_avatar_html(full_name or u_name)}"
                f"<div><div class='dev-name'>{full_name or u_name}</div>"
                f"<div class='dev-sub'>@{u_name} · ID: {u_id}</div></div></div>",
                unsafe_allow_html=True
            )
        with c2:
            st.markdown(
                f"<div class='dev-sub'>{u.get('email') or '-'}</div>"
                f"<div class='dev-sub'>{u.get('phone') or '-'}</div>",
                unsafe_allow_html=True
            )
        with c3:
            st.markdown(f"<div class='dev-sub' style='margin-top:6px;'>{u.get('created_at', '-')}</div>", unsafe_allow_html=True)
        with c4:
            if st.button("✅", key=f"pending_approve_{u_id}", use_container_width=True, help="Onayla"):
                requests.post(f"{API_BASE_URL}/admin/approve-user", json={"user_id": u_id, "action": "approve"})
                st.toast(f"{u_name} onaylandı!", icon="✅")
                st.rerun()
        with c5:
            if st.button("❌", key=f"pending_reject_{u_id}", use_container_width=True, help="Reddet"):
                requests.post(f"{API_BASE_URL}/admin/approve-user", json={"user_id": u_id, "action": "reject"})
                st.toast(f"{u_name} reddedildi!", icon="❌")
                st.rerun()

        st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)





CATEGORY_COLORS = {
    "Akarsu":        ("rgba(59,130,246,0.16)",  "#93c5fd"),
    "Baraj":         ("rgba(168,85,247,0.16)",  "#d8b4fe"),
    "Gateway":       ("rgba(20,184,166,0.16)",  "#5eead4"),
    "Yeraltı Suyu":  ("rgba(217,119,6,0.16)",   "#fbbf24"),
}


def _bar_color(pct):
    if pct >= 50:
        return "#22c55e"
    elif pct >= 20:
        return "#eab308"
    return "#ef4444"


def _render_bar_html(pct):
    color = _bar_color(pct)
    return (
        f"<div class='bar-wrap metric-col-wrap'>"
        f"<div class='bar-track'><div class='bar-fill' style='width:{pct}%; background:{color};'></div></div>"
        f"<span class='bar-pct'>%{pct}</span></div>"
    )


@st.cache_data(ttl=5)
def _get_sensor_count(station_id):
    try:
        res = requests.get(f"{API_BASE_URL}/stations/{station_id}/sensors", timeout=5)
        return len(res.json()) if res.status_code == 200 else 0
    except Exception:
        return 0


def render_istasyonlar_list():
    st.markdown("## 🛰️ İstasyonlar")
    st.caption("Sistemde kayıtlı tüm istasyonlar. Detayını görmek için satır sonundaki oka tıklayın.")

    try:
        res = requests.get(f"{API_BASE_URL}/stations", timeout=5)
        stations = res.json() if res.status_code == 200 else []
    except Exception as e:
        st.error(f"API sunucusuna bağlanılamadı ({API_BASE_URL}): {e}")
        stations = []

    if st.session_state.role == "admin":
        with st.expander("➕ Yeni İstasyon Ekle"):
            render_add_station_form()

    if not stations:
        st.warning("Veritabanında kayıtlı istasyon bulunamadı. Lütfen backend'in çalıştığından veya yukarıdan bir istasyon eklediğinizden emin olun.")
        return

    # ---- Filtre çubuğu ----
    with st.container(border=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns([2.4, 1.5, 1.5, 0.9])
        with f_col1:
            search = st.text_input("Cihaz Adı Ara...", key="station_search", label_visibility="collapsed", placeholder="🔍 Cihaz Adı Ara...")
        with f_col2:
            category_options = ["Tüm Kategoriler"] + sorted({s.get("category_name", "-") for s in stations if s.get("category_name")})
            selected_category = st.selectbox("Kategori", category_options, key="station_cat_filter", label_visibility="collapsed")
        with f_col3:
            device_options = ["Tüm Cihaz Tipleri"] + sorted({s.get("device_type", "-") for s in stations if s.get("device_type")})
            selected_device = st.selectbox("Cihaz Tipi", device_options, key="station_dev_filter", label_visibility="collapsed")
        with f_col4:
            if st.button("Temizle", key="station_filter_clear", use_container_width=True):
                st.session_state.station_search = ""
                st.session_state.station_cat_filter = "Tüm Kategoriler"
                st.session_state.station_dev_filter = "Tüm Cihaz Tipleri"
                st.rerun()

    filtered = stations
    if search:
        filtered = [s for s in filtered if search.lower().strip() in s["name"].lower()]
    if selected_category != "Tüm Kategoriler":
        filtered = [s for s in filtered if s.get("category_name") == selected_category]
    if selected_device != "Tüm Cihaz Tipleri":
        filtered = [s for s in filtered if s.get("device_type") == selected_device]

    if not filtered:
        st.info("Aramanızla eşleşen istasyon bulunamadı.")
        return

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

    col_weights = [2.3, 1.1, 1.5, 1.2, 1.3, 1.3, 0.8, 0.5]

    # ---- Başlık satırı ----
    h1, h2, h3, h4, h5, h6, h7, h8 = st.columns(col_weights)
    h1.markdown("<span>CİHAZ BİLGİSİ</span>", unsafe_allow_html=True)
    h2.markdown("<span>KATEGORİ</span>", unsafe_allow_html=True)
    h3.markdown("<span>BAĞLANTI</span>", unsafe_allow_html=True)
    h4.markdown("<span>SON GÜNCELLEME</span>", unsafe_allow_html=True)
    h5.markdown("<span>AKÜ</span>", unsafe_allow_html=True)
    h6.markdown("<span>SİNYAL</span>", unsafe_allow_html=True)
    h7.markdown("<span>SENSÖR</span>", unsafe_allow_html=True)
    h8.markdown("<span></span>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:4px 0 10px 0;'>", unsafe_allow_html=True)

    # ---- Veri satırları ----
    for s in filtered:
        battery_pct = parse_percentage(s.get("battery_percent", 0))
        gsm_pct = parse_percentage(s.get("gsm_percent", 0))
        ip = s.get("gsm_ip") or "—"
        is_online = bool(s.get("gsm_ip"))
        cat_name = s.get("category_name", "-")
        bg, fg = CATEGORY_COLORS.get(cat_name, ("rgba(255,255,255,0.06)", "#c3ccdb"))
        sensor_count = _get_sensor_count(s["id"])

        c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(col_weights)

        with c1:
            st.markdown(
                f"<div class='dev-name'>{s['name']}</div>"
                f"<div class='dev-sub'>ID: {s['id']} · {s.get('device_type', '-')}</div>",
                unsafe_allow_html=True
            )
        with c2:
            st.markdown(
                f"<div class='metric-col-wrap'><span class='cat-badge' style='background:{bg}; color:{fg};'>{cat_name}</span></div>",
                unsafe_allow_html=True
            )
        with c3:
            dot = "#22c55e" if is_online else "#ef4444"
            label = "Online" if is_online else "Offline"
            st.markdown(
                f"<div class='conn-wrap'>"
                f"<span class='conn-status'><span style='color:{dot};'>●</span> {label}</span>"
                f"<span class='conn-ip'>{ip}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        with c4:
            st.markdown(f"<div class='dev-sub' style='margin-top:6px;'>{s.get('updated_at', '-')}</div>", unsafe_allow_html=True)
        with c5:
            st.markdown(_render_bar_html(battery_pct), unsafe_allow_html=True)
        with c6:
            st.markdown(_render_bar_html(gsm_pct), unsafe_allow_html=True)
        with c7:
            st.markdown(f"<div class='metric-col-wrap'><span class='sensor-badge'>{sensor_count}</span></div>", unsafe_allow_html=True)
        with c8:
            if st.button("➡️", key=f"station_row_detail_{s['id']}", use_container_width=True):
                go_to("istasyon_detay", selected_station_id=s["id"])

        st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)


def render_live_chart_section(station_id, limit, station_name, sensor_obj):
    """Seçilen sensörün metriklerini ve zaman serisi çizim grafiğini gösterir."""

    use_date_filter = st.toggle(
        "🕒 Tarih/Saat Aralık Filtresi Uygula",
        value=False,
        key=f"toggle_filter_{station_id}_{sensor_obj['id']}"
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
            res_history = requests.get(url, timeout=5)
            sensor_logs = res_history.json() if res_history.status_code == 200 else []
        except Exception:
            sensor_logs = []

        filtered_logs = [log for log in sensor_logs if log.get("sensor_id") == sensor_obj["id"]]

        if filtered_logs:
            latest_val = filtered_logs[0].get("raw_value", 0)
            st.metric(
                label=f"⚡ Son Okunan Canlı {sensor_obj['label']} Değeri",
                value=f"{latest_val} {sensor_obj.get('default_unit', '')}"
            )

        if filtered_logs:
            df_sensor = pd.DataFrame(filtered_logs)
            if "recorded_at" in df_sensor.columns:
                df_sensor["recorded_at"] = pd.to_datetime(df_sensor["recorded_at"], errors="coerce")

            if is_filtered and start_dt and end_dt and "recorded_at" in df_sensor.columns:
                df_sensor = df_sensor[
                    (df_sensor["recorded_at"] >= start_dt) &
                    (df_sensor["recorded_at"] <= end_dt)
                ]

            chart_title = f"{station_name} — {sensor_obj['label']} Zaman Serisi Ölçüm Grafiği"

            fig = px.line(
                df_sensor,
                x="recorded_at" if "recorded_at" in df_sensor.columns else "id",
                y="raw_value",
                title=chart_title,
                markers=True,
                labels={"recorded_at": "Tarih / Zaman", "id": "Kayıt No", "raw_value": f"Değer ({sensor_obj.get('default_unit', '')})"}
            )
            fig.update_traces(line=dict(color="#3b82f6", width=3), marker=dict(size=7, color="#60a5fa"))
            fig.update_layout(
                height=450,
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
            st.info(f"ℹ️ '{sensor_obj['label']}' sensörü (Kanal ID: {sensor_obj['id']}) için henüz veritabanında log kaydı bulunmamaktadır.")

    _draw_chart(use_date_filter)


def render_istasyon_detay(station_id):
    if st.button("⬅️ İstasyonlar Listesine Dön", key="back_to_stations"):
        go_to("istasyonlar", selected_station_id=None)

    if station_id is None:
        st.warning("Görüntülenecek bir istasyon seçilmedi.")
        return

    try:
        res = requests.get(f"{API_BASE_URL}/stations/{station_id}", timeout=5)
        station = res.json() if res.status_code == 200 else None
    except Exception as e:
        st.error(f"API sunucusuna bağlanılamadı: {e}")
        station = None

    if not station:
        st.error("İstasyon bulunamadı.")
        return

    st.markdown("---")
    st.markdown(f"### 📊 [{station['name']}] Genel Durum Kartı")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("İstasyon Adı", station.get("name", "N/A"))
    c2.metric("IP Adresi", station.get("gsm_ip") or "192.168.1.100")
    c3.metric("IMEI No", station.get("imei", "N/A"))
    c4.metric("Son Güncelleme", station.get("updated_at", "N/A"))

    m1, m2, m3 = st.columns(3)
    m1.metric("🔋 Akü Durumu", get_status_indicator(station.get("battery_percent", 0)))
    m2.metric("📶 GSM Sinyali", get_status_indicator(station.get("gsm_percent", 0)))
    m3.metric("🖥️ Cihaz Tipi", station.get("device_type", "Gateway"))

    if st.session_state.role == "admin":
        with st.expander("➕ Bu İstasyona Sensör Ekle"):
            render_add_sensor_form(station_id, station["name"])

    st.markdown("---")
    st.markdown("### 2️⃣ Sensör Seçiniz")

    try:
        res_sensors = requests.get(f"{API_BASE_URL}/stations/{station_id}/sensors", timeout=5)
        station_sensors = res_sensors.json() if res_sensors.status_code == 200 else []
    except Exception:
        station_sensors = []

    if not station_sensors:
        st.warning("Bu istasyona tanımlanmış bir sensör bulunamadı. Lütfen yukarıdan sensör tanımlayınız.")
        return

    sensor_options = ["-- Lütfen Bir Sensör Seçiniz --"] + [f"{s['label']} (Kanal ID: {s['id']} | {s['default_unit']})" for s in station_sensors]
    sensor_map = {f"{s['label']} (Kanal ID: {s['id']} | {s['default_unit']})": s for s in station_sensors}

    selected_sn_str = st.selectbox("🌡️ Analiz Edilecek Sensör:", sensor_options, key=f"sensor_select_{station_id}")

    if selected_sn_str == "-- Lütfen Bir Sensör Seçiniz --":
        st.info("👈 Sensör ölçüm grafiğini ve canlı verilerini görmek için yukarıdan bir sensör seçiniz.")
        return

    selected_sensor = sensor_map[selected_sn_str]

    st.markdown("---")
    st.markdown(f"### 📈 [{station['name']}] — {selected_sensor['label']} Ölçüm Grafiği")

    with st.expander("⚙️ Veri Limit Ayarları"):
        limit = st.slider("Çekilecek Log Sayısı (Limit):", min_value=5, max_value=200, value=50)

    render_live_chart_section(station_id, limit, station["name"], selected_sensor)


# ---------------------------------------------------------
# 7. HESAPLAR — LİSTE (TABLO), ARAMA VE DETAY
# ---------------------------------------------------------
def render_hesaplar_list():
    st.markdown("## 👥 Hesaplar")
    st.caption("Sistemdeki tüm kullanıcı hesapları. Detayını görmek için satır sonundaki oka tıklayın.")

    tab_all, tab_pending = st.tabs(["📋 Tüm Kullanıcılar", "⏳ Onay Bekleyenler"])

    with tab_pending:
        render_pending_user_approvals()

    with tab_all:
        try:
            res_all = requests.get(f"{API_BASE_URL}/users", timeout=5)
            all_users_raw = res_all.json() if res_all.status_code == 200 else []
        except Exception as e:
            st.error(f"API sunucusuna bağlanılamadı: {e}")
            all_users_raw = []

        if not all_users_raw:
            st.info("Sistemde kayıtlı kullanıcı bulunamadı.")
            return

        # ---- Filtre çubuğu ----
        with st.container(border=True):
            f_col1, f_col2, f_col3, f_col4 = st.columns([2.4, 1.5, 1.5, 0.9])
            with f_col1:
                search = st.text_input(
                    "Kullanıcı Ara", key="user_search", label_visibility="collapsed",
                    placeholder="🔍 Kullanıcı Adı, Ad Soyad, E-posta veya Telefon Ara..."
                )
            with f_col2:
                role_options = ["Tüm Roller"] + sorted({u.get("role", "-") for u in all_users_raw if u.get("role")})
                selected_role = st.selectbox("Rol", role_options, key="user_role_filter", label_visibility="collapsed")
            with f_col3:
                status_options = ["Tüm Durumlar"] + sorted({u.get("status", "-") for u in all_users_raw if u.get("status")})
                selected_status = st.selectbox("Durum", status_options, key="user_status_filter", label_visibility="collapsed")
            with f_col4:
                if st.button("Temizle", key="user_filter_clear", use_container_width=True):
                    st.session_state.user_search = ""
                    st.session_state.user_role_filter = "Tüm Roller"
                    st.session_state.user_status_filter = "Tüm Durumlar"
                    st.rerun()

        users = all_users_raw
        if search and search.strip():
            s_low = search.lower().strip()
            users = [
                u for u in users
                if s_low in (u.get("username") or "").lower()
                or s_low in (u.get("full_name") or "").lower()
                or s_low in (u.get("email") or "").lower()
                or s_low in (u.get("phone") or "").lower()
            ]
        if selected_role != "Tüm Roller":
            users = [u for u in users if u.get("role") == selected_role]
        if selected_status != "Tüm Durumlar":
            users = [u for u in users if u.get("status") == selected_status]

        if not users:
            st.info("Aramanızla eşleşen kullanıcı bulunamadı.")
            return

        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

        col_weights = [2.3, 2.1, 1.0, 1.4, 1.3, 0.5]

        h1, h2, h3, h4, h5, h6 = st.columns(col_weights)
        h1.markdown("<span>KULLANICI</span>", unsafe_allow_html=True)
        h2.markdown("<span>İLETİŞİM</span>", unsafe_allow_html=True)
        h3.markdown("<span>ROL</span>", unsafe_allow_html=True)
        h4.markdown("<span>DURUM</span>", unsafe_allow_html=True)
        h5.markdown("<span>KAYIT TARİHİ</span>", unsafe_allow_html=True)
        h6.markdown("<span></span>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:4px 0 10px 0;'>", unsafe_allow_html=True)

        for u in users:
            display_name = u.get("full_name") or u["username"]
            role_bg, role_fg = ROLE_COLORS.get(u["role"], ("rgba(255,255,255,0.06)", "#c3ccdb"))
            status_bg, status_fg, status_label = STATUS_COLORS.get(
                u.get("status"), ("rgba(255,255,255,0.06)", "#c3ccdb", u.get("status") or "-")
            )

            c1, c2, c3, c4, c5, c6 = st.columns(col_weights)
            with c1:
                st.markdown(
                    f"<div class='user-row-wrap'>{_user_avatar_html(display_name)}"
                    f"<div><div class='dev-name'>{display_name}</div>"
                    f"<div class='dev-sub'>@{u['username']} · ID: {u['id']}</div></div></div>",
                    unsafe_allow_html=True
                )
            with c2:
                st.markdown(
                    f"<div class='dev-sub'>{u.get('email') or '-'}</div>"
                    f"<div class='dev-sub'>{u.get('phone') or '-'}</div>",
                    unsafe_allow_html=True
                )
            with c3:
                st.markdown(f"<span class='cat-badge' style='background:{role_bg}; color:{role_fg};'>{u['role']}</span>", unsafe_allow_html=True)
            with c4:
                st.markdown(f"<span class='cat-badge' style='background:{status_bg}; color:{status_fg};'>{status_label}</span>", unsafe_allow_html=True)
            with c5:
                st.markdown(f"<div class='dev-sub' style='margin-top:6px;'>{u.get('created_at', '-')}</div>", unsafe_allow_html=True)
            with c6:
                if st.button("➡️", key=f"user_row_detail_{u['id']}", use_container_width=True):
                    go_to("hesap_detay", selected_user_id=u["id"])

            st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)





def render_hesap_detay(user_id):
    is_own_profile = (user_id == st.session_state.user_id)
    can_manage = st.session_state.role == "admin" and not is_own_profile

    return_page = "hesaplar" if (st.session_state.role == "admin" and not is_own_profile) else "istasyonlar"
    back_label = "⬅️ Hesaplar Listesine Dön" if return_page == "hesaplar" else "⬅️ Ana Sayfaya Dön"
    if st.button(back_label, key="back_to_accounts"):
        go_to(return_page, selected_user_id=None)

    if user_id is None:
        st.warning("Görüntülenecek bir kullanıcı seçilmedi.")
        return

    try:
        res = requests.get(f"{API_BASE_URL}/users/{user_id}", timeout=5)
        user = res.json() if res.status_code == 200 else None
    except Exception as e:
        st.error(f"API sunucusuna bağlanılamadı: {e}")
        user = None

    if not user:
        st.error("Kullanıcı bulunamadı.")
        return

    st.markdown("---")
    st.markdown(f"## 🙍 {user.get('full_name') or user['username']}" + (" (Ben)" if is_own_profile else ""))

    c1, c2 = st.columns(2)
    c1.metric("Kullanıcı Adı", user["username"])
    c1.metric("E-Posta", user.get("email") or "-")
    c2.metric("Telefon", user.get("phone") or "-")
    c2.metric("Kayıt Tarihi", user.get("created_at") or "-")

    st.markdown(
        f"**Rol:** `{user['role']}`  \n**Durum:** {get_user_status_chip(user.get('status'))}"
    )

    if can_manage:
        st.markdown("---")
        st.markdown("### ⚙️ Hesap Yönetimi (Admin)")
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            new_role = st.selectbox(
                "Rol",
                ["user", "admin"],
                index=0 if user["role"] == "user" else 1,
                key=f"role_select_{user_id}"
            )
            if st.button("🔄 Rolü Güncelle", key=f"update_role_{user_id}", use_container_width=True):
                try:
                    requests.patch(f"{API_BASE_URL}/users/{user_id}", json={"role": new_role}, timeout=5)
                    st.toast("Rol güncellendi.", icon="✅")
                    st.rerun()
                except Exception as e:
                    st.error(f"Güncelleme hatası: {e}")

        with col_b:
            if user.get("status") == "pending":
                if st.button("✅ Onayla", key=f"detail_approve_{user_id}", use_container_width=True):
                    requests.post(f"{API_BASE_URL}/admin/approve-user", json={"user_id": user_id, "action": "approve"}, timeout=5)
                    st.toast("Kullanıcı onaylandı.", icon="✅")
                    st.rerun()
            elif user.get("status") == "rejected":
                if st.button("✅ Yeniden Onayla", key=f"detail_reapprove_{user_id}", use_container_width=True):
                    requests.patch(f"{API_BASE_URL}/users/{user_id}", json={"status": "approved"}, timeout=5)
                    st.toast("Kullanıcı onaylandı.", icon="✅")
                    st.rerun()
            else:
                st.caption("Kullanıcı zaten onaylı.")

        with col_c:
            if st.button("❌ Reddet / Sil", key=f"detail_reject_{user_id}", use_container_width=True):
                requests.post(f"{API_BASE_URL}/admin/approve-user", json={"user_id": user_id, "action": "reject"}, timeout=5)
                st.toast("Kullanıcı reddedildi ve silindi.", icon="❌")
                go_to("hesaplar", selected_user_id=None)


# ---------------------------------------------------------
# 8. ANA KONTROL PANELİ ROUTER'I
# ---------------------------------------------------------
def render_dashboard():
    render_top_bar()
    render_sidebar()

    page = st.session_state.page

    if page == "istasyonlar":
        render_istasyonlar_list()
    elif page == "istasyon_detay":
        render_istasyon_detay(st.session_state.selected_station_id)
    elif page == "hesaplar":
        if st.session_state.role != "admin":
            st.error("Bu sayfayı görüntülemek için yönetici yetkisine sahip olmalısınız.")
            return
        render_hesaplar_list()
    elif page == "hesap_detay":
        render_hesap_detay(st.session_state.selected_user_id)
    else:
        render_istasyonlar_list()


# ---------------------------------------------------------
# 9. UYGULAMA BAŞLATICI
# ---------------------------------------------------------
def main():
    inject_custom_css()
    if not st.session_state.authenticated:
        render_auth_page()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()
