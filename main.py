from fastapi import FastAPI, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from contextlib import asynccontextmanager
import smartcam_db as database
import sqlite3


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield

app = FastAPI(title="SmartCam Telemetri API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PYDANTIC VERİ MODELLERİ ---
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

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str

class UserApprovalRequest(BaseModel):
    user_id: int
    action: str  # 'approve' veya 'reject'

class StationCreateRequest(BaseModel):
    category_id: int
    name: str
    imei: str
    phone_number: Optional[str] = ""
    device_type: Optional[str] = "Gateway"


# --- 1. CİHAZ PAKET ALMA ENDPOINT'İ ---
@app.post("/api/device/data")
async def receive_device_data(payload: IoTDataPayload):
    # Dinamik Güvenlik Kodu & IMEI Doğrulaması
    station = database.verify_station(payload.securityCode, payload.imei)
    
    if not station:
        # Paket yanlış/yetkisiz ise ilgili yerler kesinlikle güncellenmeyecek!
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Yetkisiz veya Tanımsız İstasyon! Güvenlik kodu / IMEI eşleşmiyor."
        )

    try:
        database.process_valid_payload(station["id"], payload.model_dump())
        return {
            "status": "success", 
            "message": f"[{station['name']}] verileri veritabanına işlendi."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veritabanı işleme hatası: {str(e)}")


# --- 2. KULLANICI KAYIT OLMA (REGISTER - ADMİN ONAYINA GİDER) ---
@app.post("/api/auth/register")
async def register_user(credentials: RegisterRequest):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, role, status) VALUES (?, ?, 'user', 'pending')", 
            (credentials.username, credentials.password)
        )
        conn.commit()
        conn.close()
        return {
            "status": "success", 
            "message": f"Kayıt isteğiniz alındı! '{credentials.username}' kullanıcısı Admin onayı bekliyor."
        }
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten alınmış!")


# --- 3. KULLANICI GİRİŞİ (LOGIN - ONAYLI MI KONTROL EDER) ---
@app.post("/api/auth/login")
async def login(credentials: LoginRequest):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?", 
        (credentials.username, credentials.password)
    )
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Hatalı kullanıcı adı veya şifre!")
    
    user_dict = dict(user)
    
    # ONAY DURUM KONTROLÜ
    if user_dict["status"] == "pending":
        raise HTTPException(status_code=403, detail="Hesabınız henüz Admin tarafından onaylanmadı! Lütfen bekleyin.")
    elif user_dict["status"] == "rejected":
        raise HTTPException(status_code=403, detail="Kayıt başvurunuz Admin tarafından reddedildi.")
    
    return {
        "status": "success", 
        "message": "Giriş başarılı", 
        "username": user_dict["username"],
        "role": user_dict["role"]
    }


# --- 4. ADMİN İÇİN ONAY BEKLEYEN KULLANICILARI LİSTELEME ---
@app.get("/api/admin/pending-users")
async def get_pending_users():
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, status, created_at FROM users WHERE status = 'pending'")
    pending_users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return pending_users


# --- 5. ADMİN İÇİN KULLANICI ONAYLAMA / REDDETME ---
@app.post("/api/admin/approve-user")
async def approve_or_reject_user(req: UserApprovalRequest):
    if req.action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Geçersiz işlem! 'approve' veya 'reject' olmalı.")
        
    new_status = "approved" if req.action == "approve" else "rejected"
    
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, req.user_id))
    conn.commit()
    conn.close()
    
    action_text = "onaylandı" if req.action == "approve" else "reddedildi"
    return {"status": "success", "message": f"Kullanıcı başvurusu {action_text}."}


# --- 6. ARAYÜZ İÇİN İSTASYON LİSTESİ ---
@app.get("/api/stations")
async def get_stations():
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, c.name as category_name 
        FROM stations s
        LEFT JOIN station_categories c ON s.category_id = c.id
    ''')
    stations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return stations


# --- 7. ARAYÜZ İÇİN GRAFİK VERİSİ ---
@app.get("/api/sensor/history")
async def get_sensor_history(station_id: int = 1, limit: int = 50):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM sensor_logs 
        WHERE station_id = ? 
        ORDER BY id DESC LIMIT ?
    ''', (station_id, limit))
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return logs


# --- 8. YENİ İSTASYON VE VARSAYILAN SENSÖRLERİNİ EKLEME ---
@app.post("/api/stations")
async def create_station(station: StationCreateRequest):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    # SYSTEM OTOMATİK OLARAK 128 KARAKTERLİK HASH KODUNU ÜRETİR
    auto_security_code = database.generate_secure_token()
    
    try:
        # 1. Yeni İstasyonu Kaydet (Otomatik Hash Kodu İle)
        cursor.execute('''
            INSERT INTO stations (category_id, name, security_code, imei, phone_number, device_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            station.category_id, 
            station.name, 
            auto_security_code,
            station.imei, 
            station.phone_number, 
            station.device_type
        ))
        
        new_station_id = cursor.lastrowid
        
        # 2. İstasyona Varsayılan 0 Değerli Sensörleri Ekle
        default_sensors = [
            (new_station_id, 1, "Sıcaklık", 101, "temperature", "celsius", 0),
            (new_station_id, 2, "Su Seviyesi", 102, "level", "cm", 0),
            (new_station_id, 3, "Basınç / Debi", 103, "pressure", "bar", 0)
        ]
        
        cursor.executemany('''
            INSERT INTO sensors (station_id, sequence_number, label, channel_category_id, unit_type, default_unit, default_value)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', default_sensors)
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success", 
            "message": f"'{station.name}' istasyonu ve varsayılan sensörleri oluşturuldu.",
            "station_id": new_station_id,
            "generated_security_code": auto_security_code
        }
        
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(
            status_code=400, 
            detail="Bu IMEI numarası zaten başka bir istasyonda kayıtlı!"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
