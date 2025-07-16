# Basis-Image
FROM python:3.9-slim-buster

# Arbeitsverzeichnis im Container setzen
WORKDIR /app

# Dependencies kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Skript kopieren
COPY app.py .

# Port exponieren, auf dem die Flask-App läuft
EXPOSE 6000

# Flask-App starten
CMD ["gunicorn","-b", "0.0.0.0:6000", "app:app"]
