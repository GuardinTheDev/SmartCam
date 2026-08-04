import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import engine, Base, SessionLocal
from repositories.user_repository import UserRepository
from repositories.station_repository import StationRepository
from api.routers import auth, stations, sensors

# Veritabanı Tablolarını Oluştur
Base.metadata.create_all(bind=engine)

# Uygulama Başlarken Varsayılan Kullanıcıları (Admin/User) ve İstasyonları Ekle
try:
    with SessionLocal() as db:
        UserRepository.seed_initial_users(db)
        StationRepository.seed_initial_data(db)
except Exception as e:
    print(f"Seed verisi oluşturulurken hata: {e}")

app = FastAPI(
    title="SmartCam IoT Layered API",
    description="Katmanlı Mimari ve MySQL Tabanlı IoT Telemetri Servisi",
    version="2.0.0"
)

# CORS Yapılandırması
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları Sisteme Ekle
app.include_router(auth.router)
app.include_router(stations.router)
app.include_router(sensors.router)

@app.get("/")
def root():
    return {"message": "SmartCam Layered API Servisi Çalışıyor 🚀"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
