import requests
import time
import random

# Backend API Endpoint
API_URL = "http://127.0.0.1:8000/api/device/data"

# Test için veritabanında kayıtlı olan İstasyon Güvenlik Kodu ve IMEI
SECURITY_CODE = "zwx9x5PcMl"
IMEI = "861234567890123"

def generate_telemetry_payload(is_valid: bool = True):
    sec_code = SECURITY_CODE if is_valid else "HATALI_GUVENLIK_KODU"
    return {
        "istCode": "IST_BARAJ_01",
        "securityCode": sec_code,
        "runType": "NORMAL",
        "tVer": "v2.1.0",
        "model": "SmartCam-IoT-v1",
        "board": "ESP32-S3",
        "gsmNo": "05551112233",
        "ip": f"192.168.1.{random.randint(10, 200)}",
        "accumulatorPercent": random.randint(40, 100),
        "gsmSignalPercent": str(random.randint(50, 99)),
        "regionNo": "01",
        "basinNo": "05",
        "departmentId": "10",
        "tag": "BARAJ_SENSOR_PAKETI",
        "in": "[]",
        "out": "[]",
        "temp": str(round(random.uniform(15.0, 32.0), 1)),
        "imei": IMEI,
        "jVer": "1.0",
        "sensorData": {
            "1": ["0", "0", "0", "0", str(int(time.time())), str(round(random.uniform(20.0, 25.5), 2)), "0", "85", "90", "[21,22,23]"],
            "2": ["0", "0", "0", "0", str(int(time.time())), str(round(random.uniform(100.0, 150.0), 2)), "0", "85", "90", "[120,130]"]
        }
    }

def start_simulation():
    print("==================================================", flush=True)
    print("🚀 IoT Cihaz Simülatörü Başlatıldı!", flush=True)
    print("Her 5 saniyede bir canlı telemetri paketi gönderilecek.", flush=True)
    print("Durdurmak için klavyeden [Ctrl + C] yapabilirsiniz.", flush=True)
    print("==================================================\n", flush=True)

    counter = 1
    while True:
        send_valid = False if counter % 5 == 0 else True
        payload = generate_telemetry_payload(is_valid=send_valid)
        print(f"[{counter}. Paket] Sunucuya gönderiliyor...", end=" ", flush=True)
        try:
            response = requests.post(API_URL, json=payload, timeout=5)
            if response.status_code == 200:
                print(f"✅ BAŞARILI (200 OK) -> {response.json()['message']}", flush=True)
                print(f"   📊 Gönderilen Akü: %{payload['accumulatorPercent']} | GSM: %{payload['gsmSignalPercent']} | Sıcaklık: {payload['sensorData']['1'][5]} °C", flush=True)
            elif response.status_code == 401:
                print(f"🛑 REDDEDİLDİ (401 Unauthorized - Beklenen Güvenlik Testi) -> {response.json()['detail']}", flush=True)
            else:
                print(f"⚠️ HATA ({response.status_code}) -> {response.text}", flush=True)
        except requests.exceptions.ConnectionError:
            print("🚨 BAĞLANTI HATASI: Backend sunucusu (main.py) açık mı? Lütfen önce 'python main.py' çalıştırın!", flush=True)
        except Exception as e:
            print(f"🚨 Hata oluştu: {str(e)}", flush=True)
            
        print("-" * 60, flush=True)
        counter += 1
        time.sleep(5)

if __name__ == "__main__":
    start_simulation()
