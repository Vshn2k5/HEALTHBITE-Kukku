import requests
import json

url = "http://127.0.0.1:8000/api/health/profile"
headers = {
    "Authorization": "Bearer fake-jwt-token",
    "Content-Type": "application/json"
}

payload = {
    "age": 25,
    "weight_kg": 70,
    "height_cm": 175,
    "gender": "Male",
    "dietary_preference": "Non-Veg",
    "bmi": 22.8,
    "disease": ["Diabetes"],
    "severity": {"diabetes": "Moderate"},
    "health_values": {"diabetes": 145},
    "allergies": [{"name": "Nuts", "severity": "Moderate"}]
}

# Start the server first in background if it's not running
# But I assume it's running from my previous turns.
# I'll try to send the request.

try:
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
