import sqlite3
import os

# Static in-memory gate data as high-reliability fallback
GATES_DATA = [
    {
        'id': 'gate_1_nadal',
        'name': 'Nadal Railway Gate',
        'latitude': 11.8253,
        'longitude': 75.4361,
        'railway_line': 'Kozhikode–Kannur section',
        'nearby_station': 'Edakkad / Dharmadam',
        'station_km': 487.0,
        'section_start': 'DMD',
        'section_end': 'ETK',
        'description': 'Level Crossing at Nadal on NH 66, between Dharmadam and Edakkad stations'
    },
    {
        'id': 'gate_2_thazhe_chovva',
        'name': 'Thazhe Chovva Railway Gate',
        'latitude': 11.8520,
        'longitude': 75.3840,
        'railway_line': 'Kozhikode–Kannur–Mangaluru line',
        'nearby_station': 'Kannur South / Edakkad',
        'station_km': 495.0,
        'section_start': 'ETK',
        'section_end': 'CS',
        'description': 'Level Crossing at Thazhe Chovva near Kannur South, on NH 66'
    }
]

TRAINS_DATA = [
    {'train_no': '16629', 'train_name': 'Malabar Express', 'origin_station': 'TVC', 'dest_station': 'MAQ', 'direction': 'UP'},
    {'train_no': '16650', 'train_name': 'Parasuram Express', 'origin_station': 'MAQ', 'dest_station': 'NCJ', 'direction': 'DOWN'},
    {'train_no': '16603', 'train_name': 'Maveli Express', 'origin_station': 'MAQ', 'dest_station': 'TVC', 'direction': 'DOWN'},
    {'train_no': '16307', 'train_name': 'Executive Express', 'origin_station': 'ALLP', 'dest_station': 'CAN', 'direction': 'UP'},
    {'train_no': '20631', 'train_name': 'Vande Bharat Express', 'origin_station': 'KGQ', 'dest_station': 'TVC', 'direction': 'DOWN'},
    {'train_no': '20632', 'train_name': 'Vande Bharat Express', 'origin_station': 'TVC', 'dest_station': 'KGQ', 'direction': 'UP'},
    {'train_no': '16604', 'train_name': 'Maveli Express', 'origin_station': 'TVC', 'dest_station': 'MAQ', 'direction': 'UP'},
    {'train_no': '16649', 'train_name': 'Parasuram Express', 'origin_station': 'NCJ', 'dest_station': 'MAQ', 'direction': 'UP'},
    {'train_no': '56655', 'train_name': 'Cannanore Passenger', 'origin_station': 'CLT', 'dest_station': 'CAN', 'direction': 'UP'}
]

# Shared in-memory SQLite connection for serverless/read-only environments
_MEM_CONN = None

def _get_memory_db():
    global _MEM_CONN
    if _MEM_CONN is None:
        conn = sqlite3.connect(':memory:', check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE gates (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL,
                railway_line TEXT NOT NULL, nearby_station TEXT NOT NULL, station_km REAL NOT NULL,
                section_start TEXT NOT NULL, section_end TEXT NOT NULL, description TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE monitored_trains (
                train_no TEXT PRIMARY KEY, train_name TEXT NOT NULL, origin_station TEXT NOT NULL,
                dest_station TEXT NOT NULL, direction TEXT NOT NULL
            )
        ''')
        
        for g in GATES_DATA:
            cursor.execute('''
                INSERT INTO gates VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (g['id'], g['name'], g['latitude'], g['longitude'], g['railway_line'], g['nearby_station'], g['station_km'], g['section_start'], g['section_end'], g['description']))
            
        for t in TRAINS_DATA:
            cursor.execute('''
                INSERT INTO monitored_trains VALUES (?, ?, ?, ?, ?)
            ''', (t['train_no'], t['train_name'], t['origin_station'], t['dest_station'], t['direction']))
            
        conn.commit()
        _MEM_CONN = conn
    return _MEM_CONN

DB_PATH = os.path.join(os.path.dirname(__file__), 'gate_raksha.db')

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        return _get_memory_db()

def get_gates_list():
    try:
        conn = get_db_connection()
        gates = [dict(g) for g in conn.execute('SELECT * FROM gates').fetchall()]
        if gates:
            return gates
    except Exception:
        pass
    return GATES_DATA

def get_monitored_trains_list():
    try:
        conn = get_db_connection()
        trains = [dict(t) for t in conn.execute('SELECT * FROM monitored_trains').fetchall()]
        if trains:
            return trains
    except Exception:
        pass
    return TRAINS_DATA

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gates (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL,
                railway_line TEXT NOT NULL, nearby_station TEXT NOT NULL, station_km REAL NOT NULL,
                section_start TEXT NOT NULL, section_end TEXT NOT NULL, description TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitored_trains (
                train_no TEXT PRIMARY KEY, train_name TEXT NOT NULL, origin_station TEXT NOT NULL,
                dest_station TEXT NOT NULL, direction TEXT NOT NULL
            )
        ''')
        cursor.execute('DELETE FROM gates')
        for g in GATES_DATA:
            cursor.execute('INSERT INTO gates VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           (g['id'], g['name'], g['latitude'], g['longitude'], g['railway_line'], g['nearby_station'], g['station_km'], g['section_start'], g['section_end'], g['description']))
        cursor.execute('DELETE FROM monitored_trains')
        for t in TRAINS_DATA:
            cursor.execute('INSERT INTO monitored_trains VALUES (?, ?, ?, ?, ?)',
                           (t['train_no'], t['train_name'], t['origin_station'], t['dest_station'], t['direction']))
        conn.commit()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"File DB initialization skipped (read-only system): {e}. Using in-memory dataset.")
        _get_memory_db()

if __name__ == '__main__':
    init_db()
