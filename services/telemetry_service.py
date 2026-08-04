from sqlalchemy.orm import Session
from repositories.sensor_repository import SensorRepository

class TelemetryService:
    @staticmethod
    def record_log(db: Session, station_id: int, sensor_id: int, value: float):
        return SensorRepository.add_log(db, station_id, sensor_id, value)

    @staticmethod
    def get_history(db: Session, station_id: int, sensor_id: int = None, limit: int = 50):
        return SensorRepository.get_logs(db, station_id, sensor_id, limit)
