import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# 1. SUNUCU ADRESİ VE SAYFA YAPILANDIRMASI
# ---------------------------------------------------------
API_BASE_URL = "http://127.0.0.1:8000/api"

st.set_page_config(
    page_title="SmartCam - Telemetri Paneli",
    page_icon="📡",
    layout="wide"
)

# Oturum Durumları (Session State)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None


# ---------------------------------------------------------
# 2. YARDIMCI FONKSİYONLAR
# ---------------------------------------------------------
def get_status_indicator(value, thresholds=(50, 20)):
    if value >= thresholds[0]:
        return f"🟢 %{value} (Mükemmel)"
    elif value >= thresholds[1]:
        return f"🟡 %{value} (Normal)"
    else:
        return f"🔴 %{value} (Düşük)"


# ---------------------------------------------------------
# 3. GİRİŞ VE KAYIT EKRANI (TEST GEÇİŞLİ AUTH)
# ---------------------------------------------------------
def render_auth_page():
    st.title("📡 SmartCam Telemetri Paneli Girişi")
    
    tab_login, tab_register = st.tabs(["🔐 Giriş Yap", "📝 Kayıt Ol"])

    with tab_login:
        st.subheader("Kullanıcı Girişi")
        login_user = st.text_input("Kullanıcı Adı", key="login_user")
        login_pass = st.text_input("Şifre", type="password", key="login_pass")
        
        if st.button("Giriş Yap", type="primary", use_container_width=True):
            if login_user and login_pass:
                # ---------------------------------------------------------
                # 🛠️ GECİCİ TEST BAYPASI (BACKEND VERİTABANINDA YOKSA BİLE ÇALIŞIR)
                # ---------------------------------------------------------
                if login_user == "admin" and login_pass == "admin123":
                    st.session_state.authenticated = True
                    st.session_state.username = "admin"
                    st.session_state.role = "admin"
                    st.success("Admin test girişi başarılı!")
                    st.rerun()
                # ---------------------------------------------------------
                # DİĞER KULLANICILAR İÇİN GERÇEK API İSTEĞİ
                # ---------------------------------------------------------
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
                            st.session_state.username = data.get("username")
                            st.session_state.role = data.get("role")
                            st.success("Giriş başarılı!")
                            st.rerun()
                        elif res.status_code == 403:
                            st.warning("Hesabınız henüz Admin tarafından onaylanmamış.")
                        else:
                            st.error("Hatalı kullanıcı adı veya şifre.")
                    except requests.exceptions.ConnectionError:
                        st.error("API sunucusuna bağlanılamadı! Lütfen backend servisinin çalıştığından emin olun.")
                    except Exception as e:
                        st.error(f"Bir hata oluştu: {e}")
            else:
                st.info("Lütfen tüm alanları doldurunuz.")

    with tab_register:
        st.subheader("Yeni Kullanıcı Kaydı")
        reg_user = st.text_input("Kullanıcı Adı", key="reg_user")
        reg_pass = st.text_input("Şifre", type="password", key="reg_pass")
        
        if st.button("Kayıt Oluştur", use_container_width=True):
            if reg_user and reg_pass:
                try:
                    res = requests.post(
                        f"{API_BASE_URL}/auth/register",
                        json={"username": reg_user, "password": reg_pass},
                        timeout=5
                    )
                    if res.status_code in [200, 201]:
                        st.success("Kayıt başarılı! Hesabınız admin onayına gönderildi.")
                    else:
                        st.error("Kayıt oluşturulamadı. Kullanıcı adı zaten alınıyor olabilir.")
                except requests.exceptions.ConnectionError:
                    st.error("API sunucusuna bağlanılamadı!")
                except Exception as e:
                    st.error(f"Bir hata oluştu: {e}")
            else:
                st.info("Lütfen tüm alanları doldurunuz.")


# ---------------------------------------------------------
# 4. ADMIN PANELİ (SIDEBAR - KULLANICI ONAYLARI)
# ---------------------------------------------------------
def render_admin_panel():
    st.sidebar.markdown("---")
    st.sidebar.subheader("👑 Onay Bekleyen Kullanıcılar")
    
    try:
        res = requests.get(f"{API_BASE_URL}/admin/pending-users", timeout=5)
        if res.status_code == 200:
            pending_users = res.json()
            if not pending_users:
                st.sidebar.caption("Onay bekleyen kullanıcı yok.")
            else:
                for user in pending_users:
                    u_id = user.get("id") or user.get("user_id")
                    u_name = user.get("username")
                    
                    col_name, col_btn1, col_btn2 = st.sidebar.columns([2, 1, 1])
                    col_name.write(f"**{u_name}**")
                    
                    if col_btn1.button("✅", key=f"app_{u_id}", help="Onayla"):
                        requests.post(
                            f"{API_BASE_URL}/admin/approve-user",
                            json={"user_id": u_id, "action": "approve"}
                        )
                        st.toast(f"{u_name} onaylandı!", icon="✅")
                        st.rerun()
                    if col_btn2.button("❌", key=f"rej_{u_id}", help="Reddet"):
                        requests.post(
                            f"{API_BASE_URL}/admin/approve-user",
                            json={"user_id": u_id, "action": "reject"}
                        )
                        st.toast(f"{u_name} reddedildi!", icon="❌")
                        st.rerun()
    except Exception:
        st.sidebar.error("Onay listesi alınamadı.")


# ---------------------------------------------------------
# 5. ANA KONTROL PANELİ & SENSÖR ANALİZİ
# ---------------------------------------------------------
def render_dashboard():
    st.sidebar.title(f"👤 {st.session_state.username}")
    st.sidebar.caption(f"Rol Yetkisi: **{st.session_state.role.upper()}**")
    
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

    if st.session_state.role == "admin":
        render_admin_panel()

    st.title("📡 SmartCam İstasyon Takip ve Doğrulama Paneli")

    try:
        res = requests.get(f"{API_BASE_URL}/stations", timeout=5)
        stations = res.json() if res.status_code == 200 else []
    except Exception as e:
        st.error(f"İstasyon verileri çekilirken hata oluştu: {e}")
        stations = []

    if not stations:
        st.warning("Sistemde görüntülenecek istasyon bulunamadı.")
        return

    station_names = [s.get("name", f"İstasyon {s.get('id')}") for s in stations]
    selected_name = st.selectbox("İstasyon Seçiniz:", station_names)
    selected_station = next(s for s in stations if s.get("name", f"İstasyon {s.get('id')}") == selected_name)

    st.markdown("### 📊 İstasyon Durumu")
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Kategori", selected_station.get("category", "N/A"))
    col2.metric("IP Adresi", selected_station.get("ip_address", "N/A"))
    col3.metric("Telefon No", selected_station.get("phone", "N/A"))
    col4.write(f"**Cihaz ID:** #{selected_station.get('id')}")

    m_col1, m_col2 = st.columns(2)
    battery_val = selected_station.get("battery", 0)
    gsm_val = selected_station.get("gsm", 0)

    m_col1.metric("🔋 Akü Durumu", get_status_indicator(battery_val))
    m_col2.metric("📶 GSM Sinyal Gücü", get_status_indicator(gsm_val))

    st.markdown("---")

    st.markdown("### 📈 Sensör Zaman Serisi Grafiği")

    station_id = selected_station.get("id")
    limit = st.slider("Veri Noktası Sayısı (Limit):", min_value=10, max_value=200, value=50)

    try:
        sensor_res = requests.get(f"{API_BASE_URL}/sensor/history?station_id={station_id}&limit={limit}", timeout=5)
        raw_data = sensor_res.json() if sensor_res.status_code == 200 else []
    except Exception as e:
        st.error(f"Sensör verisi çekilemedi: {e}")
        raw_data = []

    if raw_data:
        df = pd.DataFrame(raw_data)
        
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 1, 1])

        if "timestamp" in df.columns and not df.empty:
            min_date = df["timestamp"].min().date()
            max_date = df["timestamp"].max().date()
            selected_dates = ctrl_col1.date_input("Tarih Aralığı Filtresi", [min_date, max_date])
            
            if len(selected_dates) == 2:
                start_d, end_d = selected_dates
                df = df[(df["timestamp"].dt.date >= start_d) & (df["timestamp"].dt.date <= end_d)]

        temp_unit = ctrl_col2.radio("Sıcaklık Birimi:", ["°C", "°F"], horizontal=True)
        level_unit = ctrl_col3.radio("Su Seviyesi Birimi:", ["m", "cm"], horizontal=True)

        if "temperature" in df.columns and temp_unit == "°F":
            df["temperature"] = (df["temperature"] * 9/5) + 32

        if "water_level" in df.columns and level_unit == "cm":
            df["water_level"] = df["water_level"] * 100

        numeric_cols = [col for col in df.columns if col not in ["timestamp", "station_id", "id"]]
        selected_metric = st.selectbox("Görselleştirilecek Sensör Verisi:", numeric_cols)

        if selected_metric and not df.empty:
            fig = px.line(
                df,
                x="timestamp",
                y=selected_metric,
                title=f"{selected_name} - {selected_metric.capitalize()} Zaman Serisi",
                markers=True,
                labels={"timestamp": "Zaman", selected_metric: f"Değer ({temp_unit if 'temp' in selected_metric else level_unit})"}
            )
            fig.update_layout(hovermode="x unified", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Seçilen tarih aralığında veri bulunamadı.")
    else:
        st.info("Bu istasyona ait henüz sensör ölçümü kaydı bulunmuyor.")


# ---------------------------------------------------------
# 6. UYGULAMA BAŞLATICI
# ---------------------------------------------------------
def main():
    if not st.session_state.authenticated:
        render_auth_page()
    else:
        render_dashboard()

if __name__ == "__main__":
    main()
