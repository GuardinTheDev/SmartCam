import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
import os

# Sayfa Yapılandırması
st.set_page_config(
    page_title="SmartCam IoT Control Panel",
    page_icon="🎥",
    layout="wide"
)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/device/history")

st.title("SmartCam IoT Canlı İzleme Paneli")
st.markdown("---")

# Otomatik Yenileme / Veri Çekme Butonu
col_head1, col_head2 = st.columns([4, 1])
with col_head2:
    auto_refresh = st.checkbox("Canlı Yenileme (5s)", value=True)

# API'den Veri Çekme Fonksiyonu
def fetch_data():
    try:
        response = requests.get(f"{API_URL}?limit=20")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("API Bağlantı Hatası!")
            return []
    except Exception as e:
        st.error(f"API Sunucusuna Ulaşılamadı: {e}")
        return []

data = fetch_data()

if data:
    latest = data[0]  # En son gelen veri
    df_logs = pd.DataFrame(data) # DataFrame'i en başta oluşturuyoruz

    # 1. METRİK KARTLARI (Özet Bilgiler)
    st.subheader("Cihaz Anlık Durumu")
    m1, m2, m3, m4 = st.columns(4) # Sütun değişkenlerini tanımlıyoruz
    
    ist_code_val = latest.get("ist_code", "N/A")
    temp_val = latest.get("temp", "0")
    acc_val = int(latest.get("battery_percent", 0))
    gsm_val = int(latest.get("gsm_signal", 0))

    # Batarya Durumu (Mükemmel / Normal / Düşük)
    if acc_val >= 70:
        bat_status = "🟢"
        bat_delta = f"+%{acc_val} (İyi)"
    elif acc_val >= 30:
        bat_status = "🟡"
        bat_delta = f"%{acc_val} (Normal)"
    else:
        bat_status = "🔴"
        bat_delta = f"-%{acc_val} (Düşük!)"

    # GSM Sinyal Durumu
    if gsm_val >= 60:
        gsm_status = "🟢"
        gsm_delta = f"%{gsm_val} (Mükemmel)"
    elif gsm_val >= 30:
        gsm_status = "🟡"
        gsm_delta = f"%{gsm_val} (Orta)"
    else:
        gsm_status = "🔴"
        gsm_delta = f"%{gsm_val} (Çok Düşük!)"
    # -----------------------------

    m1.metric(label="Cihaz Kodu", value=str(ist_code_val))
    m2.metric(label="Sıcaklık (°C)", value=f"{temp_val} °C")
    
    # Delta parametresi sayesinde yüzdelere durum metni ve renkli göstergeler ekliyoruz
    m3.metric(
        label=f"Batarya ({bat_status})", 
        value=f"%{acc_val}", 
        delta=bat_delta,
        delta_color="normal" if acc_val >= 30 else "inverse"
    )
    
    m4.metric(
        label=f"GSM Sinyali ({gsm_status})", 
        value=f"%{gsm_val}", 
        delta=gsm_delta,
        delta_color="normal" if gsm_val >= 30 else "inverse"
    )
    
    st.markdown("---")

    # 2. GRAFİKLER
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("🌡️ Sıcaklık Değişimi")
        if "temp" in df_logs.columns and "created_at" in df_logs.columns:
            df_logs["temp"] = pd.to_numeric(df_logs["temp"], errors='coerce')
            fig_temp = px.line(
                df_logs, 
                x="created_at", 
                y="temp", 
                title="Zamana Göre Sıcaklık (°C)",
                markers=True
            )
            st.plotly_chart(fig_temp, width="stretch")

    with col_chart2:
        st.subheader("🔋 Batarya Trendi")
        if "battery_percent" in df_logs.columns:
            df_logs["battery_percent"] = pd.to_numeric(df_logs["battery_percent"], errors='coerce').fillna(0)
            fig_bat = px.bar(
                df_logs, 
                x="created_at", 
                y="battery_percent",
                title="Batarya Yüzdesi Geçmişi",
                color="battery_percent",
                color_continuous_scale="RdYlGn",
                labels={"battery_percent": "Batarya %"}
            )
            st.plotly_chart(fig_bat, width="stretch")

    st.markdown("---")

    # 3. GÜVENLİ VERİ TABLOSU
    st.subheader("📋 Son Veri Kayıtları")
    desired_columns = ["id", "ist_code", "temp", "battery_percent", "gsm_signal", "ip_address", "created_at"]
    available_columns = [col for col in desired_columns if col in df_logs.columns]
    
    if available_columns:
        st.dataframe(df_logs[available_columns], width="stretch")
    else:
        st.dataframe(df_logs, width="stretch")

# Otomatik Yenileme Döngüsü
if auto_refresh:
    time.sleep(5)
    st.rerun()