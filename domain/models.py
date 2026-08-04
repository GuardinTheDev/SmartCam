import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from core.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"

class UserStatus(str, enum.Enum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=True)
    email = Column(String(150), unique=True, index=True, nullable=True)
    phone = Column(String(50), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.PENDING, nullable=False)
    kvkk_approved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    location = Column(String(255), nullable=True)
    gsm_ip = Column(String(50), nullable=True)
    imei = Column(String(100), nullable=True)
    device_type = Column(String(100), default="Gateway")
    battery_percent = Column(Integer, default=100)
    gsm_percent = Column(Integer, default=100)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sensors = relationship("Sensor", back_populates="station", cascade="all, delete-orphan")
    logs = relationship("SensorLog", back_populates="station", cascade="all, delete-orphan")

class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    label = Column(String(100), nullable=False)         # Örn: Sıcaklık, Nem
    sensor_type = Column(String(50), nullable=False)     # Örn: temp, humidity
    default_unit = Column(String(20), nullable=False)    # Örn: °C, %

    station = relationship("Station", back_populates="sensors")
    logs = relationship("SensorLog", back_populates="sensor", cascade="all, delete-orphan")

class SensorLog(Base):
    __tablename__ = "sensor_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)
    raw_value = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    station = relationship("Station", back_populates="logs")
    sensor = relationship("Sensor", back_populates="logs")
