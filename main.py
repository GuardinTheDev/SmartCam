from fastapi import FastAPI, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from contextlib import asynccontextmanager
import smartcam_db as database
import sqlite3
import hashlib
import time
import io
import base64
import pyotp
import qrcode
import random
import uuid

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
    totp_code: Optional[str] = None
    remember_me: Optional[bool] = False

class ValidateSessionRequest(BaseModel):
    username: str
    session_token: str

class SendOTPRequest(BaseModel):
    username: str
    channel: str  # 'email' veya 'phone'

class VerifyOTPRequest(BaseModel):
    username: str
    channel: str  # 'email' veya 'phone'
    code: str

class Setup2FARequest(BaseModel):
    username: str

class Verify2FARequest(BaseModel):
    username: str
    code: str

class Disable2FARequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    email: str
    phone: str
    kvkk_approved: bool

class UserApprovalRequest(BaseModel):
    user_id: int
    action: str  # 'approve' veya 'reject'

def validate_password_strength(password: str, username: str = "", full_name: str = ""):
    if len(password) < 6:
        return False, "Şifre en az 6 karakter uzunluğunda olmalıdır!"
    
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    if not (has_letter and has_digit):
        return False, "Şifre en az bir harf ve bir rakam içermelidir (Örn: Smart123)!"

    weak_patterns = ["123", "321", "abc", "qwerty", "admin", "password", "sifre"]
    user_lower = username.lower().strip() if username else ""
    full_lower = full_name.lower().replace(" ", "").strip() if full_name else ""
    pass_lower = password.lower().strip()

    if user_lower and user_lower in pass_lower:
        return False, f"Şifreniz kullanıcı adınızı ('{username}') içeremez! 'ad123' gibi basit şifreler yasaktır."

    if full_lower and full_lower in pass_lower:
        return False, "Şifreniz adınızı veya soyadınızı içeremez."

    for pattern in weak_patterns:
        if pass_lower == f"{user_lower}{pattern}" or pass_lower == f"{pattern}{user_lower}" or pass_lower == pattern:
            return False, f"Şifreniz '{pattern}' gibi çok basit kalıplar içeremez."

    return True, "Şifre güçlü."

class StationCreateRequest(BaseModel):
    category_id: int
    name: str
    imei: Optional[str] = None
    phone_number: Optional[str] = ""
    device_type: Optional[str] = "Gateway"

class SensorCreateRequest(BaseModel):
    id: Optional[int] = None                        # Cihazın sensorData anahtarı (Kanal ID) olarak göndereceği numara
    station_id: int
    label: str                                      
    sequence_number: Optional[int] = None          
    channel_category_id: Optional[int] = 100
    unit_type: Optional[str] = "custom"
    default_unit: Optional[str] = "unit"
    default_value: Optional[float] = 0.0


# --- 1. CİHAZ PAKET ALMA ENDPOINT'İ ---
@app.post("/api/device/data")
async def receive_device_data(payload: IoTDataPayload):
    station = database.verify_station(payload.securityCode, payload.imei)
    
    if not station:
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


# --- 2. KULLANICI KAYIT OLMA (REGISTER - AKILLI VE ESNEK KAYIT) ---
@app.post("/api/auth/register")
async def register_user(credentials: RegisterRequest):
    # 1. KVKK Onay Kontrolü
    if not credentials.kvkk_approved:
        raise HTTPException(status_code=400, detail="Kayıt olmak için KVKK Aydınlatma Metni'ni onaylamanız gerekmektedir!")

    # 2. Güçlü Şifre Kontrolü
    is_strong, msg = validate_password_strength(credentials.password, credentials.username, credentials.full_name)
    if not is_strong:
        raise HTTPException(status_code=400, detail=msg)

    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    # 3. Önce bu kullanıcı adı daha önce alınmış mı bakalım
    cursor.execute("SELECT id, status FROM users WHERE username = ?", (credentials.username,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        user_dict = dict(existing_user)
        if user_dict["status"] == "rejected":
            cursor.execute("DELETE FROM users WHERE id = ?", (user_dict["id"],))
        else:
            conn.close()
            raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten alınmış veya onay bekliyor!")
            
    try:
        email_otp = str(random.randint(100000, 999999))
        phone_otp = str(random.randint(100000, 999999))

        cursor.execute(
            '''INSERT INTO users 
               (username, password, full_name, email, phone, kvkk_approved, role, status, email_otp, phone_otp, email_verified, phone_verified) 
               VALUES (?, ?, ?, ?, ?, ?, 'user', 'pending', ?, ?, 0, 0)''', 
            (
                credentials.username, 
                credentials.password, 
                credentials.full_name, 
                credentials.email, 
                credentials.phone, 
                1 if credentials.kvkk_approved else 0,
                email_otp,
                phone_otp
            )
        )
        conn.commit()
        conn.close()
        return {
            "status": "success", 
            "message": f"Kayıt isteğiniz alındı! '{credentials.username}' ({credentials.full_name}) kullanıcısı Admin onayı bekliyor.",
            "email_otp_demo": email_otp,
            "phone_otp_demo": phone_otp
        }
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten alınmış!")


# --- 2.1. E-POSTA / TELEFON OTP KODU GÖNDERME ---
@app.post("/api/auth/send-otp")
async def send_otp(req: SendOTPRequest):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, phone FROM users WHERE username = ?", (req.username,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı!")

    new_otp = str(random.randint(100000, 999999))
    col_name = "email_otp" if req.channel == "email" else "phone_otp"
    
    cursor.execute(f"UPDATE users SET {col_name} = ? WHERE id = ?", (new_otp, user["id"]))
    conn.commit()
    conn.close()
    
    target_info = user["email"] if req.channel == "email" else user["phone"]
    return {
        "status": "success",
        "message": f"{'E-Posta' if req.channel == 'email' else 'Telefon'} ({target_info}) için 6 haneli doğrulama kodu gönderildi.",
        "otp_demo": new_otp
    }


# --- 2.2. E-POSTA / TELEFON OTP KODU DOĞRULAMA ---
@app.post("/api/auth/verify-otp")
async def verify_otp(req: VerifyOTPRequest):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    col_otp = "email_otp" if req.channel == "email" else "phone_otp"
    col_ver = "email_verified" if req.channel == "email" else "phone_verified"
    
    cursor.execute(f"SELECT id, {col_otp} FROM users WHERE username = ?", (req.username,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı!")
        
    saved_otp = user[col_otp]
    if saved_otp and saved_otp.strip() == req.code.strip():
        cursor.execute(f"UPDATE users SET {col_ver} = 1 WHERE id = ?", (user["id"],))
        conn.commit()
        conn.close()
        return {
            "status": "success",
            "message": f"✅ {'E-Posta' if req.channel == 'email' else 'Telefon'} başarıyla doğrulandı!"
        }
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Hatalı doğrulama kodu! Lütfen kontrol edip tekrar deneyiniz.")


# --- 3. KULLANICI GİRİŞİ (LOGIN - 2FA & BENİ HATIRLA DESTEKLİ) ---
@app.post("/api/auth/login")
async def login(credentials: LoginRequest):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    identifier = credentials.username.strip()
    clean_phone = identifier.replace(" ", "")
    cursor.execute(
        '''SELECT * FROM users 
           WHERE (LOWER(TRIM(username)) = LOWER(?) 
                  OR LOWER(TRIM(email)) = LOWER(?) 
                  OR REPLACE(phone, ' ', '') = ? 
                  OR LOWER(TRIM(full_name)) = LOWER(?)) 
             AND password = ?''', 
        (identifier, identifier, clean_phone, identifier, credentials.password)
    )
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Hatalı kullanıcı bilgisi veya şifre!")
    
    user_dict = dict(user)
    
    # ONAY DURUM KONTROLÜ
    if user_dict["status"] == "pending":
        raise HTTPException(status_code=403, detail="Hesabınız henüz Admin tarafından onaylanmadı! Lütfen bekleyin.")
    elif user_dict["status"] == "rejected":
        raise HTTPException(status_code=403, detail="Kayıt başvurunuz Admin tarafından reddedildi.")
    
    # 2FA (İKİ AŞAMALI DOĞRULAMA) KONTROLÜ
    is_2fa_enabled = bool(user_dict.get("is_2fa_enabled"))
    if is_2fa_enabled:
        totp_secret = user_dict.get("totp_secret")
        if not credentials.totp_code:
            return {
                "status": "2fa_required",
                "message": "İki aşamalı doğrulama (2FA) gereklidir.",
                "username": user_dict["username"]
            }
        
        # TOTP Doğrulama
        totp = pyotp.TOTP(totp_secret)
        if not totp.verify(credentials.totp_code.strip()):
            raise HTTPException(status_code=400, detail="Hatalı 2FA doğrulama kodu! Lütfen Authenticator uygulamanızı kontrol edin.")

    # TEK AKTİF OTURUM (SINGLE SESSION ENFORCEMENT)
    new_session_token = uuid.uuid4().hex
    conn_up = database.get_db_connection()
    cur_up = conn_up.cursor()
    cur_up.execute("UPDATE users SET current_session_token = ? WHERE id = ?", (new_session_token, user_dict["id"]))
    conn_up.commit()
    conn_up.close()

    # Beni Hatırla: True ise 7 gün (604800 sn), False ise 1 saat (3600 sn)
    expires_in_seconds = (7 * 24 * 3600) if credentials.remember_me else 3600

    return {
        "status": "success", 
        "message": "Giriş başarılı", 
        "username": user_dict["username"],
        "role": user_dict["role"],
        "is_2fa_enabled": is_2fa_enabled,
        "email_verified": bool(user_dict.get("email_verified")),
        "phone_verified": bool(user_dict.get("phone_verified")),
        "expires_in": expires_in_seconds,
        "session_token": new_session_token
    }


# --- 3.0. OTURUM GEÇERLİLİK KONTROLÜ (TEK AKTİF OTURUM DOĞRULAMA) ---
@app.post("/api/auth/validate-session")
async def validate_session(req: ValidateSessionRequest):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT current_session_token FROM users WHERE username = ?", (req.username,))
    user = cursor.fetchone()
    conn.close()

    if not user or user["current_session_token"] != req.session_token:
        return {
            "valid": False,
            "message": "Hesabınıza başka bir cihaz veya sekmeden giriş yapıldığı için mevcut oturumunuz sonlandırıldı!"
        }
    
    return {"valid": True, "message": "Oturum geçerli."}


# --- 3.1. 2FA QR KOD & SECRET OLUŞTURMA (SETUP 2FA) ---
@app.post("/api/auth/setup-2fa")
async def setup_2fa(req: Setup2FARequest):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, totp_secret, is_2fa_enabled FROM users WHERE username = ?", (req.username,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=44, detail="Kullanıcı bulunamadı!")
    
    user_dict = dict(user)
    totp_secret = user_dict.get("totp_secret")
    
    if not totp_secret:
        totp_secret = pyotp.random_base32()
        cursor.execute("UPDATE users SET totp_secret = ? WHERE id = ?", (totp_secret, user_dict["id"]))
        conn.commit()
    
    conn.close()
    
    # Authenticator URI Oluştur
    label = user_dict.get("email") or user_dict["username"]
    totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
        name=label,
        issuer_name="SmartCam IoT"
    )
    
    # QR Kod PNG Üret
    img = qrcode.make(totp_uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    
    return {
        "status": "success",
        "secret": totp_secret,
        "qr_code_base64": qr_base64,
        "is_2fa_enabled": bool(user_dict.get("is_2fa_enabled"))
    }


# --- 3.2. 2FA KODU DOĞRULAMA VE AKTİFLEŞTİRME ---
@app.post("/api/auth/verify-2fa")
async def verify_2fa(req: Verify2FARequest):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, totp_secret, role FROM users WHERE username = ?", (req.username,))
    user = cursor.fetchone()
    
    if not user or not user["totp_secret"]:
        conn.close()
        raise HTTPException(status_code=400, detail="2FA kurulumu bulunamadı! Önce kurulum başlatın.")
    
    totp = pyotp.TOTP(user["totp_secret"])
    if totp.verify(req.code.strip()):
        new_role = "two_factor_verified" if user["role"] == "user" else user["role"]
        cursor.execute("UPDATE users SET is_2fa_enabled = 1, role = ? WHERE id = ?", (new_role, user["id"]))
        conn.commit()
        conn.close()
        return {"status": "success", "message": "2FA doğrulaması başarılı! İki aşamalı doğrulama hesabınızda etkinleştirildi."}
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Hatalı 2FA doğrulama kodu!")


# --- 3.3. 2FA DEVRE DIŞI BIRAKMA ---
@app.post("/api/auth/disable-2fa")
async def disable_2fa(req: Disable2FARequest):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password, role FROM users WHERE username = ?", (req.username,))
    user = cursor.fetchone()
    
    if not user or user["password"] != req.password:
        conn.close()
        raise HTTPException(status_code=400, detail="Doğrulama başarısız! Şifreniz hatalı.")
    
    new_role = "user" if user["role"] == "two_factor_verified" else user["role"]
    cursor.execute("UPDATE users SET is_2fa_enabled = 0, role = ? WHERE id = ?", (new_role, user["id"]))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "İki aşamalı doğrulama (2FA) devredışı bırakıldı."}


# --- 4. ADMİN İÇİN ONAY BEKLEYEN KULLANICILARI LİSTELEME ---
@app.get("/api/admin/pending-users")
async def get_pending_users():
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, email, phone, role, status, email_verified, phone_verified, is_2fa_enabled, created_at FROM users WHERE status = 'pending'")
    pending_users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return pending_users


# --- 5. ADMİN İÇİN KULLANICI ONAYLAMA / REDDETME (SİLME DESTEKLİ) ---
@app.post("/api/admin/approve-user")
async def approve_or_reject_user(req: UserApprovalRequest):
    if req.action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Geçersiz işlem! 'approve' veya 'reject' olmalı.")
        
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    if req.action == "approve":
        cursor.execute("UPDATE users SET status = 'approved' WHERE id = ?", (req.user_id,))
        action_text = "onaylandı"
    else:
        cursor.execute("DELETE FROM users WHERE id = ?", (req.user_id,))
        action_text = "reddedildi ve sistemden silindi"
        
    conn.commit()
    conn.close()
    
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


# --- 6.1 ARAYÜZ İÇİN KATEGORİ LİSTESİ ---
@app.get("/api/station-categories")
async def get_station_categories():
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM station_categories ORDER BY id ASC")
    categories = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return categories


@app.get("/api/stations/{station_id}/sensors")
async def get_station_sensors(station_id: int):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sensors WHERE station_id = ? ORDER BY sequence_number ASC", (station_id,))
    sensors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return sensors


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
    
    auto_security_code = database.generate_secure_token()[:16]  # 16 haneli okunaklı token
    
    # Otomatik Hashlenmiş IMEI Üretimi (Eğer dışarıdan IMEI gönderilmediyse)
    final_imei = station.imei
    if not final_imei or not final_imei.strip():
        raw_seed = f"{station.name}-{station.category_id}-{time.time()}"
        hash_digest = hashlib.sha256(raw_seed.encode("utf-8")).hexdigest()
        # SHA-256 hash çıktısını 15 haneli sayısal IMEI formatına dönüştür
        final_imei = str(int(hash_digest, 16))[:15]

    try:
        cursor.execute('''
            INSERT INTO stations (category_id, name, security_code, imei, phone_number, device_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            station.category_id, 
            station.name, 
            auto_security_code,
            final_imei, 
            station.phone_number, 
            station.device_type
        ))
        
        new_station_id = cursor.lastrowid
        
        # İstasyon eklenirken başlangıçta 3 temel sensör otomatik tanımlanır
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
            "message": f"'{station.name}' istasyonu ve varsayılan sensörleri başarıyla oluşturuldu.",
            "station_id": new_station_id,
            "generated_security_code": auto_security_code,
            "imei": final_imei
        }
        
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(
            status_code=400, 
            detail="Bu IMEI numarası zaten başka bir istasyonda kayıtlı!"
        )


# --- 9. İSTASYONA YENİ SENSÖR EKLEME ---
@app.post("/api/sensors")
async def create_sensor(sensor: SensorCreateRequest):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    seq_num = sensor.sequence_number
    if not seq_num:
        cursor.execute(
            "SELECT COALESCE(MAX(sequence_number), 0) + 1 FROM sensors WHERE station_id = ?", 
            (sensor.station_id,)
        )
        seq_num = cursor.fetchone()[0]
        
    try:
        if sensor.id is not None:
            # Kullanıcının belirlediği özel Kanal ID (sensorData anahtarı) ile kaydet
            cursor.execute('''
                INSERT INTO sensors (id, station_id, sequence_number, label, channel_category_id, unit_type, default_unit, default_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sensor.id,
                sensor.station_id,
                seq_num,
                sensor.label,
                sensor.channel_category_id,
                sensor.unit_type,
                sensor.default_unit,
                sensor.default_value
            ))
            new_sensor_id = sensor.id
        else:
            # Otomatik veritabanı id'si ile kaydet
            cursor.execute('''
                INSERT INTO sensors (station_id, sequence_number, label, channel_category_id, unit_type, default_unit, default_value)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                sensor.station_id,
                seq_num,
                sensor.label,
                sensor.channel_category_id,
                sensor.unit_type,
                sensor.default_unit,
                sensor.default_value
            ))
            new_sensor_id = cursor.lastrowid
            
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": f"'{sensor.label}' sensörü başarıyla eklendi.",
            "sensor_id": new_sensor_id,
            "assigned_sequence_number": seq_num
        }
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"Belirtilen Kanal ID ({sensor.id}) bu veritabanında zaten başka bir sensör tarafından kullanılıyor!"
        )
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Sensör ekleme hatası: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
