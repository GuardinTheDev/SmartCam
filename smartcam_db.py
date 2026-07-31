import sqlite3
import secrets
import hashlib

DB_NAME = "sensor_data.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def generate_secure_token() -> str:
    """128 karakter uzunluğunda benzersiz SHA-512 Hash üretir."""
    random_bytes = secrets.token_bytes(64)
    return hashlib.sha512(random_bytes).hexdigest()

def init_db():
    """Veritabanını ve tüm gerekli ilişkisel tabloları oluşturur."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(sensor_logs)")
    cols = [row['name'] if isinstance(row, sqlite3.Row) else row[1] for row in cursor.fetchall()]
    if cols and "station_id" not in cols:
        cursor.execute("DROP TABLE sensor_logs")
        cursor.execute("DROP TABLE IF EXISTS device_logs")
        conn.commit()
    
    # 1. İstasyon Kategorileri Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS station_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    categories = ['Akarsu', 'Baraj', 'Gateway', 'Yeraltı Suyu']
    for cat in categories:
        cursor.execute("INSERT OR IGNORE INTO station_categories (name) VALUES (?)", (cat,))

    # 2. İstasyonlar Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT NOT NULL,
            security_code TEXT UNIQUE NOT NULL,
            imei TEXT UNIQUE NOT NULL,
            phone_number TEXT,
            gsm_ip TEXT,
            device_type TEXT,
            software_version TEXT,
            battery_percent INTEGER DEFAULT 0,
            gsm_percent INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES station_categories(id)
        )
    ''')

    # 3. Sensör Tanım Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id INTEGER,
            sequence_number INTEGER,
            label TEXT NOT NULL,
            channel_category_id INTEGER,
            unit_type TEXT,
            default_unit TEXT,
            default_value REAL DEFAULT 0,
            FOREIGN KEY (station_id) REFERENCES stations(id)
        )
    ''')
    
    # 4. Sensör Ölçüm Logları Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id INTEGER,
            sensor_id INTEGER,
            raw_value REAL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (station_id) REFERENCES stations(id),
            FOREIGN KEY (sensor_id) REFERENCES sensors(id)
        )
    ''')

    # 5. Kullanıcılar Tablosu (Ad Soyad, E-Posta, Telefon ve KVKK Alanları Eklendi)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            kvkk_approved INTEGER DEFAULT 0,
            role TEXT DEFAULT 'user',
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Otomatik Sütun Göçü (Migration)
    cursor.execute("PRAGMA table_info(users)")
    user_cols = [row['name'] if isinstance(row, sqlite3.Row) else row[1] for row in cursor.fetchall()]
    if user_cols:
        new_cols = {'full_name': 'TEXT', 'email': 'TEXT', 'phone': 'TEXT', 'kvkk_approved': 'INTEGER DEFAULT 0'}
        for col_name, col_type in new_cols.items():
            if col_name not in user_cols:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
    
    # Varsayılan Admin Kullanıcısı
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password, role, status) 
        VALUES ('admin', 'admin123', 'admin', 'approved')
    ''')
    
    # 1. Örnek İstasyon (Baraj)
    cursor.execute('''
        INSERT OR IGNORE INTO stations (id, category_id, name, security_code, imei, phone_number, gsm_ip, device_type, battery_percent, gsm_percent)
        VALUES (1, 1, 'Baraj İstasyonu 1', 'zwx9x5PcMl', '861234567890123', '05551112233', '192.168.1.100', 'Gateway', 95, 80)
    ''')

    # 2. Örnek İstasyon (Meteoroloji)
    cursor.execute('''
        INSERT OR IGNORE INTO stations (id, category_id, name, security_code, imei, phone_number, gsm_ip, device_type, battery_percent, gsm_percent)
        VALUES (2, 2, 'Meteoroloji İstasyonu A', 'sec998877665544', '869876543210987', '05559998877', '192.168.1.101', 'IoT Node', 88, 90)
    ''')

    # Sensör Tohumlama (Seed)
    default_sensors = [
        (1, 1, "Sıcaklık", 101, "temperature", "celsius", 24.5),
        (2, 1, "Su Seviyesi", 102, "level", "cm", 150.0),
        (3, 1, "Basınç / Debi", 103, "pressure", "bar", 3.2),
        (4, 2, "Rüzgar Hızı", 104, "speed", "km/h", 18.5),
        (5, 2, "Ortam Nemi", 105, "humidity", "%", 62.0),
        (6, 2, "Güneş Radyasyonu", 106, "radiation", "W/m²", 450.0)
    ]
    for s_id, st_id, lbl, cat, u_type, u_unit, d_val in default_sensors:
        cursor.execute('''
            INSERT OR IGNORE INTO sensors (id, station_id, sequence_number, label, channel_category_id, unit_type, default_unit, default_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (s_id, st_id, s_id, lbl, cat, u_type, u_unit, d_val))

    conn.commit()
    conn.close()
    print("Veritabanı tabloları ve 2 örnek istasyon başarıyla güncellendi.")

def verify_station(security_code: str, imei: str):
    """Gelen paketteki güvenlik kodu ve IMEI veritabanında var mı kontrol eder."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM stations WHERE security_code = ? AND imei = ?", 
        (security_code, imei)
    )
    station = cursor.fetchone()
    conn.close()
    return dict(station) if station else None

def process_valid_payload(station_id: int, payload: dict):
    """Doğrulanmış paket verilerini işler."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    update_fields = []
    update_values = []
    
    if "accumulatorPercent" in payload and isinstance(payload["accumulatorPercent"], (int, float)):
        update_fields.append("battery_percent = ?")
        update_values.append(payload["accumulatorPercent"])
        
    if "gsmSignalPercent" in payload and str(payload["gsmSignalPercent"]).isdigit():
        update_fields.append("gsm_percent = ?")
        update_values.append(int(payload["gsmSignalPercent"]))
        
    if "ip" in payload and payload["ip"]:
        update_fields.append("gsm_ip = ?")
        update_values.append(payload["ip"])
        
    if "tVer" in payload and payload["tVer"]:
        update_fields.append("software_version = ?")
        update_values.append(payload["tVer"])
        
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    
    if update_fields:
        sql_query = f"UPDATE stations SET {', '.join(update_fields)} WHERE id = ?"
        update_values.append(station_id)
        cursor.execute(sql_query, update_values)
    
    sensor_data = payload.get("sensorData", {})
    for sensor_key, sensor_arr in sensor_data.items():
        if isinstance(sensor_arr, list) and len(sensor_arr) > 5:
            raw_val_str = sensor_arr[5]
            try:
                val = float(raw_val_str)
                cursor.execute('''
                    INSERT INTO sensor_logs (station_id, sensor_id, raw_value)
                    VALUES (?, ?, ?)
                ''', (station_id, int(sensor_key), val))
            except (ValueError, TypeError):
                continue

    conn.commit()
    conn.close()
