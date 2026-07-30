# 📡 SmartCam IoT Telemetri & SCADA Takip Sistemi

Bu proje, IoT cihazlarından telemetri verisi toplayan FastAPI tabanlı backend, sahadaki cihazları simüle eden IoT aracı ve verileri canlı görselleştiren Streamlit arayüzünü içerir.

---

## 🚀 Kurulum ve Çalıştırma Adımları (Virtual Environment / venv)

Projenin bilgisayarınızdaki diğer Python kütüphaneleriyle çakışmaması ve izole bir ortamda sorunsuz çalışması için **`venv` (Virtual Environment)** kullanılması önerilir.

### 1. Sanal Ortam Oluşturma ve Aktif Etme

**Linux / macOS İçin:**
```bash
# 1. venv klasörünü oluşturun
python3 -m venv venv

# 2. Sanal ortamı aktif edin
source venv/bin/activate
```

**Windows İçin:**
```cmd
:: 1. venv klasörünü oluşturun
python -m venv venv

:: 2. Sanal ortamı aktif edin (Command Prompt / PowerShell)
venv\Scripts\activate
```

> 💡 **Not:** Ortam aktifleştiğinde terminal satırınızın başında `(venv)` ibaresi belirecektir.

---

### 2. Bağımlılıkların (Requirements) Yüklenmesi

Sanal ortam aktifken gerekli kütüphaneleri yükleyin:
```bash
pip install -r requirements.txt
```

---

### 3. Proje Bileşenlerini Çalıştırma

Projeyi çalıştırmak için 3 ayrı terminal açıp sanal ortamı (`activate`) aktif ettikten sonra sırasıyla şu komutları çalıştırın:

1. **Backend Sunucusunu Başlatın (Port 8000):**
   ```bash
   python main.py
   ```

2. **IoT Cihaz Simülatörünü Başlatın (Canlı Veri Akışı İçin):**
   ```bash
   python simulate_iot_device.py
   ```

3. **Streamlit Arayüzünü Başlatın (Port 8501):**
   ```bash
   streamlit run app.py
   ```

---

### 🚪 Sanal Ortamdan Çıkış
Çalışmanız bittiğinde sanal ortamı kapatmak için terminalde:
```bash
deactivate
```
yazmanız yeterlidir.
