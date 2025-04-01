  
import pyodbc 

liste_mit_ueberschreitungen_ID = []
liste_mit_ueberschreitungen_ZEIT = []
liste_mit_ueberschreitungen_TEMP = []

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
select_query = 'SELECT transportstationID, datetime, temperature FROM tempdata' 
cursor.execute(select_query) 
 
# Für jeden Datensatz die Entschlüsselung durchführen und ausgeben 
for row in cursor.fetchall(): 
   transportstationID, datetime, temperature = row
   
   #print(f"ID: {transportstationID}, Uhrzeit: {datetime}, Temeratur: {temperature}") 
   if temperature > 4.0 or temperature < 2.0:
       liste_mit_ueberschreitungen_ID.append(transportstationID)
       liste_mit_ueberschreitungen_ZEIT.append(datetime)
       liste_mit_ueberschreitungen_TEMP.append(temperature)
    

   
   
   
# Verbindung schließen 
cursor.close() 
conn.close() 

"""
117,
327-351,
531,  
"""