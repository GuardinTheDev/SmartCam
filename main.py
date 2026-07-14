from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List
from contextlib import asynccontextmanager
import smartcam_db as database

# Modern lifespan yapısı ile veritabanı kontrolü
@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    print("Veritabanı kontrol edildi ve hazırlandı.")
    yield

app = FastAPI(title="SmartCam IoT API", lifespan=lifespan)

# Arkadaşının tarayıcıdan senin API'ne takılmadan erişebilmesi için CORS ayarı
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gelen veri paketi doğrulama modeli
class IoTDataPayload(BaseModel):
    istCode: str
    securityCode: str
    runType: str
    tVer: str
    model: str
    board: str
    gsmNo: str
    ip: str
    accumulatorPercent: int
    gsmSignalPercent: str
    regionNo: str
    basinNo: str
    departmentId: str
    tag: str
    in_status: str = Field(default="[]", alias="in")
    out_status: str = Field(default="[]", alias="out")
    temp: str
    imei: str
    jVer: str
    sensorData: Dict[str, List[str]]

# Cihazdan veri alan POST uç noktası
@app.post("/api/device/data")
async def receive_device_data(payload: IoTDataPayload):
    if payload.securityCode != "zwx9x5PcMl":
        raise HTTPException(status_code=401, detail="Yetkisiz Cihaz")
    
    try:
        database.save_payload_to_db(payload.model_dump())
        print(f"[{payload.istCode}] verisi SQL'e başarıyla kaydedildi.")
        return {"status": "success", "message": "Veri SQL'e yazıldı."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {str(e)}")

# Son gelen verileri arayüze sunan GET uç noktası
@app.get("/api/device/history")
async def get_device_history(limit: int = 10):
    try:
        import sqlite3
        conn = sqlite3.connect("sensor_data.db")
        # Sonuçları dict (sözlük) formatında kolayca okumak için row_factory ekliyoruz
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Son eklenen ana logları getir
        cursor.execute("SELECT * FROM device_logs ORDER BY id DESC LIMIT ?", (limit,))
        logs = [dict(row) for row in cursor.fetchall()]
        
        # Her bir ana log için altındaki sensör detaylarını da çekip ekleyelim
        for log in logs:
            cursor.execute("SELECT * FROM sensor_logs WHERE device_log_id = ?", (log["id"],))
            log["sensorData"] = [dict(row) for row in cursor.fetchall()]
            
        conn.close()
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veri getirme hatası: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)