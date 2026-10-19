FROM python:3.14-slim-bookworm

ARG APP_UID=10001
ARG APP_GID=10001

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    cups-client \
    libcairo2 \
    libcups2-dev \
    libffi-dev \
    libssl-dev \
    netcat-openbsd \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid "$APP_GID" app \
    && useradd --uid "$APP_UID" --gid "$APP_GID" --create-home --shell /usr/sbin/nologin app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app .env ./
COPY --chown=app:app app/ ./app/
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app alembic/ ./alembic/

ENV FLASK_APP=app.application:peraudiere
ENV FLASK_ENV=production

USER app
