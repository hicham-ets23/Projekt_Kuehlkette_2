"""
Autoren: 
David 
Riko 
Christian V. 
Lars 
Hicham 

Kurs: 
ETS23-Python-SIZ-RSE

Projekt:
ETS-CoolChainProject-2 V2.1 Phase 2
letzte Änderung: 25.03.2025
"""

import os
import json
import pyodbc
import requests
import customtkinter as ctk
from tkinter import messagebox
from datetime import timedelta, datetime
from base64 import b64decode
from Crypto.Cipher import AES 
from Crypto.Util.Padding import unpad 

##
# \brief Lädt Vertrauliche Daten us der config File mit gitignore Eintrag.
#
# Diese Funktion verwendet os.path und json.load um auf die Datei zuzugreifen.
#
# \return Die hinterlegten Daten
def load_config():
    config_path = "config.json"
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Die Konfigurationsdatei '{config_path}' wurde nicht gefunden.")
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)
    except json.JSONDecodeError as e:
        raise ValueError(f"Fehler beim Einlesen der JSON-Datei: {e}")
    required_keys = ["server", "database", "username", "password", "password_cryp", "init_vector_crypt", "decode_key", "decode_iv"]
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Fehlender Schlüssel '{key}' in der Konfigurationsdatei.")
    return config

config = load_config()
server = config["server"]
database = config["database"]
username = config["username"]
password = config["password"]
password_cryp = config["password_cryp"]
init_vector_crypt = config["init_vector_crypt"]
api_key = config["api_key"]
decode_key = b64decode(config["decode_key"])
decode_iv = b64decode(config["decode_iv"])


conn_str = (
    f'DRIVER={{ODBC Driver 18 for SQL Server}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password}'
)

transport_ids = [
    "72359278599178561029675",
    "15668407856331648336231",
    "73491878556297128760578",
    "99346757838434834886542",
    "46204863139457546291334",
    "77631003455214677542311",
    "34778534098134729847267",
    "64296734612883933474299",
    "84356113249506843372979",
    "23964376768701928340034",
    "55638471099438572108556",
    "84552276793340958450995",
    "96853785349211053482893",
    "68345254400506854834562",
    "67424886737245693583645",
    "85746762813849598680239",
    "56993454245564893300000",
    "95662334024905944384522",
    "13456783852887496020345",
    "76381745965049879836902"
]

def get_outdoor_temperature(plz, dt_obj, api_key):
    try:
        # PLZ + ,DE als Ort
        location = f"{plz},DE"

        # Zeit auf volle Stunde runden
        dt_hour = dt_obj.replace(minute=0, second=0, microsecond=0)
        timestamp = dt_hour.strftime('%Y-%m-%dT%H:%M:%S')

        url = f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/{timestamp}'
        response = requests.get(url, params={
            'unitGroup': 'metric',
            'key': api_key,
            'include': 'hours'
        })

        if response.status_code == 200:
            data = response.json()
            temp = data["days"][0]["hours"][0]["temp"]
            return f"{temp:.1f}°C"
        else:
            print(f"API-Fehler für {location} @ {timestamp}: {response.status_code}")
            return "?"
    except Exception as e:
        print(f"Fehler bei Temperaturabfrage: {e}")
        return "?"

##
# \brief Entschlüsselt einen verschlüsselten Datenbankwert mittels AES im CBC-Modus.
#
# Diese Funktion verwendet einen globalen Schlüssel und Initialisierungsvektor,
# um verschlüsselte Spalten wie Transportstation, Kategorie und PLZ zu entschlüsseln.
#
# \param encrypted_data Der verschlüsselte Datenwert als bytes
# \return Der entschlüsselte String
def decrypt_value(encrypted_data): 
    cipher = AES.new(decode_key, AES.MODE_CBC, decode_iv)
    return unpad(cipher.decrypt(encrypted_data), AES.block_size).decode() 

##
# \brief Führt eine Datenbankabfrage zur Kühlkette aus und ruft die zugehörigen Transportdaten ab.
#
# Diese Funktion stellt eine Verbindung zur SQL-Datenbank her, führt eine verknüpfte Abfrage
# auf den Tabellen `coolchain` und `transportstation_crypt` aus, und übergibt die Ergebnisse
# zur Anzeige an die Funktion \ref display_results.
#
# \throws messagebox.showerror bei ungültiger Eingabe oder Datenbankfehler

def fetch_data():
    transport_id = dropdown_transport_id.get()
    if not transport_id:
        messagebox.showerror(lang["Fehler"], lang["Bitte eine valide Transport ID eingeben."])
        return

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # SQL-Query, um die transportstation-Daten mit der coolchain-Tabelle zu kombinieren
        query = '''
            SELECT cc.transportID, cc.transportstationID, ts.transportstation, ts.category, ts.plz, 
                   cc.direction, cc.datetime
            FROM coolchain cc
            JOIN transportstation_crypt ts ON cc.transportstationID = ts.transportstationID
            WHERE cc.transportID = ?
            ORDER BY cc.datetime ASC
            
        '''
        cursor.execute(query, (transport_id,))
        results = cursor.fetchall()
        display_results(results, transport_id)
        
    except pyodbc.Error as e:
        messagebox.showerror(lang["Fehler bei Datenbankzugriff. Netzwerkverbindung prüfen."], str(e))
    finally:
        if conn:
            conn.close()
            
##
# \brief Zeigt die abgerufenen und entschlüsselten Transportdaten im GUI an.
#
# Die Funktion verarbeitet die verschlüsselten Datenbankwerte, entschlüsselt relevante Spalten,
# berechnet Zeitdifferenzen und zeigt Warnungen für unplausible Einträge an.
# Ergebnisse werden dynamisch in einem CTkFrame dargestellt.
#
# \param results Die Ergebnisliste der SQL-Abfrage (pyodbc.fetchall)
# \param transport_id Die aktuell ausgewählte Transport-ID für die Anzeige

def display_results(results, transport_id):
    decrypted_results = []

    for row in results:
        try:
            transportID = row.transportID
            transportstationID = row.transportstationID
            transportstation = decrypt_value(row.transportstation)
            category = decrypt_value(row.category)
            plz = decrypt_value(row.plz)
            direction = row.direction
            datetime_obj = row.datetime

            decrypted_results.append((
                transportID, transportstationID, transportstation,
                category, plz, direction, datetime_obj
            ))
        except Exception as e:
            print(f"Fehler beim Entschlüsseln: {e}")
            continue

    for widget in frame_results.winfo_children():
        widget.destroy()

    if decrypted_results:
        headers = [
            lang["Transport ID"], lang["Transportstation ID"], lang["Ort"], lang["Kategorie"],
            lang["PLZ"], lang["Richtung"], lang["Zeitstempel"], lang["Dauer"],
            lang["Warnung"], lang["Außentemperatur"]
        ]

        for i, header in enumerate(headers):
            label = ctk.CTkLabel(frame_results, text=header, font=("Arial", 12, "bold"))
            label.grid(row=0, column=i, padx=10, pady=5)

        previous_datetime = None
        previous_direction = None
        first_datetime = decrypted_results[0][6]
        last_datetime = None
        previous_location = None

        for row_index, row in enumerate(decrypted_results, start=1):
            transport_id, transportstation_id, transportstation, category, plz, direction, current_datetime = row
            last_datetime = current_datetime
            last_direction = direction
            warnung = ""
            time_diff_str = "N/A"

            if previous_datetime:
                time_difference = current_datetime - previous_datetime
                time_diff_str = str(time_difference)

                if time_difference.total_seconds() < 1:
                    warnung += lang["Nicht plausibler Zeitstempel"] + " "

                if direction.strip().lower() == "'in'" and time_difference > timedelta(minutes=10):
                    warnung += lang["Übergabezeit über 10 Minuten"] + " "

                # Temperaturprüfung NUR wenn "out"-Eintrag (Ende Lagerung)
                if direction.strip().lower() == "'out'":               
                    try:
                        conn_temp = pyodbc.connect(conn_str)
                        cursor_temp = conn_temp.cursor()
                        cursor_temp.execute('''
                            SELECT datetime, temperature
                            FROM tempdata
                            WHERE transportstationID = ?
                              AND datetime BETWEEN ? AND ?
                            ORDER BY datetime ASC
                        ''', (transportstation_id, previous_datetime, current_datetime))
                        temp_rows = cursor_temp.fetchall()
                        for temp_entry in temp_rows:
                            temp = temp_entry.temperature
                            if temp < 2.0:
                                warnung += lang["Temp <2°C"] + " "
                                break
                            elif temp > 4.0:
                                warnung += lang["Temp >4°C"] + " "
                                break
                        conn_temp.close()
                    except Exception as e:
                        print(f"Fehler bei Temperaturabfrage: {e}")

            # Überprüfung auf doppelte oder fehlerhafte Richtung
            if previous_direction and previous_direction == direction:
                warnung += lang["Doppelter oder fehlender Eintrag"] + " "

            # Gleicher Ort nacheinander
            if direction.strip().lower() == "'in'" and previous_location == transportstation:
                warnung += lang["Transportstation ist doppelt"] + " "

            previous_datetime = current_datetime
            previous_direction = direction
            previous_location = transportstation

# Umgebungstemperatur nur bei gültiger PLZ ≠ 0 abfragen
            if str(plz).strip() != "0":
                outdoor_temp = get_outdoor_temperature(plz, current_datetime, api_key)
            else:
                outdoor_temp = " "
            
            row_data = [
                transport_id, transportstation_id, transportstation, category,
                plz, direction, current_datetime, time_diff_str, warnung.strip(), outdoor_temp
            ]

            for col_index, item in enumerate(row_data):
                if col_index == 8 and warnung.strip():  # Warnung farbig
                    label = ctk.CTkLabel(frame_results, text=str(item), font=("Arial", 14, "bold"), text_color="red")
                else:
                    label = ctk.CTkLabel(frame_results, text=str(item), font=("Arial", 12))
                label.grid(row=row_index, column=col_index, padx=10, pady=5)


        # Prüfung auf Transportdauer > 48h
        total_time_difference = last_datetime - first_datetime
        if total_time_difference > timedelta(hours=48):
            final_error_label = ctk.CTkLabel(
                frame_results,
                text=lang["Transportdauer über 48 Stunden"],
                font=("Arial", 14, "bold"),
                text_color="red"
            )
            final_error_label.grid(row=row_index + 1, column=8, pady=0)

        # Prüfung auf unvollständige Lieferung (letzter Eintrag war "'in'")
        if last_direction.strip().lower() == "'in'":
            delta_to_present = datetime.now() - last_datetime
            days = delta_to_present.days
            hours = delta_to_present.seconds // 3600
            final_error_label = ctk.CTkLabel(
                frame_results,
                text=lang["Lieferung nicht vollständig. Zeit seit letztem Eintrag: "] + f"{days}d {hours}h",
                font=("Arial", 14, "bold"),
                text_color="red"
            )
            final_error_label.grid(row=row_index + 2, column=8, pady=0)

    else:
        no_result_label = ctk.CTkLabel(
            frame_results,
            text=lang["Diese Transport ID existiert nicht: "] + transport_id,
            font=("Arial", 14, "bold"),
            text_color="black",
            fg_color="yellow"
        )
        no_result_label.pack(pady=20)

##
# \brief Setzt die Sprache der Benutzeroberfläche auf Deutsch.
# \details Aktualisiert globale Variable \c lang und ruft \ref update_gui_language auf.
def set_german():
    global lang
    lang = LANGUAGES["DE"]
    update_gui_language()

##
# \brief Setzt die Sprache der Benutzeroberfläche auf Englisch.
def set_english():
    global lang
    lang = LANGUAGES["EN"]
    update_gui_language()

##
# \brief Setzt die Sprache der Benutzeroberfläche auf Arabisch.
def set_arabic():
    global lang
    lang = LANGUAGES["AR"]
    update_gui_language()

##
# \brief Aktualisiert alle GUI-Elemente basierend auf der aktuellen Spracheinstellung.
#
# Diese Funktion passt Texte von Labels und Buttons an die gewählte Sprache an
# und ruft \ref fetch_data auf, um neue Daten im Sprachkontext anzuzeigen.
def update_gui_language():
    label_transport_id.configure(text=lang["Transport ID eingeben:"])

    if lang == LANGUAGES["DE"]:
        button_language_1.configure(text="EN", command=set_english)
        button_language_2.configure(text="AR", command=set_arabic)
    elif lang == LANGUAGES["EN"]:
        button_language_1.configure(text="DE", command=set_german)
        button_language_2.configure(text="AR", command=set_arabic)
    elif lang == LANGUAGES["AR"]:
        button_language_1.configure(text="DE", command=set_german)
        button_language_2.configure(text="EN", command=set_english)
        
    fetch_data()

## \var lang
#  \brief Hinterlegung der Übersetzungen
LANGUAGES = {
    "DE": {
        "Außentemperatur": "Außentemperatur",
        "Temp <2°C": "Temp <2°C",
        "Temp >4°C": "Temp >4°C",
        "Transport ID":"Transport ID",
        "Transportstation ID":"Transportstation ID",
        "PLZ":"PLZ",
        "Transport ID eingeben:": "Transport ID eingeben:",
        "Daten prüfen": "Daten prüfen",
        "Ort": "Ort",
        "Kategorie": "Kategorie",
        "Richtung": "Richtung",
        "Zeitstempel": "Zeitstempel",
        "Dauer": "Dauer",
        "Warnung": "Warnung",
        "Nicht plausibler Zeitstempel": "Nicht plausibler Zeitstempel",
        "Übergabezeit über 10 Minuten": "Übergabezeit über 10 Minuten",
        "Doppelter oder fehlender Eintrag": "Doppelter oder fehlender Eintrag",
        "Transportstation ist doppelt": "Transportstation ist doppelt",
        "Transportdauer über 48 Stunden": "Transportdauer über 48 Stunden",
        "Diese Transport ID existiert nicht: ": "Diese Transport ID existiert nicht: ",
        "Fehler": "Fehler",
        "Bitte eine valide Transport ID eingeben.": "Bitte eine valide Transport ID eingeben.",
        "Fehler bei Datenbankzugriff. Netzwerkverbindung prüfen.": "Fehler bei Datenbankzugriff. Netzwerkverbindung prüfen.",
        "Lieferung nicht vollständig. Zeit seit letztem Eintrag: ": "Lieferung nicht vollständig. Zeit seit letztem Eintrag: ",
        "Temperatur": "Temperatur"
    },
    "EN": {
        "Außentemperatur": "Outside Temperature",
        "Temp <2°C": "Temp <2°C",
        "Temp >4°C": "Temp >4°C",        
        "Transport ID":"Transport ID",
        "Transportstation ID":"Transportstation ID",
        "PLZ":"Postal Code",
        "Transport ID eingeben:": "Enter Transport ID:",
        "Daten prüfen": "Check Data",
        "Ort": "Location",
        "Kategorie": "Category",
        "Richtung": "Direction",
        "Zeitstempel": "Timestamp",
        "Dauer": "Duration",
        "Warnung": "Warning",
        "Nicht plausibler Zeitstempel": "Invalid Timestamp",
        "Übergabezeit über 10 Minuten": "Handover Time over 10 Minutes",
        "Doppelter oder fehlender Eintrag": "Duplicate or Missing Entry",
        "Transportstation ist doppelt": "Duplicate Transport Station",
        "Transportdauer über 48 Stunden": "Transport Duration over 48 Hours",
        "Diese Transport ID existiert nicht: ": "This Transport ID does not exist: ",
        "Fehler": "Error",
        "Bitte eine valide Transport ID eingeben.": "Please enter a valid Transport ID.",
        "Fehler bei Datenbankzugriff. Netzwerkverbindung prüfen.": "Database access error. Please check your network connection.",
        "Lieferung nicht vollständig. Zeit seit letztem Eintrag: ": "Delivery incomplete. Time since last entry: ",
        "Temperatur": "Temperature"
    },
    "AR": {
        "Außentemperatur": "الحارارة الخارجية",
        "Temp <2°C": "الحارارة <2°C",
        "Temp >4°C": "الحارارة >4°C",
        "Transport ID":"معرف النقل",
        "Transportstation ID":"معرف النقل",
        "PLZ": "PLZ",
        "Transport ID eingeben:": "أدخل معرف النقل:",
        "Daten prüfen": "تحقق من البيانات",
        "Ort": "الموقع",
        "Kategorie": "الفئة",
        "Richtung": "الاتجاه",
        "Zeitstempel": "الطابع الزمني",
        "Dauer": "المدة",
        "Warnung": "تحذير",
        "Nicht plausibler Zeitstempel": "طابع زمني غير صالح",
        "Übergabezeit über 10 Minuten": "وقت التسليم أكثر من 10 دقائق",
        "Doppelter oder fehlender Eintrag": "إدخال مكرر أو مفقود",
        "Transportstation ist doppelt": "محطة النقل مكررة",
        "Transportdauer über 48 Stunden": "مدة النقل أكثر من 48 ساعة",
        "Diese Transport ID existiert nicht: ": "معرف النقل هذا غير موجود: ",
        "Fehler": "خطأ",
        "Bitte eine valide Transport ID eingeben.": "يرجى إدخال معرف نقل صالح.",
        "Fehler bei Datenbankzugriff. Netzwerkverbindung prüfen.": "خطأ في الوصول إلى قاعدة البيانات. يرجى التحقق من اتصال الشبكة.",
        "Lieferung nicht vollständig. Zeit seit letztem Eintrag: ": "التسليم غير مكتمل. الوقت منذ آخر تسجيل: ",
        "Temperatur": "الحرارة"
    }
}

## \var lang
#  \brief Aktuell gewählte Sprache (Standard: Deutsch)
lang = LANGUAGES["DE"]

# UI Fenster aufsetzen: Dark mode, blaue Akzente, Name, Größe
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
## \var root
#  \brief Hauptfenster der CTk-Anwendung
root = ctk.CTk()
root.title("Kühlketten Überwachung")
root.geometry("1200x700") 

## \var label_transport_id
#  \brief Beschriftung für das Transport-ID Dropdown-Menü
label_transport_id = ctk.CTkLabel(root, text=lang["Transport ID eingeben:"], font=("Arial", 14))
label_transport_id.pack(pady=(60, 10))
## \var dropdown_transport_id
#  \brief Dropdown-Menü zur Auswahl einer Transport-ID. 
#  \details Triggert \ref fetch_data beim Auswählen eines Eintrags.
dropdown_transport_id = ctk.CTkOptionMenu(
    root,
    values=transport_ids,
    font=("Arial", 12),
    width=600,
    fg_color="black",  # Hintergrundfarbe des drop down menu
    button_color="black",  # Farbe des Schalters
    button_hover_color="darkgray",  # Farbe wenn über den Schalter/Knopf gefahren wird
    text_color="white",  # Textfarbe
    command=lambda choice: fetch_data()  # Direkte Aufruf der Funktion nach Auswahl
)
dropdown_transport_id.pack(pady=(10, 20))

## \var frame_results
#  \brief Frame zur Anzeige der entschlüsselten Transportdaten.
frame_results = ctk.CTkFrame(root, width=1280, height=400)
frame_results.pack(pady=20, padx=20, fill="both", expand=True)

## \var button_language_1
#  \brief Sprachumschalter-Button (z. B. DE/EN)
button_language_1 = ctk.CTkButton(root, text="EN", command=set_english, width=50)
button_language_1.place(relx=1.0, rely=0.0, anchor="ne", x=-80, y=20)
## \var button_language_2
#  \brief Zweiter Sprachumschalter-Button (z. B. AR)
button_language_2 = ctk.CTkButton(root, text="AR", command=set_arabic, width=50)
button_language_2.place(relx=1.0, rely=0.0, anchor="ne", x=-20, y=20)

##
# \brief Startet die GUI-Anwendung.
root.mainloop()

