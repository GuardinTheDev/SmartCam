from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

# --- KULLANICI ŞEMALARI ---
class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    kvkk_approved: bool = True

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    role: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class AdminUserAction(BaseModel):
    user_id: int
    action: str  # "approve" veya "reject"

# --- SENSÖR & İSTASYON ŞEMALARI ---
class SensorSchema(BaseModel):
    id: int
    station_id: int
    label: str
    sensor_type: str
    default_unit: str

    class Config:
        from_attributes = True

class StationSchema(BaseModel):
    id: int
    name: str
    location: Optional[str]
    gsm_ip: Optional[str]
    imei: Optional[str]
    device_type: str
    battery_percent: int
    gsm_percent: int
    updated_at: datetime
    sensors: List[SensorSchema] = []

    class Config:
        from_attributes = True

# --- TELEMETRİ GİRDİ ŞEMASI ---
class TelemetryInput(BaseModel):
    station_id: int
    sensor_id: int
    value: float
