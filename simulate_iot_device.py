import time
import random
import requests

API_URL = "http://127.0.0.1:8000/api/telemetry"

def start_simulation():
    print("🚀 SmartCam IoT Canlı Veri Simülatörü Başlatıldı...")
    while True:
        try:
            # İstasyon 1 - Sıcaklık & Nem
            requests.post(API_URL, json={"station_id": 1, "sensor_id": 1, "value": round(random.uniform(18.0, 28.0), 2)})
            requests.post(API_URL, json={"station_id": 1, "sensor_id": 2, "value": round(random.uniform(40.0, 75.0), 2)})

            # İstasyon 2 - Sıcaklık & Rüzgar
            requests.post(API_URL, json={"station_id": 2, "sensor_id": 4, "value": round(random.uniform(10.0, 22.0), 2)})
            requests.post(API_URL, json={"station_id": 2, "sensor_id": 5, "value": round(random.uniform(5.0, 45.0), 2)})

            print("📡 Canlı telemetri verileri MySQL veritabanına aktarıldı.")
        except Exception as e:
            print(f"❌ Veri gönderme hatası: {e}")
        time.sleep(5)

if __name__ == "__main__":
    start_simulation()
