from sqlalchemy.orm import Session
from repositories.station_repository import StationRepository
from core.btree_index import SmartCamBTreeIndex

class StationService:
    @staticmethod
    def get_all_stations(db: Session):
        StationRepository.seed_initial_data(db)  # İlk veri seed kontrolü
        return StationRepository.get_all(db)

    @staticmethod
    def get_station_sensors(db: Session, station_id: int):
        return StationRepository.get_sensors_by_station(db, station_id)

    @staticmethod
    def create_station(db: Session, name: str, gsm_ip: str = "", imei: str = ""):
        return StationRepository.create_station(db, name=name, gsm_ip=gsm_ip, imei=imei)

    @staticmethod
    def create_sensor(db: Session, station_id: int, label: str, sensor_type: str, default_unit: str):
        return StationRepository.create_sensor(db, station_id=station_id, label=label, sensor_type=sensor_type, default_unit=default_unit)

    @staticmethod
    def get_btree_index(db: Session):
        btree = SmartCamBTreeIndex()
        btree.build_from_db(db)
        return btree.get_tree_structure()

    @staticmethod
    def create_user_request(db: Session, username: str, req_type: str, title: str, details_dict: dict):
        return StationRepository.create_request(db, username=username, req_type=req_type, title=title, details_dict=details_dict)

    @staticmethod
    def get_pending_requests(db: Session):
        return StationRepository.get_pending_requests(db)

    @staticmethod
    def action_request(db: Session, req_id: int, action: str):
        return StationRepository.action_request(db, req_id=req_id, action=action)
