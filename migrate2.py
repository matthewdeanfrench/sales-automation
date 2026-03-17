import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS credentials VARCHAR(100) DEFAULT \'\'')
cur.execute('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS title VARCHAR(100) DEFAULT \'\'')
cur.execute('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS license_number VARCHAR(50) DEFAULT \'\'')

conn.commit()
cur.close()
conn.close()
print('Migration complete!')