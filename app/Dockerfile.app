FROM docker.io/library/python:3.14-slim-bookworm AS runtime

ARG APP_UID=10001
ARG APP_GID=10001

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    ca-certificates \
    curl \
    cups-client \
    libcairo2 \
    libcups2-dev \
    libffi-dev \
    libssl-dev \
    netcat-openbsd \
    pkg-config \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid "$APP_GID" app \
    && useradd --uid "$APP_UID" --gid "$APP_GID" --create-home --shell /usr/sbin/nologin app \
    && set -eu; \
        case "$(dpkg --print-architecture)" in \
            amd64) architecture=amd64; checksum=d2d7c97fbfefc763d5bbcbbb3f8d61f9dd3410ce5d05a737c414994b80b8cdd0 ;; \
            arm64) architecture=arm64; checksum=a1c0af9872e8de89a1ce5c1b596e26c42917d5a2cf914d98faee2e28156899e2 ;; \
            *) echo "Architecture Supercronic non prise en charge" >&2; exit 1 ;; \
        esac; \
        curl --fail --silent --show-error --location --retry 3 \
            --connect-timeout 10 --max-time 120 \
            "https://github.com/aptible/supercronic/releases/download/v0.2.50/supercronic-linux-${architecture}" \
            --output /usr/local/bin/supercronic; \
        echo "${checksum}  /usr/local/bin/supercronic" | sha256sum --check -; \
        chmod 0755 /usr/local/bin/supercronic

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app app/ ./app/
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app alembic/ ./alembic/

ENV FLASK_APP=app.application:peraudiere
ENV FLASK_ENV=production

FROM runtime AS test

COPY test/requirements.txt ./test/requirements.txt
RUN python -m pip install --no-cache-dir -r test/requirements.txt
COPY --chown=app:app test/ ./test/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHON_DOTENV_DISABLED=1

USER app
CMD ["python", "-m", "pytest", "-c", "test/pytest.ini", "test"]

FROM runtime AS production

COPY --chown=app:app .env ./

USER app
