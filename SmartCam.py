import os
import time
import json
import random
import requests

TARGET_URL = os.getenv("TARGET_URL", "http://127.0.0.1:8000/api/device/data")

def generate_sensor_array(base_val, deviance, precision=3):
    """Belirlenen baz değer etrafında küçük sapmalarla 10 adetlik ölçüm dizisi üretir."""
    arr = [round(base_val + random.uniform(-deviance, deviance), precision) for _ in range(10)]
    return arr

def run_device_simulator(interval_seconds=5):
    print(" IoT Cihaz Simülasyonu Başlatıldı ")
    
    # Sabit Cihaz Bilgileri
    device_info = {
        "istCode": "21000261",
        "securityCode": "zwx9x5PcMl",
        "runType": "3",
        "tVer": "13.0.0",
        "model": "SmartCam",
        "board": "SC10058",
        "gsmNo": "05356672248",
        "ip": "5.26.121.59",
        "regionNo": "21",
        "basinNo": "13",
        "departmentId": "12068",
        "tag": "INSDATA",
        "in": "[0,0]",
        "out": "[0,1]",
        "imei": "861234567890123",
        "jVer": "S1.000"
    }

    # Dinamik olarak değişecek başlangıç değerleri
    battery = 94
    signal = 77
    temp = 42.35

    while True:
        current_time = int(time.time())

        # Değerlerde gerçekçi küçük dalgalanmalar yapalım
        battery = max(10, min(100, battery + random.choice([-1, 0, 0, 0, 1]))) # Batarya yavaşça değişir
        signal = max(50, min(100, signal + random.randint(-3, 3)))
        temp = round(temp + random.uniform(-0.15, 0.15), 2)

        # 10'ar adetlik anlık ölçüm dizileri üretme
        s1_list = generate_sensor_array(28.85, 0.5, precision=2)  # Sıcaklık (Kanal 1)
        s2_list = generate_sensor_array(150.0, 1.2, precision=1)  # Su Seviyesi (Kanal 2)
        s3_list = generate_sensor_array(3.40, 0.05, precision=3)  # Basınç / Debi (Kanal 3)

        # Dizilerin ortalamasını hesaplama (Cihazın gönderdiği formatta string olarak)
        s1_avg = str(round(sum(s1_list) / len(s1_list), 2))
        s2_avg = str(round(sum(s2_list) / len(s2_list), 1))
        s3_avg = str(round(sum(s3_list) / len(s3_list), 3))

        # JSON formatına uygun hale getirmek için listeleri string'e çeviriyoruz
        s1_str = "[" + ",".join(f"{x:.2f}" for x in s1_list) + "]"
        s2_str = "[" + ",".join(f"{x:.1f}" for x in s2_list) + "]"
        s3_str = "[" + ",".join(f"{x:.3f}" for x in s3_list) + "]"

        # Tüm veriyi birleştirme
        payload = {
            **device_info,
            "accumulatorPercent": battery,
            "gsmSignalPercent": str(signal),
            "temp": f"{temp:.2f}",
            "sensorData": {
                "1": [
                    "3", "1", "6", "3", 
                    str(current_time), 
                    s1_avg, 
                    "9", str(battery), str(signal), 
                    s1_str, 
                    "3"
                ],
                "2": [
                    "3", "1", "20", "3", 
                    str(current_time), 
                    s2_avg, 
                    "10", str(battery), str(signal), 
                    s2_str, 
                    "2"
                ],
                "3": [
                    "3", "1", "18", "3", 
                    str(current_time), 
                    s3_avg, 
                    "5", str(battery), str(signal), 
                    s3_str, 
                    "1"
                ]
            }
        }

        # Terminale yazdır
        print(f"\n[{time.strftime('%H:%M:%S')}] Yeni Veri Paketi Üretildi:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))

        if TARGET_URL:
            try:
                response = requests.post(TARGET_URL, json=payload, timeout=5)
                print(f"-> Sunucu Yanıtı: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"-> Sunucuya gönderim başarısız: {e}")

        # Bir sonraki gönderim için bekle
        time.sleep(interval_seconds)    

if __name__ == "__main__":
    run_device_simulator(interval_seconds=5)
