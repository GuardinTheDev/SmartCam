import sqlite3

DB_NAME = "sensor_data.db"

def init_db():
    """Veritabanini ve gerekli tablolari olusturur."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ist_code TEXT,
            timestamp INTEGER,
            battery_percent INTEGER,
            gsm_signal INTEGER,
            temp REAL,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_log_id INTEGER,
            sensor_id INTEGER,
            avg_value REAL,
            raw_values TEXT,
            gsm_signal INTEGER,
            battery_percent INTEGER,
            FOREIGN KEY (device_log_id) REFERENCES device_logs(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def save_payload_to_db(payload: dict):
    """Gelen JSON verisini SQL veritabanina kaydeder."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO device_logs (ist_code, timestamp, battery_percent, gsm_signal, temp, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        payload["istCode"],
        int(payload["sensorData"]["0"][4]),
        payload["accumulatorPercent"],
        int(payload["gsmSignalPercent"]),
        float(payload["temp"]),
        payload["ip"]
    ))
    
    device_log_id = cursor.lastrowid
    
    for sensor_key, sensor_arr in payload["sensorData"].items():
        cursor.execute('''
            INSERT INTO sensor_logs (device_log_id, sensor_id, avg_value, raw_values, gsm_signal, battery_percent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            device_log_id,
            int(sensor_key),
            float(sensor_arr[5]),
            sensor_arr[9],
            int(sensor_arr[8]),
            int(sensor_arr[7])
        ))
        
    conn.commit()
    conn.close()
