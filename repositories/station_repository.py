from typing import List, Optional
from sqlalchemy.orm import Session
from domain.models import Station, Sensor, PendingRequest
import json

class StationRepository:
    @staticmethod
    def get_all(db: Session) -> List[Station]:
        return db.query(Station).all()

    @staticmethod
    def get_by_id(db: Session, station_id: int) -> Optional[Station]:
        return db.query(Station).filter(Station.id == station_id).first()

    @staticmethod
    def get_sensors_by_station(db: Session, station_id: int) -> List[Sensor]:
        return db.query(Sensor).filter(Sensor.station_id == station_id).all()

    @staticmethod
    def seed_initial_data(db: Session):
        """Veritabanında istasyon yoksa 2 adet örnek istasyon ve sensörlerini otomatik ekler."""
        if db.query(Station).count() == 0:
            st1 = Station(name="İstasyon-1 (Baraj)", gsm_ip="192.168.1.100", imei="864920049281001", battery_percent=92, gsm_percent=85)
            st2 = Station(name="İstasyon-2 (Meteoroloji)", gsm_ip="192.168.1.101", imei="864920049281002", battery_percent=78, gsm_percent=90)
            db.add_all([st1, st2])
            db.commit()
            db.refresh(st1)
            db.refresh(st2)

            sensors = [
                Sensor(station_id=st1.id, label="Sıcaklık", sensor_type="temp", default_unit="°C"),
                Sensor(station_id=st1.id, label="Nem", sensor_type="humidity", default_unit="%"),
                Sensor(station_id=st1.id, label="Basınç", sensor_type="pressure", default_unit="hPa"),
                Sensor(station_id=st2.id, label="Sıcaklık", sensor_type="temp", default_unit="°C"),
                Sensor(station_id=st2.id, label="Rüzgar Hızı", sensor_type="wind_speed", default_unit="km/h"),
                Sensor(station_id=st2.id, label="Yağış Miktarı", sensor_type="rainfall", default_unit="mm")
            ]
            db.add_all(sensors)
            db.commit()

    @staticmethod
    def create_station(db: Session, name: str, gsm_ip: Optional[str] = None, imei: Optional[str] = None) -> Station:
        station = Station(name=name, gsm_ip=gsm_ip or "127.0.0.1", imei=imei or "000000000000000", battery_percent=100, gsm_percent=100)
        db.add(station)
        db.commit()
        db.refresh(station)
        return station

    @staticmethod
    def create_sensor(db: Session, station_id: int, label: str, sensor_type: str, default_unit: str) -> Sensor:
        sensor = Sensor(station_id=station_id, label=label, sensor_type=sensor_type, default_unit=default_unit)
        db.add(sensor)
        db.commit()
        db.refresh(sensor)
        return sensor

    @staticmethod
    def create_request(db: Session, username: str, req_type: str, title: str, details_dict: dict) -> PendingRequest:
        req = PendingRequest(
            user_username=username,
            request_type=req_type,
            title=title,
            details=json.dumps(details_dict),
            status="pending"
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        return req

    @staticmethod
    def get_pending_requests(db: Session) -> List[PendingRequest]:
        return db.query(PendingRequest).filter(PendingRequest.status == "pending").all()

    @staticmethod
    def action_request(db: Session, req_id: int, action: str) -> bool:
        req = db.query(PendingRequest).filter(PendingRequest.id == req_id).first()
        if not req: return False
        if action == "approve":
            req.status = "approved"
            details = json.loads(req.details or "{}")
            if req.request_type == "station":
                StationRepository.create_station(db, name=details.get("name"), gsm_ip=details.get("gsm_ip"), imei=details.get("imei"))
            elif req.request_type == "sensor":
                StationRepository.create_sensor(db, station_id=details.get("station_id"), label=details.get("label"), sensor_type=details.get("sensor_type", "generic"), default_unit=details.get("default_unit", "unit"))
        elif action == "reject":
            req.status = "rejected"
        db.commit()
        return True