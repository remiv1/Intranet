FROM python:3.12.11-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libcups2-dev \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    pkg-config \
    netcat-openbsd

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install waitress

COPY . .

ENV FLASK_APP=run.py
ENV FLASK_ENV=production
