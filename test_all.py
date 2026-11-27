import requests

BASE = "http://127.0.0.1:8000/api"

# Login as admin
r = requests.post(f"{BASE}/login", json={"correo": "admin@demo.pe", "contrasena": "Demo2026!"})
print("Admin login:", r.status_code, r.json())
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Test all admin endpoints
for endpoint in ["/admin/panel", "/admin/casos", "/admin/actividad", "/admin/usuarios", "/admin/facultades", "/admin/fuentes-externas", "/admin/modelo-nlp"]:
    r = requests.get(f"{BASE}{endpoint}", headers=headers)
    print(f"{endpoint}: {r.status_code}")
    try:
        data = r.json()
        if isinstance(data, list):
            print(f"  -> list with {len(data)} items")
        elif isinstance(data, dict):
            print(f"  -> keys: {list(data.keys())[:10]}")
    except:
        print(f"  -> {r.text[:200]}")

# Login as professional
r = requests.post(f"{BASE}/login", json={"correo": "profesional@demo.pe", "contrasena": "Demo2026!"})
print("\nProf login:", r.status_code)
prof_token = r.json()["token"]
prof_headers = {"Authorization": f"Bearer {prof_token}"}

# Test professional endpoints
for endpoint in ["/profesional/estudiantes", "/reportes/facultad", "/alertas"]:
    r = requests.get(f"{BASE}{endpoint}", headers=prof_headers)
    print(f"{endpoint}: {r.status_code}")
    try:
        data = r.json()
        if isinstance(data, list):
            print(f"  -> list with {len(data)} items")
        elif isinstance(data, dict):
            print(f"  -> keys: {list(data.keys())[:10]}")
    except:
        print(f"  -> {r.text[:200]}")

# Login as student
r = requests.post(f"{BASE}/login", json={"correo": "estudiante@demo.pe", "contrasena": "Demo2026!"})
print("\nStudent login:", r.status_code)
