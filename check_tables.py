import pymysql
from dotenv import load_dotenv
import os

load_dotenv(r"C:\Users\73352\mente_sana_aqp\backend\.env")

conn = pymysql.connect(
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT')),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

with conn.cursor() as cur:
    cur.execute('SHOW TABLES')
    tables = cur.fetchall()
    for t in tables:
        print(t[0])

conn.close()