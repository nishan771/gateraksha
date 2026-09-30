import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'gate_raksha.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create gates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gates (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            railway_line TEXT NOT NULL,
            nearby_station TEXT NOT NULL,
            station_km REAL NOT NULL,
            section_start TEXT NOT NULL,
            section_end TEXT NOT NULL,
            description TEXT
        )
    ''')
    
    # Create monitored corridor trains table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monitored_trains (
            train_no TEXT PRIMARY KEY,
            train_name TEXT NOT NULL,
            origin_station TEXT NOT NULL,
            dest_station TEXT NOT NULL,
            direction TEXT NOT NULL -- 'UP' (Kozhikode to Kannur) or 'DOWN' (Kannur to Kozhikode)
        )
    ''')
    
    # Insert fixed monitored gates (Thalassery -> Kannur route)
    # IMPORTANT: station_km values are ABSOLUTE km from train origin (TVC),
    # matching the RailRadar API's `distance` field in route data.
    # Gate 1 (Nadal): Between Dharmadam (DMD, 485.4km) and Edakkad/Etakkot (ETK, 489.3km)
    # Gate 2 (Thazhe Chovva): Between Edakkad/Etakkot (ETK, 489.3km) and Kannur South (CS, 498.1km)
    cursor.execute('DELETE FROM gates')
    
    gates = [
        (
            'gate_1_nadal',
            'Nadal Railway Gate',
            11.8253,      # Verified latitude (Nadal/Muzhappilangad area)
            75.4361,      # Verified longitude
            'Kozhikode–Kannur section',
            'Edakkad / Dharmadam',
            487.0,        # Absolute km from origin — between DMD (485.4) and ETK (489.3)
            'DMD',        # Dharmadam station code (correct)
            'ETK',        # Edakkad/Etakkot station code (corrected from EDY)
            'Level Crossing at Nadal on NH 66, between Dharmadam and Edakkad stations'
        ),
        (
            'gate_2_thazhe_chovva',
            'Thazhe Chovva Railway Gate',
            11.8520,      # Verified latitude (Thazhe Chovva area)
            75.3840,      # Verified longitude
            'Kozhikode–Kannur–Mangaluru line',
            'Kannur South / Edakkad',
            495.0,        # Absolute km from origin — between ETK (489.3) and CS (498.1)
            'ETK',        # Edakkad/Etakkot station code (corrected from EDY)
            'CS',         # Kannur South station code (correct)
            'Level Crossing at Thazhe Chovva near Kannur South, on NH 66'
        )
    ]
    
    cursor.executemany('''
        INSERT INTO gates (id, name, latitude, longitude, railway_line, nearby_station, station_km, section_start, section_end, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', gates)
    
    # Seed Monitored Corridor Trains (Kozhikode - Kannur section)
    cursor.execute('DELETE FROM monitored_trains')
    trains = [
        ('16629', 'Malabar Express', 'TVC', 'MAQ', 'UP'),
        ('16650', 'Parasuram Express', 'MAQ', 'NCJ', 'DOWN'),
        ('16603', 'Maveli Express', 'MAQ', 'TVC', 'DOWN'),
        ('16307', 'Executive Express', 'ALLP', 'CAN', 'UP'),
        ('20631', 'Vande Bharat Express', 'KGQ', 'TVC', 'DOWN'),
        ('20632', 'Vande Bharat Express', 'TVC', 'KGQ', 'UP'),
        ('16604', 'Maveli Express', 'TVC', 'MAQ', 'UP'),
        ('16649', 'Parasuram Express', 'NCJ', 'MAQ', 'UP'),
        ('56655', 'Cannanore Passenger', 'CLT', 'CAN', 'UP')
    ]
    cursor.executemany('''
        INSERT INTO monitored_trains (train_no, train_name, origin_station, dest_station, direction)
        VALUES (?, ?, ?, ?, ?)
    ''', trains)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully with corrected gate data.")

if __name__ == '__main__':
    init_db()
