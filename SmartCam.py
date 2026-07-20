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
        "imei": "868628076823839",
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
        s0_list = generate_sensor_array(287.85, 0.01, precision=3)
        s1_list = generate_sensor_array(13.1, 0.0, precision=1) # Genelde sabit 13.1
        s2_list = generate_sensor_array(436.017, 0.003, precision=3)

        # Dizilerin ortalamasını hesaplama (Cihazın gönderdiği formatta string olarak)
        s0_avg = str(round(sum(s0_list) / len(s0_list), 5))
        s1_avg = str(round(sum(s1_list) / len(s1_list), 1))
        s2_avg = str(round(sum(s2_list) / len(s2_list), 6))

        # JSON formatına uygun hale getirmek için listeleri string'e çeviriyoruz
        s0_str = "[" + ",".join(f"{x:.3f}" for x in s0_list) + "]"
        s1_str = "[" + ",".join(f"{x:.3f}" for x in s1_list) + "]"
        s2_str = "[" + ",".join(f"{x:.3f}" for x in s2_list) + "]"

        # Tüm veriyi birleştirme
        payload = {
            **device_info,
            "accumulatorPercent": battery,
            "gsmSignalPercent": str(signal),
            "temp": f"{temp:.2f}",
            "sensorData": {
                "0": [
                    "3", "1", "6", "3", 
                    str(current_time), 
                    s0_avg, 
                    "9", str(battery), str(signal), 
                    s0_str, 
                    "3"
                ],
                "1": [
                    "3", "1", "20", "3", 
                    str(current_time), 
                    s1_avg, 
                    "10", str(battery), str(signal), 
                    s1_str, 
                    "2"
                ],
                "2": [
                    "3", "1", "18", "3", 
                    str(current_time), 
                    s2_avg, 
                    "5", str(battery), str(signal), 
                    s2_str, 
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