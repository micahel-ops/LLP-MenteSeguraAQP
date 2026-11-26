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
    cur.execute('SELECT id, correo, nombres, apellidos, rol_id, activo FROM usuario')
    for row in cur.fetchall():
        print(row)

    cur.execute('SELECT id, nombre FROM rol')
    print("\nRoles:")
    for row in cur.fetchall():
        print(row)

conn.close()