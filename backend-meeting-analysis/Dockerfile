FROM python:3.10-slim

WORKDIR /app

# Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code kopieren
COPY . .

# Standardport für Cloud Run
ENV PORT=8080

CMD ["python", "app.py"]
