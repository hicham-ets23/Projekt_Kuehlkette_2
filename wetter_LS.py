import requests
import json
from datetime import datetime

# Beispiel-Nutzung
api_key = "EFVT5R3796ZG2QMKN7KCRLYF4"
location = "26127,DE"
datetime_str = "11.03.2025 13:00" # Zeit auf die nächste volle Stunde gerundet

# Konvertiere das Datum und die Uhrzeit in das erforderliche Format
datetime_obj = datetime.strptime(datetime_str, '%d.%m.%Y %H:%M')
timestamp = datetime_obj.strftime('%Y-%m-%dT%H:%M:%S')

# Visual Crossing Weather API-Endpunkt
url = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/{timestamp}'.format(location=location, timestamp=timestamp)
response = requests.get(url, params={'unitGroup': 'metric','key':
api_key,'include': 'hours'})
data = response.json()

# Ausgabe der Temperatur
print("\nTemperatur: ", data["days"][0]["temp"],"\n")
# Ausgabe des gesamten JSON-Objekts
#json_str = json.dumps(data, indent=4)
#print(json_str)