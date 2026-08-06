import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time as pytime
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
        /* Otomatik doldurma (Autofill) renk düzeltmesi */
        input:-webkit-autofill,
        input:-webkit-autofill:hover, 
        input:-webkit-autofill:focus {
            -webkit-text-fill-color: #ffffff !important;
            -webkit-box-shadow: 0 0 0px 1000px #1e293b inset !important;
            transition: background-color 5000s ease-in-out 0s;
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

def format_relative_time(dt_input):
    """
    Tarih/zaman değerini göreceli formata dönüştürür:
    - 1 dakikadan az: 'Az önce'
    - 1 saatten az: 'X dakika önce'
    - 1 günden az: 'X saat önce'
    - 1 aydan (30 gün) az: 'X gün önce'
    - 1 yıldan (365 gün) az: 'X ay önce'
    - 1 yıldan fazla: Tam tarih ('DD.MM.YYYY HH:MM')
    """
    if not dt_input or dt_input == "N/A":
        return "Az önce"

    try:
        if isinstance(dt_input, str):
            clean_str = dt_input.replace("Z", "").replace("T", " ")
            dt_obj = datetime.fromisoformat(clean_str)
        elif isinstance(dt_input, datetime):
            dt_obj = dt_input
        else:
            return str(dt_input)

        now = datetime.now()
        diff = now - dt_obj
        seconds = int(diff.total_seconds())

        if seconds < 0 or seconds < 60:
            return "Az önce"

        minutes = seconds // 60
        hours = minutes // 60
        days = hours // 24
        months = days // 30
        years = days // 365

        if minutes < 60:
            return f"{minutes} dakika önce"
        elif hours < 24:
            return f"{hours} saat önce"
        elif days < 30:
            return f"{days} gün önce"
        elif months < 12:
            return f"{months} ay önce"
        else:
            return dt_obj.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return str(dt_input)


def check_persistent_session():
    """1 saatlik oturum süresini ve query_params/localStorage senkronizasyonunu kontrol eder."""
    current_time = pytime.time()
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "role" not in st.session_state:
        st.session_state.role = None

    # 1. Query Params üzerinden oturum kontrolü (F5 yenilemelerinde otomatik koruma)
    if not st.session_state.authenticated:
        q_user = st.query_params.get("session_user")
        q_role = st.query_params.get("session_role")
        q_exp = st.query_params.get("session_exp")

        if q_user and q_role and q_exp:
            try:
                exp_ts = float(q_exp)
                if current_time < exp_ts:
                    st.session_state.authenticated = True
                    st.session_state.username = q_user
                    st.session_state.role = q_role
                else:
                    # 1 saatlik süre dolmuş!
                    st.query_params.clear()
                    st.session_state.authenticated = False
            except Exception:
                st.query_params.clear()

    # 2. Browser LocalStorage ile otomatik senkronizasyon JS
    st.components.v1.html("""
        <script>
        (function() {
            const parentWin = window.parent;
            const savedSession = parentWin.localStorage.getItem('smartcam_user_session');
            if (savedSession) {
                try {
                    const data = JSON.parse(savedSession);
                    const now = Date.now();
                    if (data.expires_at > now) {
                        const url = new URL(parentWin.location.href);
                        if (!url.searchParams.has('session_user')) {
                            url.searchParams.set('session_user', data.username);
                            url.searchParams.set('session_role', data.role);
                            url.searchParams.set('session_exp', (data.expires_at / 1000).toString());
                            parentWin.location.href = url.href;
                        }
                    } else {
                        parentWin.localStorage.removeItem('smartcam_user_session');
                    }
                } catch(e) {}
            }
        })();
        </script>
    """, height=0)


# ---------------------------------------------------------
# 3. GİRİŞ VE KAYIT EKRANI
# ---------------------------------------------------------
def render_auth_page():
    # Klavye Yönlendirme Javascript Kodu (Enter veya Alt Ok tuşuna basınca şifre kutusuna geçer)
    st.components.v1.html("""
        <script>
        const parentDoc = window.parent.document;
        if (!window.keyboardNavInjected) {
            window.keyboardNavInjected = true;
            parentDoc.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === 'ArrowDown') {
                    const active = parentDoc.activeElement;
                    if (active && active.tagName === 'INPUT') {
                        const inputs = Array.from(parentDoc.querySelectorAll('input:not([type="hidden"]):not([type="checkbox"])'));
                        const index = inputs.indexOf(active);
                        if (index > -1 && index < inputs.length - 1) {
                            if (e.key === 'ArrowDown' || (e.key === 'Enter' && active.type !== 'password')) {
                                e.preventDefault();
                                e.stopPropagation();
                                inputs[index + 1].focus();
                            }
                        }
                    }
                }
            }, true);
        }
        </script>
    """, height=0)

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
                
                st.caption("💡 *İpucu: Kullanıcı adı kutusundayken Enter veya ⬇️ Alt Ok tuşuna basarak şifre kutusuna geçebilirsiniz.*")
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
                                username_val = data.get("username", login_user)
                                role_val = data.get("role", "user")
                                exp_time = pytime.time() + 3600  # 1 Saatlik (60 dk) Oturum Süresi

                                st.session_state.authenticated = True
                                st.session_state.username = username_val
                                st.session_state.role = role_val

                                # 1 saatlik oturumu URL query_params'a yaz
                                st.query_params["session_user"] = username_val
                                st.query_params["session_role"] = role_val
                                st.query_params["session_exp"] = str(exp_time)

                                # Browser localStorage'a 1 saatlik oturumu kaydet
                                st.components.v1.html(f"""
                                    <script>
                                    window.parent.localStorage.setItem('smartcam_user_session', JSON.stringify({{
                                        username: "{username_val}",
                                        role: "{role_val}",
                                        expires_at: {int(exp_time * 1000)}
                                    }}));
                                    </script>
                                """, height=0)

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
# 4. ADMİN İÇİN YÖNETİM MERKEZİ (İSTASYON & SENSÖR EKLEME)
# ---------------------------------------------------------
def render_admin_management_center(stations):
    """Admin kullanıcıları için İstasyon Ekleme, Sensör Ekleme ve Kullanıcı Onaylama Paneli."""
    with st.expander("🛠️ Admin Yönetim Merkezi (İstasyon, Sensör ve Kullanıcı Yönetimi)", expanded=False):
        tab_users, tab_add_station, tab_add_sensor = st.tabs([
            "👥 Kullanıcı Onayları", 
            "🛰️ Yeni İstasyon Ekle", 
            "🌡️ Yeni Sensör Ekle"
        ])

        # --- 4.1. KULLANICI ONAYLARI ---
        with tab_users:
            try:
                res = requests.get(f"{API_BASE_URL}/admin/pending-users", timeout=5)
                if res.status_code == 200:
                    pending_users = res.json()
                    if not pending_users:
                        st.info("ℹ️ Şu anda onay bekleyen kullanıcı bulunmuyor.")
                    else:
                        for user in pending_users:
                            u_id = user.get("id") or user.get("user_id")
                            u_name = user.get("username") or user.get("name") or f"Kullanıcı #{u_id}"
                            full_name = user.get("full_name") or ""
                            email = user.get("email") or ""
                            phone = user.get("phone") or ""

                            col_u1, col_u2, col_u3 = st.columns([3, 1, 1])
                            with col_u1:
                                st.markdown(f"**👤 {u_name}** ({full_name}) `ID: {u_id}`")
                                if email or phone:
                                    st.caption(f"📧 {email} | 📞 {phone}")
                            with col_u2:
                                if st.button("✅ Onayla", key=f"app_{u_id}", use_container_width=True):
                                    requests.post(
                                        f"{API_BASE_URL}/admin/approve-user",
                                        json={"user_id": u_id, "action": "approve"}
                                    )
                                    st.toast(f"{u_name} onaylandı!", icon="✅")
                                    st.rerun()
                            with col_u3:
                                if st.button("❌ Reddet", key=f"rej_{u_id}", use_container_width=True):
                                    requests.post(
                                        f"{API_BASE_URL}/admin/approve-user",
                                        json={"user_id": u_id, "action": "reject"}
                                    )
                                    st.toast(f"{u_name} reddedildi!", icon="❌")
                                    st.rerun()
                            st.markdown("---")
            except Exception:
                st.error("Kullanıcı listesi alınırken API sunucusuna bağlanılamadı.")

        # --- 4.2. YENİ İSTASYON EKLE ---
        with tab_add_station:
            # İstasyon kategorilerini API'den çekelim
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

        # --- 4.3. YENİ SENSÖR EKLE ---
        with tab_add_sensor:
            if not stations:
                st.warning("Önce sistemde en az bir istasyon tanımlı olmalıdır.")
            else:
                station_dict = {f"{s['name']} (ID: {s['id']})": s["id"] for s in stations}
                with st.form("add_sensor_form", clear_on_submit=True):
                    st.subheader("İstaya Yeni Sensör Ekle")
                    selected_st_for_sensor = st.selectbox("Sensörün Ekleneceği İstasyon:", list(station_dict.keys()))
                    
                    col_sn1, col_sn2 = st.columns(2)
                    with col_sn1:
                        sn_label = st.text_input("Sensör Adı / Etiketi", placeholder="Örn: Ortam Sıcaklığı, Su Seviyesi")
                    with col_sn2:
                        sn_id = st.number_input("Sensör Kanal ID'si (Opsiyonel - IoT Veri Anahtarı)", min_value=0, max_value=999, value=0, help="Sahadan gönderilen sensorData['ID'] ile eşleşir. 0 bırakılırsa otomatik atanır.")

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
                                    "station_id": station_dict[selected_st_for_sensor],
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


# ---------------------------------------------------------
# 4.4 CANLI GRAFİK VE SENSÖR DETAY ALANI
# ---------------------------------------------------------
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

        # Sadece seçilen sensör id'sine ait logları filtrele
        filtered_logs = [log for log in sensor_logs if log.get("sensor_id") == sensor_obj["id"]]

        # Son Okunan Canlı Ölçüm Metriğini Göster
        if filtered_logs:
            latest_val = filtered_logs[0].get("raw_value", 0)
            latest_time = filtered_logs[0].get("recorded_at")
            rel_time_str = format_relative_time(latest_time)
            st.metric(
                label=f"⚡ Son Okunan Canlı {sensor_obj['label']} Değeri ({rel_time_str})",
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

            ver_key = f"fix_zoom_ver_{station_id}_{sensor_obj['id']}"
            if ver_key not in st.session_state:
                st.session_state[ver_key] = 0

            # Grafiğin üstüne başlık ve Türkçe "Grafiği Sıfırla" butonu koyuyoruz
            c_title, c_rst = st.columns([4, 1.2])
            with c_title:
                st.markdown(f"#### 📈 {station_name} — {sensor_obj['label']} Zaman Serisi Ölçüm Grafiği")
            with c_rst:
                if st.button("🔄 Grafiği Sıfırla", key=f"reset_btn_{station_id}_{sensor_obj['id']}", help="Yakınlaştırmayı sıfırlar ve tam boyuta döner"):
                    st.session_state[ver_key] += 1
                    st.rerun()

            fig = px.line(
                df_sensor,
                x="recorded_at" if "recorded_at" in df_sensor.columns else "id",
                y="raw_value",
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
                margin=dict(l=10, r=10, t=10, b=10),
                uirevision=f"sensor_{station_id}_{sensor_obj['id']}_{st.session_state[ver_key]}",
                xaxis=dict(gridcolor="rgba(255,255,255,0.08)", fixedrange=False),
                yaxis=dict(gridcolor="rgba(255,255,255,0.08)", fixedrange=True)
            )
            st.plotly_chart(fig, use_container_width=True, key=f"telemetry_chart_{station_id}_{sensor_obj['id']}")
        else:
            st.info(f"ℹ️ '{sensor_obj['label']}' sensörü (Kanal ID: {sensor_obj['id']}) için henüz veritabanında log kaydı bulunmamaktadır.")

    _draw_chart(use_date_filter)


# ---------------------------------------------------------
# 5. ANA KONTROL PANELİ & KADEMELİ İSTASYON/SENSÖR SEÇİMİ
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
        st.query_params.clear()
        st.components.v1.html("""
            <script>
            window.parent.localStorage.removeItem('smartcam_user_session');
            </script>
        """, height=0)
        st.rerun()

    st.markdown(
        "<h1>📡 SmartCam Telemetri ve Sensör İzleme Paneli</h1>",
        unsafe_allow_html=True
    )

    # API'den İstasyon Listesini Çek (/api/stations)
    try:
        res_stations = requests.get(f"{API_BASE_URL}/stations", timeout=5)
        stations = res_stations.json() if res_stations.status_code == 200 else []
    except Exception as e:
        st.error(f"API sunucusuna bağlanılamadı ({API_BASE_URL}): {e}")
        stations = []

    # Admin ise İstasyon & Sensör & Kullanıcı Yönetim Panelini göster
    if st.session_state.role == "admin":
        render_admin_management_center(stations)

    if not stations:
        st.warning("Veritabanında kayıtlı istasyon bulunamadı. Lütfen backend'i çalıştırdığınızdan veya yukarıdaki Admin Merkezinden bir istasyon eklediğinizden emin olun.")
        return

    # --- 1. ADIM: İSTASYON SEÇİMİ ---
    st.markdown("### 1️⃣ Adım: İstasyon Seçiniz")
    station_options = ["-- Lütfen Bir İstasyon Seçiniz --"] + [f"{s['name']} (ID: {s['id']})" for s in stations]
    station_map = {f"{s['name']} (ID: {s['id']})": s for s in stations}
    
    selected_st_str = st.selectbox("🛰️ İzlemek İstediğiniz İstasyon:", station_options, key="main_st_select")

    if selected_st_str == "-- Lütfen Bir İstasyon Seçiniz --":
        st.info("👈 Lütfen yukarıdaki listeden analiz etmek istediğiniz bir istasyonu seçiniz.")
        return

    selected_station = station_map[selected_st_str]
    station_id = selected_station["id"]

    # --- İSTASYON DURUMU VE METRİK KARTLARI ---
    st.markdown("---")
    st.markdown(f"### 📊 [{selected_station['name']}] Genel Durum Kartı")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("İstasyon Adı", selected_station.get("name", "N/A"))
    c2.metric("IP Adresi", selected_station.get("gsm_ip") or "192.168.1.100")
    c3.metric("IMEI No", selected_station.get("imei", "N/A"))
    
    raw_updated = selected_station.get("updated_at")
    rel_updated = format_relative_time(raw_updated)
    c4.metric("Son Güncelleme", rel_updated)

    m1, m2, m3 = st.columns(3)
    acc_val = selected_station.get("battery_percent", 0)
    gsm_val = selected_station.get("gsm_percent", 0)
    m1.metric("🔋 Akü Durumu", get_status_indicator(acc_val))
    m2.metric("📶 GSM Sinyali", get_status_indicator(gsm_val))
    m3.metric("🖥️ Cihaz Tipi", selected_station.get("device_type", "Gateway"))

    # --- 2. ADIM: SENSÖR SEÇİMİ (İSTASYON SEÇİLİNCE GELİR) ---
    st.markdown("---")
    st.markdown("### 2️⃣ Adım: Sensör Seçiniz")

    # API'den Bu İstasyona Ait Sensörleri Çek (/api/stations/{station_id}/sensors)
    try:
        res_sensors = requests.get(f"{API_BASE_URL}/stations/{station_id}/sensors", timeout=5)
        station_sensors = res_sensors.json() if res_sensors.status_code == 200 else []
    except Exception:
        station_sensors = []

    if not station_sensors:
        st.warning("Bu istasyona tanımlanmış bağlı bir sensör bulunamadı. Lütfen 'Admin Yönetim Merkezi -> Yeni Sensör Ekle' sekmesinden sensör tanımlayınız.")
        return

    sensor_options = ["-- Lütfen Bir Sensör Seçiniz --"] + [f"{s['label']} (Kanal ID: {s['id']} | {s['default_unit']})" for s in station_sensors]
    sensor_map = {f"{s['label']} (Kanal ID: {s['id']} | {s['default_unit']})": s for s in station_sensors}

    selected_sn_str = st.selectbox("🌡️ Analiz Edilecek Sensör:", sensor_options, key=f"sensor_select_{station_id}")

    if selected_sn_str == "-- Lütfen Bir Sensör Seçiniz --":
        st.info("👈 Sensör ölçüm grafiğini ve canlı verilerini görmek için yukarıdan bir sensör seçiniz.")
        return

    selected_sensor = sensor_map[selected_sn_str]

    st.markdown("---")
    st.markdown(f"### 📈 [{selected_station['name']}] — {selected_sensor['label']} Ölçüm Grafiği")

    with st.expander("⚙️ Veri Limit Ayarları"):
        limit = st.slider("Çekilecek Log Sayısı (Limit):", min_value=5, max_value=200, value=50)

    render_live_chart_section(station_id, limit, selected_station["name"], selected_sensor)


# ---------------------------------------------------------
# 6. UYGULAMA BAŞLATICI
# ---------------------------------------------------------
def main():
    inject_custom_css()
    check_persistent_session()
    if not st.session_state.authenticated:
        render_auth_page()
    else:
        render_dashboard()

if __name__ == "__main__":
    main()
