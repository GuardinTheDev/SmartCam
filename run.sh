#!/usr/bin/env bash

# =================================================================
# 🚀 SmartCam IoT Platformu — Tek Komutla Çalıştırma Scripti
# =================================================================

# Hata oluştuğunda veya Ctrl+C yapıldığında tüm servisleri sonlandır
cleanup() {
    echo ""
    echo "🛑 Tüm servisler ve Ngrok kapatılıyor..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

echo "================================================="
echo "📡 SmartCam IoT Platformu Başlatılıyor..."
echo "================================================="

# Binaries ve PATH kontrolü
PYTHON_BIN="./venv/bin/python"
STREAMLIT_BIN="./venv/bin/streamlit"
NGROK_BIN=$(which ngrok 2>/dev/null || echo "$HOME/.local/bin/ngrok")

if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
    STREAMLIT_BIN="streamlit"
fi

# 1. Backend (FastAPI - Port 8000)
echo "⚡ 1/3: FastAPI Backend Başlatılıyor (Port 8000)..."
$PYTHON_BIN main.py &
sleep 2

# 2. Frontend (Streamlit - Port 8501, headless=true olarak başlatılır ki localhost sekmesi açılmasın)
echo "💻 2/3: Streamlit Frontend Başlatılıyor (Port 8501)..."
$STREAMLIT_BIN run app.py --server.port 8501 --server.headless true &
sleep 2

# 3. Ngrok Tüneli (Port 8501) ve Otomatik Tarayıcı Açma
NGROK_URL=""
if [ -x "$NGROK_BIN" ]; then
    echo "🌍 3/3: Ngrok Tüneli Başlatılıyor (8501)..."
    $NGROK_BIN http 8501 > /dev/null 2>&1 &
    sleep 3
    NGROK_URL=$($PYTHON_BIN -c "import urllib.request, json; print(json.loads(urllib.request.urlopen('http://127.0.0.1:4040/api/tunnels').read().decode())['tunnels'][0]['public_url'])" 2>/dev/null)
else
    echo "⚠️ Ngrok bulunamadı, tünel başlatılamadı."
fi

echo ""
echo "================================================="
echo "✅ Tüm servisler çalışıyor!"
echo "🌐 Lokal Arayüz      : http://localhost:8501"
echo "🔌 Backend API (Docs): http://localhost:8000/docs"

if [ -n "$NGROK_URL" ]; then
    echo "🌍 CANLI NGROK ADRESİ: $NGROK_URL"
    echo "🚀 Ngrok Adresi Tarayıcıda Otomatik Açılıyor..."
    echo "================================================="
    
    # Tarayıcıda varsayılan olarak NGROK adresini aç
    if command -v xdg-open > /dev/null; then
        xdg-open "$NGROK_URL" > /dev/null 2>&1
    else
        $PYTHON_BIN -m webbrowser "$NGROK_URL" > /dev/null 2>&1
    fi
else
    echo "================================================="
fi

echo "Durdurmak için klavyeden [Ctrl + C] tuşlarına basabilirsiniz."
echo ""

# Servisleri açık tut
wait
