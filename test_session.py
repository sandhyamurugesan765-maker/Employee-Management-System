import requests

BASE_URL = "http://127.0.0.1:5000/api"
session = requests.Session()

# Login
response = session.post(f"{BASE_URL}/login", 
                       json={"username": "admin", "password": "admin123"})
print("Login response:", response.json())
print("Session cookies:", session.cookies)

# Try to get employees
response = session.get(f"{BASE_URL}/employees")
print("Get employees response status:", response.status_code)
print("Get employees response:", response.json() if response.ok else response.text)