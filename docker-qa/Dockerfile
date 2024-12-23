FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier l'application
COPY app.py .

# Télécharger le modèle
RUN python -c "from transformers import pipeline; pipeline('question-answering', model='etalab-ia/camembert-base-squadFR-fquad-piaf')"

EXPOSE 5000

CMD ["python", "app.py"] 