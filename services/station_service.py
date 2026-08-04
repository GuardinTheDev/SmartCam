from sqlalchemy.orm import Session
from repositories.station_repository import StationRepository

class StationService:
    @staticmethod
    def get_all_stations(db: Session):
        StationRepository.seed_initial_data(db)  # İlk veri seed kontrolü
        return StationRepository.get_all(db)

    @staticmethod
    def get_station_sensors(db: Session, station_id: int):
        return StationRepository.get_sensors_by_station(db, station_id)
