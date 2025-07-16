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
TARGET_URL = os.environ.get('TARGET_URL')
if not TARGET_URL:
    logger.error("Umgebungsvariable 'TARGET_URL' ist nicht gesetzt. Bitte setze sie, z.B. export TARGET_URL=http://localhost:5000/ziel_endpunkt")
    exit(1) # Beende das Programm, wenn die URL fehlt

logger.info(f"Proxy konfiguriert, um Anfragen an {TARGET_URL} weiterzuleiten.")


@app.route('/convert_and_forward', methods=['POST'])
def convert_and_forward():
    logger.info(f"Empfangener Request von {request.remote_addr} mit Content-Type: {request.headers.get('Content-Type')}")

    if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
        # Daten aus www-urlencoded extrahieren
        form_data = request.form.to_dict()
        logger.debug(f"Form-Daten extrahiert: {form_data}")

        # Daten in JSON umwandeln
        json_data = jsonify(form_data).get_data(as_text=True)
        logger.debug(f"Daten in JSON konvertiert: {json_data}")

        # JSON-Daten an den Zielserver weiterleiten (Fire-and-Forget)
        try:
            headers = {'Content-Type': 'application/json'}
            logger.info(f"Leite JSON-Daten an Zielserver {TARGET_URL} weiter (Fire-and-Forget)...")
            # timeout=1 kann hier als schneller Timeout dienen, falls der Zielserver nicht erreichbar ist,
            # aber wir warten absichtlich nicht auf eine detaillierte Antwort.
            # verify=False ist nur für Testzwecke, in Produktion SSL-Verifizierung aktivieren!
            requests.post(TARGET_URL, data=json_data, headers=headers, timeout=1, verify=True)
            logger.info("Anfrage an Zielserver gesendet. Erwarte keine HTTP-Antwort.")
            # Rückmeldung an den ursprünglichen Absender, dass die Anfrage verarbeitet wurde
            return jsonify({"message": "Request received and forwarded to target server (fire-and-forget). Erfolgreich gesendet."}), 200

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout beim Senden an den Zielserver {TARGET_URL}. Dies ist beim Fire-and-Forget-Ansatz erwartet, wenn der Server langsam antwortet oder die Verbindung nicht sofort aufgebaut werden kann.")
            return jsonify({"message": "Request received and forwarded to target server (fire-and-forget). Send timeout."}), 200
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Verbindungsfehler beim Weiterleiten an den Zielserver {TARGET_URL}: {e}", exc_info=True)
            # Auch bei Verbindungsfehlern senden wir eine 200, da wir die Anfrage des Absenders "empfangen" haben
            # und versucht haben, sie weiterzuleiten. Der Absender soll nicht wissen, dass der Zielserver nicht erreichbar war.
            return jsonify({"message": f"Request received and forwarded to target server (fire-and-forget). Connection error: {e}"}), 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Unerwarteter Fehler beim Weiterleiten an den Zielserver: {e}", exc_info=True)
            return jsonify({"message": f"Request received and forwarded to target server (fire-and-forget). Unexpected error: {e}"}), 200
    else:
        logger.warning(f"Untersstützter Content-Type '{request.headers.get('Content-Type')}' empfangen von {request.remote_addr}. Erwarte 'application/x-www-form-urlencoded'.")
        return jsonify({"error": "Unsupported Content-Type. Please use application/x-www-form-urlencoded."}), 400

if __name__ == '__main__':
    logger.info("Proxy-Server wird gestartet...")
    app.run(host='0.0.0.0', port=6000)