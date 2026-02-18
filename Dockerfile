FROM python:3.13-slim

WORKDIR /app

# System deps for audio (Whisper), chromadb, and Google APIs
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    build-essential \
    libopus0 \
    libopus-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# audioop-lts backfills audioop removed in Python 3.13; needed by discord.py voice
RUN pip install --no-cache-dir audioop-lts "discord.py[voice]>=2.3.0" PyNaCl
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure data directory exists
RUN mkdir -p data/chroma_db
