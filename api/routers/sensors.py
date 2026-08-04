from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from domain.schemas import TelemetryInput
from services.telemetry_service import TelemetryService

router = APIRouter(prefix="/api", tags=["Sensör & Telemetri"])

@router.post("/telemetry")
def record_telemetry(data: TelemetryInput, db: Session = Depends(get_db)):
    log = TelemetryService.record_log(db, data.station_id, data.sensor_id, data.value)
    return {"status": "success", "log_id": log.id}

@router.get("/sensor/history")
def get_sensor_history(
    station_id: int = Query(...),
    sensor_id: int = Query(None),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    return TelemetryService.get_history(db, station_id, sensor_id, limit)
