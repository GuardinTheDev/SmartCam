from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from core.database import get_db
from services.station_service import StationService
from typing import Dict, Any

router = APIRouter(prefix="/api/stations", tags=["İstasyonlar"])

@router.get("")
def get_stations(db: Session = Depends(get_db)):
    return StationService.get_all_stations(db)

@router.post("")
def create_station(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    name = payload.get("name")
    gsm_ip = payload.get("gsm_ip", "")
    imei = payload.get("imei", "")
    return StationService.create_station(db, name=name, gsm_ip=gsm_ip, imei=imei)

@router.get("/btree")
def get_btree(db: Session = Depends(get_db)):
    return StationService.get_btree_index(db)

@router.post("/requests")
def create_request(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    username = payload.get("username", "anonymous")
    req_type = payload.get("request_type")
    title = payload.get("title", "Talepler")
    details = payload.get("details", {})
    return StationService.create_user_request(db, username=username, req_type=req_type, title=title, details_dict=details)

@router.get("/requests/pending")
def get_pending_requests(db: Session = Depends(get_db)):
    return StationService.get_pending_requests(db)

@router.post("/requests/action")
def action_request(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    req_id = payload.get("request_id")
    action = payload.get("action")
    return {"success": StationService.action_request(db, req_id=req_id, action=action)}

@router.get("/{station_id}/sensors")
def get_station_sensors(station_id: int, db: Session = Depends(get_db)):
    return StationService.get_station_sensors(db, station_id)

@router.post("/{station_id}/sensors")
def create_sensor(station_id: int, payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    label = payload.get("label")
    sensor_type = payload.get("sensor_type", "generic")
    default_unit = payload.get("default_unit", "unit")
    return StationService.create_sensor(db, station_id=station_id, label=label, sensor_type=sensor_type, default_unit=default_unit)
