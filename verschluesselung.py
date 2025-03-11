""" '''Testprogramm der Ent- und Verschlüsselung der Datenbank Daten.
Author: David Grambardt
Datum: 25.02.2025
Hinweis: pip install pycryptodome

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import pyodbc

import pyodbc

# 📡 Verbindungsinfo
server = 'sc-db-server.database.windows.net'
database = 'supplychain'
username = 'rse'
password = 'Pa$$w0rd'

# 🔗 Verbindung zur SQL Server-Datenbank herstellen
conn_str = (
    f'DRIVER={{ODBC Driver 18 for SQL Server}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password}'
)

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    print("✅ Verbindung erfolgreich!")

    # 🔍 Beispiel-Query – passe die Tabelle und Spalte an!
    query = "SELECT transportstation, category, plz FROM transportstation_crypt WHERE transportstationID = ?"
    cursor.execute(query, (1,))  # Beispiel: Eintrag mit id=1 holen

    # 📋 Daten abrufen
    result = cursor.fetchone()

    if result:
        encrypted_base64 = result[0]  # Base64-codierter String
        print(f"📋 Base64-Daten: {encrypted_base64}")
    else:
        print("❌ Kein Eintrag gefunden.")

except Exception as e:
    print(f"❌ Fehler bei der Verbindung: {e}")

finally:
    # 🔒 Verbindung schließen
    conn.close()


# 🔑 Schlüssel und Initialisierungsvektor (IV)
key = b'mysecretpassword'      # Muss 16 Bytes sein
iv = b'passwort-salzen!'       # 16 Bytes IV

# 📁 Beispiel für einen verschlüsselten Datenbankeintrag (Base64-codiert)
# Ersetze das mit deinem verschlüsselten String!
encrypted_data_base64 = 'VerschlüsselterBase64StringHier'

# 📤 Schritt 1: Base64-String dekodieren
encrypted_data = encrypted_data_base64

# 🔓 Schritt 2: AES-Cipher für Entschlüsselung initialisieren
cipher = AES.new(key, AES.MODE_CBC, iv)

# 📋 Schritt 3: Daten entschlüsseln und Padding entfernen
try:
    decrypted_padded = cipher.decrypt(encrypted_data)
    decrypted_data = unpad(decrypted_padded, AES.block_size)  # Padding entfernen

    print(f"🔓 Entschlüsselte Daten: {decrypted_data.decode('utf-8')}")
except ValueError as e:
    print("❌ Entschlüsselung fehlgeschlagen:", e)'''


Testprogramm der Ent- und Verschlüsselung der Datenbank Daten.
Author: David Grambardt
Datum: 25.02.2025
Hinweis: pip install pycryptodome

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import pyodbc

# 📡 Verbindungsinfo
server = 'sc-db-server.database.windows.net'
database = 'supplychain'
username = 'rse'
password = 'Pa$$w0rd'

# 🔗 Verbindung zur SQL Server-Datenbank herstellen
conn_str = (
    f'DRIVER={{ODBC Driver 18 for SQL Server}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password}'
)

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    print("✅ Verbindung erfolgreich!")

    # 🔍 Korrekte SQL-Abfrage – Spaltennamen anpassen!
    query = "SELECT transportstation, category, plz FROM transportstation_crypt WHERE transportstationID = ?"
    cursor.execute(query, 8)  # Beispiel: Eintrag mit id=1 holen

    # 📋 Daten abrufen
    result = cursor.fetchone()

    if result:
        encrypted_data = result[0]  # Datenbank gibt direkt `bytes` zurück
        print(f"📋 Verschlüsselte Daten (Typ: {type(encrypted_data)}): {encrypted_data}")
    else:
        print("❌ Kein Eintrag gefunden.")
        exit()

except Exception as e:
    print(f"❌ Fehler bei der Verbindung: {e}")
    exit()

finally:
    # 🔒 Verbindung schließen
    conn.close()

# 🔑 Schlüssel und Initialisierungsvektor (IV)
key = b'mysecretpassword'      # Muss 16 Bytes lang sein
iv = b'passwort-salzen!'       # Muss 16 Bytes lang sein

# 🔓 AES-Cipher für Entschlüsselung initialisieren
cipher = AES.new(key, AES.MODE_CBC, iv)

# 📋 Daten entschlüsseln und Padding entfernen
try:
    #decrypted_padded = cipher.decrypt(encrypted_data)
    decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size).decode('windows-1252')  # Padding entfernen

    print(f"🔓 Entschlüsselte Daten: {decrypted_data}")
except ValueError as e:
    print("❌ Entschlüsselung fehlgeschlagen:", e)


"""


 
  
import pyodbc 
from Crypto.Cipher import AES 
from Crypto.Util.Padding import unpad 
 
# Initialisierung 
key = b'mysecretpassword'                # 16 Byte Passwort 
iv = b'passwort-salzen!'                 # 16 Byte Initialization Vektor 

 
# Entschlüsselungsfunktion 
def decrypt_value(encrypted_data): 
    cipher = AES.new(key, AES.MODE_CBC, iv)                                 # Verschlüsselung initialisieren 
    return unpad(cipher.decrypt(encrypted_data), AES.block_size).decode() 
     
# Verbindungsdaten 
server = 'sc-db-server.database.windows.net' 
database = 'supplychain' 
username = 'rse' 
password = 'Pa$$w0rd' 
 
# Verbindungsstring 
conn_str = ( 
    f'DRIVER={{ODBC Driver 18 for SQL Server}};' 
    f'SERVER={server};' 
    f'DATABASE={database};' 
    f'UID={username};' 
    f'PWD={password}' 
) 
 
# Verbindung herstellen 
conn = pyodbc.connect(conn_str) 
cursor = conn.cursor() 
 
# Datensätze auslesen 
select_query = 'SELECT transportstationID, transportstation, category, plz FROM transportstation_crypt' 
cursor.execute(select_query) 
 
# Für jeden Datensatz die Entschlüsselung durchführen und ausgeben 
for row in cursor.fetchall(): 
   transportstationID, encrypted_transportstation, encrypted_category, encrypted_plz = row 
    
   # Da die Daten als binär gespeichert wurden, sollte hier keine Umwandlung mit str() erfolgen 
   decrypted_transportstation = decrypt_value(encrypted_transportstation) 
   decrypted_category = decrypt_value(encrypted_category) 
   decrypted_plz = decrypt_value(encrypted_plz) 
     
   print(f"ID: {transportstationID}, Transportstation: {decrypted_transportstation}, Kategorie: {decrypted_category}, PLZ: {decrypted_plz}") 


    
# Verbindung schließen 
cursor.close() 
conn.close() 
 
