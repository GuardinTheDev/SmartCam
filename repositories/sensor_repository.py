from typing import List, Optional
from sqlalchemy.orm import Session
from domain.models import SensorLog

class SensorRepository:
    @staticmethod
    def add_log(db: Session, station_id: int, sensor_id: int, raw_value: float) -> SensorLog:
        log = SensorLog(station_id=station_id, sensor_id=sensor_id, raw_value=raw_value)
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_logs(db: Session, station_id: int, sensor_id: Optional[int] = None, limit: int = 50) -> List[SensorLog]:
        query = db.query(SensorLog).filter(SensorLog.station_id == station_id)
        if sensor_id:
            query = query.filter(SensorLog.sensor_id == sensor_id)
        return query.order_by(SensorLog.recorded_at.desc()).limit(limit).all()
