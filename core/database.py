import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# MySQL Bağlantı Bilgileri
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "smartcam_db")

MYSQL_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
SQLITE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'sensor_data.db')}"

try:
    # 1. Öncelik: MySQL Bağlantısını Dene
    engine = create_engine(
        MYSQL_URL,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        pool_pre_ping=True
    )
    with engine.connect() as conn:
        pass
    print("✅ MySQL Veritabanına Başarıyla Bağlanıldı.")
except Exception:
    # 2. Öncelik: MySQL Servisi Kapalıysa veya Çalışmıyorsa SQLite'a Otomatik Geç (Yedek Koruma)
    print("⚠️  MySQL Sunucusuna Erişilemedi (Servis kapalı veya yapılandırılmamış). SQLite kullanılıyor...")
    engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI Dependency: Her istekte veritabanı oturumu açar ve kapatır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
