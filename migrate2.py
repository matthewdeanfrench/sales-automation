import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute('''
    CREATE TABLE IF NOT EXISTS resident_code (
        id SERIAL PRIMARY KEY,
        code VARCHAR(20) UNIQUE NOT NULL,
        resident_name VARCHAR(100) NOT NULL,
        facility_name VARCHAR(100),
        created_by VARCHAR(150),
        created_at TIMESTAMP DEFAULT NOW(),
        is_active BOOLEAN DEFAULT TRUE
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS family_update (
        id SERIAL PRIMARY KEY,
        resident_code VARCHAR(20) NOT NULL,
        resident_name VARCHAR(100),
        content TEXT NOT NULL,
        published_by VARCHAR(150),
        created_at TIMESTAMP DEFAULT NOW()
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS family_user (
        id SERIAL PRIMARY KEY,
        email VARCHAR(150) UNIQUE NOT NULL,
        password VARCHAR(256) NOT NULL,
        name VARCHAR(100),
        resident_code VARCHAR(20) NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    )
''')

conn.commit()
cur.close()
conn.close()
print('Migration complete!')