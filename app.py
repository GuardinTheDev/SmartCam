import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# 1. SUNUCU ADRESİ VE SAYFA YAPILANDIRMASI
# ---------------------------------------------------------
API_BASE_URL = "http://127.0.0.1:8000/api"

st.set_page_config(
    page_title="SmartCam IoT - Telemetri Paneli",
    page_icon="📡",
    layout="wide"
)

# Oturum Durumları
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None


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
    """Akü ve GSM seviyelerine renkli gösterge verir."""
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
    st.title("📡 SmartCam Telemetri Paneli Girişi")

    tab_login, tab_register = st.tabs(["🔐 Giriş Yap", "📝 Kayıt Ol"])

    with tab_login:
        st.subheader("Kullanıcı Girişi")
        login_user = st.text_input("Kullanıcı Adı", key="login_user")
        login_pass = st.text_input("Şifre", type="password", key="login_pass")
        
        if st.button("Giriş Yap", type="primary", use_container_width=True):
            if login_user == "admin" and login_pass == "admin123":
                st.session_state.authenticated = True
                st.session_state.username = "admin"
                st.session_state.role = "admin"
                st.success("Admin test girişi başarılı!")
                st.rerun()
            elif login_user and login_pass:
                # Normal kullanıcı girişi simülasyonu
                st.session_state.authenticated = True
                st.session_state.username = login_user
                st.session_state.role = "user"
                st.success("Giriş başarılı!")
                st.rerun()
            else:
                st.warning("Lütfen kullanıcı adı ve şifre giriniz.")

    with tab_register:
        st.subheader("Yeni Kullanıcı Kaydı")
        reg_user = st.text_input("Kullanıcı Adı", key="reg_user")
        reg_pass = st.text_input("Şifre", type="password", key="reg_pass")
        
        if st.button("Kayıt Oluştur", use_container_width=True):
            if reg_user and reg_pass:
                st.success("Kayıt alındı! Hesabınız admin onayına gönderildi.")
            else:
                st.info("Lütfen tüm alanları doldurunuz.")


# ---------------------------------------------------------
# 4. ADMIN PANELİ (SIDEBAR - ONLAY BEKLEYENLER)
# ---------------------------------------------------------
def render_admin_panel():
    st.sidebar.markdown("---")
    st.sidebar.subheader("👑 Admin Kontrol Paneli")
    st.sidebar.caption("Sistemde onay bekleyen kayıt talebi bulunmuyor.")


# ---------------------------------------------------------
# 5. ANA KONTROL PANELİ & SENSÖR ANALİZİ
# ---------------------------------------------------------
def render_dashboard():
    # Profil Bilgisi
    st.sidebar.title(f"👤 {st.session_state.username}")
    st.sidebar.caption(f"Rol Yetkisi: **{st.session_state.role.upper()}**")
    
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

    if st.session_state.role == "admin":
        render_admin_panel()

    st.title("📡 SmartCam IoT İstasyon ve Veri Takip Paneli")

    # API'den Son Cihaz Verilerini Çek (/api/device/history)
    limit = st.slider("Çekilecek Log Sayısı (Limit):", min_value=5, max_value=100, value=20)
    
    try:
        res = requests.get(f"{API_BASE_URL}/device/history?limit={limit}", timeout=5)
        device_logs = res.json() if res.status_code == 200 else []
    except Exception as e:
        st.error(f"API sunucusuna bağlanılamadı ({API_BASE_URL}): {e}")
        device_logs = []

    if not device_logs:
        st.warning("Veritabanında henüz cihaza ait log kaydı bulunmuyor.")
        return

    # İstasyon Kodlarına (istCode) Göre Grupla/Filtrele
    station_codes = list(set([log.get("istCode", "Bilinmeyen Cihaz") for log in device_logs if log.get("istCode")]))
    if not station_codes:
        station_codes = [f"Cihaz #{log.get('id')}" for log in device_logs]

    selected_station_code = st.selectbox("İstasyon Seçiniz (istCode):", station_codes)

    # Seçilen İstasyonun Log Kayıtlarını Süz
    selected_logs = [log for log in device_logs if log.get("istCode") == selected_station_code]
    latest_log = selected_logs[0] if selected_logs else device_logs[0]

    # --- İSTASYON METRİK KARTLARI (main.py JSON Yapısına Göre) ---
    st.markdown("### 📊 İstasyon Son Durumu")
    c1, c2, c3, c4 = st.columns(4)
    
    c1.metric("İstasyon Kodu", latest_log.get("istCode", "N/A"))
    c2.metric("Model / Kart", f"{latest_log.get('model', '')} / {latest_log.get('board', '')}")
    c3.metric("IP Adresi", latest_log.get("ip", "N/A"))
    c4.metric("GSM No", latest_log.get("gsmNo", "N/A"))

    st.markdown("#### Telemetri Durumu")
    m1, m2, m3 = st.columns(3)
    
    acc_val = latest_log.get("accumulatorPercent", 0)
    gsm_val = latest_log.get("gsmSignalPercent", "0")
    temp_val = latest_log.get("temp", "N/A")

    m1.metric("🔋 Akü Durumu", get_status_indicator(acc_val))
    m2.metric("📶 GSM Sinyali", get_status_indicator(gsm_val))
    m3.metric("🌡️ Cihaz Sıcaklığı", f"{temp_val} °C" if temp_val != "N/A" else "N/A")

    st.markdown("---")

    # --- SENSÖR GEÇMİŞİ VE PLOTLY GRAFİĞİ ---
    st.markdown("### 📈 Sensör Ölçümleri Zaman Serisi")

    df_logs = pd.DataFrame(selected_logs)

    if not df_logs.empty:
        # Sayısal Değerleri Dönüştür
        if "accumulatorPercent" in df_logs.columns:
            df_logs["accumulatorPercent"] = df_logs["accumulatorPercent"].apply(parse_percentage)
        if "gsmSignalPercent" in df_logs.columns:
            df_logs["gsmSignalPercent"] = df_logs["gsmSignalPercent"].apply(parse_percentage)
        if "temp" in df_logs.columns:
            df_logs["temp"] = pd.to_numeric(df_logs["temp"], errors="coerce")

        # Zaman Ekseni veya ID Ekseni Oluştur
        x_axis = "id"  # Tabloda timestamp sütunu yoksa primary key olan ID kullanılır
        if "created_at" in df_logs.columns:
            df_logs["created_at"] = pd.to_datetime(df_logs["created_at"])
            x_axis = "created_at"

        # Kontrol Barları (Birim Dönüştürücüler)
        ctrl_col1, ctrl_col2 = st.columns(2)
        temp_unit = ctrl_col1.radio("Sıcaklık Birimi:", ["°C", "°F"], horizontal=True)

        if "temp" in df_logs.columns and temp_unit == "°F":
            df_logs["temp"] = (df_logs["temp"] * 9/5) + 32

        # Metrik Seçimi
        available_metrics = []
        if "temp" in df_logs.columns:
            available_metrics.append("temp")
        if "accumulatorPercent" in df_logs.columns:
            available_metrics.append("accumulatorPercent")
        if "gsmSignalPercent" in df_logs.columns:
            available_metrics.append("gsmSignalPercent")

        if available_metrics:
            metric_names = {
                "temp": f"Sıcaklık ({temp_unit})",
                "accumulatorPercent": "Akü Seviyesi (%)",
                "gsmSignalPercent": "GSM Sinyal Seviyesi (%)"
            }
            selected_metric = ctrl_col2.selectbox(
                "Görselleştirilecek Metrik:", 
                available_metrics, 
                format_func=lambda x: metric_names.get(x, x)
            )

            # Plotly Grafiği
            fig = px.line(
                df_logs,
                x=x_axis,
                y=selected_metric,
                title=f"{selected_station_code} - {metric_names.get(selected_metric, selected_metric)} Zaman Serisi",
                markers=True,
                labels={x_axis: "Kayıt / Zaman", selected_metric: metric_names.get(selected_metric, selected_metric)}
            )
            fig.update_layout(hovermode="x unified", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Görselleştirilecek sayısal sensör verisi bulunamadı.")
    else:
        st.info("Seçilen istasyona ait kayıt bulunamadı.")


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
