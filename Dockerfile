# TalentMatch NLP Dockerfile
FROM python:3.9-slim

# Çalışma dizinini ayarla
WORKDIR /app

# Sistem bağımlılıklarını kur
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıklarını kopyala ve kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# spaCy modellerini indir
RUN python -m spacy download tr_core_news_sm
RUN python -m spacy download en_core_web_sm

# Uygulama kodunu kopyala
COPY . .

# Upload ve data klasörlerini oluştur
RUN mkdir -p uploads data

# Port'u aç
EXPOSE 8000

# Sağlık kontrolü
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Uygulamayı başlat
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
