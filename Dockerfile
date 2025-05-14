FROM python:3.11-slim

WORKDIR /app

# Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Für Health Checks benötigt
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Anwendungscode kopieren
COPY app.py .
COPY cal_utils/ ./cal_utils/

# Port freigeben
EXPOSE 8098

# Anwendung starten
CMD ["python", "app.py"]
