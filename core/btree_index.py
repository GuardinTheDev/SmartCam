from typing import List, Dict, Any, Optional

class BTreeNode:
    def __init__(self, key: str, data: Any = None, level: int = 1, is_leaf: bool = False):
        self.key = key          # Düğüm Tanımlayıcısı (Örn: "ROOT", "STATION_1", "SENSOR_5")
        self.data = data        # Düğüm Detayı (İstasyon veya Sensör objesi/dict)
        self.level = level      # Katman Seviyesi (1: System Root, 2: Station, 3: Sensor/Data)
        self.is_leaf = is_leaf  # Yaprak Düğüm mü?
        self.children: List['BTreeNode'] = []

    def add_child(self, child_node: 'BTreeNode'):
        self.children.append(child_node)

class SmartCamBTreeIndex:
    """
    SmartCam IoT 3 Katmanlı B-Tree İndeksleme ve Hiyerarşik Gezinti Yapısı
    Katman 1 (Root): SmartCam Sistem Ana Düğümü
    Katman 2 (Internal): Bölge ve İstasyon Düğümleri
    Katman 3 (Leaf): Sensör ve Ölçüm Düğümleri
    """
    def __init__(self):
        self.root = BTreeNode(key="SMARTCAM_ROOT", data={"name": "SmartCam IoT Ana Sistem"}, level=1)

    def build_from_db(self, db_session) -> BTreeNode:
        """Veritabanındaki istasyon ve sensörleri 3 katmanlı B-Tree yapısına dönüştürür."""
        from repositories.station_repository import StationRepository
        from repositories.sensor_repository import SensorRepository
        
        self.root.children = []  # Ağacı sıfırla
        stations = StationRepository.get_all(db_session)
        
        for st in stations:
            # 2. Katman: İstasyon Düğümü
            st_dict = {"id": st.id, "name": st.name, "imei": st.imei, "gsm_ip": st.gsm_ip}
            st_node = BTreeNode(key=f"STATION_{st.id}", data=st_dict, level=2, is_leaf=False)
            
            # 3. Katman: Sensör Düğümleri
            sensors = StationRepository.get_sensors_by_station(db_session, st.id)
            for sn in sensors:
                sn_dict = {"id": sn.id, "label": sn.label, "unit": sn.default_unit}
                sn_node = BTreeNode(key=f"SENSOR_{sn.id}", data=sn_dict, level=3, is_leaf=True)
                st_node.add_child(sn_node)
                
            self.root.add_child(st_node)
            
        return self.root

    def get_tree_structure(self) -> Dict[str, Any]:
        """Ağacın hiyerarşik sözlük çıktısını verir."""
        def serialize_node(node: BTreeNode) -> Dict[str, Any]:
            return {
                "key": node.key,
                "level": node.level,
                "data": node.data,
                "is_leaf": node.is_leaf,
                "children": [serialize_node(c) for c in node.children]
            }
        return serialize_node(self.root)
