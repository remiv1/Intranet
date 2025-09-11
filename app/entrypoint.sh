#!/bin/sh
echo "Attente de la base de données MariaDB..."
while ! nc -z db 3306; do
  sleep 1
done

echo "✅ Base de données disponible !"

# Remplacement dynamique de l'URL dans alembic.ini
if [ -n "$DB_URL" ]; then
  sed -i "s|^sqlalchemy.url =.*|sqlalchemy.url = $DB_URL|" /app/alembic.ini
fi

echo "🚀 Lancement de l'application Flask (run.py)..."
exec python app/run.py