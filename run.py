import subprocess
import sys
import time
import os
import urllib.request
import json
import webbrowser

def get_ngrok_url():
    try:
        req = urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=3)
        data = json.loads(req.read().decode('utf-8'))
        tunnels = data.get('tunnels', [])
        if tunnels:
            return tunnels[0].get('public_url')
    except Exception:
        pass
    return None

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    os.chdir(BASE_DIR)

    print("=================================================")
    print("🚀 SmartCam IoT Platformu (Fix) — Tek Komut Başlatıcı")
    print("=================================================")

    # Çevre değişkenlerinin çakışmasını önle
    os.environ.pop("VIRTUAL_ENV", None)
    os.environ.pop("PYTHONPATH", None)
    os.environ.pop("PYTHONHOME", None)

    venv_python = os.path.join(BASE_DIR, "venv", "bin", "python")
    venv_streamlit = os.path.join(BASE_DIR, "venv", "bin", "streamlit")

    if os.path.exists(venv_python):
        python_bin = venv_python
    else:
        python_bin = sys.executable

    if os.path.exists(venv_streamlit):
        streamlit_bin = venv_streamlit
    else:
        streamlit_bin = "streamlit"

    ngrok_bin = "ngrok"
    user_home = os.path.expanduser("~")
    if os.path.exists(f"{user_home}/.local/bin/ngrok"):
        ngrok_bin = f"{user_home}/.local/bin/ngrok"

    processes = []
    try:
        # 1. FastAPI Backend
        print("⚡ [1/3] FastAPI Backend başlatılıyor (Port 8000)...")
        p_backend = subprocess.Popen([python_bin, "main.py"])
        processes.append(p_backend)
        time.sleep(2)

        # 2. Streamlit Frontend (headless=true ile localhost sekmesi engellenir)
        print("💻 [2/3] Streamlit Dashboard başlatılıyor (Port 8501)...")
        p_frontend = subprocess.Popen([streamlit_bin, "run", "app.py", "--server.port", "8501", "--server.headless", "true"])
        processes.append(p_frontend)
        time.sleep(2)

        # 3. Ngrok Tüneli ve Otomatik Tarayıcı Açımı
        print("🌍 [3/3] Ngrok Canlı Yayın Tüneli başlatılıyor...")
        try:
            p_ngrok = subprocess.Popen([ngrok_bin, "http", "8501"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            processes.append(p_ngrok)
            time.sleep(3)
        except Exception as e:
            print(f"⚠️ Ngrok başlatılamadı: {e}")

        ngrok_url = get_ngrok_url()

        print("\n=================================================")
        print("✅ Tüm servisler ve Ngrok aktif!")
        print("🌐 Lokal Arayüz      : http://localhost:8501")
        print("🔌 Backend API Docs  : http://localhost:8000/docs")
        if ngrok_url:
            print(f"🌍 CANLI NGROK ADRESİ: {ngrok_url}")
            print("🚀 Ngrok Adresi Tarayıcıda Otomatik Açılıyor...")
            webbrowser.open(ngrok_url)
        print("=================================================")
        print("Durdurmak için Ctrl+C tuşlarına basınız.\n")

        for p in processes:
            p.wait()

    except KeyboardInterrupt:
        print("\n🛑 Servisler ve Ngrok kapatılıyor...")
        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass
        print("✅ Tüm servisler kapatıldı.")

if __name__ == "__main__":
    main()
