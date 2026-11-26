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
    # Check alerta table structure
    cur.execute('DESCRIBE alerta')
    print("=== ALERTA TABLE ===")
    for row in cur.fetchall():
        print(row)

    print("\n=== REGISTRO_ACTIVIDAD TABLE ===")
    cur.execute('DESCRIBE registro_actividad')
    for row in cur.fetchall():
        print(row)

    print("\n=== USUARIO TABLE ===")
    cur.execute('DESCRIBE usuario')
    for row in cur.fetchall():
        print(row)

    print("\n=== ROL TABLE ===")
    cur.execute('DESCRIBE rol')
    for row in cur.fetchall():
        print(row)

    print("\n=== CASO TABLE (if exists) ===")
    cur.execute('SHOW TABLES LIKE "caso"')
    if cur.fetchone():
        cur.execute('DESCRIBE caso')
        for row in cur.fetchall():
            print(row)
    else:
        print("No 'caso' table exists")

    print("\n=== ACTIVIDAD TABLE (if exists) ===")
    cur.execute('SHOW TABLES LIKE "actividad"')
    if cur.fetchone():
        cur.execute('DESCRIBE actividad')
        for row in cur.fetchall():
            print(row)
    else:
        print("No 'actividad' table exists")

conn.close()