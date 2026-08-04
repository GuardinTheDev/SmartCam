from typing import List, Optional
from sqlalchemy.orm import Session
from domain.models import Station, Sensor

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