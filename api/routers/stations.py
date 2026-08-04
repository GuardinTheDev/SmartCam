from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.station_service import StationService

router = APIRouter(prefix="/api/stations", tags=["İstasyonlar"])

@router.get("")
def get_stations(db: Session = Depends(get_db)):
    return StationService.get_all_stations(db)

@router.get("/{station_id}/sensors")
def get_station_sensors(station_id: int, db: Session = Depends(get_db)):
    return StationService.get_station_sensors(db, station_id)
