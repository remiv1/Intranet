#!/bin/sh

echo "⏳ Attente de la base de données MariaDB..."
while ! nc -z db 3306; do
  sleep 1
done

echo "✅ Base de données disponible !"
echo "🚀 Lancement de l'application Flask (run.py)..."
exec python app/run.py
