from flask import Flask, request, jsonify
import requests
import logging # Importiere das logging-Modul
import os

app = Flask(__name__)

# --- Logging-Konfiguration ---
# Erstelle einen Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # Setze das allgemeine Log-Level auf DEBUG

# Erstelle einen Console Handler, der DEBUG-Nachrichten oder höher ausgibt
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG) # Dieser Handler soll DEBUG-Nachrichten anzeigen

# Erstelle einen Formatter und füge ihn dem Handler hinzu
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

# Füge den Handler dem Logger hinzu
logger.addHandler(ch)

# Optional: Wenn du auch in eine Datei loggen möchtest (nur für lokale Tests, im Container eher stdout)
# fh = logging.FileHandler('proxy_log.log')
# fh.setLevel(logging.INFO) # Dieser Handler soll INFO-Nachrichten oder höher in die Datei schreiben
# fh.setFormatter(formatter)
# logger.addHandler(fh)

# --- Zielserver-URL ---
# Dies löst einen KeyError aus, wenn TARGET_URL nicht gesetzt ist
TARGET_URL = os.environ['TARGET_URL']
logging.info(f"Proxy konfiguriert, um Anfragen an {TARGET_URL} weiterzuleiten.")


@app.route('/convert_and_forward', methods=['POST'])
def convert_and_forward():
    logger.info(f"Empfangener Request von {request.remote_addr} mit Content-Type: {request.headers.get('Content-Type')}")

    if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
        # Daten aus www-urlencoded extrahieren
        form_data = request.form.to_dict()
        logger.debug(f"Form-Daten extrahiert: {form_data}")

        # Daten in JSON umwandeln
        # Flask's jsonify gibt ein Response-Objekt zurück, wir wollen den String-Inhalt
        json_data = jsonify(form_data).get_data(as_text=True)
        logger.debug(f"Daten in JSON konvertiert: {json_data}")

        # JSON-Daten an den Zielserver weiterleiten
        try:
            headers = {'Content-Type': 'application/json'}
            logger.info(f"Leite JSON-Daten an Zielserver {TARGET_URL} weiter...")
            response = requests.post(TARGET_URL, data=json_data, headers=headers)
            response.raise_for_status()  # Löst einen HTTPError für schlechte Antworten (4xx oder 5xx) aus

            logger.info(f"Antwort vom Zielserver erhalten (Status {response.status_code}): {response.text}")
            return jsonify(response.json()), response.status_code

        except requests.exceptions.RequestException as e:
            logger.error(f"Fehler beim Weiterleiten an den Zielserver: {e}", exc_info=True) # exc_info=True für Stacktrace
            return jsonify({"error": f"Fehler beim Weiterleiten an den Zielserver: {e}"}), 500
    else:
        logger.warning(f"Untersstützter Content-Type '{request.headers.get('Content-Type')}' empfangen von {request.remote_addr}. Erwarte 'application/x-www-form-urlencoded'.")
        return jsonify({"error": "Unsupported Content-Type. Please use application/x-www-form-urlencoded."}), 400

if __name__ == '__main__':
    logger.info("Proxy-Server wird gestartet...")
    app.run(host='0.0.0.0', port=6000)