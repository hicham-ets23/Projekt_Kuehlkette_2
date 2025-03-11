import os
import pyodbc
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from datetime import datetime, timedelta

def connect_db():
    """Establishes connection to SQL Server."""
    server = os.getenv("DB_SERVER", "sc-db-server.database.windows.net")
    database = os.getenv("DB_NAME", "supplychain")
    username = os.getenv("DB_USER", "rse")
    password = os.getenv("DB_PASS", "Pa$$w0rd")
    
    conn_str = (
        f'DRIVER={{ODBC Driver 18 for SQL Server}};'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password}'
    )
    return pyodbc.connect(conn_str)

# AES Decryption
KEY = b'mysecretpassword'
IV = b'passwort-salzen!'

def decrypt_value(encrypted_data):
    """Decrypts AES-CBC encrypted data."""
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    return unpad(cipher.decrypt(encrypted_data), AES.block_size).decode()

# 1️⃣ Temperature Monitoring
def check_temperature():
    """Checks if temperatures in cooling stations stay within 2°C - 4°C."""
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT transportstation, temperature, datetime FROM tempdata")
    results = cursor.fetchall()
    conn.close()
    
    warnings = []
    for station, temp, timestamp in results:
        if temp < 2 or temp > 4:
            warnings.append(f"⚠️ Temperature out of range at {station}: {temp}°C at {timestamp}")
    
    return warnings if warnings else ["✅ All temperatures are within range"]

# 2️⃣ Decrypt Encrypted Transport Data
def get_transport_data():
    """Fetch and decrypt transport data from database."""
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT company, transportstation FROM company_crypt")
    results = cursor.fetchall()
    conn.close()
    
    decrypted_data = [(decrypt_value(comp), decrypt_value(stat)) for comp, stat in results]
    return decrypted_data

# 3️⃣ Fetch Weather Data from API
def fetch_weather(zip_code, timestamp):
    """Fetches historical weather data for the given ZIP code and time."""
    api_key = "YOUR_VISUALCROSSING_API_KEY"
    formatted_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S')
    
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{zip_code}/{formatted_time}" 
    response = requests.get(url, params={'unitGroup': 'metric', 'key': api_key, 'include': 'hours'})
    data = response.json()
    
    try:
        temp = data["days"][0]["temp"]
        return f"🌡 Temperature at ZIP {zip_code} during issue: {temp}°C"
    except KeyError:
        return "❌ Error fetching weather data"

# Testing Outputs
if __name__ == "__main__":
    print("\n--- Temperature Check ---")
    print("\n".join(check_temperature()))
    
    print("\n--- Decrypted Transport Data ---")
    for company, station in get_transport_data():
        print(f"Company: {company}, Station: {station}")
    
    print("\n--- Fetching Weather Data ---")
    print(fetch_weather("26127", "2023-07-10 13:00:00"))
