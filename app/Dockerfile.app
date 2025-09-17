FROM python:3.12.11-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    cups-client \
    libcups2-dev \
    libffi-dev \
    libssl-dev \
    netcat-openbsd \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY .env ./ 
COPY app/ ./app/

ENV FLASK_APP=app/run.py
ENV FLASK_ENV=production
