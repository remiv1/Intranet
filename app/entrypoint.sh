#!/bin/sh

echo "⏳ Attente de la base de données MariaDB..."
while ! nc -z db 3306; do
  sleep 1
done

echo "✅ Base de données disponible !"

echo "🚀 Lancement de l'application Flask avec Gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --workers "${GUNICORN_WORKERS:-2}" --access-logfile - --error-logfile - app.application:peraudiere
